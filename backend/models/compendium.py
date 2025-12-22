from sqlalchemy import Column, String, Text, JSON, Boolean, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class CompendiumEntry(Base):
    __tablename__ = "compendium"
    
    # Human-readable GUID as primary key
    # Format: {system}-{entry_type}-{identifier}
    guid = Column(String(200), primary_key=True)
    
    # System identifier (e.g., "d&d5.0", "d&d5.2", "lasers-and-feelings")
    system = Column(String(50), nullable=False, index=True)
    
    # Entry type (e.g., "item", "spell", "class", "basic-rule")
    entry_type = Column(String(50), nullable=False, index=True)
    
    # Searchable name
    name = Column(String(200), nullable=False, index=True)
    
    # JSONB data matching the schema for this system/entry_type
    data = Column(JSON, nullable=False)
    
    # Hierarchical relationship - parent entry GUID
    parent_guid = Column(String(200), ForeignKey('compendium.guid'), nullable=True, index=True)
    
    # Metadata
    homebrew = Column(Boolean, default=False, index=True)
    source = Column(String(100))  # "PHB", "DMG", etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships for hierarchy navigation
    parent = relationship("CompendiumEntry", remote_side=[guid], backref="children")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_system_type', 'system', 'entry_type'),
    )
