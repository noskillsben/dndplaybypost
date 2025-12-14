from sqlalchemy import Column, Integer, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from core.database import Base


class SiteSettings(Base):
    """
    Singleton table for storing site-wide settings.
    Only one row with id=1 should ever exist.
    """
    __tablename__ = "site_settings"
    
    id = Column(Integer, primary_key=True, default=1)
    settings = Column(JSONB, nullable=False, default={})
    schema_version = Column(Integer, nullable=False, default=1)  # Version of settings structure
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Enforce singleton pattern at database level
    __table_args__ = (
        CheckConstraint('id = 1', name='singleton_site_settings'),
    )
    
    # Relationship to track who last updated settings
    updater = relationship("User")
