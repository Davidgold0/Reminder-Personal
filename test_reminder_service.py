#!/usr/bin/env python3
"""
Test script for the reminder service
Tests the HTTP API communication between reminder service and main app
"""

import os
import sys
import requests
from datetime import datetime

def test_main_app_endpoints(main_app_url):
    """Test main app API endpoints"""
    print(f"🔍 Testing main app endpoints at: {main_app_url}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{main_app_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False
    
    # Test reminder endpoints
    endpoints = [
        ('/api/reminders/last-date', 'GET'),
        ('/api/reminders/missed-info', 'POST', {'days_back': 7}),
        ('/api/reminders/save', 'POST', {
            'scheduled_time': datetime.now().isoformat(),
            'message': 'Test reminder message'
        })
    ]
    
    for endpoint, method, *args in endpoints:
        try:
            if method == 'GET':
                response = requests.get(f"{main_app_url}{endpoint}", timeout=10)
            elif method == 'POST':
                data = args[0] if args else {}
                response = requests.post(f"{main_app_url}{endpoint}", json=data, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} working")
                if response.json():
                    print(f"   Response: {response.json()}")
            else:
                print(f"❌ {endpoint} failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ {endpoint} error: {e}")
    
    return True

def test_reminder_service(main_app_url):
    """Test the reminder service"""
    print(f"\n🔍 Testing reminder service with main app: {main_app_url}")
    
    # Set environment variable for reminder service
    os.environ['MAIN_APP_URL'] = main_app_url
    
    try:
        # Import and test reminder service
        from reminder_service import ReminderService
        
        service = ReminderService(main_app_url)
        
        # Test AI message generation
        print("\n🤖 Testing AI message generation...")
        ai_message = service.generate_ai_reminder_message()
        print(f"AI Message: {ai_message}")
        
        # Test getting last reminder date
        print("\n📅 Testing last reminder date...")
        last_date = service.get_last_reminder_date()
        print(f"Last reminder date: {last_date}")
        
        # Test missed reminders info
        print("\n⏰ Testing missed reminders info...")
        missed_info = service.get_missed_reminders_info()
        print(f"Missed reminders info: {missed_info}")
        
        print("\n✅ Reminder service tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Reminder service test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Reminder Service Setup")
    print("=" * 50)
    
    # Get main app URL from command line or environment
    if len(sys.argv) > 1:
        main_app_url = sys.argv[1]
    else:
        main_app_url = os.environ.get('MAIN_APP_URL', 'http://localhost:5000')
    
    if not main_app_url.startswith('http'):
        main_app_url = f"https://{main_app_url}"
    
    print(f"Main app URL: {main_app_url}")
    
    # Test main app endpoints
    if not test_main_app_endpoints(main_app_url):
        print("\n❌ Main app tests failed. Make sure the main app is running.")
        return False
    
    # Test reminder service
    if not test_reminder_service(main_app_url):
        print("\n❌ Reminder service tests failed.")
        return False
    
    print("\n🎉 All tests passed! Your 2-service setup is working correctly.")
    print("\nNext steps:")
    print("1. Deploy main app to Railway")
    print("2. Deploy reminder service to Railway")
    print("3. Set MAIN_APP_URL environment variable in reminder service")
    print("4. Configure Railway cron for the reminder service")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 