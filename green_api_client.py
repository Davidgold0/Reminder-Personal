import requests
import json
import time
from typing import Dict, List, Optional
from config import Config

class GreenAPIClient:
    def __init__(self):
        self.base_url = Config.GREEN_API_BASE_URL
        self.id = Config.GREEN_API_ID
        self.token = Config.GREEN_API_TOKEN
        self.instance_id = Config.GREEN_API_INSTANCE_ID
        
        if not all([self.id, self.token, self.instance_id]):
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
        Get incoming notifications/messages
        
        Returns:
            List of notification objects
        """
        url = self._get_url(f"waInstance{self.instance_id}/GetNotification/{self.token}")
        
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting notifications: {e}")
            return []
    
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