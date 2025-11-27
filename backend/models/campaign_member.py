from sqlalchemy import Column, String, DateTime, ForeignKey, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from core.database import Base


class RoleEnum(str, enum.Enum):
    DM = "dm"
    PLAYER = "player"
    OBSERVER = "observer"


class CampaignMember(Base):
    __tablename__ = "campaign_members"
    
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.PLAYER)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="members")
    user = relationship("User", back_populates="campaign_memberships")
