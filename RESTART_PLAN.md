# D&D Platform v2.0 - Restart Plan

## Overview
This restart focuses on building the core content system (compendiums + character sheets) without auth, messaging, or campaigns. The goal is to test multi-system flexibility from day one and establish a solid JSONB schema foundation.

---

## Phase 0: Infrastructure Cleanup (Day 1)

### What to KEEP
- ✅ PostgreSQL + Adminer (data storage & admin UI)
- ✅ Docker Compose structure (it works well)
- ✅ FastAPI backend skeleton
- ✅ SvelteKit frontend skeleton
- ✅ Your setup.sh script (simplify it though)

### What to STRIP OUT
- ❌ Redis (no messaging this iteration)
- ❌ Nginx (direct backend/frontend access for dev simplicity)
- ❌ Certbot/SSL (local dev only)
- ❌ All auth-related code and env variables
- ❌ User, Campaign, Message tables
- ❌ WebSocket infrastructure

### Simplified docker-compose.yml
```yaml
version: '3.8'

networks:
  dnd-network:
    driver: bridge

volumes:
  postgres_data:

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: dnd-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./data/backups:/backups
    ports:
      - "${POSTGRES_PORT}:5432"
    networks:
      - dnd-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Backend
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: dnd-backend
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@dnd-postgres:5432/${POSTGRES_DB}
      DEBUG: ${DEBUG}
      CORS_ORIGINS: ${CORS_ORIGINS}
    volumes:
      - ./backend:/app
      - ./data/srd:/app/data/srd
    ports:
      - "${BACKEND_PORT}:8000"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - dnd-network

  # SvelteKit Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: dnd-frontend
    restart: unless-stopped
    environment:
      NODE_ENV: ${NODE_ENV}
      PUBLIC_API_URL: ${PUBLIC_API_URL}
      VITE_API_URL: ${VITE_API_URL}
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/build
    ports:
      - "${FRONTEND_PORT}:3000"
    depends_on:
      - backend
    networks:
      - dnd-network

  # Adminer for database management
  adminer:
    image: adminer:latest
    container_name: dnd-adminer
    restart: unless-stopped
    ports:
      - "${ADMINER_PORT}:8080"
    depends_on:
      - postgres
    networks:
      - dnd-network
```

### Simplified .env.template
```bash
# D&D Platform v2.0 - Development Configuration

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
POSTGRES_DB=dnd_pbp
POSTGRES_USER=dnd
POSTGRES_PASSWORD=change_this_password
POSTGRES_PORT=5432

# =============================================================================
# PORT CONFIGURATION
# =============================================================================
BACKEND_PORT=8000
FRONTEND_PORT=3000
ADMINER_PORT=8080

# =============================================================================
# CORS CONFIGURATION
# =============================================================================
CORS_ORIGINS=http://localhost,http://localhost:3000,http://localhost:5173

# =============================================================================
# API URLs (for frontend)
# =============================================================================
PUBLIC_API_URL=http://localhost:8000
VITE_API_URL=http://localhost:8000

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
DEBUG=true
NODE_ENV=development
```

---

## Phase 1: Core Schema System (Week 1)

### Goal
Build the `ObjectRegistration` + `field_types` module that will be the foundation for everything.

### File Structure
```
backend/
├── core/
│   ├── __init__.py
│   ├── schema_builder.py      # ObjectRegistration class
│   └── field_types.py          # field_types.short_text(), etc.
├── schemas/
│   ├── __init__.py
│   └── systems/
│       ├── __init__.py
│       ├── dnd50.py            # D&D 5.0 schema definitions
│       └── dnd52.py            # D&D 5.2 schema definitions
├── models/
│   ├── __init__.py
│   └── compendium.py           # SQLAlchemy model for compendium table
├── api/
│   ├── __init__.py
│   ├── schemas.py              # Endpoints for schema definitions
│   └── compendium.py           # CRUD for compendium entries
└── main.py
```

### Implementation Steps

#### Step 1.1: Basic ObjectRegistration
Create `backend/core/schema_builder.py`:

