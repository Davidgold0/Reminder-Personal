#!/usr/bin/env python3
"""
Test script for the escalation system
"""

import os
import sys
import requests
from datetime import datetime, timedelta
import pytz

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database import Database
from escalation_logic import EscalationLogic

def test_escalation_logic():
    """Test the escalation logic"""
    print("🧪 Testing Escalation Logic...")
    
    # Initialize escalation logic
    escalation_logic = EscalationLogic()
    
    # Test message generation for each level
    for level in range(1, 5):
        print(f"\n--- Testing Level {level} ---")
        message = escalation_logic.generate_escalation_message(level, "Test User")
        print(f"Level {level} message: {message}")
    
    # Test with no customer name
    print(f"\n--- Testing Level 1 (no name) ---")
    message = escalation_logic.generate_escalation_message(1)
    print(f"Level 1 message (no name): {message}")
    
    print("\n✅ Escalation logic tests completed")

def test_database_escalation_methods():
    """Test database escalation methods"""
    print("\n🗄️ Testing Database Escalation Methods...")
    
    db = Database()
    
    # Test getting reminders needing escalation
    reminders = db.get_reminders_needing_escalation()
    print(f"Found {len(reminders)} reminders needing escalation")
    
    # Test escalation stats
    stats = db.get_escalation_stats(7)  # Last 7 days
    print(f"Escalation stats: {stats}")
    
    print("✅ Database escalation methods tests completed")

def test_escalation_api():
    """Test escalation API endpoints"""
    print("\n🌐 Testing Escalation API...")
    
    base_url = "http://localhost:5000"
    
    # Test escalation stats
    try:
        response = requests.get(f"{base_url}/api/escalation/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Escalation stats API: {data}")
        else:
            print(f"❌ Escalation stats API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Escalation stats API error: {e}")
    
    # Test pending escalations
    try:
        response = requests.get(f"{base_url}/api/escalation/pending")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Pending escalations API: {data}")
        else:
            print(f"❌ Pending escalations API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Pending escalations API error: {e}")
    
    # Test escalation check
    try:
        response = requests.post(f"{base_url}/api/escalation/check")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Escalation check API: {data}")
        else:
            print(f"❌ Escalation check API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Escalation check API error: {e}")
    
    # Test escalation message generation
    try:
        response = requests.post(f"{base_url}/api/escalation/test/2", 
                               json={"customer_name": "Test User"})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Escalation test API: {data}")
        else:
            print(f"❌ Escalation test API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Escalation test API error: {e}")
    
    print("✅ Escalation API tests completed")

def test_escalation_flow():
    """Test the complete escalation flow"""
    print("\n🔄 Testing Complete Escalation Flow...")
    
    db = Database()
    escalation_logic = EscalationLogic()
    
    # Get current time
    israel_tz = pytz.timezone(Config.TIMEZONE)
    current_time = datetime.now(israel_tz)
    
    # Create a test reminder that needs escalation
    print("Creating test reminder...")
    
    # Get a customer
    customers = db.get_customers()
    if not customers:
        print("❌ No customers found for testing")
        return
    
    customer = customers[0]
    print(f"Using customer: {customer['name']} ({customer['phone_number']})")
    
    # Create a test daily reminder
    reminder_date = current_time.date().isoformat()
    reminder_time = current_time.strftime('%H:%M')
    test_message = "Test reminder message"
    
    try:
        # Create daily reminder
        reminder_id = db.create_daily_reminder(
            customer_id=customer['id'],
            reminder_date=reminder_date,
            reminder_time=reminder_time,
            message_sent=test_message
        )
        
        # Set escalation time to 30 minutes ago (so it needs escalation)
        past_time = (current_time - timedelta(minutes=30)).isoformat()
        db.update_escalation_level(
            reminder_id=reminder_id,
            escalation_level=0,
            escalation_message=test_message,
            next_escalation_time=past_time
        )
        
        print(f"✅ Created test reminder (ID: {reminder_id})")
        
        # Check if it needs escalation
        reminders_needing_escalation = db.get_reminders_needing_escalation()
        test_reminder = None
        for reminder in reminders_needing_escalation:
            if reminder['id'] == reminder_id:
                test_reminder = reminder
                break
        
        if test_reminder:
            print(f"✅ Test reminder found in escalation queue")
            print(f"   Current level: {test_reminder['escalation_level']}")
            print(f"   Next escalation: {test_reminder['next_escalation_time']}")
            
            # Test escalation logic
            if not escalation_logic.should_stop_escalating(test_reminder):
                print("✅ Reminder should be escalated")
                
                # Generate escalation message
                escalation_message = escalation_logic.generate_escalation_message(
                    test_reminder['escalation_level'] + 1,
                    test_reminder.get('customer_name')
                )
                print(f"   Escalation message: {escalation_message}")
            else:
                print("❌ Reminder should not be escalated")
        else:
            print("❌ Test reminder not found in escalation queue")
        
        # Clean up test reminder
        print("Cleaning up test reminder...")
        # Note: In a real test, you might want to delete the test reminder
        # For now, we'll just leave it for inspection
        
    except Exception as e:
        print(f"❌ Error in escalation flow test: {e}")
    
    print("✅ Escalation flow test completed")

def main():
    """Run all escalation tests"""
    print("🚀 Starting Escalation System Tests...")
    print("=" * 50)
    
    try:
        # Test escalation logic
        test_escalation_logic()
        
        # Test database methods
        test_database_escalation_methods()
        
        # Test API endpoints (only if app is running)
        print("\n" + "=" * 50)
        print("🌐 API Tests (requires running app)")
        print("=" * 50)
        test_escalation_api()
        
        # Test complete flow
        print("\n" + "=" * 50)
        print("🔄 Complete Flow Test")
        print("=" * 50)
        test_escalation_flow()
        
        print("\n" + "=" * 50)
        print("✅ All escalation tests completed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 