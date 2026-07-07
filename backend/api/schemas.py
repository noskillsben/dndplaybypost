"""Form-schema endpoints, backed by the entry_templates table.

Templates are data (created/edited in-app via /api/templates); the Python
definitions under schemas/systems/ are only seed data loaded by seed_data.py.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core import template_store
from database import get_db
from models.system import System
from models.template import EntryTemplate

router = APIRouter(prefix="/api/schemas", tags=["schemas"])


async def _system_exists(db: AsyncSession, system: str) -> bool:
    result = await db.execute(select(System.guid).where(System.guid == system))
    return result.scalar_one_or_none() is not None


@router.get("/systems")
async def list_systems(db: AsyncSession = Depends(get_db)):
    """List all available systems"""
    result = await db.execute(select(System.guid).order_by(System.guid))
    return {"systems": list(result.scalars().all())}


@router.get("/{system}/types")
async def list_entry_types(system: str, db: AsyncSession = Depends(get_db)):
    """List all entry types for a system"""
    if not await _system_exists(db, system):
        raise HTTPException(status_code=404, detail="System not found")
    result = await db.execute(
        select(EntryTemplate.entry_type)
        .where(EntryTemplate.system == system)
        .order_by(EntryTemplate.entry_type)
    )
    return {"types": list(result.scalars().all())}


@router.get("/{system}/{entry_type}")
async def get_schema(system: str, entry_type: str,
                     db: AsyncSession = Depends(get_db)):
    """Get form schema for a specific system and entry type"""
    registration = await template_store.get_registration(db, system, entry_type)
    if registration is None:
        if not await _system_exists(db, system):
            raise HTTPException(status_code=404, detail="System not found")
        raise HTTPException(status_code=404, detail="Entry type not found")
    return registration.form()
