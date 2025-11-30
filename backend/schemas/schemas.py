from pydantic import BaseModel, Field, UUID4, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from models.campaign_member import RoleEnum


# Campaign Schemas
class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class CampaignMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: UUID4
    username: str
    role: RoleEnum
    joined_at: datetime


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID4
    name: str
    description: Optional[str]
    settings: Dict[str, Any]
    created_by: UUID4
    created_at: datetime
    updated_at: Optional[datetime]
    members: List[CampaignMemberResponse] = []
    
    @classmethod
    def from_campaign(cls, campaign):
        """Create CampaignResponse from Campaign model"""
        members_data = [
            CampaignMemberResponse(
                user_id=member.user_id,
                username=member.user.username,
                role=member.role,
                joined_at=member.joined_at
            )
            for member in campaign.members
        ]
        
        return cls(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            settings=campaign.settings,
            created_by=campaign.created_by,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            members=members_data
        )


# Character Schemas
class CharacterCreate(BaseModel):
    campaign_id: UUID4
    name: str = Field(..., min_length=1, max_length=255)
    avatar_url: Optional[str] = None
    sheet_data: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class CharacterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    avatar_url: Optional[str] = None
    sheet_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class CharacterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID4
    campaign_id: UUID4
    player_id: UUID4
    name: str
    avatar_url: Optional[str]
    sheet_data: Dict[str, Any]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


# Message Schemas
class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    character_id: Optional[UUID4] = None
    is_ic: bool = True
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class MessageUpdate(BaseModel):
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID4
    campaign_id: UUID4
    user_id: UUID4
    character_id: Optional[UUID4]
    content: str
    is_ic: bool
    extra_data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]


# Member Management Schemas
class MemberAdd(BaseModel):
    user_id: UUID4
    role: RoleEnum = RoleEnum.PLAYER


class MemberUpdateRole(BaseModel):
    role: RoleEnum


class UserSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID4
    username: str


# WebSocket Schemas
class DiceRollData(BaseModel):
    """Dice roll data for message extra_data"""
    expression: str
    total: int
    rolls: List[int]
    breakdown: str


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str  # "message", "user_joined", "user_left", "error"
    data: Dict[str, Any]
