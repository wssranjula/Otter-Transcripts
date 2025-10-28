"""
Admin API Endpoints
REST API for managing Sybil agent configuration and WhatsApp whitelist
"""

import json
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
import re

from src.admin.auth import get_current_admin, get_admin_auth

logger = logging.getLogger(__name__)

# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class PromptSectionUpdate(BaseModel):
    section: str = Field(..., description="Prompt section name")
    content: str = Field(..., description="New content for the section")

class PromptSectionsResponse(BaseModel):
    sections: Dict[str, str]

class PhoneNumberRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number in E.164 format (+1234567890)")
    name: Optional[str] = Field(None, description="Optional name/description")

class PhoneNumberResponse(BaseModel):
    phone_number: str
    name: Optional[str] = None
    added_at: str

class WhitelistResponse(BaseModel):
    enabled: bool
    authorized_numbers: List[PhoneNumberResponse]
    blocked_numbers: List[PhoneNumberResponse]
    unauthorized_message: str

class StatsResponse(BaseModel):
    total_authorized_users: int
    total_blocked_users: int
    total_conversations: int
    recent_activity: List[Dict[str, Any]]

# Create router
router = APIRouter(prefix="/admin", tags=["Admin"])

# Global config reference (will be set by main app)
_config: Optional[Dict] = None

def init_admin_api(config: Dict):
    """Initialize admin API with config reference"""
    global _config
    _config = config

def get_config() -> Dict:
    """Get config reference"""
    if not _config:
        raise HTTPException(status_code=500, detail="Admin API not initialized")
    return _config

def save_config(config: Dict) -> bool:
    """Save config to file"""
    try:
        with open("config/config.json", "w", encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format (E.164)"""
    pattern = r'^\+[1-9]\d{1,14}$'
    return bool(re.match(pattern, phone))

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate admin user and return JWT token
    """
    auth = get_admin_auth()
    
    if not auth.authenticate(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token = auth.create_token(request.username)
    expires_in = auth.jwt_expiry_hours * 3600  # Convert hours to seconds
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in
    )

@router.get("/config/sybil-prompt", response_model=PromptSectionsResponse)
async def get_sybil_prompt(admin: Dict = Depends(get_current_admin)):
    """
    Get current Sybil prompt sections
    """
    config = get_config()
    sybil_config = config.get('sybil', {})
    prompt_sections = sybil_config.get('prompt_sections', {})
    
    return PromptSectionsResponse(sections=prompt_sections)

@router.put("/config/sybil-prompt")
async def update_sybil_prompt(
    request: PromptSectionUpdate,
    admin: Dict = Depends(get_current_admin)
):
    """
    Update a specific Sybil prompt section
    """
    config = get_config()
    
    # Ensure sybil section exists
    if 'sybil' not in config:
        config['sybil'] = {}
    if 'prompt_sections' not in config['sybil']:
        config['sybil']['prompt_sections'] = {}
    
    # Update the section
    config['sybil']['prompt_sections'][request.section] = request.content
    
    # Save to file
    if not save_config(config):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save configuration"
        )
    
    logger.info(f"Admin {admin['username']} updated prompt section: {request.section}")
    
    return {"message": "Prompt section updated successfully"}

@router.get("/whitelist", response_model=WhitelistResponse)
async def get_whitelist(admin: Dict = Depends(get_current_admin)):
    """
    Get current WhatsApp whitelist configuration
    """
    config = get_config()
    whatsapp_config = config.get('whatsapp', {})
    
    # Get authorized numbers
    authorized_numbers = []
    for phone in whatsapp_config.get('authorized_numbers', []):
        authorized_numbers.append(PhoneNumberResponse(
            phone_number=phone,
            name=None,  # Could be enhanced to store names
            added_at="Unknown"  # Could be enhanced to track timestamps
        ))
    
    # Get blocked numbers
    blocked_numbers = []
    for phone in whatsapp_config.get('blocked_numbers', []):
        blocked_numbers.append(PhoneNumberResponse(
            phone_number=phone,
            name=None,
            added_at="Unknown"
        ))
    
    return WhitelistResponse(
        enabled=whatsapp_config.get('whitelist_enabled', False),
        authorized_numbers=authorized_numbers,
        blocked_numbers=blocked_numbers,
        unauthorized_message=whatsapp_config.get('unauthorized_message', 'Access denied')
    )

