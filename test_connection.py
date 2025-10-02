#!/usr/bin/env python3
"""
Test script to debug connection issues between reminder service and main app
"""

import os
import sys
import requests
from datetime import datetime, timezone
import pytz

def test_main_app_connection(main_app_url):
    """Test connection to main app"""
    print(f"🔍 Testing connection to main app: {main_app_url}")
    
    # Test health endpoint
    try:
        health_url = f"{main_app_url}/health"
        print(f"   Testing health endpoint: {health_url}")
        response = requests.get(health_url, timeout=10)
        print(f"   Health response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Health endpoint failed: {e}")
    
    # Test last reminder date endpoint
    try:
        last_date_url = f"{main_app_url}/api/reminders/last-date"
        print(f"   Testing last date endpoint: {last_date_url}")
        response = requests.get(last_date_url, timeout=10)
        print(f"   Last date response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Last date endpoint failed: {e}")
    
    # Test status endpoint
    try:
        status_url = f"{main_app_url}/api/status"
        print(f"   Testing status endpoint: {status_url}")
        response = requests.get(status_url, timeout=10)
        print(f"   Status response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Status endpoint failed: {e}")

def test_timezone_handling():
    """Test timezone handling"""
    print("\n🕐 Testing timezone handling...")
    
    utc_tz = timezone.utc
    now = datetime.now(utc_tz)
    today = now.date()
    
    print(f"   Current time (UTC): {now}")
    print(f"   Today's date: {today}")
    
    # Test reminder time calculation
    from datetime import time
    reminder_time = datetime.combine(today, time(17, 0)).replace(tzinfo=utc_tz)  # 5 PM UTC
    print(f"   Reminder time: {reminder_time}")
    
    # Test time difference calculation
    time_diff = abs((now - reminder_time).total_seconds() / 3600)
    print(f"   Time difference: {time_diff:.1f} hours")

def main():
    """Main test function"""
    print("🧪 Reminder Service Connection Test")
    print("=" * 50)
    
    # Test timezone handling
    test_timezone_handling()
    
    # Test main app connection
    main_app_url = os.environ.get('MAIN_APP_URL')
    if not main_app_url:
        print("\n❌ MAIN_APP_URL environment variable not set")
        print("   Please set it to your main app's URL")
        print("   Example: export MAIN_APP_URL=https://your-app.railway.app")
        return
    
    print(f"\n🔗 Testing with MAIN_APP_URL: {main_app_url}")
    test_main_app_connection(main_app_url)
    
    print("\n✅ Test completed")

if __name__ == "__main__":
    main() 