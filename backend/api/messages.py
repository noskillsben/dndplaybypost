from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import datetime, timedelta

from core.database import get_db
from models.user import User
from models.campaign import Campaign
from models.campaign_member import CampaignMember, RoleEnum
from models.message import Message
from models.character import Character
from schemas.schemas import MessageCreate, MessageUpdate, MessageResponse
from api.deps import get_current_user

# Router for campaign-scoped message endpoints
campaign_messages_router = APIRouter(prefix="/campaigns", tags=["messages"])

# Router for message-specific endpoints
messages_router = APIRouter(prefix="/messages", tags=["messages"])

# Allow editing messages for 15 minutes after creation
EDIT_TIME_LIMIT = timedelta(minutes=15)


@campaign_messages_router.post("/{campaign_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    campaign_id: UUID,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a message in a campaign."""
    # Check if user is a member of the campaign
    result = await db.execute(
        select(CampaignMember)
        .where(CampaignMember.campaign_id == campaign_id)
        .where(CampaignMember.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this campaign")
    
    # If posting as a character, verify ownership
    if message_data.character_id:
        result = await db.execute(
            select(Character)
            .where(Character.id == message_data.character_id)
            .where(Character.campaign_id == campaign_id)
            .where(Character.player_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Character not found or not owned by you")
    
    # Create message
    message = Message(
        campaign_id=campaign_id,
        user_id=current_user.id,
        character_id=message_data.character_id,
        content=message_data.content,
        is_ic=message_data.is_ic,
        extra_data=message_data.extra_data
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return message


@campaign_messages_router.get("/{campaign_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    campaign_id: UUID,
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List messages in a campaign (paginated)."""
    # Check if user is a member of the campaign
    result = await db.execute(
        select(CampaignMember)
        .where(CampaignMember.campaign_id == campaign_id)
        .where(CampaignMember.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this campaign")
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.campaign_id == campaign_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    messages = result.scalars().all()
    
    return messages


@messages_router.patch("/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: UUID,
    message_data: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a message. Only owner can edit, and only within time limit."""
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user is the owner
    if message.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this message")
    
    # Check time limit
    time_since_creation = datetime.utcnow() - message.created_at.replace(tzinfo=None)
    if time_since_creation > EDIT_TIME_LIMIT:
        raise HTTPException(status_code=403, detail="Edit time limit exceeded")
    
    # Update message
    message.content = message_data.content
    await db.commit()
    await db.refresh(message)
    
    return message


@messages_router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a message. Owner or DM can delete."""
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user is owner
    is_owner = message.user_id == current_user.id
    
    # Check if user is DM
    is_dm = False
    if not is_owner:
        result = await db.execute(
            select(CampaignMember)
            .where(CampaignMember.campaign_id == message.campaign_id)
            .where(CampaignMember.user_id == current_user.id)
            .where(CampaignMember.role == RoleEnum.DM)
        )
        is_dm = result.scalar_one_or_none() is not None
    
    if not is_owner and not is_dm:
        raise HTTPException(status_code=403, detail="Not authorized to delete this message")
    
    await db.delete(message)
    await db.commit()
