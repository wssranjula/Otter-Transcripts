"""
Twilio WhatsApp API Client
Handles sending and receiving WhatsApp messages via Twilio
"""

import os
import hmac
import hashlib
from typing import Optional
from twilio.rest import Client
from twilio.request_validator import RequestValidator
import logging

logger = logging.getLogger(__name__)


class TwilioWhatsAppClient:
    """Client for Twilio WhatsApp API"""

    def __init__(self, account_sid: str, auth_token: str, whatsapp_number: str):
        """
        Initialize Twilio client

        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            whatsapp_number: Twilio WhatsApp number (format: whatsapp:+14155238886)
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.whatsapp_number = whatsapp_number
        
        # Initialize Twilio client
        self.client = Client(account_sid, auth_token)
        self.validator = RequestValidator(auth_token)
        
        logger.info(f"Twilio WhatsApp client initialized with number: {whatsapp_number}")

    def send_message(self, to: str, body: str) -> bool:
        """
        Send WhatsApp message to a recipient

        Args:
            to: Recipient phone number (format: whatsapp:+1234567890)
            body: Message text (max 1600 characters for WhatsApp)

        Returns:
            bool: True if message sent successfully
        """
        try:
            # Ensure 'to' has whatsapp: prefix
            if not to.startswith('whatsapp:'):
                to = f'whatsapp:{to}'

            # Truncate message if too long (WhatsApp limit ~1600 chars)
            if len(body) > 1600:
                body = body[:1550] + "\n\n... (message truncated)"
                logger.warning(f"Message truncated to fit WhatsApp limit")

            # Send message via Twilio
            message = self.client.messages.create(
                from_=self.whatsapp_number,
                body=body,
                to=to
            )

            logger.info(f"Message sent successfully. SID: {message.sid}")
            return True

        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False

    def send_reply(self, to: str, body: str, original_message_sid: Optional[str] = None) -> bool:
        """
        Send a reply to a WhatsApp message

        Args:
            to: Recipient phone number
            body: Message text
            original_message_sid: Optional SID of original message (for threading)

        Returns:
            bool: True if message sent successfully
        """
        # For now, same as send_message (Twilio handles threading automatically)
        return self.send_message(to, body)

    def validate_webhook(self, url: str, params: dict, signature: str) -> bool:
        """
        Validate that webhook request came from Twilio

        Args:
            url: Full webhook URL
            params: Request parameters
            signature: X-Twilio-Signature header value

        Returns:
            bool: True if signature is valid
        """
        try:
            return self.validator.validate(url, params, signature)
        except Exception as e:
            logger.error(f"Webhook validation error: {e}")
            return False

    def format_message_for_whatsapp(self, text: str) -> str:
        """
        Format text for WhatsApp (supports basic markdown)

        WhatsApp supports:
        - *bold*
        - _italic_
        - ~strikethrough~
        - ```code```

        Args:
            text: Plain text message

        Returns:
            str: Formatted text
        """
        # For now, return as-is. Can enhance with markdown conversion later.
        return text

    @staticmethod
    def parse_incoming_message(form_data: dict) -> dict:
        """
        Parse incoming Twilio webhook form data

        Args:
            form_data: Form data from Twilio webhook

        Returns:
            dict: Parsed message data
        """
        return {
            'message_sid': form_data.get('MessageSid', ''),
            'from': form_data.get('From', ''),
            'to': form_data.get('To', ''),
            'body': form_data.get('Body', ''),
            'num_media': int(form_data.get('NumMedia', 0)),
            'profile_name': form_data.get('ProfileName', 'Unknown'),
            'wa_id': form_data.get('WaId', ''),  # WhatsApp ID (phone without prefix)
            'timestamp': form_data.get('Timestamp', ''),
        }

    def get_status(self) -> dict:
        """
        Get Twilio account status

        Returns:
            dict: Account status information
        """
        try:
            account = self.client.api.accounts(self.account_sid).fetch()
            return {
                'status': account.status,
                'friendly_name': account.friendly_name,
                'type': account.type
            }
        except Exception as e:
            logger.error(f"Failed to fetch account status: {e}")
            return {'status': 'error', 'message': str(e)}

