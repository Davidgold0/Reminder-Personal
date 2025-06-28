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

def initialize_app():
    """Initialize the app components"""
    global green_api, message_processor, scheduler
    
    try:
        Config.validate_config()
        green_api = GreenAPIClient()
        message_processor = MessageProcessor()
        scheduler = ReminderScheduler()
        
        # Load existing message history
        message_processor.load_messages_from_file()
        
        print("✅ App initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize app: {e}")
        return False

def start_message_processing():
    """Start processing incoming messages in background"""
    global app_running, message_processor, green_api
    
    print("🔄 Starting message processing...")
    
    while app_running:
        try:
            # Get notifications from Green API
            notifications = green_api.get_notifications()
            
            for notification in notifications:
                if notification.get('receiptId'):
                    # Process the notification
                    if 'body' in notification:
                        response = message_processor.process_message(notification)
                        
                        if response:
                            # Send response back
                            sender = notification.get('senderData', {}).get('chatId', '').split('@')[0]
                            green_api.send_message(sender, response)
                            print(f"📨 Processed message from {sender}: {notification['body']}")
                    
                    # Delete the notification
                    green_api.delete_notification(notification['receiptId'])
            
            # Save message history periodically
            if len(message_processor.processed_messages) % 10 == 0:
                message_processor.save_messages_to_file()
            
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
    global app_running, message_thread, scheduler
    
    if app_running:
        return jsonify({"success": False, "message": "App is already running"})
    
    try:
        if not initialize_app():
            return jsonify({"success": False, "message": "Failed to initialize app"})
        
        app_running = True
        
        # Start message processing in background thread
        message_thread = threading.Thread(target=start_message_processing, daemon=True)
        message_thread.start()
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
        scheduler_thread.start()
        
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
        
        # Save message history
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 