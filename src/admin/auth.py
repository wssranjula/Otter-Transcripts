"""
Admin Authentication Module
Handles JWT token generation, validation, and password hashing for admin access
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

# Security scheme for FastAPI
security = HTTPBearer()

class AdminAuth:
    """Admin authentication handler"""
    
    def __init__(self, config: dict):
        """
        Initialize admin authentication
        
        Args:
            config: Configuration dictionary with admin settings
        """
        self.config = config
        self.admin_config = config.get('admin', {})
        
        # Get JWT settings
        self.jwt_secret = self.admin_config.get('jwt_secret', 'default-secret-change-in-production')
        self.jwt_expiry_hours = self.admin_config.get('jwt_expiry_hours', 24)
        
        # Get admin credentials
        self.username = self.admin_config.get('username', 'admin')
        self.password_hash = self.admin_config.get('password_hash', '')
        
        # If no password hash exists, create one for default password
        if not self.password_hash:
            self._create_default_password()
    
    def _create_default_password(self):
        """Create default password hash if none exists"""
        default_password = "admin123"  # Change this in production!
        self.password_hash = self._hash_password(default_password)
        logger.warning("No admin password hash found. Using default password 'admin123'. Please change this!")
    
    def _hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            str: Bcrypt hash
        """
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash
        
        Args:
            password: Plain text password
            hashed: Bcrypt hash
            
        Returns:
            bool: True if password matches
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate admin user
        
        Args:
            username: Admin username
            password: Admin password
            
        Returns:
            bool: True if credentials are valid
        """
        if username != self.username:
            return False
        
        return self.verify_password(password, self.password_hash)
    
    def create_token(self, username: str) -> str:
        """
        Create JWT token for authenticated user
        
        Args:
            username: Admin username
            
        Returns:
            str: JWT token
        """
        now = datetime.utcnow()
        expiry = now + timedelta(hours=self.jwt_expiry_hours)
        
        payload = {
            'username': username,
            'iat': now,
            'exp': expiry,
            'type': 'admin'
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Optional[Dict]: Decoded payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Check token type
            if payload.get('type') != 'admin':
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def get_current_admin(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """
        FastAPI dependency to get current authenticated admin
        
        Args:
            credentials: HTTP Bearer token
            
        Returns:
            Dict: Admin user info
            
        Raises:
            HTTPException: If token is invalid
        """
        token = credentials.credentials
        payload = self.verify_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload

# Global instance (will be initialized in main app)
admin_auth: Optional[AdminAuth] = None

def init_admin_auth(config: dict):
    """Initialize global admin auth instance"""
    global admin_auth
    admin_auth = AdminAuth(config)

def get_admin_auth() -> AdminAuth:
    """Get global admin auth instance"""
    if not admin_auth:
        raise RuntimeError("Admin auth not initialized. Call init_admin_auth() first.")
    return admin_auth

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """FastAPI dependency to get current admin"""
    return get_admin_auth().get_current_admin(credentials)
