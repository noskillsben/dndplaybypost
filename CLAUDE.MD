# D&D Play-by-Post Platform - Claude Development Guide

**Version:** 2.0 - Fresh Start  
**Date:** 2025-11-19  
**Status:** Ready for Phase 0 rebuild

---

## 🎯 The Vision (Never Forget This)

Build a self-hosted async D&D chat platform where **the character sheet is an active participant in conversation**.

### The Core Loop (This is What We're Building Toward)

```
John plays Grog the Barbarian. He types:
  "Grog flies into a rage and attacks!"

Then clicks [Rage] on his character sheet.

The app automatically:
  ✓ Activates Rage status on sheet
  ✓ Consumes 1 rage use (2/3 → 1/3)
  ✓ Attaches "Activated: Rage" to his message
  ✓ Applies +2 damage, advantage on STR, resistance to physical

He clicks [Attack: Greataxe] on his sheet.

The app rolls:
  1d20+5 (STR) +3 (prof) = [17]+5+3 = 25 to hit
  1d12+5 (STR) +2 (rage) = [8]+5+2 = 15 damage

The roll appears inline with his message in chat.
```

**This is our north star.** Every feature serves this moment of seamless storytelling + mechanics.


## 🏗️ Technical Stack (Confirmed Good)

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL 15 (structured data)
- **Cache:** Redis 7 (sessions, real-time)
- **ORM:** SQLAlchemy 2.0 with asyncpg
- **WebSocket:** FastAPI native WebSocket
- **Deployment:** Docker Compose