```python
from typing import Dict, Any, Type
from pydantic import BaseModel, create_model

class ObjectRegistration:
    """
    Builder for defining game system objects that can generate both
    Pydantic models (backend validation) and JSON schemas (frontend forms).
    """
    
    def __init__(self, system: str = None):
        self.system = system  # e.g., "d&d5.0", "d&d5.2"
        self.fields = {}  # field_name -> FieldType instance
        self._model_cache = None
        self._form_cache = None
    
    def add_field(self, name: str, type, base_field: bool = False, 
                  required: bool = False, **kwargs):
        """Add a field definition"""
        self.fields[name] = {
            'type': type,
            'base_field': base_field,
            'required': required,
            'kwargs': kwargs
        }
        # Clear caches when fields change
        self._model_cache = None
        self._form_cache = None
        return self
    
    def model(self) -> Type[BaseModel]:
        """Generate a Pydantic model for validation"""
        if self._model_cache:
            return self._model_cache
        
        # Build field definitions for Pydantic
        pydantic_fields = {}
        for field_name, field_def in self.fields.items():
            pydantic_fields[field_name] = field_def['type'].to_pydantic_field()
        
        # Create dynamic Pydantic model
        self._model_cache = create_model(
            f'{self.system or "Generic"}Model',
            **pydantic_fields
        )
        return self._model_cache
    
    def form(self) -> Dict[str, Any]:
        """Generate JSON schema for frontend form generation"""
        if self._form_cache:
            return self._form_cache
        
        form_fields = []
        for field_name, field_def in self.fields.items():
            form_field = field_def['type'].to_form_field()
            form_field['name'] = field_name
            form_field['required'] = field_def['required']
            form_field['base_field'] = field_def['base_field']
            form_fields.append(form_field)
        
        self._form_cache = {
            'system': self.system,
            'fields': form_fields
        }
        return self._form_cache
```

#### Step 1.2: Basic Field Types
Create `backend/core/field_types.py`:

```python
from typing import Any, Tuple, Optional
from pydantic import Field

class FieldType:
    """Base class for all field types"""
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        """Return (python_type, pydantic.Field) for model generation"""
        raise NotImplementedError
    
    def to_form_field(self) -> dict:
        """Return dict for frontend form generation"""
        raise NotImplementedError


class ShortText(FieldType):
    """Single-line text input"""
    
    def __init__(self, max_len: int = 100, placeholder: str = ""):
        self.max_len = max_len
        self.placeholder = placeholder
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        return (str, Field(max_length=self.max_len))
    
    def to_form_field(self) -> dict:
        return {
            'type': 'text',
            'maxLength': self.max_len,
            'placeholder': self.placeholder
        }


class LongText(FieldType):
    """Multi-line text area"""
    
    def __init__(self, max_len: int = 5000, placeholder: str = ""):
        self.max_len = max_len
        self.placeholder = placeholder
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        return (str, Field(max_length=self.max_len))
    
    def to_form_field(self) -> dict:
        return {
            'type': 'textarea',
            'maxLength': self.max_len,
            'placeholder': self.placeholder
        }


class Integer(FieldType):
    """Integer number input"""
    
    def __init__(self, min_val: Optional[int] = None, 
                 max_val: Optional[int] = None):
        self.min_val = min_val
        self.max_val = max_val
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        constraints = {}
        if self.min_val is not None:
            constraints['ge'] = self.min_val
        if self.max_val is not None:
            constraints['le'] = self.max_val
        return (int, Field(**constraints))
    
    def to_form_field(self) -> dict:
        field = {'type': 'number', 'step': 1}
        if self.min_val is not None:
            field['min'] = self.min_val
        if self.max_val is not None:
            field['max'] = self.max_val
        return field


class CompendiumLink(FieldType):
    """Dropdown that links to compendium entries"""
    
    def __init__(self, query: str, label: str = "Select..."):
        """
        Args:
            query: GUID pattern to match, e.g., "d&d5.0-basic-damage-type-*"
            label: Default label for the dropdown
        """
        self.query = query
        self.label = label
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        # Store as string GUID
        return (str, Field())
    
    def to_form_field(self) -> dict:
        return {
            'type': 'compendium_link',
            'query': self.query,
            'label': self.label
        }


# Convenience factory functions
def short_text(max_len: int = 100, placeholder: str = "") -> ShortText:
    return ShortText(max_len, placeholder)

def long_text(max_len: int = 5000, placeholder: str = "") -> LongText:
    return LongText(max_len, placeholder)

def integer(min_val: int = None, max_val: int = None) -> Integer:
    return Integer(min_val, max_val)

def compendium_link(query: str, label: str = "Select...") -> CompendiumLink:
    return CompendiumLink(query, label)
```

