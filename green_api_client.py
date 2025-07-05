import requests
import json
import time
from typing import Dict, List, Optional
from config import Config

class GreenAPIClient:
    def __init__(self):
        self.base_url = Config.GREEN_API_BASE_URL
        self.token = Config.GREEN_API_TOKEN
        self.instance_id = Config.GREEN_API_INSTANCE_ID
        
        if not all([self.token, self.instance_id]):
            raise ValueError("Green API credentials not properly configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            'Content-Type': 'application/json'
        }
    
    def _get_url(self, endpoint: str) -> str:
        """Build full API URL"""
        return f"{self.base_url}/{endpoint}"
    
    def send_message(self, phone: str, message: str) -> Dict:
        """
        Send a WhatsApp message using Green API
        
        Args:
            phone: Phone number with country code (no +)
            message: Message text to send
            
        Returns:
            API response as dictionary
        """
        url = self._get_url(f"waInstance{self.instance_id}/SendMessage/{self.token}")
        
        payload = {
            "chatId": f"{phone}@c.us",
            "message": message
        }
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending message: {e}")
            return {"error": str(e)}
    
    def get_notifications(self) -> List[Dict]:
        """
        Get incoming notifications/messages using the correct Green API endpoint
        
        Returns:
            List of notification objects
        """
        url = self._get_url(f"waInstance{self.instance_id}/ReceiveNotification/{self.token}")
        
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting notifications: {e}")
            return []
    
    def check_notifications_available(self) -> bool:
        """
        Check if there are notifications available to receive
        
        Returns:
            True if notifications are available, False otherwise
        """
        url = self._get_url(f"waInstance{self.instance_id}/ReceiveNotification/{self.token}")
        
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            notifications = response.json()
            return len(notifications) > 0
        except requests.exceptions.RequestException as e:
            print(f"Error checking notifications: {e}")
            return False
    
    def delete_notification(self, receipt_id: int) -> bool:
        """
        Delete a notification after processing
        
        Args:
            receipt_id: ID of the notification to delete
            
        Returns:
            True if successful, False otherwise
        """
        url = self._get_url(f"waInstance{self.instance_id}/DeleteNotification/{self.token}/{receipt_id}")
        
        try:
            response = requests.delete(url, headers=self._get_headers())
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error deleting notification: {e}")
            return False
    
    def get_state_instance(self) -> Dict:
        """
        Get the current state of the WhatsApp instance
        
        Returns:
            Instance state information
        """
        url = self._get_url(f"waInstance{self.instance_id}/getStateInstance/{self.token}")
        
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting instance state: {e}")
            return {"error": str(e)}
    
    def is_instance_authorized(self) -> bool:
        """
        Check if the WhatsApp instance is authorized and ready
        
        Returns:
            True if authorized, False otherwise
        """
        try:
            state = self.get_state_instance()
            return state.get('stateInstance') == 'authorized'
        except Exception as e:
            print(f"Error checking instance authorization: {e}")
            return False
    
    def set_webhook_url(self, webhook_url: str) -> Dict:
        """
        Set webhook URL for receiving notifications
        
        Args:
            webhook_url: The URL where webhooks will be sent
            
        Returns:
            API response as dictionary
        """
        url = self._get_url(f"waInstance{self.instance_id}/SetSettings/{self.token}")
        
        payload = {
            "webhookUrl": webhook_url,
            "webhookUrlToken": "your_webhook_token_here",  # Optional security token
            "incomingMessageReceived": True,
        }
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error setting webhook URL: {e}")
            return {"error": str(e)}
    
    def get_webhook_settings(self) -> Dict:
        """
        Get current webhook settings
        
        Returns:
            Webhook settings as dictionary
        """
        url = self._get_url(f"waInstance{self.instance_id}/GetSettings/{self.token}")
        
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting webhook settings: {e}")
            return {"error": str(e)}
    
    def delete_webhook_url(self) -> Dict:
        """
        Delete webhook URL (disable webhooks)
        
        Returns:
            API response as dictionary
        """
        url = self._get_url(f"waInstance{self.instance_id}/SetSettings/{self.token}")
        
        payload = {
            "webhookUrl": ""
        }
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error deleting webhook URL: {e}")
            return {"error": str(e)} 