from flask import Blueprint, render_template, jsonify
from datetime import datetime, timezone

# Create blueprint
app_control = Blueprint('app_control', __name__)

# Global variables (will be set by main app)
message_processor = None

def set_globals(processor):
    """Set global variables from main app"""
    global message_processor
    message_processor = processor

@app_control.route('/')
def home():
    """Home page with app status"""
    try:
        # Get status information
        message_stats = message_processor.get_statistics() if message_processor else {}
        recent_messages = message_processor.get_message_history(5) if message_processor else []
        
        return render_template('home.html',
                             status="Running",
                             message_stats=message_stats,
                             recent_messages=recent_messages)
    except Exception as e:
        return render_template('home.html', 
                             status="Error", 
                             error=f"Error getting status: {e}")

@app_control.route('/api/status')
def api_status():
    """Get app status as JSON"""
    try:
        message_stats = message_processor.get_statistics() if message_processor else {}
        
        return jsonify({
            "running": True,
            "messages": message_stats
        })
    except Exception as e:
        return jsonify({
            "running": False,
            "error": str(e)
        })

@app_control.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})

@app_control.route('/cron-test')
def cron_test():
    """Simple endpoint for Railway cron to test connectivity"""
    return jsonify({
        "status": "cron_test_ok", 
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Cron can reach this endpoint"
    }) 