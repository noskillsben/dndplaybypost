from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.guids import slugify
from database import get_db
from models.compendium import Compendium, CompendiumEntry

router = APIRouter(prefix="/api/compendiums", tags=["compendiums"])


class CompendiumCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    system: str = Field(min_length=1, max_length=50)
    description: Optional[str] = None
    guid: Optional[str] = None


class CompendiumUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None


def _serialize(compendium: Compendium, entry_count: int) -> dict:
    return {
        "guid": compendium.guid,
        "name": compendium.name,
        "description": compendium.description,
        "system": compendium.system,
        "entry_count": entry_count,
        "created_at": compendium.created_at,
        "updated_at": compendium.updated_at,
    }


async def _entry_count(db: AsyncSession, guid: str) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(CompendiumEntry)
        .where(CompendiumEntry.compendium_guid == guid)
    )
    return result.scalar_one()


async def _get_or_404(db: AsyncSession, guid: str) -> Compendium:
    result = await db.execute(select(Compendium).where(Compendium.guid == guid))
    compendium = result.scalar_one_or_none()
    if not compendium:
        raise HTTPException(status_code=404, detail="Compendium not found")
    return compendium


@router.get("")
async def list_compendiums(system: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """List compendiums with entry counts, optionally filtered by system."""
    stmt = (
        select(Compendium, func.count(CompendiumEntry.guid))
        .outerjoin(CompendiumEntry, CompendiumEntry.compendium_guid == Compendium.guid)
        .group_by(Compendium.guid)
        .order_by(Compendium.name)
    )
    if system:
        stmt = stmt.where(Compendium.system == system)
    result = await db.execute(stmt)
    return {"compendiums": [_serialize(c, n) for c, n in result.all()]}


@router.get("/{guid}")
async def get_compendium(guid: str, db: AsyncSession = Depends(get_db)):
    compendium = await _get_or_404(db, guid)
    return _serialize(compendium, await _entry_count(db, guid))


@router.post("", status_code=201)
async def create_compendium(payload: CompendiumCreate, db: AsyncSession = Depends(get_db)):
    guid = payload.guid or slugify(payload.name)
    existing = await db.execute(select(Compendium.guid).where(Compendium.guid == guid))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Compendium '{guid}' already exists")

    compendium = Compendium(
        guid=guid,
        name=payload.name,
        description=payload.description,
        system=payload.system,
    )
    db.add(compendium)
    await db.commit()
    await db.refresh(compendium)
    return _serialize(compendium, 0)


@router.patch("/{guid}")
async def update_compendium(guid: str, payload: CompendiumUpdate, db: AsyncSession = Depends(get_db)):
    compendium = await _get_or_404(db, guid)
    provided = payload.model_fields_set
    if "name" in provided and payload.name:
        compendium.name = payload.name
    if "description" in provided:
        compendium.description = payload.description
    await db.commit()
    await db.refresh(compendium)
    return _serialize(compendium, await _entry_count(db, guid))


@router.delete("/{guid}", status_code=204)
async def delete_compendium(guid: str, db: AsyncSession = Depends(get_db)):
    compendium = await _get_or_404(db, guid)
    count = await _entry_count(db, guid)
    if count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Compendium contains {count} entries; delete or move them first",
        )
    await db.delete(compendium)
    await db.commit()
    return None
