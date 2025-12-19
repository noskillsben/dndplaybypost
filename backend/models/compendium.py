from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, func, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid
from core.database import Base


class CompendiumItem(Base):
    """
    Stores all D&D content (races, classes, spells, items, features, backgrounds).
    Uses JSONB for flexible content structure with version tracking.
    """
    __tablename__ = "compendium_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), nullable=False, index=True)  # 'race', 'class', 'spell', 'item', 'feature', etc.
    name = Column(String(255), nullable=False, index=True)
    system = Column(String(100), nullable=False, default="D&D 5.2 (2024)", index=True)  # Game system (e.g., "D&D 5e", "D&D 5.2")
    data = Column(JSONB, nullable=False)  # Type-specific structure
    schema_version = Column(Integer, nullable=False, default=1)  # Version of data structure
    version = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_official = Column(Boolean, default=False)  # SRD vs homebrew
    is_active = Column(Boolean, default=True)
    tags = Column(ARRAY(Text), default=list)  # For search/filtering
    
    # Relationships
    creator = relationship("User", back_populates="compendium_items")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_compendium_type', 'type'),
        Index('idx_compendium_system', 'system'),
        Index('idx_compendium_version', 'version'),
        Index('idx_compendium_tags', 'tags', postgresql_using='gin'),
        Index('idx_compendium_data', 'data', postgresql_using='gin'),
        UniqueConstraint('type', 'name', 'system', name='uq_compendium_type_name_system'),
    )



class ComponentTemplate(Base):
    """
    Defines validation schemas for character sheet components.
    Allows extensibility for homebrew and other game systems.
    """
    __tablename__ = "component_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component_type = Column(String(50), nullable=False, unique=True, index=True)  # 'resource', 'attack', 'modifier', etc.
    name = Column(String(255), nullable=False)
    description = Column(Text)
    schema = Column(JSONB, nullable=False)  # JSON Schema for validation
    schema_version = Column(Integer, nullable=False, default=1)  # Version of schema structure
    for_types = Column(ARRAY(Text), default=list)  # Which compendium item types can use this
    version = Column(DateTime(timezone=True), nullable=False, default=func.now())
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_component_type', 'component_type'),
        Index('idx_for_types', 'for_types', postgresql_using='gin'),
    )
