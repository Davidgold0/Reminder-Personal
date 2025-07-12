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
if initialize_app():
    update_route_globals()
    print("✅ App started successfully!")
else:
    print("❌ Failed to initialize app")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 