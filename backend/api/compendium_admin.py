"""
Admin-only compendium endpoints for importing and managing SRD content.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from services.import_service import ImportService, check_compendium_empty
from services.compendium_service import CompendiumService
from schemas.compendium_schemas import ComponentTemplateCreate
from typing import Dict, Any
import json
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/admin/compendium", tags=["admin", "compendium"])


# TODO: Add admin authentication dependency
# from api.auth import get_current_admin_user
# admin_dep = Depends(get_current_admin_user)


@router.post("/import/srd")
async def import_srd_content(
    update_existing: bool = False,
    db: AsyncSession = Depends(get_db)
    # current_admin: User = admin_dep
):
    """
    Import all SRD content from the default SRD directory.
    
    Requires admin authentication.
    
    Args:
        update_existing: If True, update existing items. If False, skip them.
    """
    service = ImportService(db)
    
    try:
        stats = await service.import_srd_content(update_existing=update_existing)
        return {
            "success": True,
            "message": "SRD content imported successfully",
            "stats": stats
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing SRD content: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/import/file")
async def import_from_file(
    file: UploadFile = File(...),
    update_existing: bool = False,
    db: AsyncSession = Depends(get_db)
    # current_admin: User = admin_dep
):
    """
    Import compendium items from an uploaded JSON file.
    
    Requires admin authentication.
    
    The JSON file should contain an array of compendium items.
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be a JSON file")
    
    try:
        # Read file content
        content = await file.read()
        data = json.loads(content)
        
        # Save to temporary file
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, 'w') as f:
            json.dump(data, f)
        
        # Import from file
        service = ImportService(db)
        stats = await service.import_from_json_file(temp_path, update_existing)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return {
            "success": True,
            "message": f"Imported from {file.filename}",
            "stats": stats
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        logger.error(f"Error importing from file: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/import/templates")
async def import_component_templates(
    db: AsyncSession = Depends(get_db)
    # current_admin: User = admin_dep
):
    """
    Import component templates from the SRD directory.
    
    Requires admin authentication.
    """
    service = ImportService(db)
    srd_path = os.getenv("SRD_DATA_PATH", "backend/data/srd/")
    template_file = os.path.join(srd_path, "component_templates.json")
    
    try:
        stats = await service.import_component_templates(template_file)
        return {
            "success": True,
            "message": "Component templates imported successfully",
            "stats": stats
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Component templates file not found: {template_file}"
        )
    except Exception as e:
        logger.error(f"Error importing templates: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.delete("/reset")
async def reset_compendium(
    official_only: bool = False,
    db: AsyncSession = Depends(get_db)
    # current_admin: User = admin_dep
):
    """
    Clear all compendium items and optionally reimport SRD content.
    
    Requires admin authentication.
    
    WARNING: This will delete all compendium items!
    
    Args:
        official_only: If True, only clear official SRD content, keep homebrew
    """
    service = ImportService(db)
    
    try:
        count = await service.clear_compendium(official_only=official_only)
        return {
            "success": True,
            "message": f"Cleared {count} compendium items",
            "items_deleted": count
        }
    except Exception as e:
        logger.error(f"Error clearing compendium: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@router.get("/status")
async def get_import_status(db: AsyncSession = Depends(get_db)):
    """
    Get the current status of the compendium.
    
    Returns information about whether content is loaded, counts, etc.
    """
    is_empty = await check_compendium_empty(db)
    
    if is_empty:
        return {
            "is_empty": True,
            "message": "Compendium is empty. Import SRD content to get started.",
            "auto_import_enabled": os.getenv("AUTO_IMPORT_SRD", "true").lower() == "true"
        }
    
    # Get stats
    service = CompendiumService(db)
    stats = await service.get_stats()
    
    return {
        "is_empty": False,
        "message": "Compendium has content",
        "stats": stats
    }


@router.post("/template")
async def create_component_template(
    template_data: ComponentTemplateCreate,
    db: AsyncSession = Depends(get_db)
    # current_admin: User = admin_dep
):
    """
    Create a new component template.
    
    Requires admin authentication.
    
    Templates define validation rules for character sheet components.
    """
    service = CompendiumService(db)
    
    # Check if template already exists
    existing = await service.get_template(template_data.component_type)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Template for '{template_data.component_type}' already exists"
        )
    
    template = await service.create_template(template_data)
    
    return {
        "success": True,
        "message": f"Created template for {template_data.component_type}",
        "template_id": str(template.id)
    }
