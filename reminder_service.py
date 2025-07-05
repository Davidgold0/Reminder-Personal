import os
import sys
from datetime import datetime, time, timedelta
import pytz
from typing import Optional

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from green_api_client import GreenAPIClient
from database import Database
from openai import OpenAI

class ReminderService:
    def __init__(self):
        self.green_api = GreenAPIClient()
        self.db = Database()
        self.israel_tz = pytz.timezone(Config.TIMEZONE)
        
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
    
    def check_missed_reminders(self) -> bool:
        """
        Check for missed reminders and send them if appropriate
        
        Returns:
            True if a missed reminder was sent, False otherwise
        """
        now = datetime.now(self.israel_tz)
        today = now.date()
        
        # Check if we sent a reminder today
        last_reminder_date = self.db.get_last_reminder_date()
        
        if last_reminder_date:
            last_date = datetime.fromisoformat(last_reminder_date).date()
            if last_date >= today:
                print(f"✅ Reminder already sent today ({today})")
                return False
        
        # Check if it's still reasonable to send (within 2 hours of scheduled time)
        reminder_time = datetime.combine(today, time(20, 0))  # 8:00 PM
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
            
            # Save reminder to database first
            reminder_id = self.db.save_reminder(
                scheduled_time=current_time.isoformat(),
                message=reminder_message
            )
            
            # Send via WhatsApp
            response = self.green_api.send_message(
                phone=Config.RECIPIENT_PHONE,
                message=reminder_message
            )
            
            if 'error' not in response:
                # Mark reminder as sent in database
                self.db.mark_reminder_sent(reminder_id)
                print(f"✅ Reminder sent successfully! Response: {response}")
                
                # Schedule next reminder
                self.schedule_next_reminder()
                return True
            else:
                print(f"❌ Failed to send reminder: {response['error']}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending reminder: {e}")
            return False
    
    def schedule_next_reminder(self):
        """Schedule the next reminder for tomorrow"""
        tomorrow = datetime.now(self.israel_tz).date() + timedelta(days=1)
        next_reminder_time = datetime.combine(tomorrow, time(20, 0))
        
        # Save to database for tracking
        self.db.save_scheduled_reminder(next_reminder_time)
        print(f"📅 Next reminder scheduled for {next_reminder_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def get_missed_reminders_info(self, days_back: int = 7) -> dict:
        """
        Get information about missed reminders
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary with missed reminders information
        """
        missed_reminders = self.db.get_missed_reminders(days_back)
        
        return {
            "total_missed": len(missed_reminders),
            "missed_dates": [r['scheduled_date'] for r in missed_reminders],
            "last_sent": self.db.get_last_reminder_date()
        }

def main():
    """Main function called by Railway cron job"""
    print("🚀 Starting reminder service...")
    
    try:
        service = ReminderService()
        
        # Check for missed reminders first
        missed_sent = service.check_missed_reminders()
        
        # If no missed reminder was sent, send today's reminder
        if not missed_sent:
            service.send_reminder()
        
        print("✅ Reminder service completed successfully")
        
    except Exception as e:
        print(f"❌ Error in reminder service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 