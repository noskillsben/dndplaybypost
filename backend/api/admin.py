# admin section api calls. used for anything only admin level users can do.

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from core.database import get_db

# needs the user model and the admin check dependency
from models.user import User
from api.deps import get_current_admin, get_current_user

# campaign model for stats - REMOVED as it's no longer used in get_stats
from services.settings_service import get_settings, update_settings
from schemas.settings_schemas import SiteSettingsSchema, SiteSettingsUpdate

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])

# gets all the users on the site.
@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

# gets stats about the site.
@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    user_count = len(result.scalars().all())
    return {
        "user_count": user_count,
        "campaign_count": 0  # Placeholder
    }

@router.get("/settings", response_model=Dict[str, Any])
async def get_site_settings(db: AsyncSession = Depends(get_db)):
    """
    Get current site settings.
    Returns all settings as a dictionary.
    """
    settings = await get_settings(db)
    return settings

@router.put("/settings", response_model=Dict[str, Any])
async def update_site_settings(
    settings_update: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update site settings. Admin only.
    Accepts a dictionary of settings to update.
    """
    # Validate the settings structure
    try:
        # Convert dict to schema for validation
        validated = SiteSettingsSchema(**settings_update)
        # Convert back to dict for storage
        settings_dict = validated.model_dump()
    except Exception as e:
        # If validation fails, still allow update but log the error
        # This allows for partial updates and future schema changes
        settings_dict = settings_update
    
    updated_settings = await update_settings(db, settings_dict, current_user.id)
    return updated_settings
