"""
Service layer for compendium operations.
Handles CRUD, search, filtering, and version management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload
from models.compendium import CompendiumItem, ComponentTemplate
from schemas.compendium_schemas import (
    CompendiumItemCreate,
    CompendiumItemUpdate,
    CompendiumSearchParams,
    ComponentTemplateCreate,
    ComponentTemplateUpdate
)
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CompendiumService:
    """Service for compendium operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_item(
        self,
        item_data: CompendiumItemCreate,
        created_by: Optional[UUID] = None
    ) -> CompendiumItem:
        """Create a new compendium item"""
        new_item = CompendiumItem(
            type=item_data.type,
            name=item_data.name,
            data=item_data.data,
            tags=item_data.tags,
            is_official=item_data.is_official,
            created_by=created_by,
            version=datetime.now()
        )
        self.db.add(new_item)
        await self.db.commit()
        await self.db.refresh(new_item)
        return new_item
    
    async def get_item(self, item_id: UUID) -> Optional[CompendiumItem]:
        """Get a single compendium item by ID"""
        stmt = select(CompendiumItem).where(CompendiumItem.id == item_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_item_by_name(self, name: str, item_type: str) -> Optional[CompendiumItem]:
        """Get a compendium item by name and type"""
        stmt = select(CompendiumItem).where(
            and_(
                CompendiumItem.name == name,
                CompendiumItem.type == item_type
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_item(
        self,
        item_id: UUID,
        item_data: CompendiumItemUpdate
    ) -> Optional[CompendiumItem]:
        """Update a compendium item"""
        item = await self.get_item(item_id)
        if not item:
            return None
        
        update_data = item_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        
        # Update version timestamp
        item.version = datetime.now()
        
        await self.db.commit()
        await self.db.refresh(item)
        return item
    
    async def delete_item(self, item_id: UUID) -> bool:
        """Delete a compendium item"""
        item = await self.get_item(item_id)
        if not item:
            return False
        
        await self.db.delete(item)
        await self.db.commit()
        return True
    
    async def search_items(
        self,
        params: CompendiumSearchParams
    ) -> Tuple[List[CompendiumItem], int]:
        """
        Search and filter compendium items with pagination.
        
        Returns:
            Tuple of (items, total_count)
        """
        # Build base query
        stmt = select(CompendiumItem)
        count_stmt = select(func.count()).select_from(CompendiumItem)
        
        # Apply filters
        filters = []
        
        if params.type:
            filters.append(CompendiumItem.type == params.type)
        
        if params.is_official is not None:
            filters.append(CompendiumItem.is_official == params.is_official)
        
        if params.is_active is not None:
            filters.append(CompendiumItem.is_active == params.is_active)
        
        if params.tags:
            # Item must have all specified tags
            for tag in params.tags:
                filters.append(CompendiumItem.tags.contains([tag]))
        
        if params.query:
            # Search in name and data (JSONB)
            search_filter = or_(
                CompendiumItem.name.ilike(f"%{params.query}%"),
                CompendiumItem.data.astext.ilike(f"%{params.query}%")
            )
            filters.append(search_filter)
        
        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))
        
        # Get total count
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()
        
        # Apply sorting
        sort_column = getattr(CompendiumItem, params.sort_by, CompendiumItem.name)
        if params.sort_order == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(asc(sort_column))
        
        # Apply pagination
        offset = (params.page - 1) * params.page_size
        stmt = stmt.offset(offset).limit(params.page_size)
        
        # Execute query
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        
        return items, total
    
    async def get_items_by_type(
        self,
        item_type: str,
        is_active: bool = True
    ) -> List[CompendiumItem]:
        """Get all items of a specific type"""
        stmt = select(CompendiumItem).where(
            and_(
                CompendiumItem.type == item_type,
                CompendiumItem.is_active == is_active
            )
        ).order_by(CompendiumItem.name)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_items_by_ids(self, item_ids: List[UUID]) -> List[CompendiumItem]:
        """Get multiple items by their IDs"""
        stmt = select(CompendiumItem).where(CompendiumItem.id.in_(item_ids))
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def check_for_updates(
        self,
        item_id: UUID,
        current_version: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a newer version of an item exists.
        
        Returns:
            Dictionary with update info if available, None otherwise
        """
        item = await self.get_item(item_id)
        if not item:
            return None
        
        if item.version > current_version:
            return {
                "item_id": item.id,
                "name": item.name,
                "type": item.type,
                "current_version": current_version,
                "new_version": item.version,
                "has_update": True
            }
        
        return None
    
    # ========================================================================
    # Component Template Operations
    # ========================================================================
    
    async def create_template(
        self,
        template_data: ComponentTemplateCreate
    ) -> ComponentTemplate:
        """Create a new component template"""
        new_template = ComponentTemplate(
            component_type=template_data.component_type,
            name=template_data.name,
            description=template_data.description,
            schema=template_data.schema,
            for_types=template_data.for_types,
            version=datetime.now()
        )
        self.db.add(new_template)
        await self.db.commit()
        await self.db.refresh(new_template)
        return new_template
    
    async def get_template(self, component_type: str) -> Optional[ComponentTemplate]:
        """Get a component template by type"""
        stmt = select(ComponentTemplate).where(
            ComponentTemplate.component_type == component_type
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_templates(
        self,
        is_active: bool = True
    ) -> List[ComponentTemplate]:
        """Get all component templates"""
        stmt = select(ComponentTemplate)
        if is_active is not None:
            stmt = stmt.where(ComponentTemplate.is_active == is_active)
        stmt = stmt.order_by(ComponentTemplate.component_type)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update_template(
        self,
        component_type: str,
        template_data: ComponentTemplateUpdate
    ) -> Optional[ComponentTemplate]:
        """Update a component template"""
        template = await self.get_template(component_type)
        if not template:
            return None
        
        update_data = template_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        
        template.version = datetime.now()
        
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    # ========================================================================
    # Statistics and Utilities
    # ========================================================================
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get compendium statistics"""
        # Count by type
        type_counts_stmt = select(
            CompendiumItem.type,
            func.count(CompendiumItem.id)
        ).group_by(CompendiumItem.type)
        
        type_result = await self.db.execute(type_counts_stmt)
        type_counts = {row[0]: row[1] for row in type_result}
        
        # Count official vs homebrew
        official_stmt = select(func.count()).select_from(CompendiumItem).where(
            CompendiumItem.is_official == True
        )
        homebrew_stmt = select(func.count()).select_from(CompendiumItem).where(
            CompendiumItem.is_official == False
        )
        
        official_result = await self.db.execute(official_stmt)
        homebrew_result = await self.db.execute(homebrew_stmt)
        
        return {
            "total_items": sum(type_counts.values()),
            "by_type": type_counts,
            "official_count": official_result.scalar(),
            "homebrew_count": homebrew_result.scalar()
        }
