from sqlalchemy import Column, String, ForeignKey
from database import Base

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    gm_id = Column(String(50), ForeignKey("users.id"), nullable=False)
