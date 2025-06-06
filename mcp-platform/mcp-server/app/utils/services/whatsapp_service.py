import aiohttp
import asyncio
from typing import Dict, Optional, List
import logging
import json
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.api_token = settings.WHATSAPP_API_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_version = "v17.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.webhook_verify_token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
        
    async def send_message(
        self, 
        to: str, 
        message: str,
        message_type: str = "text"
    ) -> Dict[str, any]:
        """Send WhatsApp message"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            # Format phone number (ensure it has country code)
            if not to.startswith("+"):
                to = f"+55{to}"  # Default to Brazil
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": message_type,
            }
            
            if message_type == "text":
                payload["text"] = {"body": message}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        logger.info(f"Message sent successfully to {to}")
                        return {"success": True, "message_id": result.get("messages", [{}])[0].get("id")}
                    else:
                        logger.error(f"Failed to send message: {result}")
                        return {"success": False, "error": result}
                        
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_template_message(
        self,
        to: str,
        template_name: str,
        template_params: List[str]
    ) -> Dict[str, any]:
        """Send WhatsApp template message"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            # Format phone number
            if not to.startswith("+"):
                to = f"+55{to}"
            
            # Build template components
            components = []
            if template_params:
                components.append({
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": param}
                        for param in template_params
                    ]
                })
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "pt_BR"},
                    "components": components
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        logger.info(f"Template message sent to {to}")
                        return {"success": True, "message_id": result.get("messages", [{}])[0].get("id")}
                    else:
                        logger.error(f"Failed to send template message: {result}")
                        return {"success": False, "error": result}
                        
        except Exception as e:
            logger.error(f"Error sending template message: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_interactive_message(
        self,
        to: str,
        body_text: str,
        buttons: List[Dict[str, str]]
    ) -> Dict[str, any]:
        """Send interactive message with buttons"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            # Format phone number
            if not to.startswith("+"):
                to = f"+55{to}"
            
            # Build interactive message
            interactive = {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": button["id"],
                                "title": button["title"][:20]  # WhatsApp limit
                            }
                        }
                        for button in buttons[:3]  # Max 3 buttons
                    ]
                }
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": interactive
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        logger.info(f"Interactive message sent to {to}")
                        return {"success": True, "message_id": result.get("messages", [{}])[0].get("id")}
                    else:
                        logger.error(f"Failed to send interactive message: {result}")
                        return {"success": False, "error": result}
                        
        except Exception as e:
            logger.error(f"Error sending interactive message: {e}")
            return {"success": False, "error": str(e)}
    
    def parse_webhook_message(self, webhook_data: Dict) -> Optional[Dict]:
        """Parse incoming webhook message"""
        try:
            # Extract message data from webhook payload
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            # Check if it's a message
            messages = value.get("messages", [])
            if not messages:
                return None
            
            message = messages[0]
            contact = value.get("contacts", [{}])[0]
            
            # Extract relevant information
            parsed_message = {
                "message_id": message.get("id"),
                "from": message.get("from"),
                "timestamp": datetime.fromtimestamp(int(message.get("timestamp", 0))),
                "type": message.get("type"),
                "contact_name": contact.get("profile", {}).get("name", "Unknown"),
            }
            
            # Extract message content based on type
            if message["type"] == "text":
                parsed_message["text"] = message.get("text", {}).get("body", "")
            elif message["type"] == "interactive":
                parsed_message["interactive"] = message.get("interactive", {})
                # Extract button reply
                if message["interactive"]["type"] == "button_reply":
                    parsed_message["button_id"] = message["interactive"]["button_reply"]["id"]
                    parsed_message["button_title"] = message["interactive"]["button_reply"]["title"]
            
            logger.info(f"Parsed webhook message: {parsed_message}")
            return parsed_message
            
        except Exception as e:
            logger.error(f"Error parsing webhook message: {e}")
            return None
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify webhook subscription"""
        if mode == "subscribe" and token == self.webhook_verify_token:
            logger.info("Webhook verified successfully")
            return challenge
        else:
            logger.warning("Webhook verification failed")
            return None
    
    async def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"Message {message_id} marked as read")
                        return True
                    else:
                        logger.error(f"Failed to mark message as read: {await response.text()}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return False