#### Step 1.3: Test Schema Definition
Create `backend/test_schema.py` to validate the system:

```python
from core.schema_builder import ObjectRegistration
from core import field_types as ft

# Define a simple item schema for D&D 5.0
item = ObjectRegistration(system="d&d5.0")
item.add_field("name", ft.short_text(max_len=50), base_field=True, required=True)
item.add_field("description", ft.long_text(), base_field=True, required=False)
item.add_field("weight", ft.integer(min_val=0), base_field=True, required=False)
item.add_field("damage_dice", ft.short_text(max_len=20, placeholder="1d8"))
item.add_field("damage_type", ft.compendium_link(
    query="d&d5.0-basic-damage-type-*",
    label="Damage Type"
))

# Test model generation
ItemModel = item.model()
print("Generated Pydantic Model:")
print(ItemModel.model_json_schema())

# Test form generation
form_schema = item.form()
print("\nGenerated Form Schema:")
import json
print(json.dumps(form_schema, indent=2))

# Test validation
valid_data = {
    "name": "Longsword",
    "description": "A versatile sword",
    "weight": 3,
    "damage_dice": "1d8",
    "damage_type": "d&d5.0-basic-damage-type-slashing"
}

validated = ItemModel(**valid_data)
print("\nValidation passed!")
print(validated.model_dump_json(indent=2))
```

**Checkpoint 1:** Run `python backend/test_schema.py` and verify:
- Pydantic model generates correctly
- Form schema JSON looks reasonable
- Validation works

---

## Phase 2: Database Models (Week 1-2)

### Compendium Table Design
```python
# backend/models/compendium.py
from sqlalchemy import Column, String, Text, JSON, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class CompendiumEntry(Base):
    __tablename__ = "compendium"
    
    # Human-readable GUID as primary key
    guid = Column(String(200), primary_key=True)
    # e.g., "d&d5.0-item-longsword"
    
    # System identifier
    system = Column(String(50), nullable=False, index=True)
    # e.g., "d&d5.0", "d&d5.2", "lasers-and-feelings"
    
    # Entry type
    entry_type = Column(String(50), nullable=False, index=True)
    # e.g., "item", "spell", "class", "basic-rule"
    
    # Searchable name
    name = Column(String(200), nullable=False, index=True)
    
    # JSONB data matching the schema for this entry_type
    data = Column(JSON, nullable=False)
    
    # Metadata
    homebrew = Column(Boolean, default=False, index=True)
    source = Column(String(100))  # "PHB", "DMG", "Ben's Homebrew"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### GUID Structure Pattern
```
{system}-{type}-{identifier}

Examples:
- d&d5.0-item-longsword
- d&d5.0-spell-fireball
- d&d5.0-basic-damage-type-slashing
- d&d5.2-item-longsword  (same name, different system)
- lasers-feelings-character-sheet
```

**Checkpoint 2:** Create migration and verify table structure in Adminer.

---

## Phase 3: API Endpoints (Week 2)

### Schema Endpoints
```python
# backend/api/schemas.py
from fastapi import APIRouter, HTTPException
from core.schema_builder import ObjectRegistration
from schemas.systems import dnd50, dnd52

router = APIRouter(prefix="/api/schemas", tags=["schemas"])

# Registry of all schema definitions
SCHEMA_REGISTRY = {
    "d&d5.0": {
        "item": dnd50.item_schema,
        "spell": dnd50.spell_schema,
        # ... more types
    },
    "d&d5.2": {
        "item": dnd52.item_schema,
        "spell": dnd52.spell_schema,
        # ... more types
    }
}

@router.get("/{system}/{entry_type}")
def get_schema(system: str, entry_type: str):
    """Get form schema for a specific system and entry type"""
    if system not in SCHEMA_REGISTRY:
        raise HTTPException(status_code=404, detail="System not found")
    
    if entry_type not in SCHEMA_REGISTRY[system]:
        raise HTTPException(status_code=404, detail="Entry type not found")
    
    schema_def = SCHEMA_REGISTRY[system][entry_type]
    return schema_def.form()

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
```

### Compendium CRUD Endpoints
```python
# backend/api/compendium.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models.compendium import CompendiumEntry
from database import get_db
from typing import Optional

router = APIRouter(prefix="/api/compendium", tags=["compendium"])

