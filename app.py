from flask import Flask, render_template, jsonify, request
import threading
import time
import schedule
import pytz
from datetime import datetime
import os

from config import Config
from green_api_client import GreenAPIClient
from message_processor import MessageProcessor
from reminder_scheduler import ReminderScheduler

app = Flask(__name__)

# Global variables for the app
green_api = None
message_processor = None
scheduler = None
app_running = False
message_thread = None
scheduler_thread = None

def extract_message_content(notification):
    """Extract message content from Green API notification structure"""
    # Handle different message types
    if 'body' in notification:
        # Legacy format or direct body
        return notification['body']
    
    # New webhook format
    if 'messageData' in notification:
        message_data = notification['messageData']
        
        # Extended text message
        if 'extendedTextMessageData' in message_data:
            return message_data['extendedTextMessageData'].get('text', '')
        
        # Text message
        if 'textMessageData' in message_data:
            return message_data['textMessageData'].get('textMessage', '')
        
        # Other message types can be added here as needed
        print(f"⚠️ Unsupported message type: {message_data.get('typeMessage', 'unknown')}")
        return ''
    
    return ''

def initialize_app():
    """Initialize the app components"""
    global green_api, message_processor, scheduler
    
    try:
        Config.validate_config()
        green_api = GreenAPIClient()
        
        # Check if WhatsApp instance is authorized
        if not green_api.is_instance_authorized():
            raise ValueError("WhatsApp instance is not authorized. Please check your Green API setup.")
        
        message_processor = MessageProcessor()
        scheduler = ReminderScheduler()
        
        # Load existing message history (migrate from file if exists)
        message_processor.load_messages_from_file()
        
        # Set up webhook if enabled
        if Config.WEBHOOK_ENABLED:
            webhook_url = f"{Config.WEBHOOK_URL}/webhook"
            result = green_api.set_webhook_url(webhook_url)
            if 'error' not in result:
                print(f"✅ Webhook set successfully: {webhook_url}")
            else:
                print(f"⚠️ Warning: Failed to set webhook: {result['error']}")
        
        print("✅ App initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize app: {e}")
        return False

def start_background_services():
    """Start message processing and scheduler in background threads"""
    global app_running, message_thread, scheduler_thread
    
    if app_running:
        print("⚠️ App is already running")
        return False
    
    try:
        app_running = True
        
        # Start message processing in background thread
        message_thread = threading.Thread(target=start_message_processing, daemon=True)
        message_thread.start()
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
        scheduler_thread.start()
        
        print("✅ Background services started successfully")
        return True
    except Exception as e:
        print(f"❌ Error starting background services: {e}")
        app_running = False
        return False

def start_message_processing():
    """Start processing incoming messages in background"""
    global app_running, message_processor, green_api
    
    print("🔄 Starting message processing...")
    
    # If webhooks are enabled, we don't need polling
    if Config.WEBHOOK_ENABLED:
        print("📡 Webhooks enabled - using real-time notifications")
        while app_running:
            time.sleep(10)  # Just keep the thread alive
        return
    
    print("🔄 Using polling mode for message processing")
    while app_running:
        try:
            # Check if there are notifications available first
            if green_api.check_notifications_available():
                # Get notifications from Green API using correct endpoint
                notifications = green_api.get_notifications()
                
                for notification in notifications:
                    if notification.get('receiptId'):
                        # Extract message content
                        message_content = extract_message_content(notification)
                        
                        if message_content:
                            # Check if the message is from the authorized recipient
                            sender_chat_id = notification.get('senderData', {}).get('chatId', '')
                            sender_phone = sender_chat_id.split('@')[0] if '@' in sender_chat_id else sender_chat_id
                            
                            if sender_phone != Config.RECIPIENT_PHONE:
                                print(f"🚫 Ignoring message from unauthorized sender: {sender_phone} (expected: {Config.RECIPIENT_PHONE})")
                                # Still delete the notification to avoid processing it again
                                green_api.delete_notification(notification['receiptId'])
                                continue
                            
                            # Create a standardized notification structure for the message processor
                            processed_notification = {
                                'body': message_content,
                                'senderData': notification.get('senderData', {}),
                                'receiptId': notification.get('receiptId')
                            }
                            
                            response = message_processor.process_message(processed_notification)
                            
                            if response:
                                # Send response back
                                green_api.send_message(sender_phone, response)
                                print(f"📨 Processed message from {sender_phone}: {message_content}")
                        
                        # Delete the notification after processing
                        green_api.delete_notification(notification['receiptId'])
                
                # Clean up old messages periodically (every 100 messages)
                if len(message_processor.get_message_history(1000)) % 100 == 0:
                    message_processor.db.cleanup_old_messages(days_to_keep=90)
            
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            print(f"❌ Error in message processing: {e}")
            time.sleep(10)

