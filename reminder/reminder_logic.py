import os
import sys
import requests
from datetime import datetime, time, timedelta
import pytz
from typing import Optional

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from green_api_client import GreenAPIClient
from openai import OpenAI
from database import Database

class ReminderLogic:
    def __init__(self):
        self.green_api = GreenAPIClient()
        self.israel_tz = pytz.timezone(Config.TIMEZONE)
        
        # Initialize OpenAI if enabled
        if Config.OPENAI_ENABLED and Config.OPENAI_API_KEY:
            self.openai_enabled = True
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            print("🤖 AI reminder messages enabled")
        else:
            self.openai_enabled = False
            print("🤖 AI reminder messages disabled - using default message")
    
    def get_last_reminder_date(self) -> Optional[str]:
        """Get the last reminder date from database"""
        try:
            db = Database()
            return db.get_last_reminder_date()
        except Exception as e:
            print(f"❌ Error getting last reminder date: {e}")
            return None
    
    def save_reminder_to_database(self, scheduled_time: str, message: str) -> Optional[int]:
        """Save reminder to database"""
        try:
            db = Database()
            return db.save_reminder(scheduled_time, message)
        except Exception as e:
            print(f"❌ Error saving reminder to database: {e}")
            return None
    
    def mark_reminder_sent_in_database(self, reminder_id: int) -> bool:
        """Mark reminder as sent in database"""
        try:
            db = Database()
            db.mark_reminder_sent(reminder_id)
            return True
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
        
        # Check if we sent a reminder today
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
    
    def check_and_send_reminders_for_time(self, reminder_time: str) -> bool:
        """
        Check if it's time to send reminders for a specific time and send them
        
        Args:
            reminder_time: Time in HH:MM format
            
        Returns:
            True if reminders were sent, False otherwise
        """
        try:
            now = datetime.now(self.israel_tz)
            current_time_str = now.strftime('%H:%M')
            
            # Check if current time matches the reminder time (within 1 minute)
            if current_time_str == reminder_time:
                print(f"⏰ It's time to send reminders for {reminder_time}")
                return self.send_reminder(specific_time=reminder_time)
            else:
                print(f"⏰ Not time for {reminder_time} reminders yet (current: {current_time_str})")
                return False
                
        except Exception as e:
            print(f"❌ Error checking reminders for time {reminder_time}: {e}")
            return False
    
    def get_all_reminder_times(self) -> List[str]:
        """
        Get all unique reminder times from active customers
        
        Returns:
            List of reminder times in HH:MM format
        """
        try:
            db = Database()
            return db.get_all_reminder_times()
        except Exception as e:
            print(f"❌ Error getting reminder times: {e}")
            return []
    
    def send_reminder(self, is_missed: bool = False, specific_time: str = None) -> bool:
        """
        Send the daily reminder to customers with a specific reminder time
        
        Args:
            is_missed: Whether this is a missed reminder
            specific_time: Specific time to send reminders (HH:MM format). If None, sends to all active customers.
            
        Returns:
            True if sent successfully to at least one customer, False otherwise
        """
        try:
            current_time = datetime.now(self.israel_tz)
            print(f"Sending {'missed ' if is_missed else ''}reminder at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Generate AI message
            reminder_message = self.generate_ai_reminder_message()
            
            # Get customers from database
            db = Database()
            
            if specific_time:
                # Get customers for specific time
                customers = db.get_customers_by_reminder_time(specific_time)
                print(f"📱 Sending reminder to customers with time {specific_time}")
            else:
                # Get all active customers (for backward compatibility)
                customers = db.get_customers(active_only=True)
                print(f"📱 Sending reminder to all active customers")
            
            if not customers:
                print(f"❌ No active customers found in database{f' for time {specific_time}' if specific_time else ''}")
                return False
            
            print(f"📱 Sending reminder to {len(customers)} customers")
            
            success_count = 0
            failed_count = 0
            
            for customer in customers:
                try:
                    # Send via WhatsApp
                    response = self.green_api.send_message(
                        phone=customer['phone_number'],
                        message=reminder_message
                    )
                    
                    if 'error' not in response:
                        print(f"✅ Reminder sent successfully to {customer['phone_number']} ({customer.get('name', 'Unnamed')})")
                        success_count += 1
                    else:
                        print(f"❌ Failed to send reminder to {customer['phone_number']}: {response['error']}")
                        failed_count += 1
                        
                except Exception as e:
                    print(f"❌ Error sending reminder to {customer['phone_number']}: {e}")
                    failed_count += 1
            
            # Save reminder to database
            reminder_id = self.save_reminder_to_database(
                scheduled_time=current_time.isoformat(),
                message=reminder_message
            )
            
            # Create daily reminder records for each customer
            reminder_date = current_time.date().isoformat()
            reminder_time_str = current_time.strftime('%H:%M')
            
            # Calculate next escalation time (30 minutes from now)
            next_escalation_time = (current_time + timedelta(minutes=30)).isoformat()
            
            for customer in customers:
                try:
                    daily_reminder_id = db.create_daily_reminder(
                        customer_id=customer['id'],
                        reminder_date=reminder_date,
                        reminder_time=reminder_time_str,
                        message_sent=reminder_message
                    )
                    
                    # Set initial escalation time
                    db.update_escalation_level(
                        reminder_id=daily_reminder_id,
                        escalation_level=0,
                        escalation_message=reminder_message,
                        next_escalation_time=next_escalation_time
                    )
                    
                    print(f"📝 Created daily reminder record for {customer['phone_number']} (ID: {daily_reminder_id})")
                except Exception as e:
                    print(f"❌ Failed to create daily reminder record for {customer['phone_number']}: {e}")
            
            if reminder_id and success_count > 0:
                # Mark reminder as sent in database
                if self.mark_reminder_sent_in_database(reminder_id):
                    print(f"✅ Reminder sent to {success_count} customers, failed: {failed_count}")
                    return True
                else:
                    print("⚠️ Reminder sent but failed to mark as sent in database")
                    return True  # Still consider it successful
            else:
                print(f"❌ Failed to send reminder to any customers (success: {success_count}, failed: {failed_count})")
                return False
                
        except Exception as e:
            print(f"❌ Error sending reminder: {e}")
            return False
    
    def get_missed_reminders_info(self, days_back: int = 7) -> dict:
        """
        Get information about missed reminders
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary with missed reminders information
        """
        try:
            db = Database()
            missed_reminders = db.get_missed_reminders(days_back)
            last_reminder_date = db.get_last_reminder_date()
            
            return {
                "total_missed": len(missed_reminders),
                "missed_dates": [r['scheduled_date'] for r in missed_reminders if r.get('scheduled_date')],
                "last_sent": last_reminder_date
            }
        except Exception as e:
            print(f"❌ Error getting missed reminders info: {e}")
            return {"error": str(e)}
    
    def process_reminder_request(self) -> dict:
        """
        Main method to process a reminder request
        This is the entry point that should be called from your main app
        
        Returns:
            Dictionary with result information
        """
        try:
            print("🔔 Processing reminder request...")
            
            # Get all unique reminder times
            reminder_times = self.get_all_reminder_times()
            
            if not reminder_times:
                print("❌ No reminder times found in database")
                return {"status": "error", "message": "No reminder times configured"}
            
            print(f"⏰ Found {len(reminder_times)} reminder times: {reminder_times}")
            
            # Check for missed reminders first (legacy support)
            missed_sent = self.check_missed_reminders()
            
            # Check each reminder time
            reminders_sent = 0
            for reminder_time in reminder_times:
                if self.check_and_send_reminders_for_time(reminder_time):
                    reminders_sent += 1
            
            if missed_sent:
                return {"status": "success", "message": "Missed reminder sent successfully", "type": "missed"}
            elif reminders_sent > 0:
                return {"status": "success", "message": f"Reminders sent for {reminders_sent} time(s)", "type": "daily"}
            else:
                return {"status": "info", "message": "No reminders due at this time", "type": "none"}
                
        except Exception as e:
            print(f"❌ Error processing reminder request: {e}")
            return {"status": "error", "message": f"Error processing reminder: {str(e)}"} 