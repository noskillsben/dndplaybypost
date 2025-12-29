from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from typing import List, Dict, Any, Optional
import uuid
import logging

from database import get_db
from models.actor import Actor
from models.compendium import CompendiumEntry
from game_logic.baking import BakingEngine
from schemas.systems.dnd50 import LOGIC_DEFINITIONS

# Minimal Pydantic schemas for request/response
from pydantic import BaseModel

router = APIRouter(
    prefix="/actors",
    tags=["actors"]
)

baking_engine = BakingEngine()

class ActorCreate(BaseModel):
    name: str # Currently stored in raw_data, but useful validation
    campaign_id: str
    owner_id: str
    system_id: str
    entity_type: str
    system_version: str
    raw_data: Dict[str, Any]

class ActorResponse(BaseModel):
    id: uuid.UUID
    campaign_id: str
    owner_id: str
    system_id: str
    derived_data: Dict[str, Any]
    
class ItemInstanceRequest(BaseModel):
    compendium_id: str

class BakeRequest(BaseModel):
    pass # Manual trigger

@router.post("/", response_model=ActorResponse)
def create_actor(actor: ActorCreate, db: Session = Depends(get_db)):
    # 1. Create Base Actor
    # Ensure campaign/user exist? (Foreign Keys handle this at DB level, will raise 400 if invalid)
    
    # Run initial bake
    try:
        derived = baking_engine.bake(actor.raw_data, LOGIC_DEFINITIONS) # TODO: Fetch logic defs dynamically based on system_id
    except Exception as e:
        logging.error(f"Baking failed: {e}")
        derived = {}
        
    db_actor = Actor(
        campaign_id=actor.campaign_id,
        owner_id=actor.owner_id,
        system_id=actor.system_id,
        entity_type=actor.entity_type,
        system_version=actor.system_version,
        raw_data=actor.raw_data,
        derived_data=derived
    )
    
    try:
        db.add(db_actor)
        db.commit()
        db.refresh(db_actor)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid references or data error")
        
    return db_actor

@router.get("/{actor_id}", response_model=ActorResponse)
def get_actor(actor_id: uuid.UUID, db: Session = Depends(get_db)):
    actor = db.query(Actor).filter(Actor.id == actor_id).first()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")
    return actor

@router.post("/{actor_id}/items")
def add_item_instance(actor_id: uuid.UUID, item_req: ItemInstanceRequest, db: Session = Depends(get_db)):
    actor = db.query(Actor).filter(Actor.id == actor_id).first()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")

    # Fetch compendium item
    # Assuming the guid is passed
    comp_entry = db.query(CompendiumEntry).filter(CompendiumEntry.guid == item_req.compendium_id).first()
    if not comp_entry:
         raise HTTPException(status_code=404, detail="Item not found in Compendium")
         
    # Create Instance Snapshot
    instance_uuid = str(uuid.uuid4())
    item_snapshot = {
        "instance_id": instance_uuid,
        "template_id": comp_entry.guid,
        "version": "1.0.0", # TODO: Versioning from compendium
        "name": comp_entry.name,
        "data": comp_entry.data, # Copy effect data
        "equipped": False
        # "modifiers": ... extracted from data if needed here, or baked from 'data'
    }
    
    # Append to inventory in raw_data
    # We must clone raw_data to mutate it (SQLAlchemy JSONB tracking)
    raw = dict(actor.raw_data)
    inventory = raw.get("inventory", [])
    inventory.append(item_snapshot)
    raw["inventory"] = inventory
    
    actor.raw_data = raw
    
    # Auto-bake? (Maybe optional, but good for immediate feedback)
    actor.derived_data = baking_engine.bake(actor.raw_data, LOGIC_DEFINITIONS)
    
    db.commit()
    db.refresh(actor)
    return actor

@router.post("/{actor_id}/bake")
def manual_bake(actor_id: uuid.UUID, db: Session = Depends(get_db)):
    actor = db.query(Actor).filter(Actor.id == actor_id).first()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")
        
    actor.derived_data = baking_engine.bake(actor.raw_data, LOGIC_DEFINITIONS)
    db.commit()
    return actor
