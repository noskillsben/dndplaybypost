"""
Compendium API endpoints for browsing and managing D&D content.
Public endpoints for all users to browse official and homebrew content.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from services.compendium_service import CompendiumService
from schemas.compendium_schemas import (
    CompendiumItemResponse,
    CompendiumItemCreate,
    CompendiumItemUpdate,
    CompendiumItemList,
    CompendiumSearchParams,
    ComponentTemplateResponse
)
from typing import List, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/compendium", tags=["compendium"])


# ============================================================================
# Compendium Item Endpoints
# ============================================================================

@router.get("/items", response_model=CompendiumItemList)
async def list_compendium_items(
    type: Optional[str] = Query(None, description="Filter by type"),
    system: Optional[str] = Query(None, description="Filter by game system"),
    query: Optional[str] = Query(None, description="Search query"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    is_official: Optional[bool] = Query(None, description="Filter official/homebrew"),
    is_active: Optional[bool] = Query(True, description="Filter active items"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    List compendium items with filtering, search, and pagination.
    """
    service = CompendiumService(db)
    
    search_params = CompendiumSearchParams(
        type=type,
        system=system,
        query=query,
        tags=tags,
        is_official=is_official,
        is_active=is_active,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    items, total = await service.search_items(search_params)
    
    return CompendiumItemList(
        items=[CompendiumItemResponse.from_orm(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total
    )


@router.get("/items/{item_id}", response_model=CompendiumItemResponse)
async def get_compendium_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single compendium item by ID.
    """
    service = CompendiumService(db)
    item = await service.get_item(item_id)
    
    if not item:
        raise HTTPException(status_code=404, detail="Compendium item not found")
    
    return CompendiumItemResponse.from_orm(item)


@router.get("/items/type/{item_type}", response_model=List[CompendiumItemResponse])
async def get_items_by_type(
    item_type: str,
    is_active: bool = Query(True, description="Filter active items"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all compendium items of a specific type.
    
    Common types: race, class, spell, item, feature, background, subclass
    """
    service = CompendiumService(db)
    items = await service.get_items_by_type(item_type, is_active)
    
    return [CompendiumItemResponse.from_orm(item) for item in items]


@router.post("/items", response_model=CompendiumItemResponse, status_code=201)
async def create_compendium_item(
    item_data: CompendiumItemCreate,
    db: AsyncSession = Depends(get_db)
    # TODO: Add authentication dependency
    # current_user: User = Depends(get_current_user)
):
    """
    Create a new compendium item (homebrew content).
    
    Requires authentication. Created items are marked as homebrew by default.
    """
    service = CompendiumService(db)
    
    # Check if item already exists
    existing = await service.get_item_by_name(item_data.name, item_data.type)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Item '{item_data.name}' of type '{item_data.type}' already exists"
        )
    
    # TODO: Set created_by to current_user.id
    new_item = await service.create_item(item_data, created_by=None)
    
    return CompendiumItemResponse.from_orm(new_item)


@router.put("/items/{item_id}", response_model=CompendiumItemResponse)
async def update_compendium_item(
    item_id: UUID,
    item_data: CompendiumItemUpdate,
    db: AsyncSession = Depends(get_db)
    # TODO: Add authentication dependency
    # current_user: User = Depends(get_current_user)
):
    """
    Update a compendium item.
    
    Requires authentication. Users can only update their own homebrew content.
    Admins can update any content.
    """
    service = CompendiumService(db)
    
    # Check if item exists
    existing = await service.get_item(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Compendium item not found")
    
    # TODO: Check permissions (owner or admin)
    # if existing.created_by != current_user.id and not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Not authorized to update this item")
    
    updated_item = await service.update_item(item_id, item_data)
    
    return CompendiumItemResponse.from_orm(updated_item)


@router.delete("/items/{item_id}", status_code=204)
async def delete_compendium_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db)
    # TODO: Add authentication dependency
    # current_user: User = Depends(get_current_user)
):
    """
    Delete a compendium item.
    
    Requires authentication. Users can only delete their own homebrew content.
    Admins can delete any content.
    """
    service = CompendiumService(db)
    
    # Check if item exists
    existing = await service.get_item(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Compendium item not found")
    
    # TODO: Check permissions (owner or admin)
    # if existing.created_by != current_user.id and not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Not authorized to delete this item")
    
    await service.delete_item(item_id)


# ============================================================================
# Component Template Endpoints
# ============================================================================

@router.get("/templates", response_model=List[ComponentTemplateResponse])
async def list_component_templates(
    is_active: bool = Query(True, description="Filter active templates"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all component templates.
    
    Templates define the structure and validation rules for character sheet components.
    """
    service = CompendiumService(db)
    templates = await service.get_all_templates(is_active)
    
    return [ComponentTemplateResponse.from_orm(template) for template in templates]


@router.get("/templates/{component_type}", response_model=ComponentTemplateResponse)
async def get_component_template(
    component_type: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific component template by type.
    
    Common types: resource, modifier, attack, spell_slot
    """
    service = CompendiumService(db)
    template = await service.get_template(component_type)
    
    if not template:
        raise HTTPException(status_code=404, detail="Component template not found")
    
    return ComponentTemplateResponse.from_orm(template)


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get("/stats")
async def get_compendium_stats(db: AsyncSession = Depends(get_db)):
    """
    Get compendium statistics.
    
    Returns counts by type, official vs homebrew, etc.
    """
    service = CompendiumService(db)
    stats = await service.get_stats()
    
    return stats