### Frontend (Fresh Start)
- **Framework:** SvelteKit (agreed choice for Ben's learning)
- **Styling:** Tailwind CSS
- **State:** Svelte stores + page stores
- **Real-time:** WebSocket client
- **Build:** Vite

### Data Storage Strategy
- **PostgreSQL:** Users, campaigns, characters, compendium
- **SQLite per-campaign:** Messages (portability)
- **NetworkX graphs:** Relationships (future Phase 4)
- **JSONB:** Flexible character sheets & compendium content

---

## 📊 Database Schema (Current State)

### Core Tables

```sql
-- Users & Auth
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaigns
CREATE TABLE campaigns (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaign Members (roles)
CREATE TABLE campaign_members (
    campaign_id UUID REFERENCES campaigns(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(20) CHECK (role IN ('dm', 'player', 'observer')),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (campaign_id, user_id)
);

-- Characters (JSONB for flexibility)
CREATE TABLE characters (
    id UUID PRIMARY KEY,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    player_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    sheet_data JSONB NOT NULL,  -- Complete character sheet
    location_id UUID,  -- Future: references locations
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Compendium (all D&D content)
CREATE TABLE compendium_entries (
    id UUID PRIMARY KEY,
    entry_type VARCHAR(50) NOT NULL,  -- 'class', 'race', 'spell', etc.
    name VARCHAR(255) NOT NULL,
    content JSONB NOT NULL,  -- Type-specific structure
    source VARCHAR(100),  -- 'PHB', 'XGE', 'homebrew'
    is_official BOOLEAN DEFAULT true,
    is_homebrew BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Search optimization
    search_vector tsvector,
    tags TEXT[]
);

-- Indexes for performance
CREATE INDEX idx_compendium_type ON compendium_entries(entry_type);
CREATE INDEX idx_compendium_name ON compendium_entries(name);
CREATE INDEX idx_compendium_search ON compendium_entries USING GIN(search_vector);
CREATE INDEX idx_compendium_tags ON compendium_entries USING GIN(tags);
CREATE INDEX idx_characters_campaign ON characters(campaign_id);
```

---

## 📐 Data Schemas (Complete Reference)

### Character Sheet Structure

The `sheet_data` JSONB field contains:

```json
{
  "basic_info": {
    "name": "Grog Strongjaw",
    "class": "Barbarian",
    "level": 5,
    "race": "Goliath",
    "background": "Soldier",
    "alignment": "Chaotic Neutral",
    "experience_points": 6500
  },
  
  "ability_scores": {
    "strength": {
      "base": 19,
      "racial_bonus": 2,
      "asi_bonus": 0,
      "total": 21,
      "modifier": 5
    },
    "dexterity": { "base": 13, "total": 13, "modifier": 1 },
    "constitution": { "base": 18, "racial_bonus": 1, "total": 19, "modifier": 4 },
    "intelligence": { "base": 8, "total": 8, "modifier": -1 },
    "wisdom": { "base": 10, "total": 10, "modifier": 0 },
    "charisma": { "base": 12, "total": 12, "modifier": 1 }
  },
  
  "combat_stats": {
    "armor_class": 15,
    "ac_calculation": "10 + 1 (DEX) + 4 (CON unarmored defense)",
    "initiative": 1,
    "speed": 40,
    "hit_points": {
      "current": 52,
      "maximum": 52,
      "temporary": 0
    },
    "hit_dice": {
      "total": "5d12",
      "current": 3
    },
    "death_saves": {
      "successes": 0,
      "failures": 0
    }
  },
  
  "proficiencies": {
    "proficiency_bonus": 3,
    "armor": ["light", "medium", "shields"],
    "weapons": ["simple", "martial"],
    "tools": ["vehicles_land"],
    "saving_throws": ["strength", "constitution"],
    "skills": {
      "athletics": { "proficient": true, "expertise": false, "bonus": 8 },
      "intimidation": { "proficient": true, "expertise": false, "bonus": 4 },
      "perception": { "proficient": false, "expertise": false, "bonus": 0 },
      "survival": { "proficient": true, "expertise": false, "bonus": 3 }
    },
    "languages": ["Common", "Giant"]
  },
  
  "features": [
    {
      "name": "Rage",
      "source": "Barbarian 1",
      "description": "Enter a rage as a bonus action...",
      "uses": {
        "current": 3,
        "maximum": 3,
        "reset_on": "long_rest"
      },
      "effects": [
        { "type": "damage_bonus", "value": 2, "condition": "melee" },
        { "type": "advantage", "on": "strength_checks" },
        { "type": "advantage", "on": "strength_saves" },
        { "type": "resistance", "to": ["bludgeoning", "piercing", "slashing"] }
      ]
    },
    {
      "name": "Reckless Attack",
      "source": "Barbarian 2",
      "description": "When you make your first attack...",
      "uses": null,
      "effects": [
        { "type": "advantage", "on": "attack_rolls", "duration": "turn" },
        { "type": "grant_advantage", "to": "attackers", "duration": "turn" }
      ]
    },
    {
      "name": "Stone's Endurance",
      "source": "Goliath racial",
      "description": "You can use your reaction...",
      "uses": {
        "current": 1,
        "maximum": 1,
        "reset_on": "short_rest"
      }
    }
  ],
  
  "active_effects": [
    {
      "name": "Rage",
      "duration": {
        "type": "rounds",
        "remaining": 8
      },
      "effects": [
        { "type": "damage_bonus", "value": 2 },
        { "type": "advantage", "on": "strength_checks" },
        { "type": "resistance", "to": ["physical"] }
      ]
    }
  ],
  
  "attacks": [
    {
      "name": "Greataxe",
      "type": "melee_weapon",
      "attack_bonus": 8,
      "attack_calculation": "5 (STR) + 3 (prof)",
      "damage_dice": "1d12",
      "damage_bonus": 5,
      "damage_type": "slashing",
      "properties": ["heavy", "two-handed"],
      "notes": "Rage adds +2 damage"
    },
    {
      "name": "Handaxe",
      "type": "melee_weapon",
      "attack_bonus": 8,
      "damage_dice": "1d6",
      "damage_bonus": 5,
      "damage_type": "slashing",
      "range": "20/60",
      "properties": ["light", "thrown"]
    }
  ],
  
  "equipment": {
    "currency": {
      "cp": 0,
      "sp": 5,
      "gp": 127,
      "pp": 0
    },
    "items": [
      {
        "name": "Greataxe",
        "quantity": 1,
        "weight": 7,
        "equipped": true,
        "attuned": false
      },
      {
        "name": "Handaxe",
        "quantity": 2,
        "weight": 2,
        "equipped": true
      },
      {
        "name": "Potion of Healing",
        "quantity": 3,
        "weight": 0.5
      }
    ],
    "encumbrance": {
      "carried_weight": 85,
      "capacity": 315,
      "push_drag_lift": 630
    }
  },
  
  "personality": {
    "traits": ["I face problems head-on. A simple, direct solution is the best path to success."],
    "ideals": ["Nation. My city, nation, or people are all that matter. (Any)"],
    "bonds": ["I would still lay down my life for the people I served with."],
    "flaws": ["I made a terrible mistake in battle that cost many lives—and I would do anything to keep that mistake secret."]
  }
}
```

### Compendium Entry Types

#### Class Entry
```json
{
  "name": "Barbarian",
  "hit_die": 12,
  "primary_ability": "Strength",
  "proficiencies": {
    "armor": ["light", "medium", "shields"],
    "weapons": ["simple", "martial"],
    "tools": [],
    "saving_throws": ["strength", "constitution"],
    "skills": {
      "choose": 2,
      "from": ["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"]
    }
  },
  "starting_equipment": "...",
  "features_by_level": {
    "1": [
      {
        "name": "Rage",
        "description": "In battle, you fight with primal ferocity...",
        "uses": { "value": 2, "reset_on": "long_rest" }
      },
      {
        "name": "Unarmored Defense",
        "description": "While you are not wearing any armor, your AC equals 10 + DEX + CON..."
      }
    ],
    "2": [
      {
        "name": "Reckless Attack",
        "description": "Starting at 2nd level, you can throw aside all concern for defense..."
      },
      {
        "name": "Danger Sense",
        "description": "At 2nd level, you gain an uncanny sense of when things nearby aren't as they should be..."
      }
    ]
  },
  "subclasses": [
    {
      "name": "Path of the Berserker",
      "description": "...",
      "features_by_level": {
        "3": ["Frenzy"],
        "6": ["Mindless Rage"]
      }
    }
  ],
  "spellcasting": null
}
```

#### Spell Entry
```json
{
  "name": "Fireball",
  "level": 3,
  "school": "evocation",
  "casting_time": "1 action",
  "range": "150 feet",
  "components": {
    "verbal": true,
    "somatic": true,
    "material": "a tiny ball of bat guano and sulfur"
  },
  "duration": "Instantaneous",
  "description": "A bright streak flashes from your pointing finger...",
  "damage": {
    "base": "8d6",
    "type": "fire",
    "save": "dexterity",
    "save_effect": "half"
  },
  "scaling": {
    "slot_level": 4,
    "damage_increase": "1d6"
  },
  "classes": ["Sorcerer", "Wizard"],
  "ritual": false,
  "concentration": false
}
```

#### Race Entry
```json
{
  "name": "Goliath",
  "size": "Medium",
  "speed": 30,
  "ability_score_increase": {
    "strength": 2,
    "constitution": 1
  },
  "age": "Goliaths have lifespans comparable to humans...",
  "alignment": "Goliath society, with its clear roles and tasks, has a strong lawful bent...",
  "languages": ["Common", "Giant"],
  "traits": [
    {
      "name": "Natural Athlete",
      "description": "You have proficiency in the Athletics skill."
    },
    {
      "name": "Stone's Endurance",
      "description": "You can focus yourself to occasionally shrug off injury...",
      "uses": { "value": 1, "reset_on": "short_rest" }
    },
    {
      "name": "Powerful Build",
      "description": "You count as one size larger when determining your carrying capacity..."
    }
  ],
  "subraces": []
}
```

---

## 🎯 Phase 0: Character System Foundation

**Goal:** Build a complete character system before touching chat integration.

### Why Phase 0 First?

Character sheets are the core of D&D. They're complex, interconnected, and can't be faked. We need:
- Auto-calculation of modifiers
- Feature tracking with uses
- Active effects system
- Attack/spell resolution
- Level-up mechanics

Once this foundation exists, chat integration is straightforward.

### Phase 0 Roadmap (14 Weeks)

#### 0.1: Compendium Browser (Weeks 1-2) 👈 **START HERE**

**Goal:** Create a browser for D&D content (classes, races, spells, etc.)

**Features:**
- Navigate to `/compendium`
- Tabs for each type (Classes, Races, Spells, Items, Feats, Backgrounds)
- List view with search/filter
- Detail view (read-only modal or page)
- Create sample D&D content for testing

**Why First:** Need a content foundation before building character creation.

**API Endpoints (to build):**
```
GET /api/v1/compendium/classes
GET /api/v1/compendium/races  
GET /api/v1/compendium/spells?level=3&class=Wizard
GET /api/v1/compendium/items?type=weapon
GET /api/v1/compendium/feats
GET /api/v1/compendium/backgrounds
```

#### 0.2: Character Creation Wizard (Weeks 3-5)

**Goal:** Create Level 1 characters through step-by-step process

**Steps:**
1. Choose Race (apply ASI, traits, languages)
2. Choose Class (apply proficiencies, starting equipment)
3. Roll/Assign Abilities (standard array, point buy, or rolled)
4. Choose Background (skills, tools, equipment, personality)
5. Choose Starting Equipment
6. Finalize (name, description, portrait)

**Output:** Complete `sheet_data` JSON saved to database.

#### 0.3: Character Sheet Viewer (Weeks 6-7)

**Goal:** Display full character sheet with auto-calculations

**Sections:**
- Header (name, class, level, race, XP)
- Ability Scores (with modifiers)
- Combat Stats (AC, Initiative, Speed, HP)
- Proficiencies (saves, skills, tools, languages)
- Features & Traits (expandable with descriptions)
- Equipment & Attacks
- Spells (if applicable)

**Read-Only:** Just display, no interaction yet.

#### 0.4: Interactive Sheet (Weeks 8-9)

**Goal:** Make the sheet functional

**Features:**
- Click attack → roll with modifiers
- Click spell → roll damage/save
- Click feature → use resource (Rage 3/3 → 2/3)
- Track active effects
- Modify HP, temp HP
- Take short/long rest (restore resources)

**This is the critical milestone.** When complete, we have D&D Beyond-level functionality.

#### 0.5: Level Up System (Weeks 10-11)

**Goal:** Advance characters through levels

**Features:**
- Detect XP threshold reached
- Level-up wizard:
  - Roll HP (or take average)
  - Unlock class features
  - Choose spells (if caster)
  - ASI or Feat selection (levels 4, 8, 12, etc.)
- Update all calculated values

**Test:** Level 1 Wizard → Level 2, gain spell slots + features.

#### 0.6: Content Creators (Weeks 12-14)

**Goal:** Let users create custom content

**Priority Order:**
1. **Background Creator** (simplest - just text + skills)
2. **Feat Creator** (prerequisites + benefits)
3. **Item Creator** (properties, magical effects)
4. **Spell Creator** (complex but follows template)

**Output:** New entries in `compendium_entries` with `is_homebrew=true`.

---

## 🔧 The Dice Roller (Keep As-Is)

We have an excellent dice roller service already built. **Do not change this.**

```python
# Usage examples:
roller = DiceRoller()

# Basic roll
result = roller.roll("1d20+5")
print(result.total)  # e.g., 23
print(result.details)  # "[18] +5"

# Character references
character_values = {
    "str": 5,      # Strength modifier
    "prof": 3,     # Proficiency bonus
    "rage": 2      # Rage damage bonus
}

result = roller.roll("1d20+@str+@prof", character_values)
# Resolves to: 1d20+5+3

# Advantage/Disadvantage
result = roller.roll_advantage("1d20+5")  # Rolls 2d20, keeps highest

# Attack with damage
attack = roller.roll("1d20+@str+@prof", character_values)
if attack.total >= target_ac:
    damage = roller.roll("1d12+@str+@rage", character_values)
    print(f"Hit! {damage.total} damage")
```

**Critical Features:**
- Standard notation (1d20+5, 2d6, etc.)
- Character references (@strength, @proficiency)
- Advantage/disadvantage
- Keep highest/lowest (4d6k3)
- Reroll below threshold (1d20r1)
- Exploding dice (6!)
- Detailed breakdown of rolls

Frontend will send dice expressions to backend, which uses this service.

---

## 📱 Frontend Architecture (Fresh Start)

### SvelteKit Structure

```
frontend/
├── src/
│   ├── routes/
│   │   ├── +layout.svelte                 # App shell
│   │   ├── +page.svelte                   # Home/dashboard
│   │   ├── campaigns/
│   │   │   ├── +page.svelte              # Campaign list
│   │   │   └── [id]/
│   │   │       ├── +page.svelte          # Campaign view
│   │   │       └── +page.server.ts       # Load data
│   │   ├── compendium/                   # 👈 START HERE
│   │   │   ├── +page.svelte              # Compendium browser
│   │   │   ├── classes/+page.svelte
│   │   │   ├── races/+page.svelte
│   │   │   ├── spells/+page.svelte
│   │   │   └── [type]/[id]/+page.svelte  # Detail view
│   │   └── characters/
│   │       ├── create/+page.svelte        # Creation wizard
│   │       └── [id]/
│   │           ├── +page.svelte           # Sheet viewer
│   │           └── edit/+page.svelte      # Sheet editor
│   ├── lib/
│   │   ├── components/
│   │   │   ├── character/
│   │   │   │   ├── AbilityScores.svelte
│   │   │   │   ├── AttackBlock.svelte
│   │   │   │   ├── FeatureCard.svelte
│   │   │   │   └── SpellList.svelte
│   │   │   ├── compendium/
│   │   │   │   ├── ClassCard.svelte
│   │   │   │   ├── SpellCard.svelte
│   │   │   │   └── SearchBar.svelte
│   │   │   └── dice/
│   │   │       └── DiceRoller.svelte
│   │   ├── stores/
│   │   │   ├── auth.ts
│   │   │   ├── campaign.ts
│   │   │   └── character.ts
│   │   ├── api/
│   │   │   ├── client.ts              # Fetch wrapper
│   │   │   ├── compendium.ts          # Compendium API calls
│   │   │   ├── characters.ts
│   │   │   └── dice.ts
│   │   └── utils/
│   │       ├── calculations.ts        # Ability modifiers, AC, etc.
│   │       └── formatters.ts
│   └── app.css                        # Tailwind imports
├── static/                            # Static assets
└── tailwind.config.js
```

### Key Svelte Concepts for Ben

**1. Components are files:**
```svelte
<!-- AbilityScores.svelte -->
<script>
  // This is like __init__ in a Python class
  export let character;  // Props passed from parent
  
  // Reactive statements (recalculates when character changes)
  $: strMod = Math.floor((character.abilities.strength - 10) / 2);
</script>

<div class="ability-scores">
  <div class="ability">
    <span class="name">Strength</span>
    <span class="score">{character.abilities.strength}</span>
    <span class="modifier">{strMod >= 0 ? '+' : ''}{strMod}</span>
  </div>
  <!-- More abilities... -->
</div>

<style>
  /* Scoped styles (only affect this component) */
  .ability-scores { display: grid; }
</style>
```

**2. Stores are like global state:**
```typescript
// stores/character.ts
import { writable } from 'svelte/store';

// Like a class variable that notifies subscribers
export const currentCharacter = writable(null);

// Usage in component:
import { currentCharacter } from '$lib/stores/character';

// Subscribe ($ prefix is shorthand)
$: if ($currentCharacter) {
  console.log('Character loaded:', $currentCharacter.name);
}

// Update
currentCharacter.set(newCharacter);
```

**3. API calls:**
```typescript
// lib/api/compendium.ts
const API_BASE = 'http://localhost:8000/api/v1';

export async function getClasses() {
  const response = await fetch(`${API_BASE}/compendium/classes`);
  if (!response.ok) throw new Error('Failed to fetch classes');
  return response.json();
}

export async function getSpells(filters?: { level?: number, class?: string }) {
  const params = new URLSearchParams(filters);
  const response = await fetch(`${API_BASE}/compendium/spells?${params}`);
  return response.json();
}
```

---

## 🚀 Getting Started (The Rebuild Process)

### Prerequisites

```bash
# On your Raspberry Pi
sudo apt update
sudo apt install docker.io docker-compose git python3-pip node npm
```

### Step 1: Create New Repository Structure

```bash

# Backend
mkdir -p backend/{api,models,services,tests}
mkdir -p data/{uploads,exports,campaigns,graphs,backups}

# Frontend
npx create-svelte@latest frontend
# Choose: Skeleton project, TypeScript, Prettier, Playwright

# Copy working files
cp /old/backend/services/dice_roller.py backend/services/
cp /old/docker-compose.yml .
```

### Step 2: Backend Setup

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="D&D Platform API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # SvelteKit dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "D&D Platform API v2.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
```

### Step 3: Frontend Setup

```bash
cd frontend
npm install
npm install -D tailwindcss autoprefixer postcss
npx tailwindcss init -p

# Install additional packages
npm install @sveltejs/adapter-node
```

### Step 4: Docker Compose

Use the existing `docker-compose.yml` - it's solid.

### Step 5: First API Endpoint

```python
# backend/api/compendium.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..models import CompendiumEntry
from ..database import get_db

router = APIRouter(prefix="/compendium", tags=["compendium"])

@router.get("/classes")
async def get_classes(db: AsyncSession = Depends(get_db)):
    """Get all class entries"""
    result = await db.execute(
        select(CompendiumEntry).where(
            CompendiumEntry.entry_type == 'class'
        )
    )
    entries = result.scalars().all()
    return [{"id": e.id, "name": e.name, "content": e.content} for e in entries]
```

### Step 6: First Frontend Page

```svelte
<!-- frontend/src/routes/compendium/+page.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  
  let classes = [];
  let loading = true;
  
  onMount(async () => {
    const response = await fetch('http://localhost:8000/api/v1/compendium/classes');
    classes = await response.json();
    loading = false;
  });
</script>

<h1>Compendium Browser</h1>

{#if loading}
  <p>Loading...</p>
{:else}
  <div class="grid grid-cols-3 gap-4">
    {#each classes as classEntry}
      <div class="card">
        <h2>{classEntry.name}</h2>
        <p>Hit Die: d{classEntry.content.hit_die}</p>
      </div>
    {/each}
  </div>
{/if}

<style>
  .card {
    @apply p-4 border rounded-lg shadow hover:shadow-lg transition;
  }
</style>
```

---

## 📚 Teaching Approach (For Ben's Learning)

### Explain Before Coding

**Good:**
```
"We need to create a Svelte component for displaying spells. 
In Svelte, components are just .svelte files that combine:
- <script> for logic (like a Python class)
- HTML markup (like Jinja templates)
- <style> for CSS (scoped to this component only)

Let's start with the spell card component..."
```

**Bad:**
```
[Dumps 500 lines of code]
"Here's the complete spell system."
```

### Connect to Python Knowledge

- **Svelte stores** = Python class variables with observers
- **Components** = Python classes with render methods
- **Props** = Function parameters
- **Reactive statements ($:)** = @property decorators
- **{#each}** = Python for loops
- **{#if}** = Python if statements
- **onMount()** = __init__ method

### Build Incrementally

1. Create empty component
2. Add basic structure
3. Add styling
4. Add interactivity
5. Connect to API
6. Test
7. Refine

Never more than one new concept per step.

---

## 🎨 UI/UX Guidelines

### Compendium Browser
- **Layout:** Sidebar with type tabs, main content area
- **Cards:** Show key info at a glance (spell level, class features)
- **Search:** Live filtering as you type
- **Details:** Modal or side panel with full description

### Character Sheet
- **Inspiration:** D&D Beyond's layout
- **Mobile-first:** Sheet should work on phone (overlay or tabs)
- **Click-to-roll:** Every bonus/modifier is clickable
- **Active effects:** Visual indicator when Rage, Bless, etc. active
- **Resource tracking:** Show uses with dots or numbers (●●○○)

### Color Palette (Future Chat Integration)
- **Dialogue (IC):** Purple/blue (`#9b59b6`)
- **Action (IC):** Yellow/gold (`#f1c40f`)
- **Context (DM):** Red/orange (`#e74c3c`)
- **OOC:** Gray (`#95a5a6`)
- **System:** Blue (`#3498db`)

---

## 🧪 Testing Strategy

### Backend Tests
```python
# tests/test_dice_roller.py
def test_basic_roll():
    roller = DiceRoller()
    result = roller.roll("1d20+5")
    assert result.total >= 6  # Min is 1+5
    assert result.total <= 25  # Max is 20+5
    assert "+5" in result.details

def test_character_reference():
    roller = DiceRoller()
    result = roller.roll("1d20+@str", {"str": 5})
    assert result.expression == "1d20+@str"
    assert "+5" in result.details or "5" in result.details
```

### Frontend Tests
```typescript
// tests/compendium.test.ts
import { render, screen } from '@testing-library/svelte';
import CompendiumBrowser from '$lib/components/CompendiumBrowser.svelte';

test('displays class list', async () => {
  const classes = [
    { id: 1, name: 'Fighter', content: { hit_die: 10 } }
  ];
  
  render(CompendiumBrowser, { classes });
  expect(screen.getByText('Fighter')).toBeInTheDocument();
});
```

---

## 🚧 What NOT to Build (Scope Control)

### ❌ Out of Scope for Phase 0
- Chat system (that's Phase 1+)
- VTT features (maps, tokens)
- Video/voice integration
- AI assistance
- Mobile native apps
- Multi-game system support

### ❌ Premature Optimization
- Caching layer (Redis not needed yet)
- GraphQL (REST is fine)
- Microservices (monolith is perfect)
- CDN (static assets can wait)

### ❌ Overengineering
- Complex state management (Svelte stores are enough)
- Testing frameworks (start with Playwright)
- CI/CD pipelines (manual deploy is fine)

**Stay focused:** Complete character system before touching chat.

---

## 🔄 Development Workflow

### Daily Process
```bash
# Start containers
docker compose up -d

# Backend development
docker compose logs -f backend

# Frontend development
cd frontend
npm run dev
# Visit http://localhost:5173

# Database access (if needed)
docker exec -it dnd-db psql -U dnd dnd_platform
```

### Git Workflow
```bash
# Feature branches
git checkout -b feature/compendium-browser
# ... make changes ...
git add .
git commit -m "feat: add compendium browser with class list"
git push origin feature/compendium-browser
```

### Commit Message Format
```
feat: add spell detail modal
fix: dice roller handles negative modifiers
docs: update API documentation
refactor: simplify character calculations
test: add tests for ability score modifiers
```

---

## 📊 Success Metrics

### Phase 0.1 Complete When:
- [ ] Can navigate to `/compendium`
- [ ] See tabs for each content type
- [ ] Click "Classes" and see list
- [ ] Click "Fighter" and see full details
- [ ] Search/filter works
- [ ] Data displays with no errors

### Phase 0 Complete When:
- [ ] Create Level 1 character through wizard
- [ ] View complete character sheet
- [ ] Click attack and see roll results
- [ ] Use feature (Rage) and see resources decrease
- [ ] Take rest and see resources restore
- [ ] Level up Level 1 → Level 2
- [ ] Create custom background
- [ ] Export character as JSON

---

## 🆘 When You Get Stuck

### Problem: "I don't understand this Svelte syntax"
→ Ask: "Can you explain this in terms of Python? What's the equivalent?"

### Problem: "The API isn't returning data"
→ Check:
1. Backend logs: `docker compose logs backend`
2. Network tab in browser DevTools
3. Database: Does the data exist?

### Problem: "Calculations are wrong"
→ Reference the dice_roller.py - it has correct D&D math

### Problem: "Too much to build"
→ Remember: One feature at a time. Compendium browser first.

---


## 🎓 Remember

**You're building this to learn.** Every piece of code is a teaching moment. Every decision has a reason. Every feature serves the core loop of seamless D&D storytelling.

**The goal isn't to finish fast.** The goal is to build something you understand completely, that works reliably, and that brings joy to playing D&D.

**When in doubt, ask:**
- "Does this help the core loop?" (sheet + chat integration)
- "Do I understand why this works?"
- "Is this the simplest solution?"

If yes to all three, build it. If not, rethink.

---

**Now go build the compendium browser. You've got this. 🎲**
