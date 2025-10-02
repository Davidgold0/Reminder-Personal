import os
import sys
from datetime import datetime, timedelta
import pytz
from typing import Optional, Tuple

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from green_api_client import GreenAPIClient
from openai import OpenAI

class EscalationLogic:
    def __init__(self):
        self.green_api = GreenAPIClient()
        self.utc_tz = pytz.timezone('UTC')  # Use UTC timezone
        
        # Initialize OpenAI if enabled
        if Config.OPENAI_ENABLED and Config.OPENAI_API_KEY:
            self.openai_enabled = True
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            print("🤖 Escalation AI enabled")
        else:
            self.openai_enabled = False
            print("🤖 Escalation AI disabled - using template responses")
    
    def generate_escalation_message(self, escalation_level: int, customer_name: str = None) -> str:
        """
        Generate an escalation message based on the level
        
        Args:
            escalation_level: Level of escalation (1-4)
            customer_name: Optional customer name for personalization
            
        Returns:
            Escalation message
        """
        if not self.openai_enabled:
            return self._template_escalation_message(escalation_level, customer_name)
        
        try:
            escalation_prompts = {
                1: "Gentle reminder - slightly more urgent than initial message, show concern but not angry",
                2: "More direct - emphasize the importance and show growing concern",
                3: "Firm but caring - make it clear this is serious but still supportive",
                4: "Final warning - urgent and direct but still caring, emphasize the consequences"
            }
            
            system_prompt = f"""אתה מערכת AI ששולחת תזכורות הולכות ומתעצמות לגלולת מניעת הריון. 

התפקיד שלך הוא ליצור הודעה ברמת הסלמה {escalation_level}:
{escalation_prompts[escalation_level]}

כללים:
- תמיד בעברית
- תמיד עם אימוג'ים מתאימים
- התייחס לזמן שחלף (30 דקות, שעה, שעה וחצי, שעתיים)
- הדגש את החשיבות של לקיחת הגלולה
- היה אמפתי אבל הולך ומתעצם
- השתמש במונחים: כדור, גלולה
- הודעה קצרה (מקסימום 2-3 משפטים)

דוגמאות לרמות הסלמה:
1: "היי! עדיין לא לקחת את הכדור? ⏰💊"
2: "אני מחכה... הכדור שלך עדיין מחכה! 😤💊"
3: "זה כבר שעה וחצי! הכדור לא יקח את עצמו! 😠💊"
4: "שתי שעות! זה לא משחק! קחי את הכדור עכשיו! 😡💊"

צור הודעה מתאימה לרמה {escalation_level}:"""

            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"צור הודעת הסלמה לרמה {escalation_level}"}
                ],
                max_tokens=150,
                temperature=0.7
            )

            escalation_message = response.choices[0].message.content.strip()
            print(f"🤖 AI Generated Escalation Level {escalation_level}: {escalation_message}")
            return escalation_message
            
        except Exception as e:
            print(f"❌ OpenAI API error generating escalation: {e}")
            return self._template_escalation_message(escalation_level, customer_name)
    
    def _template_escalation_message(self, escalation_level: int, customer_name: str = None) -> str:
        """
        Template-based escalation messages (fallback when AI is disabled)
        
        Args:
            escalation_level: Level of escalation (1-4)
            customer_name: Optional customer name for personalization
            
        Returns:
            Escalation message
        """
        name_part = f"{customer_name}! " if customer_name else ""
        
        escalation_templates = {
            1: f"{name_part}היי! עדיין לא לקחת את הכדור? ⏰💊\nזכרי - זה חשוב לבריאות שלך!",
            2: f"{name_part}אני מחכה... הכדור שלך עדיין מחכה! 😤💊\nזה כבר שעה - אל תשכחי!",
            3: f"{name_part}זה כבר שעה וחצי! הכדור לא יקח את עצמו! 😠💊\nבואי, זה רק דקה אחת!",
            4: f"{name_part}שתי שעות! זה לא משחק! קחי את הכדור עכשיו! 😡💊\nזה חשוב מדי בשביל לדחות!"
        }
        
        return escalation_templates.get(escalation_level, escalation_templates[1])
    
    def send_escalation(self, reminder_data: dict) -> bool:
        """
        Send an escalation message to a customer
        
        Args:
            reminder_data: Daily reminder data from database
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            customer_phone = reminder_data['phone_number']
            escalation_level = reminder_data['escalation_level'] + 1
            customer_name = reminder_data.get('customer_name')
            
            print(f"🚨 Sending escalation level {escalation_level} to {customer_phone}")
            
            # Generate escalation message
            escalation_message = self.generate_escalation_message(escalation_level, customer_name)
            
            # Send via WhatsApp
            response = self.green_api.send_message(
                phone=customer_phone,
                message=escalation_message
            )
            
            if 'error' not in response:
                print(f"✅ Escalation level {escalation_level} sent successfully to {customer_phone}")
                return True
            else:
                print(f"❌ Failed to send escalation to {customer_phone}: {response['error']}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending escalation: {e}")
            return False
    
    def calculate_next_escalation_time(self, current_time: datetime, escalation_level: int) -> str:
        """
        Calculate when the next escalation should be sent
        
        Args:
            current_time: Current time
            escalation_level: Current escalation level
            
        Returns:
            Next escalation time as ISO string
        """
        # Each escalation is 30 minutes apart
        next_time = current_time + timedelta(minutes=30)
        # Return format compatible with MySQL STR_TO_DATE function
        return next_time.strftime('%Y-%m-%d %H:%M:%S')
    
    def should_stop_escalating(self, reminder_data: dict) -> bool:
        """
        Check if escalation should stop for this reminder
        
        Args:
            reminder_data: Daily reminder data from database
            
        Returns:
            True if escalation should stop, False otherwise
        """
        # Stop if confirmed
        if reminder_data.get('confirmed', False):
            return True
        
        # Stop if max escalation level reached (4 escalations + initial = 5 total)
        if reminder_data.get('escalation_level', 0) >= 4:
            return True
        
        # Stop if more than 2 hours have passed since initial reminder
        created_at = datetime.fromisoformat(reminder_data['created_at'])
        current_time = datetime.now(self.utc_tz)
        time_diff = (current_time - created_at).total_seconds() / 3600
        
        if time_diff > 2:
            return True
        
        return False 