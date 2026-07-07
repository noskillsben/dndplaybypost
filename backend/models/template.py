from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from database import Base

JSONVariant = JSON().with_variant(JSONB(), "postgresql")


class EntryTemplate(Base):
    """Data-driven entry-type template: the fields that define a content type
    (spell, class, rollable table...). Stored as data so users can create and
    edit types in the browser; Python definitions in schemas/systems/ are only
    seed data for this table."""
    __tablename__ = "entry_templates"

    system = Column(String(50), primary_key=True)
    entry_type = Column(String(50), primary_key=True)

    # Display name (defaults to entry_type) and optional description
    label = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)

    # List of field specs:
    # [{"name": ..., "type": ..., "required": bool, "base_field": bool, "params": {...}}]
    fields = Column(JSONVariant, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
