import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Green API Configuration
    GREEN_API_TOKEN = os.getenv('GREEN_API_TOKEN')
    GREEN_API_INSTANCE_ID = os.getenv('GREEN_API_INSTANCE_ID')
    
    # Recipient phone number (with country code, no +)
    RECIPIENT_PHONE = os.getenv('RECIPIENT_PHONE')
    
    # Reminder settings
    REMINDER_TIME = "20:00"  # 8:00 PM Israel time
    REMINDER_MESSAGE = "Time to take your pill! 💊"
    
    # Timezone
    TIMEZONE = "Asia/Jerusalem"
    
    # API endpoints
    GREEN_API_BASE_URL = "https://api.green-api.com"
    
    # Webhook settings
    WEBHOOK_ENABLED = os.getenv('WEBHOOK_ENABLED', 'false').lower() == 'true'
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
    WEBHOOK_TOKEN = os.getenv('WEBHOOK_TOKEN', 'your_webhook_token_here')
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        required_vars = [
            'GREEN_API_TOKEN', 
            'GREEN_API_INSTANCE_ID',
            'RECIPIENT_PHONE'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Validate webhook configuration if enabled
        if cls.WEBHOOK_ENABLED and not cls.WEBHOOK_URL:
            raise ValueError("WEBHOOK_ENABLED is true but WEBHOOK_URL is not set")
        
        return True 