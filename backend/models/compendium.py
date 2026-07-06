from sqlalchemy import Column, String, Text, Boolean, DateTime, Index, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# JSONB on PostgreSQL, plain JSON elsewhere (e.g. SQLite test database)
JSONVariant = JSON().with_variant(JSONB(), "postgresql")

class Compendium(Base):
    """A named container of compendium entries (e.g. "D&D 5e 2014 SRD",
    "Ben's homebrew"). Entries belong to a compendium; games subscribe to
    compendiums (subscription lands with the Game model in EPIC 5)."""
    __tablename__ = "compendiums"

    # Human-readable slug PK, e.g. "d&d5.0-core", "bens-homebrew"
    guid = Column(String(100), primary_key=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # System this compendium's content is for (e.g. "d&d5.0")
    system = Column(String(50), nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    entries = relationship("CompendiumEntry", back_populates="compendium")


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

    # Owning compendium (nullable for legacy/loose entries)
    compendium_guid = Column(String(100), ForeignKey('compendiums.guid'), nullable=True, index=True)
    
    # Metadata
    homebrew = Column(Boolean, default=False, index=True)
    # Source info as JSON: {"name": "PHB", "page": 123, "link": "https://..."}
    source = Column(JSONVariant, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships for hierarchy navigation
    parent = relationship("CompendiumEntry", remote_side=[guid], backref="children")
    compendium = relationship("Compendium", back_populates="entries")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_system_type', 'system', 'entry_type'),
        # GIN index on JSONB data (PostgreSQL only; ignored on other dialects)
        Index('idx_compendium_data_gin', 'data', postgresql_using='gin'),
    )


class GuidRedirect(Base):
    """Redirect record left behind when an entry is renamed (old guid -> new guid)."""
    __tablename__ = "guid_redirects"

    old_guid = Column(String(200), primary_key=True)
    new_guid = Column(String(200), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
