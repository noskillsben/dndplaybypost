from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime
from database import Base

class System(Base):
    __tablename__ = "systems"
    
    # Unique identifier (e.g., "d&d5.0", "d&d5.2")
    guid = Column(String(50), primary_key=True)
    
    # Full name (e.g., "Dungeons & Dragons 5e (2014)")
    name = Column(String(200), nullable=False)
    
    # Description of the system
    description = Column(Text, nullable=True)
    
    # URL to system homepage
    link = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
