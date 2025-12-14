from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from core.database import Base


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"), nullable=True)  # Optional: posted as character
    content = Column(Text, nullable=False)
    is_ic = Column(Boolean, default=True)  # In-character vs out-of-character
    extra_data = Column(JSONB, default={})  # Dice rolls, attachments, etc.
    schema_version = Column(Integer, nullable=False, default=1)  # Version of extra_data structure
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="messages")
    user = relationship("User")
    character = relationship("Character", back_populates="messages")
