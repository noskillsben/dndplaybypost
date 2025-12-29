import sys
import os
import uuid
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock
import sqlalchemy.dialects.postgresql

# Patch JSONB and UUID for SQLite testing
sqlalchemy.dialects.postgresql.JSONB = sqlalchemy.types.JSON
sqlalchemy.dialects.postgresql.UUID = sqlalchemy.types.Uuid

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import Base
from models.actor import Actor
from models.user import User
from models.campaign import Campaign
from models.compendium import CompendiumEntry
from game_logic.baking import BakingEngine
from schemas.systems.dnd50 import LOGIC_DEFINITIONS

# Mock DB Setup
# We'll use sqlite for in-memory testing or just mock the session objects if possible.
# But since we depend on SQLAlchemy models, lightweight sqlite is best.
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def get_value(data, path):
    parts = path.split('.')
    curr = data
    for p in parts:
        curr = curr.get(p, {})
    
    # If it's a dict with 'value', return that, else return itself (scalar)
    if isinstance(curr, dict) and 'value' in curr:
        return curr['value']
    return curr

def run_verification():
    print("1. Creating Mock Data (User, Campaign)...")
    user = User(id="user1", username="ben", email="ben@example.com", password_hash="hash")
    campaign = Campaign(id="camp1", name="Test Campaign", gm_id="user1")
    session.add(user)
    session.add(campaign)
    session.commit()
    
    print("2. Creating Actor with Base Stats...")
    raw_data = {
        "proficiency_bonus": 2,
        "stats": {
            "strength": {"base": 16},
            "dexterity": {"base": 14}
        },
        "inventory": [],
        "skills": {
            "athletics": {"prof": True},
            "acrobatics": {"prof": False}
        }
    }
    
    # Bake initial
    engine = BakingEngine()
    derived = engine.bake(raw_data, LOGIC_DEFINITIONS)
    
    actor = Actor(
        campaign_id="camp1", 
        owner_id="user1", 
        system_id="d&d5.0", 
        entity_type="character", 
        system_version="1.0.0",
        raw_data=raw_data,
        derived_data=derived
    )
    session.add(actor)
    session.commit()
    
    str_mod = get_value(derived, 'stats.strength.mod')
    print(f"   Actor Created. Derived Strength Mod: {str_mod}")
    assert str_mod == 3, f"Strength mod should be 3, got {str_mod}"
    
    dex_mod = get_value(derived, 'stats.dexterity.mod')
    assert dex_mod == 2, f"Dexterity mod should be 2, got {dex_mod}"
    
    # Check dependency resolution
    # Athletics: Str Mod (3) + Prof (2) = 5
    athletics = get_value(derived, 'skills.athletics.total')
    print(f"   Athletics: {athletics}")
    # Depending on float math it might be 5.0
    assert int(athletics) == 5, f"Athletics should be 5, got {athletics}"
    
    print("3. Testing Item Instancing & Modifiers...")
    # Add an item that boosts Strength by 2
    item_uuid = str(uuid.uuid4())
    
    # Let's test a simpler additive mod first: +2 Strength
    ring = {
         "instance_id": str(uuid.uuid4()),
        "name": "Ring of Strength",
        "equipped": True,
        "modifiers": [
            {"target": "stats.strength.total", "value": 2, "type": "additive", "priority": 10}
        ]
    }
    
    actor.raw_data['inventory'].append(ring)
    
    # Bake
    derived = engine.bake(actor.raw_data, LOGIC_DEFINITIONS)
    str_total = get_value(derived, 'stats.strength.total')
    print(f"   Equipped Ring (+2 Str). Strength Total: {str_total}")
    
    # Base 16 + 2 = 18.
    assert str_total == 18, f"Strength should be 18, got {str_total}"
    # New Mod: (18-10)//2 = 4
    new_str_mod = get_value(derived, 'stats.strength.mod')
    assert new_str_mod == 4, f"New Str Mod should be 4, got {new_str_mod}"
    # Updates Athletics: 4 + 2 = 6
    new_athletics = get_value(derived, 'skills.athletics.total')
    assert int(new_athletics) == 6, f"New Athletics should be 6, got {new_athletics}"
    
    print("VERIFICATION SUCCESSFUL: Baking Engine, Dependency Resolution, and Modifier Application working.")

if __name__ == "__main__":
    try:
        run_verification()
    except AssertionError as e:
        print(f"VERIFICATION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
