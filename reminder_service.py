import os
import sys
import requests
from datetime import datetime
import pytz

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

class ReminderService:
    def __init__(self, main_app_url: str = None):
        self.israel_tz = pytz.timezone(Config.TIMEZONE)
        
        # Main app URL for API calls
        self.main_app_url = main_app_url or os.environ.get('MAIN_APP_URL', 'http://localhost:5000')
        if not self.main_app_url.startswith('http'):
            self.main_app_url = f"https://{self.main_app_url}"
        
        print(f"🔗 Reminder service configured with main app URL: {self.main_app_url}")
    
    def _call_main_app_api(self, endpoint: str, method: str = 'GET', data: dict = None) -> dict:
        """
        Make HTTP call to main app API
        
        Args:
            endpoint: API endpoint (e.g., '/api/reminder/trigger')
            method: HTTP method (GET, POST, etc.)
            data: Data to send (for POST requests)
            
        Returns:
            Response data as dictionary
        """
        try:
            url = f"{self.main_app_url}{endpoint}"
            headers = {'Content-Type': 'application/json'}
            
            print(f"🌐 Calling main app API: {method} {url}")
            
            if method.upper() == 'GET':
                response = requests.get(url, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ API call successful: {endpoint}")
                return result
            else:
                print(f"❌ API call failed: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection error calling main app API: {e}")
            print(f"   Main app URL: {self.main_app_url}")
            print(f"   Endpoint: {endpoint}")
            return {"error": f"Connection error: {str(e)}"}
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout error calling main app API: {e}")
            return {"error": f"Timeout error: {str(e)}"}
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error calling main app API: {e}")
            return {"error": f"Network error: {str(e)}"}
        except Exception as e:
            print(f"❌ Error calling main app API: {e}")
            return {"error": f"API error: {str(e)}"}
    
    def trigger_reminder(self) -> bool:
        """
        Trigger the reminder logic in the main app
        
        Returns:
            True if the API call was successful, False otherwise
        """
        try:
            current_time = datetime.now(self.israel_tz)
            print(f"🔔 Triggering reminder at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Call the main app to handle the reminder logic
            response = self._call_main_app_api('/api/reminder/trigger', method='POST')
            
            if 'error' not in response:
                print(f"✅ Reminder triggered successfully! Response: {response}")
                return True
            else:
                print(f"❌ Failed to trigger reminder: {response['error']}")
                return False
                
        except Exception as e:
            print(f"❌ Error triggering reminder: {e}")
            return False
    
    def check_escalations(self) -> bool:
        """
        Check for reminders that need escalation and send them
        
        Returns:
            True if the API call was successful, False otherwise
        """
        try:
            current_time = datetime.now(self.israel_tz)
            print(f"🚨 Checking escalations at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Call the main app to handle escalation logic
            response = self._call_main_app_api('/api/escalation/check', method='POST')
            
            if 'error' not in response:
                escalations_sent = response.get('escalations_sent', 0)
                failed_escalations = response.get('failed_escalations', 0)
                total_checked = response.get('total_checked', 0)
                
                print(f"✅ Escalation check completed!")
                print(f"   Escalations sent: {escalations_sent}")
                print(f"   Failed escalations: {failed_escalations}")
                print(f"   Total checked: {total_checked}")
                return True
            else:
                print(f"❌ Failed to check escalations: {response['error']}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking escalations: {e}")
            return False

def main():
    """Main function called by Railway cron job"""
    print("🚀 Starting reminder service...")
    
    try:
        # Get main app URL from environment
        main_app_url = os.environ.get('MAIN_APP_URL')
        if not main_app_url:
            print("❌ MAIN_APP_URL environment variable not set")
            print("   Please set MAIN_APP_URL environment variable to your main app's URL")
            print("   Example: https://your-main-app.railway.app")
            return
        
        print(f"🔗 Using main app URL: {main_app_url}")
        
        service = ReminderService(main_app_url)
        
        # Test connection to main app first
        print("🔍 Testing connection to main app...")
        status_response = service._call_main_app_api('/health')
        if 'error' in status_response:
            print(f"❌ Cannot connect to main app: {status_response['error']}")
            print("   Please check:")
            print("   1. MAIN_APP_URL is correct")
            print("   2. Main app is running and accessible")
            print("   3. Network connectivity")
            return
        
        print("✅ Successfully connected to main app")
        
        # Trigger the reminder logic in the main app
        success = service.trigger_reminder()
        if success:
            print("✅ Reminder triggered successfully")
        else:
            print("❌ Failed to trigger reminder")
        
        # Check for escalations
        print("🚨 Checking for escalations...")
        escalation_success = service.check_escalations()
        if escalation_success:
            print("✅ Escalation check completed")
        else:
            print("❌ Failed to check escalations")
            
    except Exception as e:
        print(f"❌ Error in reminder service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 