from flask import Blueprint, jsonify, request
from config import Config

# Create blueprint
reminder_routes = Blueprint('reminder_routes', __name__)

# Global variables (will be set by main app)
message_processor = None

def set_globals(processor):
    """Set global variables from main app"""
    global message_processor
    message_processor = processor

@reminder_routes.route('/api/test-reminder', methods=['POST'])
def test_reminder():
    """Send a test reminder (legacy endpoint - use /api/send-reminder instead)"""
    return send_reminder()

@reminder_routes.route('/api/test-ai-reminder', methods=['POST'])
def test_ai_reminder():
    """Test AI reminder message generation"""
    try:
        # Import and use the reminder logic
        from reminder.reminder_logic import ReminderLogic
        logic = ReminderLogic()
        
        # Generate AI message without sending
        ai_message = logic.generate_ai_reminder_message()
        
        return jsonify({
            "success": True,
            "message": ai_message,
            "ai_enabled": logic.openai_enabled,
            "is_ai_generated": ai_message != Config.REMINDER_MESSAGE
        })
    except Exception as e:
        print(f"❌ Error testing AI reminder: {e}")
        return jsonify({"success": False, "error": f"Error generating AI reminder: {str(e)}"})

@reminder_routes.route('/api/send-reminder', methods=['POST'])
def send_reminder():
    """Send daily reminder (called by Railway cron or manual test)"""
    try:
        # Import and use the reminder logic
        from reminder.reminder_logic import ReminderLogic
        logic = ReminderLogic()
        
        # Process the reminder request
        result = logic.process_reminder_request()
        
        if result["status"] == "success":
            return jsonify({
                "success": True,
                "message": result["message"],
                "type": result.get("type", "unknown")
            })
        else:
            return jsonify({"success": False, "error": result["message"]})
            
    except Exception as e:
        print(f"❌ Error sending reminder: {e}")
        return jsonify({"success": False, "error": f"Error sending reminder: {str(e)}"})

@reminder_routes.route('/api/check-missed-reminders', methods=['POST'])
def check_missed_reminders():
    """Manually check for missed reminders"""
    try:
        from reminder.reminder_logic import ReminderLogic
        logic = ReminderLogic()
        
        # Get missed reminders info
        missed_info = logic.get_missed_reminders_info()
        
        # Try to send missed reminder
        missed_sent = logic.check_missed_reminders()
        
        return jsonify({
            "success": True,
            "missed_sent": missed_sent,
            "missed_info": missed_info,
            "message": "Missed reminders checked"
        })
        
    except Exception as e:
        print(f"❌ Error checking missed reminders: {e}")
        return jsonify({"success": False, "error": f"Error checking missed reminders: {str(e)}"})

@reminder_routes.route('/api/reminder/trigger', methods=['POST'])
def trigger_reminder():
    """Trigger reminder logic (called by reminder service)"""
    try:
        # Import and use the reminder logic
        from reminder.reminder_logic import ReminderLogic
        logic = ReminderLogic()
        
        # Process the reminder request
        result = logic.process_reminder_request()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error triggering reminder: {e}")
        return jsonify({"error": f"Error triggering reminder: {str(e)}"}), 500 