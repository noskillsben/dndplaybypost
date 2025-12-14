from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.site_settings import SiteSettings
from typing import Any, Dict
from uuid import UUID


# Default settings structure
DEFAULT_SETTINGS = {
    # Site Branding
    "site_name": "D&D Play-by-Post",
    "site_domain": "",
    "site_logo": "",
    "colors": {
        "primary": "#3B82F6",
        "secondary": "#8B5CF6",
        "background": "#1F2937"
    },
    
    # Email Settings
    "email": {
        "enabled": False,
        "provider": "gmail",
        "from_address": "",
        "gmail_client_id": "",
        "gmail_client_secret": "",
        "gmail_refresh_token": "",
        "gmail_access_token": "",
        "gmail_token_expires_at": None,
        "gmail_authorized": False
    },
    
    # User Registration
    "user_registration": {
        "allow_new_users": True,
        "registration_mode": "open",  # "open" | "invite_only" | "closed"
        "require_email": True,
        "require_email_verification": False,
        "new_users_can_create_campaigns": True,
        "new_users_can_join_campaigns": True
    },
    
    # Campaign Defaults
    "campaigns": {
        "max_per_user": 10,
        "max_characters_per_campaign": 8,
        "default_visibility": "private",
        "allow_invites": True
    },
    
    # Features
    "features": {
        "compendium_enabled": True,
        "allow_homebrew": False,
        "dice_rolling_enabled": True,
        "messaging_enabled": True
    },
    
    # Security
    "security": {
        "session_timeout_minutes": 1440,  # 24 hours
        "max_login_attempts": 5,
        "require_strong_passwords": True,
        "password_min_length": 8
    },
    
    # File Uploads
    "uploads": {
        "max_file_size_mb": 5,
        "allowed_image_types": ["image/png", "image/jpeg", "image/webp", "image/gif"]
    }
}


async def get_settings(db: AsyncSession) -> Dict[str, Any]:
    """
    Get site settings. Creates settings with defaults if they don't exist.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary containing all site settings
    """
    result = await db.execute(select(SiteSettings).where(SiteSettings.id == 1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create settings with defaults
        settings = SiteSettings(id=1, settings=DEFAULT_SETTINGS)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return settings.settings


async def update_settings(
    db: AsyncSession, 
    new_settings: Dict[str, Any], 
    user_id: UUID
) -> Dict[str, Any]:
    """
    Update site settings. Admin only.
    
    Args:
        db: Database session
        new_settings: New settings dictionary
        user_id: ID of user making the update
        
    Returns:
        Updated settings dictionary
    """
    result = await db.execute(select(SiteSettings).where(SiteSettings.id == 1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create if doesn't exist
        settings = SiteSettings(id=1, settings=new_settings, updated_by=user_id)
        db.add(settings)
    else:
        # Update existing
        settings.settings = new_settings
        settings.updated_by = user_id
    
    await db.commit()
    await db.refresh(settings)
    
    return settings.settings


async def get_setting(db: AsyncSession, key: str, default: Any = None) -> Any:
    """
    Get a specific setting value by key.
    
    Args:
        db: Database session
        key: Dot-notation key (e.g., "email.enabled" or "site_name")
        default: Default value if key not found
        
    Returns:
        Setting value or default
    """
    settings = await get_settings(db)
    
    # Support dot notation for nested keys
    keys = key.split('.')
    value = settings
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value
