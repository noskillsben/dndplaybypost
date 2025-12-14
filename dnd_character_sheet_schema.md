# D&D Character Sheet Schema Design
## Modular, Version-Aware Character Management System

**Version:** 1.0.0  
**Date:** 2024-11-30  
**System:** D&D 5e (2024) / 5.2  
**Design Philosophy:** Self-contained sheets with version-tracked references for selective updates

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [Component Types](#component-types)
4. [Character Sheet Structure](#character-sheet-structure)
5. [Template System](#template-system)
6. [Update Propagation](#update-propagation)
7. [Implementation Examples](#implementation-examples)

---

## Architecture Overview

### Core Principles

**Self-Contained Character Sheets**
- All data lives in `characters.sheet_data` JSONB field
- Character sheet is fully renderable without external queries
- Each component includes both data AND metadata (guid, version, source)

**Version-Aware References**
- Every imported component tracks: `{guid, version, source_type, source_name}`
- DM can see "updates available" for characters
- Selective update propagation (update this character, all characters, or none)

**Modular Components**
- Templates define component types (not full systems)
- Homebrew creators add new component types
- Generic enough for other game systems (Cyberpunk, Pathfinder, etc.)

### Three-Table Architecture

```
compendium_items
  ├─ type: 'race', 'class', 'spell', 'item', 'feature', 'background', etc.
  ├─ data_jsonb: {component-specific structure}
  └─ version: timestamp

component_templates  
  ├─ component_type: 'ability', 'resource', 'attack', 'spell_slot', etc.
  └─ schema_jsonb: {validation rules}

characters
  └─ sheet_data: {self-contained character with versioned refs}
```

---

## Database Schema

### Table: `compendium_items`

```sql
CREATE TABLE compendium_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL,  -- 'race', 'class', 'spell', 'item', 'feature', etc.
    name VARCHAR(255) NOT NULL,
    data JSONB NOT NULL,
    version TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    is_official BOOLEAN DEFAULT FALSE,  -- SRD vs homebrew
    is_active BOOLEAN DEFAULT TRUE,
    tags TEXT[],  -- For search/filtering
    
    -- Indexes
    INDEX idx_type (type),
    INDEX idx_version (version),
    INDEX idx_tags USING GIN (tags),
    INDEX idx_data USING GIN (data)
);
```

**Key Design Decisions:**
- `type` uses lowercase strings (more flexible than ENUM)
- `version` is timestamp (human-readable, sortable)
- `data` structure varies by type (see Component Types section)
- `tags` array for flexible categorization

### Table: `component_templates`

```sql
CREATE TABLE component_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    component_type VARCHAR(50) NOT NULL UNIQUE,  -- 'resource', 'attack', 'modifier', etc.
    name VARCHAR(255) NOT NULL,
    description TEXT,
    schema JSONB NOT NULL,  -- JSON Schema for validation
    for_types TEXT[],  -- Which compendium item types can use this
    version TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_component_type (component_type),
    INDEX idx_for_types USING GIN (for_types)
);
```

**Purpose:**
- Defines structure for character sheet components
- Validates homebrew content
- Allows new game systems to define their own components

### Existing Table: `characters` (Modified)

```sql
-- Add these columns to existing characters table:
ALTER TABLE characters ADD COLUMN IF NOT EXISTS
    system VARCHAR(50) DEFAULT 'dnd5e_2024',  -- Game system identifier
    sheet_version TIMESTAMP DEFAULT NOW(),  -- Last structural change
    compendium_version TIMESTAMP;  -- Last content update check
```

---

## Component Types

### Overview

Components are the building blocks stored in `compendium_items`. Each has:
- A `type` (what kind of thing it is)
- A `data` structure (specific to that type)
- Common metadata (guid, version, name)

### Core D&D 5e Types

#### 1. Race (Species)

```json
{
  "type": "race",
  "data": {
    "description": "Dragonborn trace their ancestry to chromatic, gem, and metallic dragons...",
    "size": "Medium",
    "speed": 30,
    "creature_type": "Humanoid",
    "age": {
      "maturity": 15,
      "lifespan": 80
    },
    "ability_score_increases": [
      {
        "template_type": "modifier",
        "applies_to": "ability_choice",
        "choices": ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"],
        "choose_count": 1,
        "value": 2,
        "description": "Increase one ability by 2"
      },
      {
        "template_type": "modifier",
        "applies_to": "ability_choice",
        "choices": ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"],
        "choose_count": 1,
        "value": 1,
        "description": "Increase a different ability by 1",
        "exclude_previous": true
      }
    ],
    "traits": [
      {
        "guid": "feature_guid_123",
        "name": "Draconic Ancestry",
        "description": "Your lineage stems from a dragon...",
        "requires_choice": {
          "type": "dragon_type",
          "options": ["black", "blue", "brass", "bronze", "copper", "gold", "green", "red", "silver", "white"],
          "grants": {
            "damage_type": "{{choice}}",  // Template variable
            "breath_weapon": "breath_weapon_{{choice}}"
          }
        }
      }
    ],
    "languages": ["Common", "Draconic"],
    "darkvision": 60
  }
}
```

#### 2. Class

```json
{
  "type": "class",
  "data": {
    "description": "Signaling for your allies to wait...",
    "hit_die": "d12",
    "primary_abilities": ["strength"],
    "saving_throw_proficiencies": ["strength", "constitution"],
    "skill_proficiencies": {
      "choose_count": 2,
      "options": ["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"]
    },
    "weapon_proficiencies": ["simple", "martial"],
    "armor_training": ["light", "medium", "shields"],
    "starting_equipment": {
      "option_a": [
        {"item_guid": "item_greataxe", "quantity": 1},
        {"item_guid": "item_handaxe", "quantity": 4},
        {"item_guid": "item_explorers_pack", "quantity": 1},
        {"money": {"gp": 15}}
      ],
      "option_b": [
        {"money": {"gp": 75}}
      ]
    },
    "features_by_level": {
      "1": [
        {
          "guid": "feature_rage",
          "name": "Rage",
          "grants": {
            "template_type": "resource",
            "resource_name": "Rage",
            "max_uses": 2,
            "recovery": "long_rest",
            "partial_recovery": {
              "short_rest": 1
            }
          }
        },
        {
          "guid": "feature_unarmored_defense",
          "name": "Unarmored Defense"
        }
      ],
      "2": [
        {
          "guid": "feature_danger_sense",
          "name": "Danger Sense"
        }
      ]
      // ... levels 3-20
    },
    "subclasses": {
      "level": 3,
      "options": ["path_of_berserker", "path_of_world_tree", "path_of_zealot", "path_of_wild_heart"]
    },
    "spellcasting": null  // Barbarians don't cast spells
  }
}
```

#### 3. Subclass

```json
{
  "type": "subclass",
  "data": {
    "parent_class_guid": "class_barbarian",
    "name": "Path of the Berserker",
    "description": "Barbarians who walk the Path of the Berserker direct their Rage...",
    "features_by_level": {
      "3": [
        {
          "guid": "feature_frenzy",
          "name": "Frenzy"
        }
      ],
      "6": [
        {
          "guid": "feature_mindless_rage",
          "name": "Mindless Rage"
        }
      ]
      // ... etc
    }
  }
}
```

#### 4. Background

```json
{
  "type": "background",
  "data": {
    "description": "You devoted yourself to scholarship as a sage...",
    "ability_score_increases": {
      "options": [
        ["constitution", "intelligence", "wisdom"],
        {"choose": 1, "value": 2, "from": ["constitution", "intelligence", "wisdom"]},
        {"choose": 1, "value": 1, "from": ["constitution", "intelligence", "wisdom"], "different": true}
      ],
      "alternate": {
        "all_three": 1
      }
    },
    "feat_guid": "feat_magic_initiate_wizard",
    "skill_proficiencies": ["Arcana", "History"],
    "tool_proficiency": {
      "category": "calligraphers_supplies"
    },
    "equipment_options": {
      "option_a": [
        {"item_guid": "item_quarterstaff", "quantity": 1},
        {"item_guid": "item_calligraphers_supplies", "quantity": 1},
        {"item_guid": "item_book_history", "quantity": 1},
        {"item_guid": "item_parchment", "quantity": 8},
        {"item_guid": "item_robe", "quantity": 1},
        {"money": {"gp": 8}}
      ],
      "option_b": [
        {"money": {"gp": 50}}
      ]
    }
  }
}
```

#### 5. Feature

Features are abilities, class features, racial traits, feats, etc.

```json
{
  "type": "feature",
  "data": {
    "name": "Rage",
    "source_type": "class",
    "source_name": "Barbarian",
    "level_requirement": 1,
    "description": "You can imbue yourself with a primal power called Rage...",
    "activation": {
      "type": "bonus_action",
      "restriction": "Cannot wear Heavy armor"
    },
    "duration": {
      "type": "rounds",
      "base": 1,
      "extension_methods": [
        "Attack an enemy",
        "Force enemy saving throw",
        "Take Bonus Action to extend"
      ],
      "max_duration": "10 minutes",
      "ends_early_if": ["don Heavy armor", "Incapacitated condition"]
    },
    "resource": {
      "template_type": "resource",
      "name": "Rage Uses",
      "max_formula": "[[level_table:barbarian:rages]]",  // References class table
      "recovery": "long_rest",
      "partial_recovery": {
        "short_rest": 1
      }
    },
    "effects": [
      {
        "template_type": "modifier",
        "type": "damage_resistance",
        "damage_types": ["bludgeoning", "piercing", "slashing"],
        "while_active": true
      },
      {
        "template_type": "modifier",
        "type": "damage_bonus",
        "applies_to": "strength_weapon_damage",
        "value": "[[level_table:barbarian:rage_damage]]",
        "while_active": true
      },
      {
        "template_type": "modifier",
        "type": "advantage",
        "applies_to": ["strength_checks", "strength_saves"],
        "while_active": true
      },
      {
        "template_type": "restriction",
        "type": "cannot_concentrate",
        "while_active": true
      },
      {
        "template_type": "restriction",
        "type": "cannot_cast_spells",
        "while_active": true
      }
    ]
  }
}
```

#### 6. Spell

```json
{
  "type": "spell",
  "data": {
    "name": "Fireball",
    "level": 3,
    "school": "evocation",
    "casting_time": {
      "type": "action",
      "count": 1
    },
    "range": {
      "type": "ranged",
      "distance": 150,
      "unit": "feet"
    },
    "components": {
      "verbal": true,
      "somatic": true,
      "material": {
        "required": true,
        "description": "a tiny ball of bat guano and sulfur",
        "consumed": false,
        "cost_gp": 0
      }
    },
    "duration": {
      "type": "instantaneous"
    },
    "description": "A bright streak flashes from your pointing finger...",
    "area_of_effect": {
      "type": "sphere",
      "radius": 20,
      "unit": "feet"
    },
    "saving_throw": {
      "ability": "dexterity",
      "success_effect": "half_damage"
    },
    "damage": {
      "base": "8d6",
      "type": "fire",
      "scaling": {
        "slot_level": {
          "additional_per_level": "1d6"
        }
      }
    },
    "tags": ["damage", "area", "fire"],
    "classes": ["sorcerer", "wizard"],
    "ritual": false,
    "concentration": false
  }
}
```

#### 7. Item (Equipment/Magic Items)

```json
{
  "type": "item",
  "data": {
    "name": "+1 Longsword",
    "category": "weapon",
    "subcategory": "martial_melee",
    "rarity": "uncommon",
    "requires_attunement": false,
    "description": "You have a +1 bonus to attack and damage rolls made with this magic weapon.",
    "base_item_guid": "item_longsword",  // Reference to nonmagical version
    "cost": {
      "gp": 0  // Not purchasable, magic item
    },
    "weight_lbs": 3,
    "properties": ["versatile"],
    "damage": {
      "one_handed": "1d8",
      "two_handed": "1d10",
      "type": "slashing"
    },
    "magic_properties": {
      "attack_bonus": 1,
      "damage_bonus": 1
    },
    "tags": ["weapon", "magic", "melee", "slashing"]
  }
}
```

#### 8. Item (Mundane)

```json
{
  "type": "item",
  "data": {
    "name": "Longsword",
    "category": "weapon",
    "subcategory": "martial_melee",
    "cost": {
      "gp": 15
    },
    "weight_lbs": 3,
    "damage": {
      "one_handed": "1d8",
      "two_handed": "1d10",
      "type": "slashing"
    },
    "properties": ["versatile"],
    "mastery": "sap",
    "description": "Proficiency with a longsword allows you to add your proficiency bonus...",
    "tags": ["weapon", "martial", "melee", "slashing", "versatile"]
  }
}
```

---

## Character Sheet Structure

### Overview

The `characters.sheet_data` JSONB field contains a complete, self-contained character sheet. It has three layers:

1. **Core Stats** - Current character state
2. **Components** - Imported features with version tracking
3. **Choices** - Player decisions and customizations

### Full Character Sheet Example

```json
{
  "meta": {
    "system": "dnd5e_2024",
    "sheet_version": "2024-11-30T10:00:00Z",
    "last_rest": {
      "type": "long",
      "timestamp": "2024-11-29T20:00:00Z"
    }
  },
  
  "basic_info": {
    "name": "Grog Strongjaw",
    "player_name": "Travis Willingham",
    "level": 5,
    "experience_points": 6500,
    "alignment": "Chaotic Neutral",
    "background": {
      "guid": "background_soldier",
      "version": "2024-11-25T12:00:00Z",
      "name": "Soldier",
      "source": "compendium"
    },
    "race": {
      "guid": "race_goliath",
      "version": "2024-11-25T12:00:00Z",
      "name": "Goliath",
      "source": "compendium",
      "choices": {
        "ability_increase_2": "strength",
        "ability_increase_1": "constitution"
      }
    },
    "classes": [
      {
        "guid": "class_barbarian",
        "version": "2024-11-25T12:00:00Z",
        "name": "Barbarian",
        "level": 5,
        "hit_die": "d12",
        "source": "compendium",
        "choices": {
          "skill_proficiencies": ["Athletics", "Intimidation"],
          "weapon_mastery": ["Greataxe", "Handaxe"]
        },
        "subclass": {
          "guid": "subclass_path_berserker",
          "version": "2024-11-25T12:00:00Z",
          "name": "Path of the Berserker",
          "level_taken": 3,
          "source": "compendium"
        }
      }
    ]
  },

  "ability_scores": {
    "strength": {
      "base": 15,  // Rolled/assigned
      "race_bonus": 2,  // Goliath choice
      "other_bonuses": 0,
      "total": 17,
      "modifier": 3
    },
    "dexterity": {
      "base": 13,
      "race_bonus": 0,
      "other_bonuses": 0,
      "total": 13,
      "modifier": 1
    },
    "constitution": {
      "base": 14,
      "race_bonus": 1,  // Goliath choice
      "other_bonuses": 0,
      "total": 15,
      "modifier": 2
    },
    "intelligence": {
      "base": 10,
      "race_bonus": 0,
      "other_bonuses": 0,
      "total": 10,
      "modifier": 0
    },
    "wisdom": {
      "base": 12,
      "race_bonus": 0,
      "other_bonuses": 0,
      "total": 12,
      "modifier": 1
    },
    "charisma": {
      "base": 8,
      "race_bonus": 0,
      "other_bonuses": 0,
      "total": 8,
      "modifier": -1
    }
  },

  "proficiencies": {
    "proficiency_bonus": 3,
    "armor": ["light", "medium", "shields"],
    "weapons": ["simple", "martial"],
    "tools": ["dice_set"],
    "saving_throws": ["strength", "constitution"],
    "skills": {
      "acrobatics": {"proficient": false, "expertise": false},
      "animal_handling": {"proficient": false, "expertise": false},
      "arcana": {"proficient": false, "expertise": false},
      "athletics": {"proficient": true, "expertise": false},
      "deception": {"proficient": false, "expertise": false},
      "history": {"proficient": false, "expertise": false},
      "insight": {"proficient": false, "expertise": false},
      "intimidation": {"proficient": true, "expertise": false},
      "investigation": {"proficient": false, "expertise": false},
      "medicine": {"proficient": false, "expertise": false},
      "nature": {"proficient": false, "expertise": false},
      "perception": {"proficient": false, "expertise": false},
      "performance": {"proficient": false, "expertise": false},
      "persuasion": {"proficient": false, "expertise": false},
      "religion": {"proficient": false, "expertise": false},
      "sleight_of_hand": {"proficient": false, "expertise": false},
      "stealth": {"proficient": false, "expertise": false},
      "survival": {"proficient": false, "expertise": false}
    },
    "languages": ["Common", "Giant", "Dwarvish"]
  },

  "combat_stats": {
    "armor_class": {
      "base": 10,
      "dex_modifier": 1,
      "con_modifier": 2,  // Unarmored Defense
      "armor_bonus": 0,
      "shield_bonus": 0,
      "other_bonuses": 0,
      "total": 13,
      "calculation_method": "unarmored_defense"
    },
    "initiative": {
      "base_modifier": 1,
      "other_bonuses": 0,
      "total": 1,
      "advantage": false
    },
    "speed": {
      "walk": 40,  // 30 base + 10 Fast Movement
      "climb": 30,
      "swim": 30,
      "fly": 0,
      "burrow": 0
    },
    "hit_points": {
      "maximum": 52,  // (12 + 2) + 4*(7+2) = 14 + 36 = 50, or rolled higher
      "current": 52,
      "temporary": 0
    },
    "hit_dice": {
      "d12": {
        "total": 5,
        "current": 3  // Spent 2 on short rest
      }
    },
    "death_saves": {
      "successes": 0,
      "failures": 0
    }
  },

  "features": [
    {
      "guid": "feature_rage",
      "version": "2024-11-25T12:00:00Z",
      "name": "Rage",
      "source_type": "class",
      "source_name": "Barbarian",
      "level_gained": 1,
      "source": "compendium",
      "description": "You can imbue yourself with a primal power...",
      "resource": {
        "name": "Rage Uses",
        "current": 2,
        "maximum": 3,
        "recovery": "long_rest",
        "partial_recovery": {"short_rest": 1}
      },
      "active": false,
      "effects_while_active": [
        {"type": "damage_resistance", "damage_types": ["bludgeoning", "piercing", "slashing"]},
        {"type": "damage_bonus", "applies_to": "strength_weapon", "value": 2},
        {"type": "advantage", "applies_to": ["strength_checks", "strength_saves"]},
        {"type": "cannot_concentrate"},
        {"type": "cannot_cast_spells"}
      ]
    },
    {
      "guid": "feature_unarmored_defense",
      "version": "2024-11-25T12:00:00Z",
      "name": "Unarmored Defense",
      "source_type": "class",
      "source_name": "Barbarian",
      "level_gained": 1,
      "source": "compendium",
      "description": "While you aren't wearing any armor...",
      "effects": [
        {"type": "ac_calculation", "formula": "10 + dex_mod + con_mod", "requires": "no_armor"}
      ]
    },
    {
      "guid": "feature_danger_sense",
      "version": "2024-11-25T12:00:00Z",
      "name": "Danger Sense",
      "source_type": "class",
      "source_name": "Barbarian",
      "level_gained": 2,
      "source": "compendium",
      "description": "You gain an uncanny sense...",
      "effects": [
        {"type": "advantage", "applies_to": "dexterity_saves", "unless": "incapacitated"}
      ]
    },
    {
      "guid": "feature_reckless_attack",
      "version": "2024-11-25T12:00:00Z",
      "name": "Reckless Attack",
      "source_type": "class",
      "source_name": "Barbarian",
      "level_gained": 2,
      "source": "compendium",
      "description": "You can throw aside all concern for defense...",
      "activation": {
        "type": "toggle",
        "timing": "first_attack_of_turn"
      },
      "active": false,
      "effects_while_active": [
        {"type": "advantage", "applies_to": "strength_attacks"},
        {"type": "grant_advantage_against_you"}
      ]
    },
    {
      "guid": "feature_extra_attack",
      "version": "2024-11-25T12:00:00Z",
      "name": "Extra Attack",
      "source_type": "class",
      "source_name": "Barbarian",
      "level_gained": 5,
      "source": "compendium",
      "description": "You can attack twice instead of once...",
      "effects": [
        {"type": "attack_count", "value": 2, "action_type": "Attack"}
      ]
    },
    {
      "guid": "feature_fast_movement",
      "version": "2024-11-25T12:00:00Z",
      "name": "Fast Movement",
      "source_type": "class",
      "source_name": "Barbarian",
      "level_gained": 5,
      "source": "compendium",
      "description": "Your speed increases by 10 feet...",
      "effects": [
        {"type": "speed_bonus", "value": 10, "unless": "heavy_armor"}
      ]
    },
    {
      "guid": "feature_frenzy",
      "version": "2024-11-25T12:00:00Z",
      "name": "Frenzy",
      "source_type": "subclass",
      "source_name": "Path of the Berserker",
      "level_gained": 3,
      "source": "compendium",
      "description": "If you use Reckless Attack while your Rage is active...",
      "effects": [
        {
          "type": "damage_bonus",
          "applies_to": "first_hit_if_reckless_and_raging",
          "value": "2d6",  // Rage damage is +2 at this level
          "damage_type": "weapon"
        }
      ]
    },
    {
      "guid": "feat_savage_attacker",
      "version": "2024-11-25T12:00:00Z",
      "name": "Savage Attacker",
      "source_type": "background",
      "source_name": "Soldier",
      "level_gained": 1,
      "source": "compendium",
      "description": "You've trained to deal particularly damaging strikes...",
      "resource": {
        "name": "Savage Attacker Uses",
        "current": 3,
        "maximum": 3,
        "recovery": "long_rest"
      }
    }
  ],

  "attacks": [
    {
      "name": "Greataxe",
      "item_guid": "item_greataxe",
      "item_version": "2024-11-25T12:00:00Z",
      "source": "compendium",
      "type": "melee_weapon",
      "category": "martial",
      "attack_bonus": {
        "strength_mod": 3,
        "proficiency_bonus": 3,
        "magic_bonus": 0,
        "other_bonuses": 0,
        "total": 6
      },
      "damage": {
        "base_dice": "1d12",
        "strength_mod": 3,
        "rage_bonus": 2,  // When raging
        "magic_bonus": 0,
        "other_bonuses": 0,
        "total_static": 5,
        "total_with_rage": 7,
        "type": "slashing"
      },
      "properties": ["heavy", "two-handed"],
      "mastery": "cleave",
      "equipped": true
    },
    {
      "name": "Handaxe (Melee)",
      "item_guid": "item_handaxe",
      "item_version": "2024-11-25T12:00:00Z",
      "source": "compendium",
      "type": "melee_weapon",
      "category": "simple",
      "attack_bonus": {
        "strength_mod": 3,
        "proficiency_bonus": 3,
        "magic_bonus": 0,
        "other_bonuses": 0,
        "total": 6
      },
      "damage": {
        "base_dice": "1d6",
        "strength_mod": 3,
        "rage_bonus": 2,
        "magic_bonus": 0,
        "other_bonuses": 0,
        "total_static": 5,
        "total_with_rage": 7,
        "type": "slashing"
      },
      "properties": ["light", "thrown"],
      "range": {"normal": 20, "long": 60},
      "mastery": "vex",
      "equipped": true
    },
    {
      "name": "Handaxe (Thrown)",
      "item_guid": "item_handaxe",
      "item_version": "2024-11-25T12:00:00Z",
      "source": "compendium",
      "type": "ranged_weapon",
      "category": "simple",
      "attack_bonus": {
        "strength_mod": 3,
        "proficiency_bonus": 3,
        "magic_bonus": 0,
        "other_bonuses": 0,
        "total": 6
      },
      "damage": {
        "base_dice": "1d6",
        "strength_mod": 3,
        "rage_bonus": 0,  // Rage only applies to melee
        "magic_bonus": 0,
        "other_bonuses": 0,
        "total_static": 3,
        "type": "slashing"
      },
      "properties": ["light", "thrown"],
      "range": {"normal": 20, "long": 60},
      "mastery": "vex",
      "equipped": true
    }
  ],

  "spellcasting": null,  // Barbarians don't cast spells

  "inventory": {
    "currency": {
      "cp": 0,
      "sp": 5,
      "ep": 0,
      "gp": 127,
      "pp": 0
    },
    "carried_weight": 65,
    "carry_capacity": 255,  // 15 * Strength score
    "items": [
      {
        "guid": "item_greataxe",
        "version": "2024-11-25T12:00:00Z",
        "name": "Greataxe",
        "quantity": 1,
        "equipped": true,
        "attuned": false,
        "weight_lbs": 7,
        "source": "compendium"
      },
      {
        "guid": "item_handaxe",
        "version": "2024-11-25T12:00:00Z",
        "name": "Handaxe",
        "quantity": 4,
        "equipped": true,
        "attuned": false,
        "weight_lbs": 2,
        "source": "compendium"
      },
      {
        "guid": "item_explorers_pack",
        "version": "2024-11-25T12:00:00Z",
        "name": "Explorer's Pack",
        "quantity": 1,
        "equipped": true,
        "attuned": false,
        "weight_lbs": 59,
        "contains": [
          "backpack", "bedroll", "mess kit", "tinderbox",
          "10 torches", "10 days rations", "waterskin", "50ft rope"
        ],
        "source": "compendium"
      },
      {
        "guid": "item_potion_healing",
        "version": "2024-11-25T12:00:00Z",
        "name": "Potion of Healing",
        "quantity": 2,
        "equipped": false,
        "attuned": false,
        "weight_lbs": 0.5,
        "source": "compendium"
      }
    ],
    "attunement_slots": {
      "used": 0,
      "maximum": 3
    }
  },

  "conditions": [],  // e.g., ["poisoned", "frightened"]
  
  "temporary_effects": [
    // Active buffs/debuffs not from features
    // {
    //   "name": "Bless",
    //   "source": "Cleric ally",
    //   "duration": {"rounds": 10},
    //   "effects": [{"type": "d4_to_attacks_and_saves"}],
    //   "concentration_by": "ally_character_id"
    // }
  ],

  "notes": {
    "personality_traits": "I face problems head-on. A simple, direct solution is the best path to success.",
    "ideals": "Greater Good. Our lot is to lay down our lives in defense of others.",
    "bonds": "I would still lay down my life for the people I served with.",
    "flaws": "I have little respect for anyone who is not a proven warrior.",
    "backstory": "Grog Strongjaw is a goliath barbarian...",
    "appearance": "Grog is a goliath with light gray skin and black tattoos...",
    "other": "Likes ale. Doesn't like reading."
  }
}
```

---

## Template System

### Purpose

Templates define the **structure** and **validation rules** for character sheet components. They ensure:
- Consistent data format
- Type safety
- Extensibility for homebrew
- Cross-system compatibility

### Component Template Types

#### 1. Resource Template

Used for: Rage uses, spell slots, ki points, sorcery points, wild shapes, etc.

```json
{
  "component_type": "resource",
  "name": "Resource Component",
  "description": "Tracks limited-use features",
  "schema": {
    "type": "object",
    "required": ["name", "maximum", "current", "recovery"],
    "properties": {
      "name": {
        "type": "string",
        "description": "Display name of the resource"
      },
      "current": {
        "type": "integer",
        "minimum": 0,
        "description": "Current uses remaining"
      },
      "maximum": {
        "type": ["integer", "string"],
        "description": "Max uses, or formula like [[level_table:class:column]]"
      },
      "recovery": {
        "type": "string",
        "enum": ["short_rest", "long_rest", "dawn", "dusk", "per_day", "never"],
        "description": "When resource refreshes"
      },
      "partial_recovery": {
        "type": "object",
        "description": "Recover some uses on other triggers",
        "properties": {
          "short_rest": {"type": "integer"},
          "dawn": {"type": "integer"}
        }
      }
    }
  },
  "for_types": ["feature", "class", "subclass", "spell"]
}
```

#### 2. Modifier Template

Used for: Stat bonuses, damage resistance, advantage/disadvantage, etc.

```json
{
  "component_type": "modifier",
  "name": "Modifier Component",
  "description": "Alters character stats, rolls, or capabilities",
  "schema": {
    "type": "object",
    "required": ["type"],
    "properties": {
      "type": {
        "type": "string",
        "enum": [
          "ability_bonus", "skill_bonus", "save_bonus", "ac_bonus",
          "damage_bonus", "attack_bonus", "speed_bonus",
          "damage_resistance", "damage_immunity", "damage_vulnerability",
          "condition_immunity",
          "advantage", "disadvantage"
        ]
      },
      "applies_to": {
        "type": ["string", "array"],
        "description": "What this modifies (skill name, ability, damage type, etc.)"
      },
      "value": {
        "type": ["integer", "string"],
        "description": "Numeric bonus or formula"
      },
      "while_active": {
        "type": "boolean",
        "description": "Only applies when parent feature is active"
      },
      "conditional": {
        "type": "string",
        "description": "When this applies (e.g., 'while_raging', 'if_unarmored')"
      }
    }
  },
  "for_types": ["feature", "item", "spell", "condition"]
}
```

#### 3. Attack Template

Used for: Weapon attacks, spell attacks, unarmed strikes

```json
{
  "component_type": "attack",
  "name": "Attack Component",
  "description": "Represents an attack a character can make",
  "schema": {
    "type": "object",
    "required": ["name", "type", "attack_bonus", "damage"],
    "properties": {
      "name": {"type": "string"},
      "type": {
        "type": "string",
        "enum": ["melee_weapon", "ranged_weapon", "melee_spell", "ranged_spell", "unarmed"]
      },
      "attack_bonus": {
        "type": "object",
        "description": "Breakdown of attack roll bonus",
        "properties": {
          "ability_mod": {"type": "integer"},
          "proficiency_bonus": {"type": "integer"},
          "magic_bonus": {"type": "integer"},
          "other_bonuses": {"type": "integer"},
          "total": {"type": "integer"}
        }
      },
      "damage": {
        "type": "object",
        "required": ["base_dice", "type"],
        "properties": {
          "base_dice": {"type": "string", "pattern": "^\\d+d\\d+$"},
          "ability_mod": {"type": "integer"},
          "magic_bonus": {"type": "integer"},
          "other_bonuses": {"type": "integer"},
          "total_static": {"type": "integer"},
          "type": {
            "type": "string",
            "enum": ["slashing", "piercing", "bludgeoning", "fire", "cold", "lightning", "thunder", "acid", "poison", "radiant", "necrotic", "force", "psychic"]
          }
        }
      },
      "properties": {
        "type": "array",
        "items": {"type": "string"}
      },
      "range": {
        "type": "object",
        "properties": {
          "normal": {"type": "integer"},
          "long": {"type": "integer"}
        }
      }
    }
  },
  "for_types": ["item", "feature", "spell"]
}
```

#### 4. Spell Slot Template

Used for: Spellcasting classes

```json
{
  "component_type": "spell_slot",
  "name": "Spell Slot Component",
  "description": "Tracks spell slots by level",
  "schema": {
    "type": "object",
    "required": ["slots_by_level"],
    "properties": {
      "slots_by_level": {
        "type": "object",
        "description": "Spell slots for each level 1-9",
        "properties": {
          "1": {"type": "object", "properties": {"total": {"type": "integer"}, "current": {"type": "integer"}}},
          "2": {"type": "object", "properties": {"total": {"type": "integer"}, "current": {"type": "integer"}}},
          "3": {"type": "object", "properties": {"total": {"type": "integer"}, "current": {"type": "integer"}}},
          "4": {"type": "object", "properties": {"total": {"type": "integer"}, "current": {"type": "integer"}}},
          "5": {"type": "object", "properties": {"total": {"type": "integer"}, "current": {"type": "integer"}}},
          "6": {"type": "object", "properties": {"total": {"type": "integer"}, "current": {"type": "integer"}}},
          "7": {"type": "object", "properties": {"total": {"type": "integer"}, "current": {"type": "integer"}}},
          "8": {"type": "object", "properties": {"total": {"type": "integer"}, "current": {"type": "integer"}}},
          "9": {"type": "object", "properties": {"total": {"type": "integer"}, "current": {"type": "integer"}}}
        }
      },
      "recovery": {
        "type": "string",
        "enum": ["long_rest", "short_rest"],
        "default": "long_rest"
      }
    }
  },
  "for_types": ["class"]
}
```

#### 5. Prepared Spell List Template

```json
{
  "component_type": "prepared_spell_list",
  "name": "Prepared Spell List",
  "description": "Spells a character has prepared",
  "schema": {
    "type": "object",
    "required": ["spells", "preparation_type"],
    "properties": {
      "spells": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["guid", "name", "level"],
          "properties": {
            "guid": {"type": "string"},
            "version": {"type": "string", "format": "date-time"},
            "name": {"type": "string"},
            "level": {"type": "integer", "minimum": 0, "maximum": 9},
            "always_prepared": {"type": "boolean", "default": false},
            "source": {"type": "string"}
          }
        }
      },
      "cantrips": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "guid": {"type": "string"},
            "version": {"type": "string", "format": "date-time"},
            "name": {"type": "string"}
          }
        }
      },
      "preparation_type": {
        "type": "string",
        "enum": ["daily", "on_level", "known"],
        "description": "When spells can be changed"
      },
      "max_prepared": {
        "type": ["integer", "string"],
        "description": "Max spells that can be prepared, or formula"
      }
    }
  },
  "for_types": ["class"]
}
```

---

## Update Propagation

### The Problem

When compendium content changes (errata, balance updates, homebrew fixes):
- Which characters get the update?
- When does it apply?
- What if the change breaks existing characters?

### The Solution: DM-Controlled Selective Updates

#### Update Detection

```python
# Backend pseudo-code
def check_for_updates(character_id):
    """Returns list of available updates for a character"""
    character = db.get_character(character_id)
    updates = []
    
    # Check each versioned component in sheet_data
    for feature in character.sheet_data['features']:
        compendium_item = db.compendium_items.get(
            guid=feature['guid']
        )
        
        if compendium_item.version > feature['version']:
            updates.append({
                'component': feature['name'],
                'component_type': 'feature',
                'current_version': feature['version'],
                'new_version': compendium_item.version,
                'changes': diff(feature, compendium_item.data)
            })
    
    return updates
```

#### Update UI Flow

```
1. DM opens campaign management
2. System shows: "3 characters have updates available"
3. DM clicks to see details:
   
   Grog Strongjaw:
   - Rage (v2024-11-25) → (v2024-11-30)
     Changes: Rage damage at level 5 increased from +2 to +3
   - Frenzy (v2024-11-25) → (v2024-11-30)
     Changes: Description clarified, no mechanical change
   
   [Update This Character] [Update All Characters] [Ignore]
   
4. DM chooses update strategy per change:
   - Update now
   - Schedule for next long rest
   - Ignore (keep old version)
```

#### Update Application

```python
def apply_update(character_id, component_guid, new_version):
    """Updates a single component to new version"""
    character = db.get_character(character_id)
    compendium_item = db.compendium_items.get(guid=component_guid)
    
    # Find component in sheet_data
    for feature in character.sheet_data['features']:
        if feature['guid'] == component_guid:
            # Preserve player choices and current state
            old_resource = feature.get('resource', {})
            old_active = feature.get('active', False)
            
            # Update to new data
            feature.update(compendium_item.data)
            feature['version'] = new_version
            
            # Restore state
            if 'resource' in feature:
                feature['resource']['current'] = old_resource.get('current', feature['resource']['maximum'])
            feature['active'] = old_active
            
            break
    
    character.sheet_data['meta']['sheet_version'] = datetime.now()
    db.save_character(character)
```

### Versioning Best Practices

1. **Semantic Versioning with Timestamps**
   - Major changes: New timestamp, breaking changes
   - Minor changes: New timestamp, backward compatible
   - Patches: New timestamp, bug fixes only

2. **Migration Functions**
   - Some updates may need custom migration logic
   - Store migration functions in compendium items:
   
   ```json
   {
     "guid": "feature_rage",
     "version": "2024-11-30T10:00:00Z",
     "migration_from": {
       "2024-11-25T12:00:00Z": {
         "function": "migrate_rage_damage_increase",
         "description": "Recalculate rage damage bonus"
       }
     }
   }
   ```

3. **Audit Trail**
   - Log all updates to character
   - Keep update history:
   
   ```json
   {
     "update_history": [
       {
         "timestamp": "2024-11-30T14:00:00Z",
         "component": "Rage",
         "old_version": "2024-11-25T12:00:00Z",
         "new_version": "2024-11-30T10:00:00Z",
         "applied_by": "dm_user_id",
         "changes": "Rage damage +2 → +3"
       }
     ]
   }
   ```

---

## Implementation Examples

### Example 1: Creating a Character from Scratch

```python
# 1. Player selects race
race = compendium_items.get(name="Goliath", type="race")

character_sheet = {
    "basic_info": {
        "race": {
            "guid": race.id,
            "version": race.version,
            "name": race.data['name'],
            "source": "compendium",
            "choices": {}  # Will fill in during creation wizard
        }
    },
    "ability_scores": {
        # Initialize all to 0, will be set during ability score step
    }
}

# 2. Player makes race choices (ability score increases)
# UI shows: "Choose one ability to increase by 2"
player_choice_1 = "strength"
player_choice_2 = "constitution"

character_sheet["basic_info"]["race"]["choices"] = {
    "ability_increase_2": player_choice_1,
    "ability_increase_1": player_choice_2
}

# 3. Player rolls ability scores
character_sheet["ability_scores"]["strength"]["base"] = 15
character_sheet["ability_scores"]["strength"]["race_bonus"] = 2  # From choice
character_sheet["ability_scores"]["strength"]["total"] = 17
# ... etc for other abilities

# 4. Player selects class
barbarian_class = compendium_items.get(name="Barbarian", type="class")

character_sheet["basic_info"]["classes"] = [{
    "guid": barbarian_class.id,
    "version": barbarian_class.version,
    "name": "Barbarian",
    "level": 1,
    "source": "compendium",
    "choices": {
        "skill_proficiencies": [],  # Will choose 2
        "weapon_mastery": []  # Will choose 2
    }
}]

# 5. Add class features for level 1
for feature_ref in barbarian_class.data['features_by_level']['1']:
    feature = compendium_items.get(guid=feature_ref['guid'])
    
    character_sheet["features"].append({
        "guid": feature.id,
        "version": feature.version,
        "name": feature.data['name'],
        "source_type": "class",
        "source_name": "Barbarian",
        "level_gained": 1,
        "source": "compendium",
        "description": feature.data['description'],
        **feature.data  # Copy all feature data
    })
    
    # Initialize resources if feature has them
    if 'resource' in feature_ref.get('grants', {}):
        character_sheet["features"][-1]["resource"]["current"] = \
            character_sheet["features"][-1]["resource"]["maximum"]

# Save to database
db.characters.create(
    campaign_id=campaign_id,
    player_id=player_id,
    name="Grog Strongjaw",
    sheet_data=character_sheet
)
```

### Example 2: Using a Feature (Activating Rage)

```python
def use_feature(character_id, feature_guid):
    """Player activates a feature like Rage"""
    character = db.get_character(character_id)
    
    # Find the feature
    feature = next(
        f for f in character.sheet_data['features']
        if f['guid'] == feature_guid
    )
    
    # Check if has uses remaining
    if feature.get('resource'):
        if feature['resource']['current'] <= 0:
            return {"error": "No uses remaining"}
        
        # Consume a use
        feature['resource']['current'] -= 1
    
    # Activate the feature
    feature['active'] = True
    
    # Apply effects (this would trigger UI updates, recalculations, etc.)
    # For Rage, this would:
    # - Add damage resistance to character.sheet_data['temporary_effects']
    # - Increase damage bonuses on attacks
    # - Grant advantage on Strength checks/saves
    
    db.save_character(character)
    
    return {
        "success": True,
        "feature": feature['name'],
        "uses_remaining": feature['resource']['current']
    }
```

### Example 3: Taking a Long Rest

```python
def long_rest(character_id):
    """Character takes a long rest, recovering resources"""
    character = db.get_character(character_id)
    sheet = character.sheet_data
    
    # Restore HP
    sheet['combat_stats']['hit_points']['current'] = \
        sheet['combat_stats']['hit_points']['maximum']
    
    # Restore all hit dice up to half
    for die_type, dice in sheet['combat_stats']['hit_dice'].items():
        dice['current'] = max(dice['current'], dice['total'] // 2)
    
    # Restore resources that recover on long rest
    for feature in sheet['features']:
        if feature.get('resource'):
            if feature['resource'].get('recovery') == 'long_rest':
                feature['resource']['current'] = feature['resource']['maximum']
    
    # Restore spell slots (if caster)
    if sheet.get('spellcasting'):
        for level, slots in sheet['spellcasting']['spell_slots'].items():
            slots['current'] = slots['total']
    
    # Clear temporary effects
    sheet['temporary_effects'] = []
    
    # Remove exhaustion level
    if 'exhaustion' in sheet['conditions']:
        # Remove one level, or entire condition if only 1 level
        pass
    
    # Update last rest timestamp
    sheet['meta']['last_rest'] = {
        'type': 'long',
        'timestamp': datetime.now().isoformat()
    }
    
    db.save_character(character)
    
    return {"success": True, "message": "Long rest completed"}
```

### Example 4: Leveling Up

```python
def level_up(character_id, class_guid):
    """Character gains a level in a class"""
    character = db.get_character(character_id)
    sheet = character.sheet_data
    
    # Find the class
    char_class = next(
        c for c in sheet['basic_info']['classes']
        if c['guid'] == class_guid
    )
    
    old_level = char_class['level']
    new_level = old_level + 1
    
    # Update level
    char_class['level'] = new_level
    sheet['basic_info']['level'] = sum(c['level'] for c in sheet['basic_info']['classes'])
    
    # Get class from compendium
    compendium_class = db.compendium_items.get(guid=class_guid)
    
    # Add HP (roll or take average)
    hit_die_size = int(compendium_class.data['hit_die'][1:])  # "d12" -> 12
    con_mod = sheet['ability_scores']['constitution']['modifier']
    
    # Could let player roll, or use fixed value
    hp_gain = (hit_die_size // 2 + 1) + con_mod  # Average
    sheet['combat_stats']['hit_points']['maximum'] += max(1, hp_gain)
    sheet['combat_stats']['hit_points']['current'] += max(1, hp_gain)
    
    # Add hit die
    die_type = compendium_class.data['hit_die']
    sheet['combat_stats']['hit_dice'][die_type]['total'] += 1
    sheet['combat_stats']['hit_dice'][die_type]['current'] += 1
    
    # Update proficiency bonus if needed
    new_prof = 2 + ((new_level - 1) // 4)
    sheet['proficiencies']['proficiency_bonus'] = new_prof
    
    # Add new class features for this level
    if str(new_level) in compendium_class.data['features_by_level']:
        for feature_ref in compendium_class.data['features_by_level'][str(new_level)]:
            feature = db.compendium_items.get(guid=feature_ref['guid'])
            
            sheet['features'].append({
                "guid": feature.id,
                "version": feature.version,
                "name": feature.data['name'],
                "source_type": "class",
                "source_name": compendium_class.data['name'],
                "level_gained": new_level,
                "source": "compendium",
                **feature.data
            })
            
            # Initialize resources
            if feature.get('resource'):
                sheet['features'][-1]['resource']['current'] = \
                    sheet['features'][-1]['resource']['maximum']
    
    # Update spell slots if caster
    if compendium_class.data.get('spellcasting'):
        # Recalculate spell slots based on new level
        pass
    
    # Ability Score Improvement at levels 4, 8, 12, 16, 19
    if new_level in [4, 8, 12, 16, 19]:
        # Trigger ASI/Feat selection
        pass
    
    db.save_character(character)
    
    return {"success": True, "new_level": new_level}
```

---

## Additional Considerations

### 1. Calculated Values

Some values are derived from others and should be recalculated on demand rather than stored:

**Always Recalculate:**
- Ability modifiers (from scores)
- Skill bonuses (ability mod + proficiency)
- Attack bonuses (ability mod + proficiency + magic)
- Spell save DC (8 + proficiency + spellcasting ability mod)
- Passive Perception (10 + Wisdom (Perception) bonus)

**Store with Calculation Metadata:**
```json
{
  "armor_class": {
    "total": 15,
    "calculation": {
      "method": "light_armor",
      "base": 10,
      "armor": 2,
      "dex_mod": 3,
      "shield": 0,
      "other": 0
    }
  }
}
```

### 2. Multiclassing

Characters with multiple classes:

```json
{
  "basic_info": {
    "level": 7,  // Total character level
    "classes": [
      {
        "guid": "class_fighter",
        "version": "2024-11-25T12:00:00Z",
        "name": "Fighter",
        "level": 5,
        "subclass": {
          "guid": "subclass_champion",
          "level_taken": 3
        }
      },
      {
        "guid": "class_rogue",
        "version": "2024-11-25T12:00:00Z",
        "name": "Rogue",
        "level": 2,
        "subclass": null  // Not high enough level yet
      }
    ]
  },
  "combat_stats": {
    "hit_dice": {
      "d10": {"total": 5, "current": 3},  // Fighter
      "d8": {"total": 2, "current": 2}     // Rogue
    }
  }
}
```

### 3. Temporary Effects

Active buffs/debuffs that aren't features:

```json
{
  "temporary_effects": [
    {
      "name": "Bless",
      "source": "Cleric Ally",
      "source_character_id": "uuid_of_cleric",
      "duration": {
        "type": "rounds",
        "remaining": 7
      },
      "effects": [
        {
          "type": "bonus_to_rolls",
          "applies_to": ["attacks", "saves"],
          "value": "1d4",
          "description": "Add 1d4 to attack rolls and saving throws"
        }
      ],
      "concentration": true,
      "concentration_by": "uuid_of_cleric"
    }
  ]
}
```

### 4. Conditions

Status effects that impose mechanical penalties:

```json
{
  "conditions": [
    {
      "name": "poisoned",
      "source": "Giant Spider bite",
      "save_dc": 11,
      "save_ability": "constitution",
      "save_interval": "end_of_turn",
      "effects": [
        {
          "type": "disadvantage",
          "applies_to": ["attack_rolls", "ability_checks"]
        }
      ]
    }
  ]
}
```

### 5. Homebrew Content

Homebrew uses the same structure but is flagged differently:

```sql
INSERT INTO compendium_items (type, name, data, version, created_by, is_official)
VALUES (
  'race',
  'Catfolk',
  '{"description": "Agile feline humanoids...", ...}',
  NOW(),
  'user_id_of_creator',
  FALSE  -- Not official SRD content
);
```

### 6. Content Packs

Groups of homebrew content can be packaged together:

```sql
CREATE TABLE content_packs (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    author_id UUID REFERENCES users(id),
    version TIMESTAMP NOT NULL DEFAULT NOW(),
    items UUID[] REFERENCES compendium_items(id),
    is_published BOOLEAN DEFAULT FALSE,
    tags TEXT[]
);
```

---

## Summary

This schema design provides:

✅ **Self-Contained Sheets** - All data in sheet_data JSONB  
✅ **Version Tracking** - Every component has guid + version  
✅ **Selective Updates** - DM controls update propagation  
✅ **Modular Components** - Template-based validation  
✅ **System Agnostic** - Works for D&D, Cyberpunk, etc.  
✅ **Homebrew Ready** - Same structure for official + custom content  
✅ **Future-Proof** - Easy to extend with new component types  

The timestamp-based versioning gives you human-readable, sortable versions, and the three-table architecture (compendium_items, component_templates, characters) keeps things simple while remaining flexible enough for any game system.
