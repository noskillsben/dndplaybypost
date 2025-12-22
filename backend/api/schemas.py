from fastapi import APIRouter, HTTPException
from schemas.systems import dnd50, dnd52

router = APIRouter(prefix="/api/schemas", tags=["schemas"])

# Registry of all schema definitions
SCHEMA_REGISTRY = {
    "d&d5.0": dnd50.SCHEMAS,
    "d&d5.2": dnd52.SCHEMAS,
}

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
