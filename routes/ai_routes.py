from flask import Blueprint, jsonify, request

# Create blueprint
ai_routes = Blueprint('ai_routes', __name__)

# Global variables (will be set by main app)
message_processor = None

def set_globals(processor):
    """Set global variables from main app"""
    global message_processor
    message_processor = processor

@ai_routes.route('/api/test-ai-message', methods=['POST'])
def test_ai_message():
    """Test AI message processing"""
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