import schedule
import time
import pytz
from datetime import datetime, time as dt_time
from green_api_client import GreenAPIClient
from config import Config
from database import Database
from openai import OpenAI
import os

class ReminderScheduler:
    def __init__(self):
        self.green_api = GreenAPIClient()
        self.israel_tz = pytz.timezone(Config.TIMEZONE)
        self.db = Database()
        self.last_reminder_sent = None
        
        # Initialize OpenAI if enabled
        if Config.OPENAI_ENABLED and Config.OPENAI_API_KEY:
            self.openai_enabled = True
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            print("🤖 AI reminder messages enabled")
        else:
            self.openai_enabled = False
            print("🤖 AI reminder messages disabled - using default message")
    
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
        
    def send_daily_reminder(self):
        """Send the daily pill reminder"""
        try:
            current_time = datetime.now(self.israel_tz)
            print(f"Sending daily pill reminder at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Generate AI message or use default
            reminder_message = self.generate_ai_reminder_message()
            
            # Save reminder to database first
            reminder_id = self.db.save_reminder(
                scheduled_time=current_time.isoformat(),
                message=reminder_message
            )
            
            response = self.green_api.send_message(
                phone=Config.RECIPIENT_PHONE,
                message=reminder_message
            )
            
            if 'error' not in response:
                # Mark reminder as sent in database
                self.db.mark_reminder_sent(reminder_id)
                self.last_reminder_sent = current_time
                print(f"Reminder sent successfully! Response: {response}")
            else:
                print(f"Failed to send reminder: {response['error']}")
                
        except Exception as e:
            print(f"Error sending daily reminder: {e}")
    
    def should_send_reminder(self):
        """Check if it's time to send the reminder based on Israel timezone"""
        now = datetime.now(self.israel_tz)
        
        # Parse the reminder time
        reminder_hour, reminder_minute = map(int, Config.REMINDER_TIME.split(':'))
        reminder_time = dt_time(reminder_hour, reminder_minute)
        
        # Check if we haven't sent a reminder today yet
        if self.last_reminder_sent:
            last_reminder_date = self.last_reminder_sent.date()
            if now.date() <= last_reminder_date:
                return False
        
        # Check if current time matches reminder time (within 1 minute)
        current_time = now.time()
        time_diff = abs((current_time.hour * 60 + current_time.minute) - 
                       (reminder_time.hour * 60 + reminder_time.minute))
        
        return time_diff <= 1
    
    def setup_schedule(self):
        """Setup the daily reminder schedule"""
        # Schedule a job that runs every minute to check if it's time for the reminder
        schedule.every().minute.do(self.check_and_send_reminder)
        
        print(f"Daily reminder scheduled for {Config.REMINDER_TIME} {Config.TIMEZONE}")
        print(f"Recipient: {Config.RECIPIENT_PHONE}")
    
    def check_and_send_reminder(self):
        """Check if it's time to send the reminder and send it if needed"""
        if self.should_send_reminder():
            self.send_daily_reminder()
    
    def run_scheduler(self):
        """Run the scheduler loop"""
        print("Starting reminder scheduler...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nScheduler stopped by user")
        except Exception as e:
            print(f"Scheduler error: {e}")
    
    def send_test_reminder(self):
        """Send a test reminder immediately"""
        print("Sending test reminder...")
        self.send_daily_reminder()
    
    def get_next_reminder_time(self):
        """Get the next scheduled reminder time"""
        now = datetime.now(self.israel_tz)
        reminder_hour, reminder_minute = map(int, Config.REMINDER_TIME.split(':'))
        
        # Calculate next reminder time
        next_reminder = now.replace(hour=reminder_hour, minute=reminder_minute, second=0, microsecond=0)
        
        # If today's reminder time has passed, schedule for tomorrow
        if next_reminder <= now:
            from datetime import timedelta
            next_reminder += timedelta(days=1)
        
        return next_reminder
    
    def get_status(self):
        """Get current scheduler status"""
        return {
            'next_reminder': self.get_next_reminder_time().isoformat(),
            'last_reminder_sent': self.last_reminder_sent.isoformat() if self.last_reminder_sent else None,
            'timezone': Config.TIMEZONE,
            'recipient': Config.RECIPIENT_PHONE,
            'message': Config.REMINDER_MESSAGE
        } 