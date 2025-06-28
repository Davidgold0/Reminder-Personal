import schedule
import time
import pytz
from datetime import datetime
from green_api_client import GreenAPIClient
from config import Config

class ReminderScheduler:
    def __init__(self):
        self.green_api = GreenAPIClient()
        self.israel_tz = pytz.timezone(Config.TIMEZONE)
        self.last_reminder_sent = None
        
    def send_daily_reminder(self):
        """Send the daily pill reminder"""
        try:
            print(f"Sending daily pill reminder at {datetime.now(self.israel_tz).strftime('%Y-%m-%d %H:%M:%S')}")
            
            response = self.green_api.send_message(
                phone=Config.RECIPIENT_PHONE,
                message=Config.REMINDER_MESSAGE
            )
            
            if 'error' not in response:
                self.last_reminder_sent = datetime.now(self.israel_tz)
                print(f"Reminder sent successfully! Response: {response}")
            else:
                print(f"Failed to send reminder: {response['error']}")
                
        except Exception as e:
            print(f"Error sending daily reminder: {e}")
    
    def setup_schedule(self):
        """Setup the daily reminder schedule"""
        # Schedule reminder for 8:00 PM Israel time
        schedule.every().day.at(Config.REMINDER_TIME).timezone(Config.TIMEZONE).do(self.send_daily_reminder)
        
        print(f"Daily reminder scheduled for {Config.REMINDER_TIME} {Config.TIMEZONE}")
        print(f"Recipient: {Config.RECIPIENT_PHONE}")
    
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
        jobs = schedule.get_jobs()
        for job in jobs:
            if hasattr(job, 'at_time') and job.at_time:
                return job.at_time
        return None
    
    def get_status(self):
        """Get current scheduler status"""
        return {
            'next_reminder': self.get_next_reminder_time(),
            'last_reminder_sent': self.last_reminder_sent.isoformat() if self.last_reminder_sent else None,
            'timezone': Config.TIMEZONE,
            'recipient': Config.RECIPIENT_PHONE,
            'message': Config.REMINDER_MESSAGE
        } 