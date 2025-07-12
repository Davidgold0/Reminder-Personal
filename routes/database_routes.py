from flask import Blueprint, jsonify, request

# Create blueprint
database_routes = Blueprint('database_routes', __name__)

# Global variables (will be set by main app)
message_processor = None

def set_globals(processor):
    """Set global variables from main app"""
    global message_processor
    message_processor = processor

@database_routes.route('/api/database/stats')
def database_stats():
    """Get database statistics"""
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

@database_routes.route('/api/database/cleanup', methods=['POST'])
def cleanup_database():
    """Clean up old messages"""
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