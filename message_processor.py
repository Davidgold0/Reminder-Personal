import json
from datetime import datetime
from typing import Dict, List, Optional
from openai import OpenAI
from config import Config
import os

class MessageProcessor:
    def __init__(self):
        self.processed_messages = []
        self.response_templates = {
            "confirm": "Great! I've recorded that you took your pill. Stay healthy! 💪",
            "missed": "No worries! Please take it as soon as possible. Your health is important! 🏥",
            "help": "I'm here to remind you to take your pill daily at 8:00 PM. You can respond with:\n- 'taken' or 'yes' to confirm you took it\n- 'missed' if you missed it\n- 'help' for this message",
            "unknown": "I didn't understand that. Type 'help' for available commands."
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
            system_prompt = """You are a friendly pill reminder assistant. Your role is to help users manage their daily pill medication.

Key responsibilities:
- Confirm when users have taken their pills
- Provide encouragement and support
- Handle missed doses with care and urgency
- Answer questions about medication management
- Be empathetic and health-focused

Available actions:
- 'taken'/'yes' - User confirms taking the pill
- 'missed'/'no' - User missed the dose
- 'help' - User needs assistance
- Other responses - Handle naturally with AI

Keep responses:
- Friendly and supportive
- Under 200 characters
- Include relevant emojis
- Focus on health and wellness
- In the same language as the user's message

Context: This is a daily pill reminder system for 8:00 PM."""

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
        
        # Check for confirmation patterns
        confirm_patterns = ['taken', 'yes', 'done', 'ok', '✅', 'took', 'taken it', 'swallowed', 'consumed']
        if any(pattern in message_lower for pattern in confirm_patterns):
            return 'pill_confirmed'
        
        # Check for missed patterns
        missed_patterns = ['missed', 'no', 'forgot', '❌', 'didn\'t', 'havent', 'haven\'t', 'forgotten']
        if any(pattern in message_lower for pattern in missed_patterns):
            return 'pill_missed'
        
        # Check for help patterns
        help_patterns = ['help', 'commands', '?', 'what', 'how', 'assist', 'support']
        if any(pattern in message_lower for pattern in help_patterns):
            return 'help_requested'
        
        return 'unknown_command'
    
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
            timestamp = datetime.now().isoformat()
            
            # Create message record
            message_record = {
                'sender': sender,
                'message': message_body,
                'timestamp': timestamp,
                'processed': True
            }
            
            # Try AI processing first if enabled
            response = None
            if self.openai_enabled:
                response = self._get_ai_response(message_body, sender)
            
            # Fallback to template-based processing if AI fails or is disabled
            if not response:
                message_lower = message_body.lower().strip()
                
                if message_lower in ['taken', 'yes', 'done', 'ok', '✅']:
                    response = self.response_templates['confirm']
                elif message_lower in ['missed', 'no', 'forgot', '❌']:
                    response = self.response_templates['missed']
                elif message_lower in ['help', 'commands', '?', 'what']:
                    response = self.response_templates['help']
                else:
                    response = self.response_templates['unknown']
            
            # Classify the message intent for statistics
            message_record['action'] = self._classify_message_intent(message_body)
            message_record['ai_processed'] = self.openai_enabled and response != self.response_templates.get('unknown')
            
            # Store processed message
            self.processed_messages.append(message_record)
            
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
        return self.processed_messages[-limit:] if self.processed_messages else []
    
    def get_statistics(self) -> Dict:
        """
        Get message processing statistics
        
        Returns:
            Dictionary with statistics
        """
        if not self.processed_messages:
            return {
                'total_messages': 0,
                'pill_confirmed': 0,
                'pill_missed': 0,
                'help_requests': 0,
                'unknown_commands': 0,
                'ai_processed': 0,
                'ai_enabled': self.openai_enabled
            }
        
        stats = {
            'total_messages': len(self.processed_messages),
            'pill_confirmed': 0,
            'pill_missed': 0,
            'help_requests': 0,
            'unknown_commands': 0,
            'ai_processed': 0,
            'ai_enabled': self.openai_enabled
        }
        
        for msg in self.processed_messages:
            action = msg.get('action', 'unknown')
            if action in stats:
                stats[action] += 1
            
            # Count AI-processed messages
            if msg.get('ai_processed', False):
                stats['ai_processed'] += 1
        
        return stats
    
    def save_messages_to_file(self, filename: str = 'message_history.json'):
        """Save processed messages to a JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.processed_messages, f, indent=2, ensure_ascii=False)
            print(f"Message history saved to {filename}")
        except Exception as e:
            print(f"Error saving message history: {e}")
    
    def load_messages_from_file(self, filename: str = 'message_history.json'):
        """Load processed messages from a JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.processed_messages = json.load(f)
            print(f"Message history loaded from {filename}")
        except FileNotFoundError:
            print(f"Message history file {filename} not found. Starting with empty history.")
        except Exception as e:
            print(f"Error loading message history: {e}") 