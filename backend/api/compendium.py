from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Dict, Any
from models.compendium import CompendiumEntry
from database import get_db
from api.schemas import SCHEMA_REGISTRY
import datetime

from pydantic import BaseModel

router = APIRouter(prefix="/api/compendium", tags=["compendium"])

class CompendiumCreate(BaseModel):
    system: str
    entry_type: str
    name: str  # Included explicitly for easier GUID generation and search indexing
    data: Dict[str, Any]
    homebrew: bool = False
    source: str = "Unknown"

@router.get("/")
async def list_entries(
    system: Optional[str] = None,
    entry_type: Optional[str] = None,
    search: Optional[str] = None,
    homebrew: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List compendium entries with filters"""
    stmt = select(CompendiumEntry)
    
    if system:
        stmt = stmt.where(CompendiumEntry.system == system)
    if entry_type:
        stmt = stmt.where(CompendiumEntry.entry_type == entry_type)
    if search:
        stmt = stmt.where(CompendiumEntry.name.ilike(f"%{search}%"))
    if homebrew is not None:
        stmt = stmt.where(CompendiumEntry.homebrew == homebrew)
    
    # Order by name
    stmt = stmt.order_by(CompendiumEntry.name)
    
    result = await db.execute(stmt)
    entries = result.scalars().all()
    return {"entries": entries}

@router.get("/{guid}")
async def get_entry(guid: str, db: AsyncSession = Depends(get_db)):
    """Get a specific compendium entry"""
    result = await db.execute(select(CompendiumEntry).where(CompendiumEntry.guid == guid))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.post("/", status_code=201)
async def create_entry(
    payload: CompendiumCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new compendium entry"""
    # 1. Validate against schema
    if payload.system not in SCHEMA_REGISTRY:
        raise HTTPException(status_code=400, detail="Invalid system")
    if payload.entry_type not in SCHEMA_REGISTRY[payload.system]:
        raise HTTPException(status_code=400, detail="Invalid entry type")
    
    schema_def = SCHEMA_REGISTRY[payload.system][payload.entry_type]
    Model = schema_def.model()
    
    try:
        # Ensure name is in data for validation if the schema expects it
        data_to_validate = payload.data.copy()
        if "name" not in data_to_validate:
            data_to_validate["name"] = payload.name
            
        validated = Model(**data_to_validate)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    
    # 2. Generate GUID from name
    guid_base = f"{payload.system}-{payload.entry_type}-{payload.name.lower().replace(' ', '-')}"
    guid = guid_base
    
    # 3. Check for duplicates and increment if needed
    counter = 1
    while True:
        check = await db.execute(select(CompendiumEntry).where(CompendiumEntry.guid == guid))
        if not check.scalar_one_or_none():
            break
        guid = f"{guid_base}-{counter}"
        counter += 1
    
    # 4. Create entry
    entry = CompendiumEntry(
        guid=guid,
        system=payload.system,
        entry_type=payload.entry_type,
        name=payload.name,
        data=validated.model_dump(),
        homebrew=payload.homebrew,
        source=payload.source
    )
    
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    
    return entry

@router.delete("/{guid}", status_code=204)
async def delete_entry(guid: str, db: AsyncSession = Depends(get_db)):
    """Delete a compendium entry"""
    result = await db.execute(select(CompendiumEntry).where(CompendiumEntry.guid == guid))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    await db.delete(entry)
    await db.commit()
    return None
