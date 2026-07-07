from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core import guids as guid_service
from core import template_store
from core.template_store import TemplateSpecError
from database import get_db
from models.compendium import CompendiumEntry
from models.system import System
from models.template import EntryTemplate

router = APIRouter(prefix="/api/templates", tags=["templates"])

# Every entry type gets a required "name" base field — entries are unnameable
# without it (guid generation and search index both rely on it).
NAME_FIELD_SPEC = {
    "name": "name",
    "type": "short_text",
    "required": True,
    "base_field": True,
    "params": {"max_len": 200},
}


class TemplateCreate(BaseModel):
    system: str
    entry_type: str
    label: Optional[str] = None
    description: Optional[str] = None
    fields: List[Dict[str, Any]] = []


class TemplateReplace(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    fields: List[Dict[str, Any]]


def _ensure_name_field(fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for field in fields:
        if isinstance(field, dict) and field.get("name") == "name":
            return list(fields)
    return [dict(NAME_FIELD_SPEC)] + list(fields)


def _validate_fields(system: str, entry_type: str,
                     fields: List[Dict[str, Any]]) -> None:
    """Build the registration, validation model and form schema once so bad
    specs are rejected at write time, not when an entry is submitted."""
    try:
        registration = template_store.registration_from_fields(system, entry_type, fields)
        registration.model()
        registration.form()
    except TemplateSpecError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid template fields: {e}")


async def _validate_system(db: AsyncSession, system: str) -> None:
    result = await db.execute(select(System.guid).where(System.guid == system))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="System not found")


async def _get_template_or_404(db: AsyncSession, system: str,
                               entry_type: str) -> EntryTemplate:
    template = await template_store.get_template(db, system, entry_type)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.get("")
async def list_templates(
    system: Optional[str] = Query(None, description="Filter by system guid"),
    db: AsyncSession = Depends(get_db),
):
    """List entry-type templates (without their field specs)"""
    stmt = select(EntryTemplate).order_by(EntryTemplate.system, EntryTemplate.entry_type)
    if system:
        stmt = stmt.where(EntryTemplate.system == system)
    result = await db.execute(stmt)
    templates = result.scalars().all()
    return {
        "templates": [
            {
                "system": t.system,
                "entry_type": t.entry_type,
                "label": t.label,
                "description": t.description,
                "field_count": len(t.fields or []),
            }
            for t in templates
        ]
    }


@router.get("/{system}/{entry_type}")
async def get_template(system: str, entry_type: str,
                       db: AsyncSession = Depends(get_db)):
    """Get a template including its full field specs"""
    return await _get_template_or_404(db, system, entry_type)


@router.post("", status_code=201)
async def create_template(payload: TemplateCreate,
                          db: AsyncSession = Depends(get_db)):
    """Create a new entry-type template. A required 'name' field is added
    automatically if the spec doesn't include one."""
    await _validate_system(db, payload.system)

    entry_type = guid_service.slugify(payload.entry_type)
    if not entry_type:
        raise HTTPException(status_code=400, detail="Invalid entry_type")

    existing = await template_store.get_template(db, payload.system, entry_type)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Template '{entry_type}' already exists for system '{payload.system}'",
        )

    fields = _ensure_name_field(payload.fields)
    _validate_fields(payload.system, entry_type, fields)

    template = EntryTemplate(
        system=payload.system,
        entry_type=entry_type,
        label=payload.label or entry_type.replace("-", " ").replace("_", " ").title(),
        description=payload.description,
        fields=fields,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.put("/{system}/{entry_type}")
async def replace_template(system: str, entry_type: str,
                           payload: TemplateReplace,
                           db: AsyncSession = Depends(get_db)):
    """Replace a template's label, description and field specs. Existing
    entries are not migrated — they re-validate against the new template on
    their next write (S-07 covers versioning)."""
    template = await _get_template_or_404(db, system, entry_type)

    fields = _ensure_name_field(payload.fields)
    _validate_fields(system, entry_type, fields)

    if payload.label is not None:
        template.label = payload.label
    if payload.description is not None:
        template.description = payload.description
    template.fields = fields

    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/{system}/{entry_type}", status_code=204)
async def delete_template(system: str, entry_type: str,
                          db: AsyncSession = Depends(get_db)):
    """Delete a template. Blocked while entries of this type exist."""
    template = await _get_template_or_404(db, system, entry_type)

    count_stmt = select(func.count()).select_from(CompendiumEntry).where(
        CompendiumEntry.system == system,
        CompendiumEntry.entry_type == entry_type,
    )
    entry_count = (await db.execute(count_stmt)).scalar_one()
    if entry_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete template: {entry_count} entries of this type exist",
        )

    await db.delete(template)
    await db.commit()
    return None
