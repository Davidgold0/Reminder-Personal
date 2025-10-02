from flask import Flask, render_template, jsonify, request
from datetime import datetime
import os

from config import Config
from green_api_client import GreenAPIClient
from message_processor import MessageProcessor

# Import route blueprints
from routes.app_control import app_control
from routes.reminder_routes import reminder_routes
from routes.ai_routes import ai_routes
from routes.webhook_routes import webhook_routes
from routes.database_routes import database_routes
from routes.reminder_service_routes import reminder_service_routes
from routes.customer_routes import customer_routes
from routes.confirmation_routes import confirmation_routes
from routes.escalation_routes import escalation_routes

app = Flask(__name__)

# Register blueprints
app.register_blueprint(app_control)
app.register_blueprint(reminder_routes)
app.register_blueprint(ai_routes)
app.register_blueprint(webhook_routes)
app.register_blueprint(database_routes)
app.register_blueprint(reminder_service_routes)
app.register_blueprint(customer_routes)
app.register_blueprint(confirmation_routes)
app.register_blueprint(escalation_routes)

# Global variables for the app
green_api = None
message_processor = None

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    try:
        # Check various components
        status = {
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'green_api': 'ok' if green_api is not None else 'not_initialized',
                'message_processor': 'ok' if message_processor is not None else 'not_initialized',
                'database': 'not_checked'
            }
        }
        
        # Test database connection if available
        if message_processor and message_processor.db:
            try:
                # Try a simple database operation
                with message_processor.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                status['components']['database'] = 'ok'
            except Exception as e:
                status['components']['database'] = f'error: {str(e)}'
        else:
            status['components']['database'] = 'not_initialized'
        
        # Determine overall status
        if all(comp in ['ok', 'not_checked'] for comp in status['components'].values()):
            return jsonify(status), 200
        else:
            status['status'] = 'degraded'
            return jsonify(status), 200
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/debug/config')
def debug_config():
    """Debug endpoint to check configuration (for development only)"""
    try:
        from config import Config
        
        # Only show this in development or if specifically enabled
        if not os.environ.get('DEBUG_CONFIG_ENABLED', 'false').lower() == 'true':
            return jsonify({
                'error': 'Debug endpoint disabled. Set DEBUG_CONFIG_ENABLED=true to enable.'
            }), 403
        
        config_info = {
            'database_url_exists': bool(Config.DATABASE_URL),
            'mysql_host': Config.MYSQL_HOST if Config.MYSQL_HOST else None,
            'mysql_port': Config.MYSQL_PORT,
            'mysql_database': Config.MYSQL_DATABASE if Config.MYSQL_DATABASE else None,
            'mysql_user': Config.MYSQL_USER if Config.MYSQL_USER else None,
            'mysql_password_set': bool(Config.MYSQL_PASSWORD),
            'use_mysql': Config.USE_MYSQL,
            'green_api_configured': bool(Config.GREEN_API_TOKEN and Config.GREEN_API_INSTANCE_ID),
            'webhook_enabled': Config.WEBHOOK_ENABLED,
            'openai_enabled': Config.OPENAI_ENABLED
        }
        
        return jsonify(config_info)
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

def initialize_app():
    """Initialize the app components"""
    global green_api, message_processor
    
    try:
        Config.validate_config()
        green_api = GreenAPIClient()
        
        # Check if WhatsApp instance is authorized
        if not green_api.is_instance_authorized():
            raise ValueError("WhatsApp instance is not authorized. Please check your Green API setup.")
        
        message_processor = MessageProcessor()
        
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

def update_route_globals():
    """Update global variables in all route modules"""
    from routes.app_control import set_globals as set_app_control_globals
    from routes.reminder_routes import set_globals as set_reminder_globals
    from routes.ai_routes import set_globals as set_ai_globals
    from routes.webhook_routes import set_globals as set_webhook_globals
    from routes.database_routes import set_globals as set_database_globals
    from routes.reminder_service_routes import set_globals as set_reminder_service_globals
    from routes.customer_routes import set_globals as set_customer_globals
    from routes.confirmation_routes import set_globals as set_confirmation_globals
    from routes.escalation_routes import set_globals as set_escalation_globals
    
    # Check if message_processor and its database are available
    if message_processor is None:
        print("⚠️ Warning: message_processor is None - database routes will not work")
        return
    
    if message_processor.db is None:
        print("⚠️ Warning: Database is None - database routes will not work")
        return
    
    # Update globals in each route module
    set_app_control_globals(message_processor)
    set_reminder_globals(message_processor)
    set_ai_globals(message_processor)
    set_webhook_globals(message_processor, green_api)
    set_database_globals(message_processor)
    set_reminder_service_globals(message_processor)
    set_customer_globals(message_processor.db)
    set_confirmation_globals(message_processor.db)
    set_escalation_globals(message_processor.db)

# Initialize app on startup
print("🚀 Initializing reminder app...")
initialization_success = initialize_app()
if initialization_success and message_processor is not None:
    update_route_globals()
    print("✅ App started successfully!")
else:
    print("❌ Failed to initialize app - some features may not work properly")
    print("❌ Database-dependent routes will return errors")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 