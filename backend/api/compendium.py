from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Dict, Any
from models.compendium import CompendiumEntry
from database import get_db
from api.schemas import SCHEMA_REGISTRY
from core import guids as guid_service
import datetime

from pydantic import BaseModel, ValidationError

from core.errors import schema_validation_error

router = APIRouter(prefix="/api/compendium", tags=["compendium"])

class CompendiumCreate(BaseModel):
    system: str
    entry_type: str
    name: str  # Included explicitly for easier GUID generation and search indexing
    data: Dict[str, Any]
    parent_guid: Optional[str] = None  # For hierarchical entries
    guid: Optional[str] = None  # Optional custom GUID (will auto-generate if not provided)
    guid_suffix: Optional[str] = None  # Optional disambiguating suffix, e.g. "srd"
    homebrew: bool = False
    source: Optional[Dict[str, Any]] = None  # e.g., {"name": "PHB", "page": 123, "link": "https://..."}

class CompendiumRename(BaseModel):
    new_name: str
    guid_suffix: Optional[str] = None

class CompendiumReplace(BaseModel):
    name: str
    data: Dict[str, Any]
    parent_guid: Optional[str] = None
    homebrew: bool = False
    source: Optional[Dict[str, Any]] = None

class CompendiumPatch(BaseModel):
    name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    parent_guid: Optional[str] = None
    homebrew: Optional[bool] = None
    source: Optional[Dict[str, Any]] = None


async def _get_entry_or_404(db: AsyncSession, guid: str) -> CompendiumEntry:
    resolved = await guid_service.resolve_guid(db, guid)
    result = await db.execute(select(CompendiumEntry).where(CompendiumEntry.guid == resolved))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


async def _validate_parent(db: AsyncSession, parent_guid: str, self_guid: Optional[str] = None):
    if self_guid is not None and parent_guid == self_guid:
        raise HTTPException(status_code=400, detail="Entry cannot be its own parent")
    parent_check = await db.execute(
        select(CompendiumEntry).where(CompendiumEntry.guid == parent_guid)
    )
    if not parent_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Parent entry not found")


