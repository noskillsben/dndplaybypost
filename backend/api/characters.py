from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from models.user import User
from models.campaign import Campaign
from models.campaign_member import CampaignMember, RoleEnum
from models.character import Character
from schemas.schemas import CharacterCreate, CharacterUpdate, CharacterResponse
from api.deps import get_current_user

router = APIRouter(prefix="/characters", tags=["characters"])


async def get_character_or_404(character_id: UUID, db: AsyncSession) -> Character:
    """Helper to get character or raise 404"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


async def check_can_modify_character(character: Character, user: User, db: AsyncSession) -> bool:
    """Check if user can modify character (owner or DM)"""
    # Owner can always modify
    if character.player_id == user.id:
        return True
    
    # Check if user is DM of the campaign
    result = await db.execute(
        select(CampaignMember)
        .where(CampaignMember.campaign_id == character.campaign_id)
        .where(CampaignMember.user_id == user.id)
        .where(CampaignMember.role == RoleEnum.DM)
    )
    return result.scalar_one_or_none() is not None


@router.post("", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    character_data: CharacterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new character."""
    # Check if campaign exists and user is a member
    result = await db.execute(
        select(Campaign)
        .join(CampaignMember)
        .where(Campaign.id == character_data.campaign_id)
        .where(CampaignMember.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found or you are not a member")
    
    # Create character
    character = Character(
        campaign_id=character_data.campaign_id,
        player_id=current_user.id,
        name=character_data.name,
        avatar_url=character_data.avatar_url,
        sheet_data=character_data.sheet_data,
        notes=character_data.notes
    )
    db.add(character)
    await db.commit()
    await db.refresh(character)
    
    return character


@router.get("", response_model=List[CharacterResponse])
async def list_characters(
    campaign_id: Optional[UUID] = Query(None, description="Filter by campaign ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List characters. Optionally filter by campaign."""
    query = select(Character).where(Character.player_id == current_user.id)
    
    if campaign_id:
        # Verify user is a member of the campaign
        result = await db.execute(
            select(CampaignMember)
            .where(CampaignMember.campaign_id == campaign_id)
            .where(CampaignMember.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not a member of this campaign")
        
        query = query.where(Character.campaign_id == campaign_id)
    
    query = query.order_by(Character.created_at.desc())
    result = await db.execute(query)
    characters = result.scalars().all()
    
    return characters


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get character details."""
    character = await get_character_or_404(character_id, db)
    
    # Check if user is a member of the campaign
    result = await db.execute(
        select(CampaignMember)
        .where(CampaignMember.campaign_id == character.campaign_id)
        .where(CampaignMember.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this campaign")
    
    return character


@router.patch("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: UUID,
    character_data: CharacterUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update character. Only owner or DM can update."""
    character = await get_character_or_404(character_id, db)
    
    # Check permissions
    if not await check_can_modify_character(character, current_user, db):
        raise HTTPException(status_code=403, detail="Not authorized to modify this character")
    
    # Update fields
    if character_data.name is not None:
        character.name = character_data.name
    if character_data.avatar_url is not None:
        character.avatar_url = character_data.avatar_url
    if character_data.sheet_data is not None:
        character.sheet_data = character_data.sheet_data
    if character_data.notes is not None:
        character.notes = character_data.notes
    
    await db.commit()
    await db.refresh(character)
    
    return character


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete character. Only owner or DM can delete."""
    character = await get_character_or_404(character_id, db)
    
    # Check permissions
    if not await check_can_modify_character(character, current_user, db):
        raise HTTPException(status_code=403, detail="Not authorized to delete this character")
    
    await db.delete(character)
    await db.commit()