@router.post("/whitelist", response_model=PhoneNumberResponse)
async def add_to_whitelist(
    request: PhoneNumberRequest,
    admin: Dict = Depends(get_current_admin)
):
    """
    Add phone number to authorized list
    """
    if not validate_phone_number(request.phone_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format. Use E.164 format (+1234567890)"
        )
    
    config = get_config()
    
    # Ensure whatsapp section exists
    if 'whatsapp' not in config:
        config['whatsapp'] = {}
    if 'authorized_numbers' not in config['whatsapp']:
        config['whatsapp']['authorized_numbers'] = []
    
    # Check if already exists
    if request.phone_number in config['whatsapp']['authorized_numbers']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already in whitelist"
        )
    
    # Add to whitelist
    config['whatsapp']['authorized_numbers'].append(request.phone_number)
    
    # Save config
    if not save_config(config):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save configuration"
        )
    
    logger.info(f"Admin {admin['username']} added phone number to whitelist: {request.phone_number}")
    
    return PhoneNumberResponse(
        phone_number=request.phone_number,
        name=request.name,
        added_at="Now"
    )

@router.delete("/whitelist/{phone_number}")
async def remove_from_whitelist(
    phone_number: str,
    admin: Dict = Depends(get_current_admin)
):
    """
    Remove phone number from authorized list
    """
    config = get_config()
    whatsapp_config = config.get('whatsapp', {})
    authorized_numbers = whatsapp_config.get('authorized_numbers', [])
    
    if phone_number not in authorized_numbers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not found in whitelist"
        )
    
    # Remove from whitelist
    authorized_numbers.remove(phone_number)
    config['whatsapp']['authorized_numbers'] = authorized_numbers
    
    # Save config
    if not save_config(config):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save configuration"
        )
    
    logger.info(f"Admin {admin['username']} removed phone number from whitelist: {phone_number}")
    
    return {"message": "Phone number removed from whitelist"}

@router.put("/whitelist/enable")
async def toggle_whitelist(
    enabled: bool,
    admin: Dict = Depends(get_current_admin)
):
    """
    Enable or disable whitelist functionality
    """
    config = get_config()
    
    # Ensure whatsapp section exists
    if 'whatsapp' not in config:
        config['whatsapp'] = {}
    
    config['whatsapp']['whitelist_enabled'] = enabled
    
    # Save config
    if not save_config(config):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save configuration"
        )
    
    logger.info(f"Admin {admin['username']} {'enabled' if enabled else 'disabled'} whitelist")
    
    return {"message": f"Whitelist {'enabled' if enabled else 'disabled'}"}

@router.get("/stats", response_model=StatsResponse)
async def get_stats(admin: Dict = Depends(get_current_admin)):
    """
    Get system statistics
    """
    config = get_config()
    whatsapp_config = config.get('whatsapp', {})
    
    # Count authorized users
    authorized_count = len(whatsapp_config.get('authorized_numbers', []))
    blocked_count = len(whatsapp_config.get('blocked_numbers', []))
    
    # TODO: Get conversation stats from database
    # For now, return mock data
    total_conversations = 0
    recent_activity = []
    
    return StatsResponse(
        total_authorized_users=authorized_count,
        total_blocked_users=blocked_count,
        total_conversations=total_conversations,
        recent_activity=recent_activity
    )

@router.get("/health")
async def admin_health(admin: Dict = Depends(get_current_admin)):
    """
    Admin health check
    """
    return {
        "status": "healthy",
        "admin": admin['username'],
        "timestamp": "now"
    }

@router.post("/chat")
async def chat_with_sybil(
    message: str,
    context: str = "",
    admin: Dict = Depends(get_current_admin)
):
    """
    Chat with Sybil agent directly
    """
    try:
        from src.agents.sybil_agent import SybilAgent
        
        # Get config
        config = get_config()
        
        # Initialize Sybil agent with individual parameters
        neo4j_config = config['neo4j']
        mistral_key = config.get('mistral', {}).get('api_key', '')
        mistral_model = config.get('mistral', {}).get('model', 'mistral-small-latest')
        
        sybil_agent = SybilAgent(
            neo4j_uri=neo4j_config['uri'],
            neo4j_user=neo4j_config['user'],
            neo4j_password=neo4j_config['password'],
            mistral_api_key=mistral_key,
            config=config,
            model=mistral_model
        )
        
        # Get response from Sybil
        response = sybil_agent.query(user_question=message)
        
        return {
            "response": response,
            "timestamp": "Now",
            "user": admin['username']
        }
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )
