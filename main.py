#!/usr/bin/env python3
"""
Reminder App - Daily Pill Reminder using Green API
Sends daily reminders at 8:00 PM Israel time and processes incoming messages
"""

import time
import threading
from datetime import datetime
import pytz

from config import Config
from green_api_client import GreenAPIClient
from message_processor import MessageProcessor
from reminder_scheduler import ReminderScheduler

class ReminderApp:
    def __init__(self):
        # Validate configuration
        Config.validate_config()
        
        # Initialize components
        self.green_api = GreenAPIClient()
        self.message_processor = MessageProcessor()
        self.scheduler = ReminderScheduler()
        
        # Load existing message history
        self.message_processor.load_messages_from_file()
        
        # Threading control
        self.running = False
        self.message_thread = None
        
    def start_message_processing(self):
        """Start processing incoming messages in a separate thread"""
        print("Starting message processing...")
        
        while self.running:
            try:
                # Get notifications from Green API
                notifications = self.green_api.get_notifications()
                
                for notification in notifications:
                    if notification.get('receiptId'):
                        # Process the notification
                        if 'body' in notification:
                            response = self.message_processor.process_message(notification)
                            
                            if response:
                                # Send response back
                                sender = notification.get('senderData', {}).get('chatId', '').split('@')[0]
                                self.green_api.send_message(sender, response)
                                print(f"Processed message from {sender}: {notification['body']}")
                        
                        # Delete the notification
                        self.green_api.delete_notification(notification['receiptId'])
                
                # Save message history periodically
                if len(self.message_processor.processed_messages) % 10 == 0:
                    self.message_processor.save_messages_to_file()
                
                time.sleep(5)  # Check for new messages every 5 seconds
                
            except Exception as e:
                print(f"Error in message processing: {e}")
                time.sleep(10)  # Wait longer on error
    
    def start(self):
        """Start the reminder app"""
        print("🚀 Starting Reminder App...")
        print("=" * 50)
        
        # Check Green API instance state
        state = self.green_api.get_state_instance()
        print(f"Green API Instance State: {state}")
        
        # Setup and start scheduler
        self.scheduler.setup_schedule()
        
        # Start message processing in background thread
        self.running = True
        self.message_thread = threading.Thread(target=self.start_message_processing, daemon=True)
        self.message_thread.start()
        
        # Start scheduler in main thread
        self.scheduler.run_scheduler()
    
    def stop(self):
        """Stop the reminder app"""
        print("\n🛑 Stopping Reminder App...")
        self.running = False
        
        if self.message_thread:
            self.message_thread.join(timeout=5)
        
        # Save final message history
        self.message_processor.save_messages_to_file()
        print("Reminder App stopped.")
    
    def send_test_reminder(self):
        """Send a test reminder"""
        self.scheduler.send_test_reminder()
    
    def show_status(self):
        """Show current app status"""
        print("\n📊 Reminder App Status:")
        print("=" * 30)
        
        # Scheduler status
        status = self.scheduler.get_status()
        print(f"Next Reminder: {status['next_reminder']}")
        print(f"Last Reminder: {status['last_reminder_sent']}")
        print(f"Timezone: {status['timezone']}")
        print(f"Recipient: {status['recipient']}")
        print(f"Message: {status['message']}")
        
        # Message statistics
        stats = self.message_processor.get_statistics()
        print(f"\nMessage Statistics:")
        print(f"Total Messages: {stats['total_messages']}")
        print(f"Pill Confirmed: {stats['pill_confirmed']}")
        print(f"Pill Missed: {stats['pill_missed']}")
        print(f"Help Requests: {stats['help_requests']}")
        print(f"Unknown Commands: {stats['unknown_commands']}")
        
        # Recent messages
        recent = self.message_processor.get_message_history(5)
        if recent:
            print(f"\nRecent Messages:")
            for msg in recent[-5:]:
                print(f"- {msg['timestamp']}: {msg['message']} ({msg.get('action', 'unknown')})")

def main():
    """Main function with command-line interface"""
    app = ReminderApp()
    
    print("💊 Pill Reminder App")
    print("=" * 30)
    print("Commands:")
    print("  start    - Start the reminder app")
    print("  test     - Send a test reminder")
    print("  status   - Show app status")
    print("  help     - Show this help")
    print("  quit     - Exit the app")
    print()
    
    while True:
        try:
            command = input("Enter command: ").strip().lower()
            
            if command == 'start':
                try:
                    app.start()
                except KeyboardInterrupt:
                    app.stop()
                    break
                    
            elif command == 'test':
                app.send_test_reminder()
                
            elif command == 'status':
                app.show_status()
                
            elif command == 'help':
                print("Commands:")
                print("  start    - Start the reminder app")
                print("  test     - Send a test reminder")
                print("  status   - Show app status")
                print("  help     - Show this help")
                print("  quit     - Exit the app")
                
            elif command in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
                
            else:
                print("Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main() 