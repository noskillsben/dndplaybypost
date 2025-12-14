from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from core.database import Base


class Character(Base):
    __tablename__ = "characters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    avatar_url = Column(String(500))  # Optional character image
    sheet_data = Column(JSONB, nullable=False, default={})  # Flexible character data
    schema_version = Column(Integer, nullable=False, default=1)  # Version of sheet_data structure
    system = Column(String(50), default='dnd5e_2024')  # Game system identifier
    sheet_version = Column(DateTime(timezone=True), default=func.now())  # Last structural change
    compendium_version = Column(DateTime(timezone=True))  # Last content update check
    notes = Column(Text)  # DM/player notes

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="characters")
    player = relationship("User", back_populates="characters")
    messages = relationship("Message", back_populates="character")
