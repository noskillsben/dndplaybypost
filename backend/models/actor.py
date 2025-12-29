import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from database import Base

class Actor(Base):
    __tablename__ = "actors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(String(50), ForeignKey("campaigns.id"), nullable=False, index=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    
    # System metadata
    system_id = Column(String(50), nullable=False)  # e.g., "d&d5.0"
    entity_type = Column(String(50), nullable=False) # e.g., "character", "npc"
    system_version = Column(String(20), nullable=False) # e.g., "1.0.0"
    
    # The raw state of the actor (user input, choices, inventory items)
    # Expected structure:
    # {
    #   "stats": {"strength": 16, ...},
    #   "inventory": [{"id": "uuid", "name": "Sword", "modifiers": [...]}, ...],
    #   "features": [...]
    # }
    raw_data = Column(JSONB, nullable=False, default=dict)
    
    # The computed state of the actor (stats after modifiers, etc.)
    derived_data = Column(JSONB, nullable=False, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
