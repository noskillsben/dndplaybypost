from fastapi import APIRouter, HTTPException
import importlib
import pkgutil
from pathlib import Path
import logging

router = APIRouter(prefix="/api/schemas", tags=["schemas"])

logger = logging.getLogger(__name__)

# Auto-discover and load all system modules.
SCHEMA_REGISTRY = {}

# scans all the files in the schemas/systems directory and loads them into the registry.
# this is used to dynamically load all the system schemas.
# each system should have a SYSTEM_INFO and SCHEMAS dictionary.
# SYSTEM_INFO should have a guid, name, and description.
# SCHEMAS should have a dictionary of entry types and their corresponding schemas.
# each schema should have a form() method that returns a dictionary of the schema.
# each schema should also have a form_data() method that returns a dictionary of the schema data.



systems_dir = Path(__file__).parent.parent / "schemas" / "systems"
for _, module_name, _ in pkgutil.iter_modules([str(systems_dir)]):
    if module_name.startswith('_'):  # Skip __init__ and private modules
        continue
    
    try:
        module = importlib.import_module(f"schemas.systems.{module_name}")
        
        # Each system module should have SYSTEM_INFO and SCHEMAS
        if hasattr(module, 'SYSTEM_INFO') and hasattr(module, 'SCHEMAS'):
            system_guid = module.SYSTEM_INFO['guid']
            SCHEMA_REGISTRY[system_guid] = module.SCHEMAS
            logger.info(f"Registered system: {system_guid} from module {module_name}")
        else:
            logger.warning(f"System module {module_name} is missing SYSTEM_INFO or SCHEMAS")
    except Exception as e:
        logger.error(f"Failed to load system module {module_name}: {e}")

@router.get("/systems")
def list_systems():
    """List all available systems"""
    return {"systems": list(SCHEMA_REGISTRY.keys())}

@router.get("/{system}/types")
def list_entry_types(system: str):
    """List all entry types for a system"""
    if system not in SCHEMA_REGISTRY:
        raise HTTPException(status_code=404, detail="System not found")
    
    return {"types": list(SCHEMA_REGISTRY[system].keys())}

@router.get("/{system}/{entry_type}")
def get_schema(system: str, entry_type: str):
    """Get form schema for a specific system and entry type"""
    if system not in SCHEMA_REGISTRY:
        raise HTTPException(status_code=404, detail="System not found")
    
    if entry_type not in SCHEMA_REGISTRY[system]:
        raise HTTPException(status_code=404, detail="Entry type not found")
    
    schema_def = SCHEMA_REGISTRY[system][entry_type]
    return schema_def.form()
