import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from openai import OpenAI
from config import Config
from database import Database
from confirmation_ai import ConfirmationAI
import os

class MessageProcessor:
    def __init__(self):
        try:
            self.db = Database()
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            self.db = None
            
        try:
            self.confirmation_ai = ConfirmationAI()
        except Exception as e:
            print(f"❌ Failed to initialize confirmation AI: {e}")
            self.confirmation_ai = None
        self.response_templates = {
            "confirm": "מעולה! רשמתי שלקחת את הגלולה. תישארי בריאה! 💪",
            "missed": "אל דאגה! קחי אותה בהקדם האפשרי. הבריאות שלך חשובה! 🏥",
            "help": "אני כאן כדי להזכיר לך לקחת את הגלולה יומית בשעה 8:00 בערב. את יכולה להגיב עם:\n- 'לקחתי' או 'כן' כדי לאשר שלקחת\n- 'החמצתי' אם החמצת\n- 'עזרה' להודעה הזו",
            "unknown": "לא הבנתי את זה. תכתבי 'עזרה' לפקודות זמינות."
        }
        
        # Initialize OpenAI if enabled
        if Config.OPENAI_ENABLED and Config.OPENAI_API_KEY:
            self.openai_enabled = True
            self.client = OpenAI(
                api_key=os.environ.get("OPENAI_API_KEY")
            )
            print("🤖 OpenAI integration enabled")
        else:
            self.openai_enabled = False
            print("🤖 OpenAI integration disabled - using template responses")
    
    def _get_ai_response(self, message_body: str, sender: str) -> Optional[str]:
        """
        Get AI-powered response using OpenAI
        
        Args:
            message_body: The user's message
            sender: The sender's phone number
            
        Returns:
            AI-generated response or None if AI fails
        """
        if not self.openai_enabled:
            return None
            
        try:
            system_prompt = """אתה עוזר אישי ידידותי לתזכורות גלולת מניעת הריון. התפקיד שלך הוא לעזור למשתמשות לנהל את הגלולה היומית שלהן.

תפקידים עיקריים:
- לאשר כשהמשתמשות לקחו את הגלולה
- לספק עידוד ותמיכה
- לטפל במינונים שהוחמצו בזהירות ודחיפות
- לענות על שאלות בנוגע לניהול הגלולה
- להיות אמפתי ומתמקד בבריאות

פעולות זמינות:
- 'לקחתי'/'כן' - המשתמשת מאשרת שלקחה את הגלולה
- 'החמצתי'/'לא' - המשתמשת החמיצה את המינון
- 'עזרה' - המשתמשת צריכה עזרה
- תגובות אחרות - לטפל באופן טבעי עם AI

שמור על תגובות:
- ידידותיות ותומכות
- פחות מ-200 תווים
- כולל אימוג'ים רלוונטיים
- מתמקד בבריאות ורווחה
- באותה שפה כמו הודעת המשתמשת

הקשר: זהו מערכת תזכורות יומיות לגלולה בשעה 8:00 בערב."""

            response = self.client.responses.create(
                model=Config.OPENAI_MODEL,
                instructions=system_prompt,
                input=message_body,
            )

            ai_response = response.output_text.strip()
            print(f"🤖 AI Response: {ai_response}")
            return ai_response
            
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return None
    
    def _classify_message_intent(self, message_body: str) -> str:
        """
        Classify the intent of the message for statistics
        
        Args:
            message_body: The user's message
            
        Returns:
            Intent classification
        """
        message_lower = message_body.lower().strip()
        
        # Check for confirmation patterns (Hebrew and English)
        confirm_patterns = ['taken', 'yes', 'done', 'ok', '✅', 'took', 'taken it', 'swallowed', 'consumed',
                           'לקחתי', 'כן', 'סיימתי', 'אוקיי', 'לקחת', 'בלעתי', 'גמרתי']
        if any(pattern in message_lower for pattern in confirm_patterns):
            return 'pill_confirmed'
        
        # Check for missed patterns (Hebrew and English)
        missed_patterns = ['missed', 'no', 'forgot', '❌', 'didn\'t', 'havent', 'haven\'t', 'forgotten',
                          'החמצתי', 'לא', 'שכחתי', 'לא לקחתי', 'לא לקחת', 'שכחת']
        if any(pattern in message_lower for pattern in missed_patterns):
            return 'pill_missed'
        
        # Check for help patterns (Hebrew and English)
        help_patterns = ['help', 'commands', '?', 'what', 'how', 'assist', 'support',
                        'עזרה', 'פקודות', 'מה', 'איך', 'תעזור', 'תמיכה', 'מה זה']
        if any(pattern in message_lower for pattern in help_patterns):
            return 'help_requested'
        
        return 'unknown_command'
    
    def _process_confirmation(self, message_body: str, sender: str) -> Optional[str]:
        """
        Process a message as a potential confirmation of taking the pill
        
        Args:
            message_body: The user's message
            sender: The sender's phone number
            
        Returns:
            Response message if this was a confirmation, None otherwise
        """
        try:
            # Get customer by phone number
            customer = self.db.get_customer_by_phone(sender)
            if not customer:
                print(f"📱 No customer found for phone number: {sender}")
                return None
            
            # Check if there's a pending daily reminder for today
            today = datetime.now(timezone.utc).date().isoformat()
            daily_reminder = self.db.get_daily_reminder(customer['id'], today)
            
            if not daily_reminder:
                print(f"📱 No pending reminder found for {sender} on {today}")
                return None
            
            if daily_reminder['confirmed']:
                print(f"📱 Reminder already confirmed for {sender} on {today}")
                return None
            
            # Use AI to analyze the confirmation
            confirmed, response_message = self.confirmation_ai.analyze_confirmation(message_body, sender)
            
            # Update the daily reminder with confirmation status
            self.db.update_daily_reminder_confirmation(
                customer_id=customer['id'],
                reminder_date=today,
                confirmed=confirmed,
                confirmation_message=message_body
            )
            
            # Stop escalations if user confirmed
            if confirmed:
                self.db.stop_escalations_for_customer(customer['id'], today)
                print(f"✅ Confirmation recorded for {sender} on {today} - escalations stopped")
            else:
                print(f"❌ Missed pill recorded for {sender} on {today}")
            
            return response_message
            
        except Exception as e:
            print(f"❌ Error processing confirmation: {e}")
            return None
    
    def process_message(self, message_data: Dict) -> Optional[str]:
        """
        Process incoming message and return appropriate response
        
        Args:
            message_data: Message data from Green API
            
        Returns:
            Response message to send back, or None if no response needed
        """
        try:
            # Extract message content
            if 'body' not in message_data:
                return None
            
            message_body = message_data['body'].strip()
            sender = message_data.get('senderData', {}).get('chatId', '').split('@')[0]
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Create message record
            message_record = {
                'sender': sender,
                'message': message_body,
                'timestamp': timestamp,
                'processed': True
            }
            
            # Check if this is a confirmation message
            confirmation_result = self._process_confirmation(message_body, sender)
            if confirmation_result:
                response = confirmation_result
                message_record['action'] = 'confirmation_processed'
            else:
                # Try AI processing first if enabled
                response = None
                if self.openai_enabled:
                    response = self._get_ai_response(message_body, sender)
                
                # Fallback to template-based processing if AI fails or is disabled
                if not response:
                    message_lower = message_body.lower().strip()
                    
                    # Check Hebrew and English patterns
                    if message_lower in ['taken', 'yes', 'done', 'ok', '✅', 'לקחתי', 'כן', 'סיימתי', 'אוקיי']:
                        response = self.response_templates['confirm']
                    elif message_lower in ['missed', 'no', 'forgot', '❌', 'החמצתי', 'לא', 'שכחתי']:
                        response = self.response_templates['missed']
                    elif message_lower in ['help', 'commands', '?', 'what', 'עזרה', 'פקודות', 'מה']:
                        response = self.response_templates['help']
                    else:
                        response = self.response_templates['unknown']
                
                # Classify the message intent for statistics
                message_record['action'] = self._classify_message_intent(message_body)
            
            message_record['ai_processed'] = self.openai_enabled and response != self.response_templates.get('unknown')
            
            # Store processed message in database
            message_record['response'] = response
            self.db.save_message(message_record)
            
            return response
            
        except Exception as e:
            print(f"Error processing message: {e}")
            return "Sorry, I encountered an error processing your message. Please try again."
    
    def get_message_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent message history
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of recent messages
        """
        return self.db.get_message_history(limit)
    
    def get_statistics(self) -> Dict:
        """
        Get message processing statistics
        
        Returns:
            Dictionary with statistics
        """
        stats = self.db.get_statistics()
        stats['ai_enabled'] = self.openai_enabled
        return stats
    
    def save_messages_to_file(self, filename: str = 'message_history.json'):
        """Save processed messages to a JSON file (legacy method for backup)"""
        try:
            messages = self.db.get_message_history(1000)  # Get last 1000 messages
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            print(f"Message history backup saved to {filename}")
        except Exception as e:
            print(f"Error saving message history backup: {e}")
    
    def load_messages_from_file(self, filename: str = 'message_history.json'):
        """Load processed messages from a JSON file (legacy method for migration)"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                messages = json.load(f)
            
            # Migrate old messages to database
            for message in messages:
                if 'response' not in message:
                    message['response'] = ''
                self.db.save_message(message)
            
            print(f"Migrated {len(messages)} messages from {filename} to database")
        except FileNotFoundError:
            print(f"Message history file {filename} not found. Starting with empty database.")
        except Exception as e:
            print(f"Error migrating message history: {e}") 