@router.get("/")
async def list_entries(
    system: Optional[str] = None,
    entry_type: Optional[str] = None,
    search: Optional[str] = None,
    homebrew: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List compendium entries with filters"""
    query = db.query(CompendiumEntry)
    
    if system:
        query = query.filter(CompendiumEntry.system == system)
    if entry_type:
        query = query.filter(CompendiumEntry.entry_type == entry_type)
    if search:
        query = query.filter(CompendiumEntry.name.ilike(f"%{search}%"))
    if homebrew is not None:
        query = query.filter(CompendiumEntry.homebrew == homebrew)
    
    results = await query.all()
    return {"entries": results}

@router.get("/{guid}")
async def get_entry(guid: str, db: AsyncSession = Depends(get_db)):
    """Get a specific compendium entry"""
    entry = await db.get(CompendiumEntry, guid)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.post("/")
async def create_entry(
    system: str,
    entry_type: str,
    data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a new compendium entry"""
    # Validate against schema
    from api.schemas import SCHEMA_REGISTRY
    
    if system not in SCHEMA_REGISTRY:
        raise HTTPException(status_code=400, detail="Invalid system")
    if entry_type not in SCHEMA_REGISTRY[system]:
        raise HTTPException(status_code=400, detail="Invalid entry type")
    
    schema_def = SCHEMA_REGISTRY[system][entry_type]
    Model = schema_def.model()
    
    try:
        validated = Model(**data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    
    # Generate GUID from name
    name = data.get("name", "unnamed")
    guid_base = f"{system}-{entry_type}-{name.lower().replace(' ', '-')}"
    guid = guid_base
    
    # Check for duplicates and increment if needed
    counter = 1
    while await db.get(CompendiumEntry, guid):
        guid = f"{guid_base}-{counter}"
        counter += 1
    
    # Create entry
    entry = CompendiumEntry(
        guid=guid,
        system=system,
        entry_type=entry_type,
        name=data.get("name"),
        data=validated.model_dump(),
        homebrew=data.get("homebrew", False),
        source=data.get("source", "Unknown")
    )
    
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    
    return entry
```

**Checkpoint 3:** Test endpoints with curl/Postman:
```bash
# List systems
curl http://localhost:8000/api/schemas/systems

# Get item schema for D&D 5.0
curl http://localhost:8000/api/schemas/d&d5.0/item

# Create an item
curl -X POST http://localhost:8000/api/compendium \
  -H "Content-Type: application/json" \
  -d '{
    "system": "d&d5.0",
    "entry_type": "item",
    "data": {
      "name": "Longsword",
      "description": "A versatile sword",
      "weight": 3,
      "damage_dice": "1d8",
      "damage_type": "d&d5.0-basic-damage-type-slashing"
    }
  }'
```

---

## Phase 4: Frontend Form Generation (Week 3)

### Generic Form Component
```svelte
<!-- frontend/src/lib/components/DynamicForm.svelte -->
<script>
  import { onMount } from 'svelte';
  
  export let system;
  export let entryType;
  export let initialData = {};
  export let onSubmit;
  
  let formSchema = null;
  let formData = { ...initialData };
  let loading = true;
  let error = null;
  
  onMount(async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/schemas/${system}/${entryType}`);
      if (!response.ok) throw new Error('Failed to load schema');
      formSchema = await response.json();
      loading = false;
    } catch (e) {
      error = e.message;
      loading = false;
    }
  });
  
  function handleSubmit(e) {
    e.preventDefault();
    if (onSubmit) {
      onSubmit(formData);
    }
  }
  
  async function fetchCompendiumOptions(query) {
    // Parse query like "d&d5.0-basic-damage-type-*"
    const [system, type] = query.split('-').slice(0, 2);
    const response = await fetch(
      `http://localhost:8000/api/compendium?system=${system}&entry_type=${type}`
    );
    const data = await response.json();
    return data.entries;
  }
</script>

