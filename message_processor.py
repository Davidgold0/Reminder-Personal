import json
from datetime import datetime
from typing import Dict, List, Optional

class MessageProcessor:
    def __init__(self):
        self.processed_messages = []
        self.response_templates = {
            "confirm": "Great! I've recorded that you took your pill. Stay healthy! 💪",
            "missed": "No worries! Please take it as soon as possible. Your health is important! 🏥",
            "help": "I'm here to remind you to take your pill daily at 8:00 PM. You can respond with:\n- 'taken' or 'yes' to confirm you took it\n- 'missed' if you missed it\n- 'help' for this message",
            "unknown": "I didn't understand that. Type 'help' for available commands."
        }
    
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
            
            message_body = message_data['body'].lower().strip()
            sender = message_data.get('senderData', {}).get('chatId', '').split('@')[0]
            timestamp = datetime.now().isoformat()
            
            # Create message record
            message_record = {
                'sender': sender,
                'message': message_body,
                'timestamp': timestamp,
                'processed': True
            }
            
            # Process based on message content
            response = None
            
            if message_body in ['taken', 'yes', 'done', 'ok', '✅']:
                response = self.response_templates['confirm']
                message_record['action'] = 'pill_confirmed'
                
            elif message_body in ['missed', 'no', 'forgot', '❌']:
                response = self.response_templates['missed']
                message_record['action'] = 'pill_missed'
                
            elif message_body in ['help', 'commands', '?', 'what']:
                response = self.response_templates['help']
                message_record['action'] = 'help_requested'
                
            else:
                response = self.response_templates['unknown']
                message_record['action'] = 'unknown_command'
            
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
                'unknown_commands': 0
            }
        
        stats = {
            'total_messages': len(self.processed_messages),
            'pill_confirmed': 0,
            'pill_missed': 0,
            'help_requests': 0,
            'unknown_commands': 0
        }
        
        for msg in self.processed_messages:
            action = msg.get('action', 'unknown')
            if action in stats:
                stats[action] += 1
        
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