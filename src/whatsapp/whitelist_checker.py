"""
WhatsApp Whitelist Checker
Middleware to check if WhatsApp numbers are authorized to use the bot
"""

import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WhitelistChecker:
    """Check if WhatsApp numbers are authorized"""
    
    def __init__(self, admin_db, config: dict):
        """
        Initialize whitelist checker
        
        Args:
            admin_db: AdminDatabase instance
            config: Configuration dictionary
        """
        self.admin_db = admin_db
        self.config = config
        self.enabled = config.get('whatsapp', {}).get('whitelist_enabled', False)
        self.unauthorized_message = config.get('whatsapp', {}).get(
            'unauthorized_message',
            'Sorry, you are not authorized to use this bot. Please contact an administrator for access.'
        )
        
        logger.info(f"Whitelist checker initialized (enabled: {self.enabled})")
    
    def is_authorized(self, phone_number: str) -> bool:
        """
        Check if phone number is authorized
        
        Args:
            phone_number: Phone number to check (in various formats)
        
        Returns:
            True if authorized (or whitelist disabled)
        """
        # If whitelist is disabled, everyone is authorized
        if not self.enabled:
            logger.info(f"[WHITELIST] Whitelist disabled - allowing all numbers")
            return True
        
        # Normalize phone number (remove 'whatsapp:' prefix if present)
        normalized_phone = self._normalize_phone(phone_number)
        
        try:
            # Check database
            is_whitelisted = self.admin_db.check_phone_whitelisted(normalized_phone)
            
            # Log the check result with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if is_whitelisted:
                logger.info(f"[WHITELIST] [{timestamp}] AUTHORIZED: {normalized_phone}")
            else:
                logger.warning(f"[WHITELIST] [{timestamp}] BLOCKED: {normalized_phone} - Not in whitelist")
                # Also log to a separate unauthorized access file for monitoring
                self._log_unauthorized_access(normalized_phone)
            
            return is_whitelisted
            
        except Exception as e:
            logger.error(f"[WHITELIST] Error checking whitelist for {normalized_phone}: {e}")
            # On error, default to DENY for security
            logger.warning(f"[WHITELIST] Defaulting to DENY due to error")
            return False
    
    def _log_unauthorized_access(self, phone_number: str):
        """Log unauthorized access attempts to a separate file"""
        try:
            with open('unauthorized_whatsapp.log', 'a', encoding='utf-8') as f:
                timestamp = datetime.now().isoformat()
                f.write(f"{timestamp} | UNAUTHORIZED | {phone_number}\n")
        except Exception as e:
            logger.error(f"Failed to log unauthorized access: {e}")
    
    def _normalize_phone(self, phone_number: str) -> str:
        """
        Normalize phone number format
        
        Args:
            phone_number: Phone number (may include 'whatsapp:' prefix)
        
        Returns:
            Normalized phone number
        """
        # Remove 'whatsapp:' prefix
        if phone_number.startswith('whatsapp:'):
            phone_number = phone_number.replace('whatsapp:', '')
        
        # Remove any whitespace
        phone_number = phone_number.strip()
        
        # Ensure it starts with '+'
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        return phone_number
    
    def get_unauthorized_message(self) -> str:
        """
        Get the unauthorized access message
        
        Returns:
            Unauthorized message
        """
        return self.unauthorized_message
    
    def check_and_respond(self, phone_number: str) -> Optional[str]:
        """
        Check authorization and return error message if unauthorized
        
        Args:
            phone_number: Phone number to check
        
        Returns:
            Error message if unauthorized, None if authorized
        """
        if not self.is_authorized(phone_number):
            return self.get_unauthorized_message()
        return None

