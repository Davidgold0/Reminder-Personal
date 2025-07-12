import os
from openai import OpenAI
from config import Config
from typing import Dict, Tuple

class ConfirmationAI:
    def __init__(self):
        """Initialize the confirmation AI service"""
        if Config.OPENAI_ENABLED and Config.OPENAI_API_KEY:
            self.openai_enabled = True
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            print("🤖 Confirmation AI enabled")
        else:
            self.openai_enabled = False
            print("🤖 Confirmation AI disabled - using template responses")
    
    def analyze_confirmation(self, message: str, sender: str) -> Tuple[bool, str]:
        """
        Analyze a message to determine if the user confirmed taking their pill
        
        Args:
            message: The user's message
            sender: The sender's phone number
            
        Returns:
            Tuple of (confirmed: bool, response_message: str)
        """
        if not self.openai_enabled:
            return self._template_confirmation_analysis(message)
        
        try:
            system_prompt = """אתה מערכת AI שמנתחת הודעות תגובה לתזכורות גלולת מניעת הריון. התפקיד שלך הוא לקבוע אם המשתמשת אישרה שלקחה את הגלולה או לא.

כללים:
1. אם המשתמשת אישרה שלקחה את הגלולה - החזר TRUE
2. אם המשתמשת אמרה שלא לקחה או החמיצה - החזר FALSE
3. אם ההודעה לא ברורה - החזר FALSE

דוגמאות לאישור (TRUE):
- "לקחתי", "כן", "סיימתי", "אוקיי", "✅"
- "taken", "yes", "done", "ok"
- "בלעתי", "גמרתי", "לקחת"

דוגמאות להחמצה (FALSE):
- "לא", "החמצתי", "שכחתי", "❌"
- "no", "missed", "forgot"
- "לא לקחתי", "לא לקחת"

בנוסף, צור תגובה מתאימה:
- אם אישרה: תגובה מעודדת ותומכת
- אם החמיצה: תגובה אמפתית עם הנחיות
- אם לא ברור: בקשה לבהירות

החזר תשובה בפורמט JSON:
{
    "confirmed": true/false,
    "response": "תגובה בעברית עם אימוג'ים"
}"""

            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"הודעת המשתמשת: {message}"}
                ],
                max_tokens=200,
                temperature=0.3
            )

            ai_response = response.choices[0].message.content.strip()
            print(f"🤖 AI Confirmation Analysis: {ai_response}")
            
            # Try to parse JSON response
            import json
            try:
                result = json.loads(ai_response)
                confirmed = result.get('confirmed', False)
                response_message = result.get('response', 'תודה על התגובה!')
                return confirmed, response_message
            except json.JSONDecodeError:
                print(f"❌ Failed to parse AI response as JSON: {ai_response}")
                return self._template_confirmation_analysis(message)
            
        except Exception as e:
            print(f"❌ OpenAI API error in confirmation analysis: {e}")
            return self._template_confirmation_analysis(message)
    
    def _template_confirmation_analysis(self, message: str) -> Tuple[bool, str]:
        """
        Template-based confirmation analysis (fallback when AI is disabled)
        
        Args:
            message: The user's message
            
        Returns:
            Tuple of (confirmed: bool, response_message: str)
        """
        message_lower = message.lower().strip()
        
        # Check for confirmation patterns (Hebrew and English)
        confirm_patterns = ['taken', 'yes', 'done', 'ok', '✅', 'took', 'taken it', 'swallowed', 'consumed',
                           'לקחתי', 'כן', 'סיימתי', 'אוקיי', 'לקחת', 'בלעתי', 'גמרתי']
        
        # Check for missed patterns (Hebrew and English)
        missed_patterns = ['missed', 'no', 'forgot', '❌', 'didn\'t', 'havent', 'haven\'t', 'forgotten',
                          'החמצתי', 'לא', 'שכחתי', 'לא לקחתי', 'לא לקחת', 'שכחת']
        
        if any(pattern in message_lower for pattern in confirm_patterns):
            return True, "מעולה! רשמתי שלקחת את הגלולה. תישארי בריאה! 💪"
        elif any(pattern in message_lower for pattern in missed_patterns):
            return False, "אל דאגה! קחי אותה בהקדם האפשרי. הבריאות שלך חשובה! 🏥"
        else:
            return False, "לא הבנתי את זה. תכתבי 'לקחתי' אם לקחת או 'החמצתי' אם החמצת." 