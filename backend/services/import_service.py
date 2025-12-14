"""
Service for importing compendium content from JSON files.
Handles bulk imports, duplicate detection, and version management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from models.compendium import CompendiumItem, ComponentTemplate
from schemas.compendium_schemas import CompendiumItemCreate, ComponentTemplateCreate
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ImportService:
    """Service for importing SRD and homebrew content"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.stats = {
            "total": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }
    
    async def import_from_json_file(
        self,
        file_path: str,
        update_existing: bool = False
    ) -> Dict[str, int]:
        """
        Import compendium items from a JSON file.
        
        Args:
            file_path: Path to JSON file
            update_existing: Whether to update existing items or skip them
            
        Returns:
            Dictionary with import statistics
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both array and single object
            items = data if isinstance(data, list) else [data]
            
            self.stats["total"] = len(items)
            logger.info(f"Importing {len(items)} items from {file_path}")
            
            for item_data in items:
                try:
                    await self._import_single_item(item_data, update_existing)
                except Exception as e:
                    logger.error(f"Error importing item {item_data.get('name', 'unknown')}: {e}")
                    self.stats["errors"] += 1
            
            await self.db.commit()
            logger.info(f"Import complete: {self.stats}")
            return self.stats
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error importing from {file_path}: {e}")
            raise
    
    async def _import_single_item(
        self,
        item_data: Dict[str, Any],
        update_existing: bool = False
    ):
        """Import a single compendium item"""
        
        # Check if item already exists by name and type
        stmt = select(CompendiumItem).where(
            and_(
                CompendiumItem.name == item_data["name"],
                CompendiumItem.type == item_data["type"]
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            if update_existing:
                # Update existing item
                existing.data = item_data["data"]
                existing.tags = item_data.get("tags", [])
                existing.version = datetime.now()
                self.stats["updated"] += 1
                logger.debug(f"Updated: {item_data['name']}")
            else:
                self.stats["skipped"] += 1
                logger.debug(f"Skipped existing: {item_data['name']}")
        else:
            # Create new item
            new_item = CompendiumItem(
                type=item_data["type"],
                name=item_data["name"],
                data=item_data["data"],
                tags=item_data.get("tags", []),
                is_official=item_data.get("is_official", True),
                is_active=item_data.get("is_active", True),
                version=datetime.now()
            )
            self.db.add(new_item)
            self.stats["created"] += 1
            logger.debug(f"Created: {item_data['name']}")
    
    async def import_directory(
        self,
        directory_path: str,
        pattern: str = "*.json",
        update_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Import all JSON files from a directory.
        
        Args:
            directory_path: Path to directory containing JSON files
            pattern: File pattern to match (default: *.json)
            update_existing: Whether to update existing items
            
        Returns:
            Dictionary with overall statistics
        """
        path = Path(directory_path)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        json_files = list(path.glob(pattern))
        logger.info(f"Found {len(json_files)} JSON files in {directory_path}")
        
        overall_stats = {
            "files_processed": 0,
            "total_items": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }
        
        for json_file in json_files:
            logger.info(f"Processing {json_file.name}...")
            self.stats = {"total": 0, "created": 0, "updated": 0, "skipped": 0, "errors": 0}
            
            try:
                file_stats = await self.import_from_json_file(str(json_file), update_existing)
                overall_stats["files_processed"] += 1
                overall_stats["total_items"] += file_stats["total"]
                overall_stats["created"] += file_stats["created"]
                overall_stats["updated"] += file_stats["updated"]
                overall_stats["skipped"] += file_stats["skipped"]
                overall_stats["errors"] += file_stats["errors"]
            except Exception as e:
                logger.error(f"Failed to process {json_file.name}: {e}")
                overall_stats["errors"] += 1
        
        return overall_stats
    
    async def import_srd_content(
        self,
        srd_path: Optional[str] = None,
        update_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Import all SRD content from the default SRD directory.
        
        Args:
            srd_path: Path to SRD directory (defaults to backend/data/srd/)
            update_existing: Whether to update existing items
            
        Returns:
            Dictionary with import statistics
        """
        if srd_path is None:
            srd_path = os.getenv("SRD_DATA_PATH", "backend/data/srd/")
        
        logger.info(f"Importing SRD content from {srd_path}")
        return await self.import_directory(srd_path, update_existing=update_existing)
    
    async def clear_compendium(self, official_only: bool = False):
        """
        Clear all compendium items.
        
        Args:
            official_only: If True, only clear official SRD content
        """
        if official_only:
            stmt = select(CompendiumItem).where(CompendiumItem.is_official == True)
        else:
            stmt = select(CompendiumItem)
        
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        
        for item in items:
            await self.db.delete(item)
        
        await self.db.commit()
        logger.info(f"Cleared {len(items)} compendium items")
        return len(items)
    
    async def import_component_templates(
        self,
        file_path: str
    ) -> Dict[str, int]:
        """
        Import component templates from a JSON file.
        
        Args:
            file_path: Path to component templates JSON file
            
        Returns:
            Dictionary with import statistics
        """
        stats = {"total": 0, "created": 0, "updated": 0, "skipped": 0, "errors": 0}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            
            stats["total"] = len(templates)
            
            for template_data in templates:
                try:
                    # Check if template exists
                    stmt = select(ComponentTemplate).where(
                        ComponentTemplate.component_type == template_data["component_type"]
                    )
                    result = await self.db.execute(stmt)
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        # Update existing template
                        existing.name = template_data["name"]
                        existing.description = template_data.get("description")
                        existing.schema = template_data["schema"]
                        existing.for_types = template_data.get("for_types", [])
                        existing.version = datetime.now()
                        stats["updated"] += 1
                    else:
                        # Create new template
                        new_template = ComponentTemplate(
                            component_type=template_data["component_type"],
                            name=template_data["name"],
                            description=template_data.get("description"),
                            schema=template_data["schema"],
                            for_types=template_data.get("for_types", []),
                            version=datetime.now()
                        )
                        self.db.add(new_template)
                        stats["created"] += 1
                        
                except Exception as e:
                    logger.error(f"Error importing template {template_data.get('component_type')}: {e}")
                    stats["errors"] += 1
            
            await self.db.commit()
            logger.info(f"Component template import complete: {stats}")
            return stats
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error importing component templates: {e}")
            raise


async def check_compendium_empty(db: AsyncSession) -> bool:
    """Check if the compendium is empty"""
    stmt = select(CompendiumItem).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is None