{#if loading}
  <p>Loading form...</p>
{:else if error}
  <p class="text-red-500">Error: {error}</p>
{:else if formSchema}
  <form on:submit={handleSubmit} class="space-y-4">
    {#each formSchema.fields as field}
      <div class="field">
        <label for={field.name} class="block font-medium">
          {field.name}
          {#if field.required}<span class="text-red-500">*</span>{/if}
        </label>
        
        {#if field.type === 'text'}
          <input
            type="text"
            id={field.name}
            bind:value={formData[field.name]}
            maxlength={field.maxLength}
            placeholder={field.placeholder || ''}
            required={field.required}
            class="w-full border rounded px-3 py-2"
          />
        
        {:else if field.type === 'textarea'}
          <textarea
            id={field.name}
            bind:value={formData[field.name]}
            maxlength={field.maxLength}
            placeholder={field.placeholder || ''}
            required={field.required}
            rows="4"
            class="w-full border rounded px-3 py-2"
          />
        
        {:else if field.type === 'number'}
          <input
            type="number"
            id={field.name}
            bind:value={formData[field.name]}
            min={field.min}
            max={field.max}
            step={field.step}
            required={field.required}
            class="w-full border rounded px-3 py-2"
          />
        
        {:else if field.type === 'compendium_link'}
          <!-- TODO: Implement async dropdown -->
          <select
            id={field.name}
            bind:value={formData[field.name]}
            required={field.required}
            class="w-full border rounded px-3 py-2"
          >
            <option value="">{field.label}</option>
            <!-- Options loaded dynamically -->
          </select>
        {/if}
      </div>
    {/each}
    
    <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded">
      Submit
    </button>
  </form>
{/if}
```

### Simple Compendium Browser
```svelte
<!-- frontend/src/routes/compendium/+page.svelte -->
<script>
  import { onMount } from 'svelte';
  
  let systems = [];
  let selectedSystem = null;
  let selectedType = null;
  let entries = [];
  let types = [];
  
  onMount(async () => {
    const res = await fetch('http://localhost:8000/api/schemas/systems');
    const data = await res.json();
    systems = data.systems;
  });
  
  async function selectSystem(system) {
    selectedSystem = system;
    const res = await fetch(`http://localhost:8000/api/schemas/${system}/types`);
    const data = await res.json();
    types = data.types;
  }
  
  async function selectType(type) {
    selectedType = type;
    const res = await fetch(
      `http://localhost:8000/api/compendium?system=${selectedSystem}&entry_type=${type}`
    );
    const data = await res.json();
    entries = data.entries;
  }
</script>

<div class="container mx-auto p-4">
  <h1 class="text-3xl font-bold mb-4">Compendium Browser</h1>
  
  <div class="grid grid-cols-3 gap-4 mb-8">
    <!-- System selector -->
    <div>
      <h2 class="font-bold mb-2">System</h2>
      {#each systems as system}
        <button
          on:click={() => selectSystem(system)}
          class="block w-full text-left px-3 py-2 rounded mb-1"
          class:bg-blue-500={selectedSystem === system}
          class:text-white={selectedSystem === system}
          class:bg-gray-200={selectedSystem !== system}
        >
          {system}
        </button>
      {/each}
    </div>
    
    <!-- Type selector -->
    <div>
      <h2 class="font-bold mb-2">Type</h2>
      {#each types as type}
        <button
          on:click={() => selectType(type)}
          class="block w-full text-left px-3 py-2 rounded mb-1"
          class:bg-blue-500={selectedType === type}
          class:text-white={selectedType === type}
          class:bg-gray-200={selectedType !== type}
        >
          {type}
        </button>
      {/each}
    </div>
    
    <!-- Entry list -->
    <div>
      <h2 class="font-bold mb-2">Entries</h2>
      {#each entries as entry}
        <div class="border rounded px-3 py-2 mb-2">
          <div class="font-bold">{entry.name}</div>
          <div class="text-sm text-gray-600">{entry.guid}</div>
        </div>
      {/each}
    </div>
  </div>
</div>
```

**Checkpoint 4:** 
- Create an item via the form
- See it appear in the compendium browser
- Verify data in Adminer

---

## Phase 5: Define D&D Systems (Week 3-4)

### D&D 5.0 Schema Definitions
```python
# backend/schemas/systems/dnd50.py
from core.schema_builder import ObjectRegistration
from core import field_types as ft

# ============================================================================
# BASIC RULES (damage types, conditions, etc.)
# ============================================================================

damage_type_schema = ObjectRegistration(system="d&d5.0")
damage_type_schema.add_field("name", ft.short_text(50), required=True)
damage_type_schema.add_field("description", ft.long_text())

# ============================================================================
# ITEMS
# ============================================================================

item_schema = ObjectRegistration(system="d&d5.0")
item_schema.add_field("name", ft.short_text(100), required=True)
item_schema.add_field("description", ft.long_text())
item_schema.add_field("weight", ft.integer(min_val=0))
item_schema.add_field("cost_copper", ft.integer(min_val=0))  # Store in copper pieces
item_schema.add_field("rarity", ft.short_text(50))  # Common, Uncommon, Rare, etc.

# Weapon-specific
item_schema.add_field("damage_dice", ft.short_text(20))
item_schema.add_field("damage_type", ft.compendium_link("d&d5.0-basic-damage-type-*"))
item_schema.add_field("properties", ft.long_text())  # For now, just text
item_schema.add_field("versatile_damage", ft.short_text(20))

# Armor-specific
item_schema.add_field("armor_class", ft.integer(min_val=0, max_val=30))
item_schema.add_field("armor_type", ft.short_text(50))  # Light, Medium, Heavy
item_schema.add_field("stealth_disadvantage", ft.short_text(10))  # "Yes" or "No" for now

# ============================================================================
# SPELLS
# ============================================================================

spell_schema = ObjectRegistration(system="d&d5.0")
spell_schema.add_field("name", ft.short_text(100), required=True)
spell_schema.add_field("level", ft.integer(min_val=0, max_val=9), required=True)
spell_schema.add_field("school", ft.short_text(50), required=True)
spell_schema.add_field("casting_time", ft.short_text(100))
spell_schema.add_field("range", ft.short_text(100))
spell_schema.add_field("components", ft.short_text(200))
spell_schema.add_field("duration", ft.short_text(100))
spell_schema.add_field("description", ft.long_text(), required=True)
spell_schema.add_field("higher_levels", ft.long_text())
spell_schema.add_field("ritual", ft.short_text(10))  # "Yes" or "No"
spell_schema.add_field("concentration", ft.short_text(10))  # "Yes" or "No"

# ============================================================================
# REGISTRY
# ============================================================================

SCHEMAS = {
    "damage-type": damage_type_schema,
    "item": item_schema,
    "spell": spell_schema,
}
```

### D&D 5.2 (copy/paste for now)
```python
# backend/schemas/systems/dnd52.py
# For now, just copy dnd50.py and change system identifier
# Later, we'll see what actually differs
```

**Checkpoint 5:** 
- Define at least 3 entry types for D&D 5.0
- Test creating entries of each type
- Copy to D&D 5.2 and verify they're separate systems

---

## Build Order Summary

### Phase 0.1: Compendium Browser (MVP Goal)
**Target: End of Week 2**

What you'll have:
- ✅ Stripped-down infrastructure
- ✅ `ObjectRegistration` + `field_types` working
- ✅ Compendium table with human-readable GUIDs
- ✅ API endpoints for schemas and compendium
- ✅ Basic Svelte compendium browser
- ✅ Ability to create and view items in D&D 5.0

### Phase 0.2: Multi-System Test
**Target: End of Week 3**

What you'll add:
- ✅ D&D 5.2 system (mostly copied from 5.0)
- ✅ A simple 1-page RPG (like Lasers & Feelings)
- ✅ Verify the architecture handles different systems

### Phase 0.3: Content Population
**Target: End of Week 4**

What you'll add:
- ✅ Basic damage types
- ✅ ~20 items (weapons, armor)
- ✅ ~10 spells
- ✅ Learn: What's painful? What feels natural?

### Future Phases (Not This Iteration)
- Character sheets
- Character creation wizard
- NPC sheets
- Gameplay systems (initiative, actions, etc.)
- Messaging integration

---

## Testing Your Boundaries

At each checkpoint, ask yourself:

**What's System-Specific?**
- Schema definitions (items, spells, classes)
- GUID prefixes
- Form layouts (eventually)

**What's Generic?**
- `ObjectRegistration` class
- `field_types` module
- Compendium table structure
- API endpoints
- Form rendering logic

**What's Unclear?**
- Character sheet structure (wait until Phase 0.4)
- How to handle references between entries
- Versioning and migrations

---

## Next Steps After Reading This

1. ✅ Review this plan - does it match your vision?
2. ✅ Adjust the docker-compose and .env files
3. ✅ Create the file structure
4. ✅ Start with `ObjectRegistration` in Antigravity
5. ✅ Test, iterate, learn

Let me know if you want me to clarify any section!
