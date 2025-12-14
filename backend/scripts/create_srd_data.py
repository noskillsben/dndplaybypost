"""
SRD Extraction Utility

This script extracts D&D 5e SRD content and converts it to JSON format
compatible with the compendium system.

Since the SRD PDF may not always be available, this script can work with:
1. PDF extraction (if PDF is available)
2. Manual data entry (structured Python dictionaries)
3. Alternative sources (online APIs, text files)

For now, we'll create sample data structures that match the schema.
The actual extraction can be done manually or with additional tooling.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


# ============================================================================
# Sample SRD Data - Replace with actual extraction
# ============================================================================

def create_sample_barbarian_class() -> Dict[str, Any]:
    """Create sample Barbarian class data"""
    return {
        "type": "class",
        "name": "Barbarian",
        "data": {
            "description": "A fierce warrior of primitive background who can enter a battle rage",
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
                    {"item_name": "Greataxe", "quantity": 1},
                    {"item_name": "Handaxe", "quantity": 2},
                    {"item_name": "Explorer's Pack", "quantity": 1},
                    {"item_name": "Javelin", "quantity": 4}
                ],
                "option_b": [
                    {"money": {"gp": 75}}
                ]
            },
            "features_by_level": {
                "1": [
                    {
                        "name": "Rage",
                        "description": "In battle, you fight with primal ferocity. On your turn, you can enter a rage as a bonus action."
                    },
                    {
                        "name": "Unarmored Defense",
                        "description": "While you are not wearing any armor, your Armor Class equals 10 + your Dexterity modifier + your Constitution modifier."
                    }
                ],
                "2": [
                    {
                        "name": "Reckless Attack",
                        "description": "You can throw aside all concern for defense to attack with fierce desperation."
                    },
                    {
                        "name": "Danger Sense",
                        "description": "You have advantage on Dexterity saving throws against effects that you can see."
                    }
                ],
                "3": [
                    {
                        "name": "Primal Path",
                        "description": "You choose a path that shapes the nature of your rage."
                    }
                ],
                "5": [
                    {
                        "name": "Extra Attack",
                        "description": "You can attack twice, instead of once, whenever you take the Attack action on your turn."
                    },
                    {
                        "name": "Fast Movement",
                        "description": "Your speed increases by 10 feet while you aren't wearing heavy armor."
                    }
                ]
            },
            "subclasses": {
                "level": 3,
                "options": ["Path of the Berserker", "Path of the Totem Warrior"]
            },
            "spellcasting": None
        },
        "tags": ["class", "martial", "melee"],
        "is_official": True
    }


def create_sample_human_race() -> Dict[str, Any]:
    """Create sample Human race data"""
    return {
        "type": "race",
        "name": "Human",
        "data": {
            "description": "Humans are the most adaptable and ambitious people among the common races.",
            "size": "Medium",
            "speed": 30,
            "creature_type": "Humanoid",
            "age": {
                "maturity": 18,
                "lifespan": 80
            },
            "ability_score_increases": [
                {
                    "applies_to": "all",
                    "value": 1,
                    "description": "All ability scores increase by 1"
                }
            ],
            "traits": [],
            "languages": ["Common", "one extra language of your choice"],
            "darkvision": None
        },
        "tags": ["race", "humanoid", "versatile"],
        "is_official": True
    }


def create_sample_fireball_spell() -> Dict[str, Any]:
    """Create sample Fireball spell data"""
    return {
        "type": "spell",
        "name": "Fireball",
        "data": {
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
                "verbal": True,
                "somatic": True,
                "material": {
                    "required": True,
                    "description": "a tiny ball of bat guano and sulfur",
                    "consumed": False,
                    "cost_gp": 0
                }
            },
            "duration": {
                "type": "instantaneous"
            },
            "description": "A bright streak flashes from your pointing finger to a point you choose within range and then blossoms with a low roar into an explosion of flame.",
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
            "ritual": False,
            "concentration": False
        },
        "tags": ["spell", "evocation", "fire", "damage"],
        "is_official": True
    }


def create_sample_longsword_item() -> Dict[str, Any]:
    """Create sample Longsword item data"""
    return {
        "type": "item",
        "name": "Longsword",
        "data": {
            "category": "weapon",
            "subcategory": "martial_melee",
            "rarity": "common",
            "requires_attunement": False,
            "description": "Proficiency with a longsword allows you to add your proficiency bonus to the attack roll for any attack you make with it.",
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
            "tags": ["weapon", "martial", "melee", "slashing", "versatile"]
        },
        "tags": ["item", "weapon", "martial", "melee"],
        "is_official": True
    }


def create_sample_soldier_background() -> Dict[str, Any]:
    """Create sample Soldier background data"""
    return {
        "type": "background",
        "name": "Soldier",
        "data": {
            "description": "War has been your life for as long as you care to remember.",
            "ability_score_increases": None,
            "feat_guid": None,
            "skill_proficiencies": ["Athletics", "Intimidation"],
            "tool_proficiency": {
                "category": "gaming_set",
                "options": ["dice", "cards", "chess"]
            },
            "equipment_options": {
                "option_a": [
                    {"item_name": "Insignia of rank", "quantity": 1},
                    {"item_name": "Trophy from fallen enemy", "quantity": 1},
                    {"item_name": "Gaming set", "quantity": 1},
                    {"item_name": "Common clothes", "quantity": 1},
                    {"money": {"gp": 10}}
                ]
            }
        },
        "tags": ["background", "martial"],
        "is_official": True
    }


def create_component_templates() -> List[Dict[str, Any]]:
    """Create component template definitions"""
    return [
        {
            "component_type": "resource",
            "name": "Resource Component",
            "description": "Tracks limited-use features",
            "schema": {
                "type": "object",
                "required": ["name", "maximum", "current", "recovery"],
                "properties": {
                    "name": {"type": "string"},
                    "current": {"type": "integer", "minimum": 0},
                    "maximum": {"type": ["integer", "string"]},
                    "recovery": {
                        "type": "string",
                        "enum": ["short_rest", "long_rest", "dawn", "dusk", "per_day", "never"]
                    }
                }
            },
            "for_types": ["feature", "class", "subclass", "spell"]
        },
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
                            "condition_immunity", "advantage", "disadvantage"
                        ]
                    },
                    "applies_to": {"type": ["string", "array"]},
                    "value": {"type": ["integer", "string"]},
                    "while_active": {"type": "boolean"},
                    "conditional": {"type": "string"}
                }
            },
            "for_types": ["feature", "item", "spell", "condition"]
        }
    ]


# ============================================================================
# Export Functions
# ============================================================================

def export_to_json(data: Any, output_path: str):
    """Export data to JSON file"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Exported to {output_path}")


def create_sample_srd_data():
    """Create sample SRD data files"""
    base_path = Path("backend/data/srd")
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Export sample classes
    classes = [create_sample_barbarian_class()]
    export_to_json(classes, str(base_path / "classes.json"))
    
    # Export sample races
    races = [create_sample_human_race()]
    export_to_json(races, str(base_path / "races.json"))
    
    # Export sample spells
    spells = [create_sample_fireball_spell()]
    export_to_json(spells, str(base_path / "spells.json"))
    
    # Export sample items
    items = [create_sample_longsword_item()]
    export_to_json(items, str(base_path / "items.json"))
    
    # Export sample backgrounds
    backgrounds = [create_sample_soldier_background()]
    export_to_json(backgrounds, str(base_path / "backgrounds.json"))
    
    # Export component templates
    templates = create_component_templates()
    export_to_json(templates, str(base_path / "component_templates.json"))
    
    print("\nSample SRD data created successfully!")
    print(f"Location: {base_path}")
    print("\nTo add more content:")
    print("1. Edit the sample data functions in this script")
    print("2. Or manually create JSON files following the same structure")
    print("3. Or implement PDF extraction (requires pypdf2 or pdfplumber)")


if __name__ == "__main__":
    create_sample_srd_data()
