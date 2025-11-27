from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from core.database import get_db
from models.user import User
from models.campaign import Campaign
from models.campaign_member import CampaignMember, RoleEnum
from schemas.schemas import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignMemberResponse,
    MemberAdd,
    MemberUpdateRole
)
from api.deps import get_current_user

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


async def get_campaign_or_404(campaign_id: UUID, db: AsyncSession) -> Campaign:
    """Helper to get campaign or raise 404"""
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.members).selectinload(CampaignMember.user))
        .where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


async def check_is_dm(campaign: Campaign, user: User):
    """Check if user is DM of the campaign"""
    for member in campaign.members:
        if member.user_id == user.id and member.role == RoleEnum.DM:
            return True
    return False


async def check_is_member(campaign: Campaign, user: User):
    """Check if user is a member of the campaign"""
    for member in campaign.members:
        if member.user_id == user.id:
            return True
    return False


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new campaign. Creator automatically becomes DM."""
    # Create campaign
    campaign = Campaign(
        name=campaign_data.name,
        description=campaign_data.description,
        settings=campaign_data.settings,
        created_by=current_user.id
    )
    db.add(campaign)
    await db.flush()  # Get campaign ID
    
    # Add creator as DM
    member = CampaignMember(
        campaign_id=campaign.id,
        user_id=current_user.id,
        role=RoleEnum.DM
    )
    db.add(member)
    
    await db.commit()
    await db.refresh(campaign)
    
    # Load members for response
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.members).selectinload(CampaignMember.user))
        .where(Campaign.id == campaign.id)
    )
    campaign = result.scalar_one()
    
    return CampaignResponse.from_campaign(campaign)


@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all campaigns the current user is a member of."""
    result = await db.execute(
        select(Campaign)
        .join(CampaignMember)
        .options(selectinload(Campaign.members).selectinload(CampaignMember.user))
        .where(CampaignMember.user_id == current_user.id)
        .order_by(Campaign.created_at.desc())
    )
    campaigns = result.scalars().all()
    return [CampaignResponse.from_campaign(c) for c in campaigns]


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get campaign details."""
    campaign = await get_campaign_or_404(campaign_id, db)
    
    # Check if user is a member
    if not await check_is_member(campaign, current_user):
        raise HTTPException(status_code=403, detail="Not a member of this campaign")
    
    return CampaignResponse.from_campaign(campaign)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    campaign_data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update campaign. Only DM can update."""
    campaign = await get_campaign_or_404(campaign_id, db)
    
    # Check if user is DM
    if not await check_is_dm(campaign, current_user):
        raise HTTPException(status_code=403, detail="Only DM can update campaign")
    
    # Update fields
    if campaign_data.name is not None:
        campaign.name = campaign_data.name
    if campaign_data.description is not None:
        campaign.description = campaign_data.description
    if campaign_data.settings is not None:
        campaign.settings = campaign_data.settings
    
    await db.commit()
    
    # Reload with members
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.members).selectinload(CampaignMember.user))
        .where(Campaign.id == campaign.id)
    )
    campaign = result.scalar_one()
    
    return CampaignResponse.from_campaign(campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete campaign. Only DM can delete."""
    campaign = await get_campaign_or_404(campaign_id, db)
    
    # Check if user is DM
    if not await check_is_dm(campaign, current_user):
        raise HTTPException(status_code=403, detail="Only DM can delete campaign")
    
    await db.delete(campaign)
    await db.commit()


@router.post("/{campaign_id}/members", response_model=CampaignMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    campaign_id: UUID,
    member_data: MemberAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a member to the campaign. Only DM can add members."""
    campaign = await get_campaign_or_404(campaign_id, db)
    
    # Check if user is DM
    if not await check_is_dm(campaign, current_user):
        raise HTTPException(status_code=403, detail="Only DM can add members")
    
    # Check if user exists
    result = await db.execute(select(User).where(User.id == member_data.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already a member
    result = await db.execute(
        select(CampaignMember)
        .where(CampaignMember.campaign_id == campaign_id)
        .where(CampaignMember.user_id == member_data.user_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member")
    
    # Add member
    member = CampaignMember(
        campaign_id=campaign_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    db.add(member)
    await db.commit()
    
    # Return member with user info
    result = await db.execute(
        select(CampaignMember)
        .options(selectinload(CampaignMember.user))
        .where(CampaignMember.campaign_id == campaign_id)
        .where(CampaignMember.user_id == member_data.user_id)
    )
    member = result.scalar_one()
    
    return CampaignMemberResponse(
        user_id=member.user_id,
        username=member.user.username,
        role=member.role,
        joined_at=member.joined_at
    )


@router.delete("/{campaign_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    campaign_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a member from the campaign. Only DM can remove members."""
    campaign = await get_campaign_or_404(campaign_id, db)
    
    # Check if user is DM
    if not await check_is_dm(campaign, current_user):
        raise HTTPException(status_code=403, detail="Only DM can remove members")
    
    # Can't remove yourself if you're the only DM
    dm_count = sum(1 for m in campaign.members if m.role == RoleEnum.DM)
    if user_id == current_user.id and dm_count == 1:
        raise HTTPException(status_code=400, detail="Cannot remove the only DM")
    
    # Remove member
    result = await db.execute(
        select(CampaignMember)
        .where(CampaignMember.campaign_id == campaign_id)
        .where(CampaignMember.user_id == user_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    await db.delete(member)
    await db.commit()


@router.patch("/{campaign_id}/members/{user_id}", response_model=CampaignMemberResponse)
async def update_member_role(
    campaign_id: UUID,
    user_id: UUID,
    role_data: MemberUpdateRole,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a member's role. Only DM can update roles."""
    campaign = await get_campaign_or_404(campaign_id, db)
    
    # Check if user is DM
    if not await check_is_dm(campaign, current_user):
        raise HTTPException(status_code=403, detail="Only DM can update member roles")
    
    # Can't demote yourself if you're the only DM
    if user_id == current_user.id and role_data.role != RoleEnum.DM:
        dm_count = sum(1 for m in campaign.members if m.role == RoleEnum.DM)
        if dm_count == 1:
            raise HTTPException(status_code=400, detail="Cannot demote the only DM")
    
    # Update role
    result = await db.execute(
        select(CampaignMember)
        .options(selectinload(CampaignMember.user))
        .where(CampaignMember.campaign_id == campaign_id)
        .where(CampaignMember.user_id == user_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    member.role = role_data.role
    await db.commit()
    await db.refresh(member)
    
    return CampaignMemberResponse(
        user_id=member.user_id,
        username=member.user.username,
        role=member.role,
        joined_at=member.joined_at
    )
