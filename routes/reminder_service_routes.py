from flask import Blueprint, jsonify, request

# Create blueprint
reminder_service_routes = Blueprint('reminder_service_routes', __name__)

# Global variables (will be set by main app)
message_processor = None

def set_globals(processor):
    """Set global variables from main app"""
    global message_processor
    message_processor = processor

@reminder_service_routes.route('/api/reminders/save', methods=['POST'])
def save_reminder():
    """Save a reminder to database (called by reminder service)"""
    if not message_processor:
        return jsonify({"error": "Message processor not initialized"}), 400
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        scheduled_time = data.get('scheduled_time')
        message = data.get('message')
        
        if not scheduled_time or not message:
            return jsonify({"error": "scheduled_time and message are required"}), 400
        
        # Save to database
        reminder_id = message_processor.db.save_reminder(scheduled_time, message)
        
        return jsonify({
            "success": True,
            "reminder_id": reminder_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@reminder_service_routes.route('/api/reminders/mark-sent', methods=['POST'])
def mark_reminder_sent():
    """Mark a reminder as sent (called by reminder service)"""
    if not message_processor:
        return jsonify({"error": "Message processor not initialized"}), 400
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        reminder_id = data.get('reminder_id')
        if not reminder_id:
            return jsonify({"error": "reminder_id is required"}), 400
        
        # Mark as sent in database
        message_processor.db.mark_reminder_sent(reminder_id)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@reminder_service_routes.route('/api/reminders/missed-info', methods=['POST'])
def get_missed_reminders_info():
    """Get missed reminders information (called by reminder service)"""
    if not message_processor:
        return jsonify({"error": "Message processor not initialized"}), 400
    
    try:
        data = request.get_json() or {}
        days_back = data.get('days_back', 7)
        
        # Get missed reminders from database
        missed_reminders = message_processor.db.get_missed_reminders(days_back)
        last_reminder_date = message_processor.db.get_last_reminder_date()
        
        return jsonify({
            "total_missed": len(missed_reminders),
            "missed_dates": [r['scheduled_date'] for r in missed_reminders if r.get('scheduled_date')],
            "last_sent": last_reminder_date
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@reminder_service_routes.route('/api/reminders/last-date')
def get_last_reminder_date():
    """Get the last reminder date (called by reminder service)"""
    if not message_processor:
        return jsonify({"error": "Message processor not initialized"}), 400
    
    try:
        last_reminder_date = message_processor.db.get_last_reminder_date()
        return jsonify({
            "last_reminder_date": last_reminder_date
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500 