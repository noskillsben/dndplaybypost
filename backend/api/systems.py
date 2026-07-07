from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from core import guids as guid_service
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


class SystemCreate(BaseModel):
    guid: Optional[str] = None  # Derived from name if omitted
    name: str
    description: Optional[str] = None
    link: Optional[str] = None


@router.get("", response_model=List[SystemResponse])
async def list_systems(db: AsyncSession = Depends(get_db)):
    """List all available game systems"""
    result = await db.execute(select(System))
    systems = result.scalars().all()
    return systems


@router.post("", response_model=SystemResponse, status_code=201)
async def create_system(payload: SystemCreate, db: AsyncSession = Depends(get_db)):
    """Create a new game system (entry-type templates hang off it)"""
    guid = payload.guid or guid_service.slugify(payload.name)
    if not guid:
        raise HTTPException(status_code=400, detail="System guid could not be derived from name")

    existing = await db.execute(select(System).where(System.guid == guid))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"System '{guid}' already exists")

    system = System(
        guid=guid,
        name=payload.name,
        description=payload.description,
        link=payload.link,
    )
    db.add(system)
    await db.commit()
    await db.refresh(system)
    return system


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
