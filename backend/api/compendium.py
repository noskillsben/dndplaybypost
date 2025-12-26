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
    parent_guid: Optional[str] = None  # For hierarchical entries
    guid: Optional[str] = None  # Optional custom GUID (will auto-generate if not provided)
    homebrew: bool = False
    source: Optional[Dict[str, Any]] = None  # e.g., {"name": "PHB", "page": 123, "link": "https://..."}

@router.get("/")
async def list_entries(
    system: Optional[str] = None,
    entry_type: Optional[str] = None,
    search: Optional[str] = None,
    homebrew: Optional[bool] = None,
    parent_guid: Optional[str] = Query(None, description="Filter by parent GUID, use 'null' for top-level entries"),
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
    if parent_guid is not None:
        if parent_guid.lower() == "null":
            stmt = stmt.where(CompendiumEntry.parent_guid.is_(None))
        else:
            stmt = stmt.where(CompendiumEntry.parent_guid == parent_guid)
    
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
    # 1. Validate parent_guid if provided
    if payload.parent_guid:
        parent_check = await db.execute(
            select(CompendiumEntry).where(CompendiumEntry.guid == payload.parent_guid)
        )
        if not parent_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Parent entry not found")
    
    # 2. Validate against schema
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
    
    # 3. Generate or use custom GUID
    if payload.guid:
        # Use custom GUID if provided
        guid = payload.guid
        # Check if it already exists
        check = await db.execute(select(CompendiumEntry).where(CompendiumEntry.guid == guid))
        if check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"GUID '{guid}' already exists")
    else:
        # Auto-generate GUID from name
        guid_base = f"{payload.system}-{payload.entry_type}-{payload.name.lower().replace(' ', '-')}"
        guid = guid_base
        
        # 4. Check for duplicates and increment if needed
        counter = 1
        while True:
            check = await db.execute(select(CompendiumEntry).where(CompendiumEntry.guid == guid))
            if not check.scalar_one_or_none():
                break
            guid = f"{guid_base}-{counter}"
            counter += 1
    
    # 5. Create entry
    entry = CompendiumEntry(
        guid=guid,
        system=payload.system,
        entry_type=payload.entry_type,
        name=payload.name,
        data=validated.model_dump(),
        parent_guid=payload.parent_guid,
        homebrew=payload.homebrew,
        source=payload.source
    )
    
    db.add(entry)
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
