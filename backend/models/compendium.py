from sqlalchemy import Column, String, Text, Boolean, DateTime, Index, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# JSONB on PostgreSQL, plain JSON elsewhere (e.g. SQLite test database)
JSONVariant = JSON().with_variant(JSONB(), "postgresql")

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
    data = Column(JSONVariant, nullable=False)
    
    # Hierarchical relationship - parent entry GUID
    parent_guid = Column(String(200), ForeignKey('compendium.guid'), nullable=True, index=True)
    
    # Metadata
    homebrew = Column(Boolean, default=False, index=True)
    # Source info as JSON: {"name": "PHB", "page": 123, "link": "https://..."}
    source = Column(JSONVariant, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships for hierarchy navigation
    parent = relationship("CompendiumEntry", remote_side=[guid], backref="children")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_system_type', 'system', 'entry_type'),
        # GIN index on JSONB data (PostgreSQL only; ignored on other dialects)
        Index('idx_compendium_data_gin', 'data', postgresql_using='gin'),
    )