def _validate_data(system: str, entry_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    if system not in SCHEMA_REGISTRY:
        raise HTTPException(status_code=400, detail="Invalid system")
    if entry_type not in SCHEMA_REGISTRY[system]:
        raise HTTPException(status_code=400, detail="Invalid entry type")
    Model = SCHEMA_REGISTRY[system][entry_type].model()
    try:
        return Model(**data).model_dump()
    except ValidationError as e:
        raise schema_validation_error(e)

@router.get("/")
async def list_entries(
    system: Optional[str] = None,
    entry_type: Optional[str] = None,
    search: Optional[str] = None,
    homebrew: Optional[bool] = None,
    parent_guid: Optional[str] = Query(None, description="Filter by parent GUID, use 'null' for top-level entries"),
    guid_prefix: Optional[str] = Query(None, description="Filter by GUID prefix, e.g. 'd&d5.0-rule-'"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List compendium entries with filters and pagination"""
    filters = []

    if system:
        filters.append(CompendiumEntry.system == system)
    if entry_type:
        filters.append(CompendiumEntry.entry_type == entry_type)
    if search:
        filters.append(CompendiumEntry.name.ilike(f"%{search}%"))
    if homebrew is not None:
        filters.append(CompendiumEntry.homebrew == homebrew)
    if parent_guid is not None:
        if parent_guid.lower() == "null":
            filters.append(CompendiumEntry.parent_guid.is_(None))
        else:
            filters.append(CompendiumEntry.parent_guid == parent_guid)
    if guid_prefix:
        filters.append(CompendiumEntry.guid.startswith(guid_prefix, autoescape=True))

    count_stmt = select(func.count()).select_from(CompendiumEntry).where(*filters)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(CompendiumEntry)
        .where(*filters)
        .order_by(CompendiumEntry.name)
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()
    return {"entries": entries, "total": total, "limit": limit, "offset": offset}

@router.get("/{guid}")
async def get_entry(guid: str, db: AsyncSession = Depends(get_db)):
    """Get a specific compendium entry (follows rename redirects)"""
    return await _get_entry_or_404(db, guid)

@router.post("/", status_code=201)
async def create_entry(
    payload: CompendiumCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new compendium entry"""
    # 1. Validate parent_guid if provided
    if payload.parent_guid:
        parent_check = await db.execute(
            select(CompendiumEntry).where(CompendiumEntry.guid == payload.parent_guid)
        )
        if not parent_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Parent entry not found")
    
    # 2. Validate against schema (name injected if the payload didn't repeat it)
    data_to_validate = payload.data.copy()
    data_to_validate.setdefault("name", payload.name)
    validated_data = _validate_data(payload.system, payload.entry_type, data_to_validate)
    
    # 3. Generate or use custom GUID
    if payload.guid:
        # Use custom GUID if provided
        guid = payload.guid
        if await guid_service.guid_in_use(db, guid):
            raise HTTPException(status_code=400, detail=f"GUID '{guid}' already exists")
    else:
        # Auto-generate GUID from name (slugified), with collision handling
        guid = await guid_service.generate_unique_guid(
            db, payload.system, payload.entry_type, payload.name,
            suffix=payload.guid_suffix,
        )
    
    # 5. Create entry
    entry = CompendiumEntry(
        guid=guid,
        system=payload.system,
        entry_type=payload.entry_type,
        name=payload.name,
        data=validated_data,
        parent_guid=payload.parent_guid,
        homebrew=payload.homebrew,
        source=payload.source
    )
    
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    
    return entry

@router.put("/{guid}")
async def replace_entry(
    guid: str,
    payload: CompendiumReplace,
    db: AsyncSession = Depends(get_db)
):
    """Full replace of an entry's content (guid stays stable; use /rename to change it)"""
    entry = await _get_entry_or_404(db, guid)

    if payload.parent_guid:
        await _validate_parent(db, payload.parent_guid, self_guid=entry.guid)

    data_to_validate = payload.data.copy()
    data_to_validate.setdefault("name", payload.name)
    validated = _validate_data(entry.system, entry.entry_type, data_to_validate)

    entry.name = payload.name
    entry.data = validated
    entry.parent_guid = payload.parent_guid
    entry.homebrew = payload.homebrew
    entry.source = payload.source

    await db.commit()
    await db.refresh(entry)
    return entry

@router.patch("/{guid}")
async def patch_entry(
    guid: str,
    payload: CompendiumPatch,
    db: AsyncSession = Depends(get_db)
):
    """Partial update: provided data keys are merged into existing data,
    then the merged result is re-validated against the entry-type template."""
    entry = await _get_entry_or_404(db, guid)
    provided = payload.model_fields_set

    if "parent_guid" in provided and payload.parent_guid:
        await _validate_parent(db, payload.parent_guid, self_guid=entry.guid)

    merged = dict(entry.data)
    if payload.data is not None:
        merged.update(payload.data)
    if "name" in provided and payload.name:
        merged["name"] = payload.name
    validated = _validate_data(entry.system, entry.entry_type, merged)

    entry.data = validated
    if "name" in provided and payload.name:
        entry.name = payload.name
    if "parent_guid" in provided:
        entry.parent_guid = payload.parent_guid
    if "homebrew" in provided and payload.homebrew is not None:
        entry.homebrew = payload.homebrew
    if "source" in provided:
        entry.source = payload.source

    await db.commit()
    await db.refresh(entry)
    return entry

@router.post("/{guid}/rename")
async def rename_entry(
    guid: str,
    payload: CompendiumRename,
    db: AsyncSession = Depends(get_db)
):
    """Rename an entry: assigns a new guid derived from the new name and
    leaves a redirect record so the old guid keeps resolving."""
    entry = await _get_entry_or_404(db, guid)

    entry = await guid_service.rename_entry(
        db, entry, payload.new_name, suffix=payload.guid_suffix
    )
    await db.commit()
    await db.refresh(entry)
    return entry

@router.get("/{guid}/children")
async def get_children(guid: str, db: AsyncSession = Depends(get_db)):
    """Get all direct children of an entry"""
    # Verify parent exists
    parent_result = await db.execute(select(CompendiumEntry).where(CompendiumEntry.guid == guid))
    parent = parent_result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Get children
    children_result = await db.execute(
        select(CompendiumEntry)
        .where(CompendiumEntry.parent_guid == guid)
        .order_by(CompendiumEntry.name)
    )
    children = children_result.scalars().all()
    return {"parent": parent, "children": children}

@router.get("/{guid}/tree")
async def get_tree(guid: str, max_depth: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """Get full subtree (recursive) starting from this entry"""
    async def build_tree(entry_guid: str, current_depth: int = 0):
        result = await db.execute(select(CompendiumEntry).where(CompendiumEntry.guid == entry_guid))
        entry = result.scalar_one_or_none()
        if not entry:
            return None
        
        entry_dict = {
            "guid": entry.guid,
            "system": entry.system,
            "entry_type": entry.entry_type,
            "name": entry.name,
            "data": entry.data,
            "parent_guid": entry.parent_guid,
            "homebrew": entry.homebrew,
            "source": entry.source,
            "children": []
        }
        
        # Recursively get children if not at max depth
        if max_depth is None or current_depth < max_depth:
            children_result = await db.execute(
                select(CompendiumEntry)
                .where(CompendiumEntry.parent_guid == entry_guid)
                .order_by(CompendiumEntry.name)
            )
            children = children_result.scalars().all()
            for child in children:
                child_tree = await build_tree(child.guid, current_depth + 1)
                if child_tree:
                    entry_dict["children"].append(child_tree)
        
        return entry_dict
    
    tree = await build_tree(guid)
    if not tree:
        raise HTTPException(status_code=404, detail="Entry not found")
    return tree

@router.get("/{guid}/ancestors")
async def get_ancestors(guid: str, db: AsyncSession = Depends(get_db)):
    """Get breadcrumb trail from this entry to root"""
    ancestors = []
    current_guid = guid
    
    # Prevent infinite loops (shouldn't happen with proper FK constraints, but safety first)
    max_iterations = 100
    iterations = 0
    
    while current_guid and iterations < max_iterations:
        result = await db.execute(select(CompendiumEntry).where(CompendiumEntry.guid == current_guid))
        entry = result.scalar_one_or_none()
        if not entry:
            if len(ancestors) == 0:
                raise HTTPException(status_code=404, detail="Entry not found")
            break
        
        ancestors.insert(0, entry)  # Insert at beginning to maintain order from root to current
        current_guid = entry.parent_guid
        iterations += 1
    
    return {"ancestors": ancestors}

@router.get("/{guid}/render")
async def render_entry_markdown(
    guid: str,
    max_depth: Optional[int] = None,
    include_categories: Optional[str] = Query(None, description="Comma-separated list of categories to include"),
    db: AsyncSession = Depends(get_db)
):
    """Render entry and its subtree as markdown"""
    from core.markdown_renderer import render_tree
    
    # Parse categories if provided
    categories = None
    if include_categories:
        categories = [c.strip() for c in include_categories.split(",")]
    
    # Render the tree
    markdown = await render_tree(db, guid, max_depth=max_depth, include_categories=categories)
    if not markdown:
        raise HTTPException(status_code=404, detail="Entry not found or no content to render")
    
    return {"markdown": markdown}

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
