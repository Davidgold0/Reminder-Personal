import os
import sys
import requests
from datetime import datetime, time, timedelta
import pytz
from typing import Optional

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from green_api_client import GreenAPIClient
from openai import OpenAI

class ReminderService:
    def __init__(self, main_app_url: str = None):
        self.green_api = GreenAPIClient()
        self.israel_tz = pytz.timezone(Config.TIMEZONE)
        
        # Main app URL for API calls
        self.main_app_url = main_app_url or os.environ.get('MAIN_APP_URL', 'http://localhost:5000')
        if not self.main_app_url.startswith('http'):
            self.main_app_url = f"https://{self.main_app_url}"
        
        print(f"🔗 Reminder service configured with main app URL: {self.main_app_url}")
        
        # Initialize OpenAI if enabled
        if Config.OPENAI_ENABLED and Config.OPENAI_API_KEY:
            self.openai_enabled = True
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            print("🤖 AI reminder messages enabled")
        else:
            self.openai_enabled = False
            print("🤖 AI reminder messages disabled - using default message")
    
    def _call_main_app_api(self, endpoint: str, method: str = 'GET', data: dict = None) -> dict:
        """
        Make HTTP call to main app API
        
        Args:
            endpoint: API endpoint (e.g., '/api/status')
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
    
    def get_last_reminder_date(self) -> Optional[str]:
        """Get the last reminder date from main app database"""
        try:
            # Call main app to get last reminder date
            response = self._call_main_app_api('/api/reminders/last-date')
            if 'error' not in response:
                return response.get('last_reminder_date')
            return None
        except Exception as e:
            print(f"❌ Error getting last reminder date: {e}")
            return None
    
    def save_reminder_to_main_app(self, scheduled_time: str, message: str) -> Optional[int]:
        """Save reminder to main app database"""
        try:
            data = {
                'scheduled_time': scheduled_time,
                'message': message
            }
            response = self._call_main_app_api('/api/reminders/save', method='POST', data=data)
            if 'error' not in response:
                return response.get('reminder_id')
            return None
        except Exception as e:
            print(f"❌ Error saving reminder to main app: {e}")
            return None
    
    def mark_reminder_sent_in_main_app(self, reminder_id: int) -> bool:
        """Mark reminder as sent in main app database"""
        try:
            data = {'reminder_id': reminder_id}
            response = self._call_main_app_api('/api/reminders/mark-sent', method='POST', data=data)
            return 'error' not in response
        except Exception as e:
            print(f"❌ Error marking reminder as sent: {e}")
            return False
    
    def generate_ai_reminder_message(self) -> str:
        """
        Generate a personalized reminder message using AI
        
        Returns:
            AI-generated reminder message in Hebrew
        """
        if not self.openai_enabled:
            return Config.REMINDER_MESSAGE
        
        try:
            system_prompt = """אתה עוזר אישי מצחיק וסרקסטי ששולח תזכורות יומיות לגלולת מניעת הריון. 

המאפיינים שלך:
- דובר עברית שוטפת
- מצחיק וסרקסטי (לא רשמי מדי)
- מכוון לנשים
- משתמש באימוג'ים מתאימים
- מגוון הודעות (לא אותו דבר כל יום)
- ידידותי אבל עם קצת ציניות
- תמיד מתייחס לכדור/גלולה (לא "תרופה" או "כדור רפואי")

דוגמאות להודעות:
- "היי יפה! 🕗 8:00 - זמן לכדור! אל תשכחי שאת לא רוצה להיות בהריון 😅💊"
- "טאק טאק! 🚪 מי שם? הגלולה שלך! היא מחכה כבר 5 דקות... ⏰💊"
- "היי! 🎯 זוכרת מה צריך לעשות עכשיו? כן, בדיוק - הכדור! 💊✨"
- "אוקיי, בואי נספור: 1, 2, 3... הגלולה! 🧮💊 לא, זה לא משחק - זה מניעת הריון! 😂"
- "היי! 🕐 8:00 - הכדור שלך קורא לך! אל תעשי לו אייבי 💊😅"

