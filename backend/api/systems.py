from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from models.system import System
from database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/api/systems", tags=["systems"])


class SystemResponse(BaseModel):
    guid: str
    name: str
    description: str | None
    link: str | None
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[SystemResponse])
async def list_systems(db: AsyncSession = Depends(get_db)):
    """List all available game systems"""
    result = await db.execute(select(System))
    systems = result.scalars().all()
    return systems


@router.get("/{guid}", response_model=SystemResponse)
async def get_system(guid: str, db: AsyncSession = Depends(get_db)):
    """Get details for a specific system"""
    result = await db.execute(
        select(System).where(System.guid == guid)
    )
    system = result.scalar_one_or_none()
    
    if not system:
        raise HTTPException(status_code=404, detail=f"System '{guid}' not found")
    
    return system
