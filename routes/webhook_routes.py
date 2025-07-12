from flask import Blueprint, jsonify, request
from config import Config

# Create blueprint
webhook_routes = Blueprint('webhook_routes', __name__)

# Global variables (will be set by main app)
message_processor = None
green_api = None

def set_globals(processor, api):
    """Set global variables from main app"""
    global message_processor, green_api
    message_processor = processor
    green_api = api

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

@webhook_routes.route('/webhook', methods=['POST'])
def webhook_handler():
    """Handle incoming webhook notifications from Green API"""
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

@webhook_routes.route('/api/webhook/status')
def webhook_status():
    """Get webhook configuration status"""
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

@webhook_routes.route('/api/webhook/setup', methods=['POST'])
def setup_webhook():
    """Set up webhook URL"""
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

@webhook_routes.route('/api/webhook/disable', methods=['POST'])
def disable_webhook():
    """Disable webhook"""
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