def start_scheduler():
    """Start the reminder scheduler"""
    global scheduler
    
    print("⏰ Starting reminder scheduler...")
    scheduler.setup_schedule()
    
    while app_running:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            print(f"❌ Scheduler error: {e}")
            time.sleep(60)

@app.route('/')
def home():
    """Home page with app status"""
    global app_running, green_api, message_processor, scheduler
    
    if not app_running:
        return render_template('home.html', 
                             status="Stopped", 
                             error="App not running. Click 'Start App' to begin.")
    
    try:
        # Get status information
        scheduler_status = scheduler.get_status() if scheduler else {}
        message_stats = message_processor.get_statistics() if message_processor else {}
        recent_messages = message_processor.get_message_history(5) if message_processor else []
        
        return render_template('home.html',
                             status="Running",
                             scheduler_status=scheduler_status,
                             message_stats=message_stats,
                             recent_messages=recent_messages)
    except Exception as e:
        return render_template('home.html', 
                             status="Error", 
                             error=f"Error getting status: {e}")

@app.route('/api/start', methods=['POST'])
def start_app():
    """Start the reminder app"""
    if app_running:
        return jsonify({"success": False, "message": "App is already running"})
    
    try:
        if not initialize_app():
            return jsonify({"success": False, "message": "Failed to initialize app"})
        
        if not start_background_services():
            return jsonify({"success": False, "message": "Failed to start background services"})
        
        return jsonify({"success": True, "message": "App started successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error starting app: {e}"})

@app.route('/api/stop', methods=['POST'])
def stop_app():
    """Stop the reminder app"""
    global app_running, message_processor
    
    if not app_running:
        return jsonify({"success": False, "message": "App is not running"})
    
    try:
        app_running = False
        
        # Wait for threads to finish (with timeout)
        if message_thread and message_thread.is_alive():
            message_thread.join(timeout=5)
        if scheduler_thread and scheduler_thread.is_alive():
            scheduler_thread.join(timeout=5)
        
        # Save message history backup
        if message_processor:
            message_processor.save_messages_to_file()
        
        return jsonify({"success": True, "message": "App stopped successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error stopping app: {e}"})

@app.route('/api/test-reminder', methods=['POST'])
def test_reminder():
    """Send a test reminder"""
    global scheduler, app_running
    
    if not app_running:
        return jsonify({"success": False, "message": "App is not running"})
    
    try:
        scheduler.send_test_reminder()
        return jsonify({"success": True, "message": "Test reminder sent"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error sending test reminder: {e}"})

@app.route('/api/test-ai-reminder', methods=['POST'])
def test_ai_reminder():
    """Test AI reminder message generation"""
    global scheduler, app_running
    
    if not app_running:
        return jsonify({"success": False, "error": "App is not running"})
    
    if not scheduler:
        return jsonify({"success": False, "error": "Scheduler not initialized"})
    
    try:
        # Generate AI message without sending
        ai_message = scheduler.generate_ai_reminder_message()
        
        return jsonify({
            "success": True,
            "message": ai_message,
            "ai_enabled": scheduler.openai_enabled,
            "is_ai_generated": ai_message != Config.REMINDER_MESSAGE
        })
    except Exception as e:
        print(f"❌ Error testing AI reminder: {e}")
        return jsonify({"success": False, "error": f"Error generating AI reminder: {str(e)}"})

@app.route('/api/test-ai-message', methods=['POST'])
def test_ai_message():
    """Test AI message processing"""
    global message_processor, app_running
    
    if not app_running:
        return jsonify({"success": False, "error": "App is not running"})
    
    if not message_processor:
        return jsonify({"success": False, "error": "Message processor not initialized"})
    
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"success": False, "error": "Message is required"})
        
        test_message = data['message'].strip()
        if not test_message:
            return jsonify({"success": False, "error": "Message cannot be empty"})
        
        # Create a mock message data structure similar to what Green API sends
        mock_message_data = {
            'body': test_message,
            'senderData': {
                'chatId': 'test_user@c.us'
            }
        }
        
        # Process the message using the message processor
        response = message_processor.process_message(mock_message_data)
        
        if response:
            # Get the last processed message to extract intent and AI processing info
            last_message = message_processor.processed_messages[-1] if message_processor.processed_messages else {}
            
            return jsonify({
                "success": True,
                "response": response,
                "ai_processed": last_message.get('ai_processed', False),
                "intent": last_message.get('action', 'unknown_command'),
                "ai_enabled": message_processor.openai_enabled
            })
        else:
            return jsonify({"success": False, "error": "No response generated"})
            
    except Exception as e:
        print(f"❌ Error testing AI message: {e}")
        return jsonify({"success": False, "error": f"Error processing message: {str(e)}"})

