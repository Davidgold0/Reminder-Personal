#!/usr/bin/env python3
"""
Test script for AI message processing
Run this script to test the AI functionality without starting the full web app
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from message_processor import MessageProcessor

def test_ai_message(message):
    """Test AI message processing"""
    try:
        # Initialize message processor
        processor = MessageProcessor()
        
        # Create mock message data
        mock_message = {
            'body': message,
            'senderData': {
                'chatId': 'test_user@c.us'
            }
        }
        
        # Process the message
        response = processor.process_message(mock_message)
        
        if response:
            # Get the last processed message
            last_message = processor.processed_messages[-1] if processor.processed_messages else {}
            
            print(f"\n🤖 AI Test Results:")
            print(f"📝 Input Message: '{message}'")
            print(f"💬 Response: '{response}'")
            print(f"🔧 Processing Method: {'🤖 AI Processing' if last_message.get('ai_processed', False) else '📝 Template Response'}")
            print(f"🎯 Intent Classified: {last_message.get('action', 'unknown_command')}")
            print(f"🤖 AI Enabled: {processor.openai_enabled}")
            
            return True
        else:
            print("❌ No response generated")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function"""
    print("🤖 AI Message Processing Test")
    print("=" * 40)
    
    # Check if AI is enabled
    if not Config.OPENAI_ENABLED:
        print("⚠️  AI is disabled. Set OPENAI_ENABLED=true in your .env file")
        print("   The test will still work with template responses.")
    
    if not Config.OPENAI_API_KEY:
        print("⚠️  No OpenAI API key found. Set OPENAI_API_KEY in your .env file")
        print("   The test will still work with template responses.")
    
    print()
    
    # Test messages
    test_messages = [
        "I took my pill just now",
        "I forgot to take it yesterday", 
        "What time should I take my medicine?",
        "Yes, I took it",
        "No, I missed it",
        "Help me remember",
        "I'm feeling better today",
        "Can you remind me again?",
        "תודה לך על התזכורת"  # Hebrew: "Thank you for the reminder"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n🧪 Test {i}/{len(test_messages)}")
        print("-" * 30)
        test_ai_message(message)
        
        if i < len(test_messages):
            input("\nPress Enter to continue to next test...")
    
    print(f"\n✅ All tests completed!")
    print("💡 Try the web interface at http://localhost:5000 for interactive testing")

if __name__ == "__main__":
    main() 