from flask import Blueprint, request, jsonify
from database import Database
from escalation_logic import EscalationLogic
from datetime import datetime, timezone

escalation_routes = Blueprint('escalation_routes', __name__)

# Global variables
db = None
escalation_logic = None

def set_globals(database):
    """Set global variables for this route module"""
    global db, escalation_logic
    db = database
    escalation_logic = EscalationLogic()

@escalation_routes.route('/api/escalation/check', methods=['POST'])
def check_and_send_escalations():
    """Check for reminders that need escalation and send them"""
    try:
        # Get reminders that need escalation
        reminders_needing_escalation = db.get_reminders_needing_escalation()
        
        if not reminders_needing_escalation:
            return jsonify({
                'success': True,
                'message': 'No reminders need escalation',
                'escalations_sent': 0
            })
        
        print(f"🚨 Found {len(reminders_needing_escalation)} reminders needing escalation")
        
        escalations_sent = 0
        failed_escalations = 0
        
        for reminder in reminders_needing_escalation:
            try:
                # Check if we should stop escalating
                if escalation_logic.should_stop_escalating(reminder):
                    print(f"⏹️ Stopping escalation for {reminder['phone_number']} - conditions met")
                    continue
                
                # Send escalation
                success = escalation_logic.send_escalation(reminder)
                
                if success:
                    # Update escalation level in database
                    current_time = datetime.now(timezone.utc)
                    next_escalation_time = escalation_logic.calculate_next_escalation_time(
                        current_time, 
                        reminder['escalation_level'] + 1
                    )
                    
                    # Get the escalation message that was sent
                    escalation_message = escalation_logic.generate_escalation_message(
                        reminder['escalation_level'] + 1,
                        reminder.get('customer_name')
                    )
                    
                    # Update database
                    db.update_escalation(
                        reminder_id=reminder['id'],
                        escalation_level=reminder['escalation_level'] + 1,
                        next_escalation_time=next_escalation_time,
                        escalation_message=escalation_message
                    )
                    
                    escalations_sent += 1
                    print(f"✅ Escalation sent and recorded for {reminder['phone_number']}")
                else:
                    failed_escalations += 1
                    print(f"❌ Failed to send escalation for {reminder['phone_number']}")
                    
            except Exception as e:
                failed_escalations += 1
                print(f"❌ Error processing escalation for {reminder['phone_number']}: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Escalation check completed',
            'escalations_sent': escalations_sent,
            'failed_escalations': failed_escalations,
            'total_checked': len(reminders_needing_escalation)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@escalation_routes.route('/api/escalation/stats', methods=['GET'])
def get_escalation_stats():
    """Get escalation statistics"""
    try:
        days_back = request.args.get('days_back', 30, type=int)
        stats = db.get_escalation_stats(days_back)
        
        return jsonify({
            'success': True,
            'stats': stats,
            'days_back': days_back
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@escalation_routes.route('/api/escalation/pending', methods=['GET'])
def get_pending_escalations():
    """Get reminders that are pending escalation"""
    try:
        reminders_needing_escalation = db.get_reminders_needing_escalation()
        
        # Filter out reminders that should stop escalating
        pending_escalations = []
        for reminder in reminders_needing_escalation:
            if not escalation_logic.should_stop_escalating(reminder):
                pending_escalations.append(reminder)
        
        return jsonify({
            'success': True,
            'pending_escalations': pending_escalations,
            'count': len(pending_escalations)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@escalation_routes.route('/api/escalation/test/<int:escalation_level>', methods=['POST'])
def test_escalation_message(escalation_level):
    """Test escalation message generation"""
    try:
        data = request.get_json() or {}
        customer_name = data.get('customer_name')
        
        if escalation_level < 1 or escalation_level > 4:
            return jsonify({
                'success': False,
                'error': 'Escalation level must be between 1 and 4'
            }), 400
        
        # Generate test escalation message
        escalation_message = escalation_logic.generate_escalation_message(escalation_level, customer_name)
        
        return jsonify({
            'success': True,
            'escalation_level': escalation_level,
            'message': escalation_message,
            'ai_enabled': escalation_logic.openai_enabled
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 