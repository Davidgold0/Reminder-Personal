#!/usr/bin/env python3
"""
Test script for webhook functionality
This script simulates webhook notifications to test your webhook endpoint
"""

import requests
import json
import sys

def test_webhook(webhook_url, test_data=None):
    """
    Test webhook endpoint with sample data
    
    Args:
        webhook_url: The webhook URL to test
        test_data: Optional test data, uses default if not provided
    """
    
    if test_data is None:
        # Sample webhook notification data
        test_data = {
            "receiptId": 12345,
            "body": "taken",
            "timestamp": 1234567890,
            "senderData": {
                "chatId": "972501234567@c.us",
                "sender": "972501234567@c.us",
                "senderName": "Test User"
            },
            "messageData": {
                "typeMessage": "textMessage",
                "textMessageData": {
                    "textMessage": "taken"
                }
            }
        }
    
    try:
        print(f"🧪 Testing webhook at: {webhook_url}")
        print(f"📤 Sending test data: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook test successful!")
        else:
            print("❌ Webhook test failed!")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing webhook: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Main function to run webhook tests"""
    
    if len(sys.argv) < 2:
        print("Usage: python test_webhook.py <webhook_url>")
        print("Example: python test_webhook.py https://your-domain.com/webhook")
        sys.exit(1)
    
    webhook_url = sys.argv[1]
    
    # Test different message types
    test_cases = [
        {
            "name": "Pill Taken",
            "data": {
                "receiptId": 12345,
                "body": "taken",
                "timestamp": 1234567890,
                "senderData": {
                    "chatId": "972501234567@c.us",
                    "sender": "972501234567@c.us",
                    "senderName": "Test User"
                },
                "messageData": {
                    "typeMessage": "textMessage",
                    "textMessageData": {
                        "textMessage": "taken"
                    }
                }
            }
        },
        {
            "name": "Pill Missed",
            "data": {
                "receiptId": 12346,
                "body": "missed",
                "timestamp": 1234567891,
                "senderData": {
                    "chatId": "972501234567@c.us",
                    "sender": "972501234567@c.us",
                    "senderName": "Test User"
                },
                "messageData": {
                    "typeMessage": "textMessage",
                    "textMessageData": {
                        "textMessage": "missed"
                    }
                }
            }
        },
        {
            "name": "Help Request",
            "data": {
                "receiptId": 12347,
                "body": "help",
                "timestamp": 1234567892,
                "senderData": {
                    "chatId": "972501234567@c.us",
                    "sender": "972501234567@c.us",
                    "senderName": "Test User"
                },
                "messageData": {
                    "typeMessage": "textMessage",
                    "textMessageData": {
                        "textMessage": "help"
                    }
                }
            }
        }
    ]
    
    print("🧪 Starting webhook tests...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 50)
        test_webhook(webhook_url, test_case['data'])
        print("\n")
        
        # Small delay between tests
        import time
        time.sleep(1)

if __name__ == "__main__":
    main() 