כללים:
- תמיד בעברית
- תמיד עם אימוג'ים
- מצחיק וסרקסטי
- לא רשמי מדי
- קצר (מקסימום 2-3 משפטים)
- מגוון - אל תחזור על אותו דבר
- השתמש במונחים: כדור, גלולה (לא תרופה או כדור רפואי)
- התייחס למניעת הריון (לא לבריאות כללית)"""

            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "צור תזכורת יומית לגלולת מניעת הריון בשעה 8:00 בערב"}
                ],
                max_tokens=150,
                temperature=0.8  # Add some creativity
            )

            ai_message = response.choices[0].message.content.strip()
            print(f"🤖 AI Generated Reminder: {ai_message}")
            return ai_message
            
        except Exception as e:
            print(f"❌ OpenAI API error generating reminder: {e}")
            return Config.REMINDER_MESSAGE
    
    def check_missed_reminders(self) -> bool:
        """
        Check for missed reminders and send them if appropriate
        
        Returns:
            True if a missed reminder was sent, False otherwise
        """
        now = datetime.now(self.israel_tz)
        today = now.date()
        
        # Check if we sent a reminder today by calling main app
        last_reminder_date = self.get_last_reminder_date()
        
        if last_reminder_date:
            try:
                # Parse the date string and ensure it's timezone-aware
                last_datetime = datetime.fromisoformat(last_reminder_date)
                if last_datetime.tzinfo is None:
                    # If timezone-naive, assume it's in Israel timezone
                    last_datetime = self.israel_tz.localize(last_datetime)
                last_date = last_datetime.date()
                if last_date >= today:
                    print(f"✅ Reminder already sent today ({today})")
                    return False
            except Exception as e:
                print(f"⚠️ Error parsing last reminder date '{last_reminder_date}': {e}")
                pass
        
        # Check if it's still reasonable to send (within 2 hours of scheduled time)
        reminder_time = datetime.combine(today, time(20, 0)).replace(tzinfo=self.israel_tz)  # 8:00 PM
        time_diff = abs((now - reminder_time).total_seconds() / 3600)
        
        if time_diff <= 2:  # Within 2 hours
            print(f"📨 Sending missed reminder for {today} (time diff: {time_diff:.1f} hours)")
            return self.send_reminder(is_missed=True)
        else:
            print(f"⏰ Too late to send missed reminder for {today} (time diff: {time_diff:.1f} hours)")
            return False
    
    def send_reminder(self, is_missed: bool = False) -> bool:
        """
        Send the daily reminder
        
        Args:
            is_missed: Whether this is a missed reminder
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            current_time = datetime.now(self.israel_tz)
            print(f"Sending {'missed ' if is_missed else ''}reminder at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Generate AI message
            reminder_message = self.generate_ai_reminder_message()
            
            # Save reminder to main app database first
            reminder_id = self.save_reminder_to_main_app(
                scheduled_time=current_time.isoformat(),
                message=reminder_message
            )
            
            if not reminder_id:
                print("❌ Failed to save reminder to main app database")
                return False
            
            # Send via WhatsApp
            response = self.green_api.send_message(
                phone=Config.RECIPIENT_PHONE,
                message=reminder_message
            )
            
            if 'error' not in response:
                # Mark reminder as sent in main app database
                if self.mark_reminder_sent_in_main_app(reminder_id):
                    print(f"✅ Reminder sent successfully! Response: {response}")
                    return True
                else:
                    print("⚠️ Reminder sent but failed to mark as sent in database")
                    return True  # Still consider it successful
            else:
                print(f"❌ Failed to send reminder: {response['error']}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending reminder: {e}")
            return False
    
    def get_missed_reminders_info(self, days_back: int = 7) -> dict:
        """
        Get information about missed reminders from main app
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary with missed reminders information
        """
        try:
            data = {'days_back': days_back}
            response = self._call_main_app_api('/api/reminders/missed-info', method='POST', data=data)
            if 'error' not in response:
                return response
            else:
                return {"error": response['error']}
        except Exception as e:
            print(f"❌ Error getting missed reminders info: {e}")
            return {"error": str(e)}

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
        
        # Check for missed reminders first
        missed_sent = service.check_missed_reminders()
        
        # If no missed reminder was sent, send today's reminder
        if not missed_sent:
            success = service.send_reminder()
            if success:
                print("✅ Daily reminder sent successfully")
            else:
                print("❌ Failed to send daily reminder")
        else:
            print("✅ Missed reminder sent successfully")
            
    except Exception as e:
        print(f"❌ Error in reminder service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 