@app.route('/api/status')
def api_status():
    """Get app status as JSON"""
    global app_running, scheduler, message_processor
    
    if not app_running:
        return jsonify({
            "running": False,
            "message": "App is not running"
        })
    
    try:
        scheduler_status = scheduler.get_status() if scheduler else {}
        message_stats = message_processor.get_statistics() if message_processor else {}
        
        return jsonify({
            "running": True,
            "scheduler": scheduler_status,
            "messages": message_stats
        })
    except Exception as e:
        return jsonify({
            "running": False,
            "error": str(e)
        })

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """Handle incoming webhook notifications from Green API"""
    global message_processor, green_api
    
    try:
        # Get the notification data
        notification = request.get_json()
        
        if not notification:
            return jsonify({"error": "No data received"}), 400
        
        print(f"📨 Received webhook notification: {notification}")
        
        # Extract message content
        message_content = extract_message_content(notification)
        
        if message_content:
            # Check if the message is from the authorized recipient
            sender_chat_id = notification.get('senderData', {}).get('chatId', '')
            sender_phone = sender_chat_id.split('@')[0] if '@' in sender_chat_id else sender_chat_id
            
            if sender_phone != Config.RECIPIENT_PHONE:
                print(f"🚫 Ignoring message from unauthorized sender: {sender_phone} (expected: {Config.RECIPIENT_PHONE})")
                return jsonify({"success": True, "message": "Unauthorized sender ignored"}), 200
            
            # Create a standardized notification structure for the message processor
            processed_notification = {
                'body': message_content,
                'senderData': notification.get('senderData', {}),
                'receiptId': notification.get('receiptId') or notification.get('idMessage')
            }
            
            response = message_processor.process_message(processed_notification)
            
            if response:
                # Send response back
                green_api.send_message(sender_phone, response)
                print(f"📨 Processed webhook message from {sender_phone}: {message_content}")
            
            # Delete the notification if we have a receiptId (for polling mode)
            receipt_id = notification.get('receiptId')
            if receipt_id:
                green_api.delete_notification(receipt_id)
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/webhook/status')
def webhook_status():
    """Get webhook configuration status"""
    global green_api
    
    if not green_api:
        return jsonify({"error": "Green API client not initialized"}), 400
    
    try:
        settings = green_api.get_webhook_settings()
        return jsonify({
            "webhook_enabled": Config.WEBHOOK_ENABLED,
            "webhook_url": Config.WEBHOOK_URL,
            "current_settings": settings
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/webhook/setup', methods=['POST'])
def setup_webhook():
    """Set up webhook URL"""
    global green_api
    
    if not green_api:
        return jsonify({"error": "Green API client not initialized"}), 400
    
    try:
        data = request.get_json()
        webhook_url = data.get('webhook_url')
        
        if not webhook_url:
            return jsonify({"error": "webhook_url is required"}), 400
        
        result = green_api.set_webhook_url(webhook_url)
        
        if 'error' not in result:
            return jsonify({"success": True, "message": "Webhook set successfully"})
        else:
            return jsonify({"error": result['error']}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/webhook/disable', methods=['POST'])
def disable_webhook():
    """Disable webhook"""
    global green_api
    
    if not green_api:
        return jsonify({"error": "Green API client not initialized"}), 400
    
    try:
        result = green_api.delete_webhook_url()
        
        if 'error' not in result:
            return jsonify({"success": True, "message": "Webhook disabled successfully"})
        else:
            return jsonify({"error": result['error']}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/database/stats')
def database_stats():
    """Get database statistics"""
    global message_processor
    
    if not message_processor:
        return jsonify({"error": "Message processor not initialized"}), 400
    
    try:
        db = message_processor.db
        stats = db.get_statistics()
        db_size = db.get_database_size()
        
        return jsonify({
            "database_size_bytes": db_size,
            "database_size_mb": round(db_size / (1024 * 1024), 2),
            "statistics": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/database/cleanup', methods=['POST'])
def cleanup_database():
    """Clean up old messages"""
    global message_processor
    
    if not message_processor:
        return jsonify({"error": "Message processor not initialized"}), 400
    
    try:
        data = request.get_json() or {}
        days_to_keep = data.get('days_to_keep', 90)
        
        db = message_processor.db
        db.cleanup_old_messages(days_to_keep)
        
        return jsonify({
            "success": True, 
            "message": f"Cleaned up messages older than {days_to_keep} days"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# Auto-start the app when the module is loaded (for production deployment)
def auto_start_app():
    """Automatically start the app when the module is loaded"""
    import time
    
    print("🚀 Auto-starting reminder app...")
    
    # Wait a moment for the web server to start
    time.sleep(2)
    
    try:
        if initialize_app():
            if start_background_services():
                print("✅ App auto-started successfully!")
            else:
                print("❌ Failed to start background services")
        else:
            print("❌ Failed to initialize app")
    except Exception as e:
        print(f"❌ Error during auto-start: {e}")

# Start the app automatically when deployed
if os.environ.get('AUTO_START', 'true').lower() == 'true':
    # Use a separate thread to avoid blocking the web server startup
    auto_start_thread = threading.Thread(target=auto_start_app, daemon=True)
    auto_start_thread.start() 