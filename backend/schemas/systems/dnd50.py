from core.schema_builder import ObjectRegistration
from core import field_types as ft

# System metadata
SYSTEM_INFO = {
    "guid": "d&d5.0",
    "name": "Dungeons & Dragons 5e (2014)",
    "description": "The 2014 release of the fifth edition of Dungeons & Dragons.",
    "link": "https://www.dndbeyond.com/"
}

# Basic Rule Schema - for hierarchical rule definitions
basic_rule = ObjectRegistration(system="d&d5.0")
basic_rule.add_field("name", ft.short_text(100), base_field=True, required=True)
basic_rule.add_markdown_field("description", max_len=10000, required=False)
basic_rule.add_parent_field()
basic_rule.add_category_field()

# Item Schema - updated to use new field types and demonstrate hierarchy
item = ObjectRegistration(system="d&d5.0")
item.add_field("name", ft.short_text(100), base_field=True, required=True)
item.add_markdown_field("description", required=False)
item.add_field("weight", ft.integer(min_val=0), base_field=True)
item.add_field("damage_dice", ft.short_text(20), placeholder="1d8")
item.add_field("damage_type", ft.compendium_link(
    query="d&d5.0-basic-rule-*",
    label="Damage Type"
))
# Link to weapon category (e.g., "Simple Melee Weapon")
item.add_field("item_category", ft.compendium_link(
    query="d&d5.0-basic-rule-*",
    label="Item Category"
))
# Link to mastery type if applicable
item.add_field("mastery_type", ft.compendium_link(
    query="d&d5.0-basic-rule-*",
    label="Mastery Type"
))

# Spell Schema
spell = ObjectRegistration(system="d&d5.0")
spell.add_field("name", ft.short_text(100), base_field=True, required=True)
spell.add_markdown_field("description", required=False)
spell.add_field("level", ft.integer(min_val=0, max_val=9), required=True)
spell.add_field("school", ft.short_text(20), placeholder="Evocation")
spell.add_field("casting_time", ft.short_text(50), placeholder="1 action")
spell.add_field("range", ft.short_text(50))
spell.add_field("components", ft.short_text(50), placeholder="V, S, M")
spell.add_field("duration", ft.short_text(50))
spell.add_field("concentration", ft.short_text(5), placeholder="Yes/No")

# Class Schema
character_class = ObjectRegistration(system="d&d5.0")
character_class.add_field("name", ft.short_text(50), base_field=True, required=True)
character_class.add_markdown_field("description", required=False)
character_class.add_field("hit_die", ft.short_text(5), placeholder="d8")
character_class.add_field("primary_ability", ft.short_text(50), placeholder="Strength/Dexterity")

# Seed data - foundational entries created on startup
SEED_ENTRIES = [
    # Damage Types Container
    {
        "guid": "d&d5.0-basic-rule-damage-types",
        "name": "Damage Types",
        "entry_type": "basic-rule",
        "data": {
            "name": "Damage Types",
            "description": "# Damage Types\n\nThe various types of damage that can be dealt in D&D 5e.",
            "entry_category": "container"
        },
        "source": {"name": "PHB"}
    },
    # Physical Damage Types
    {
        "guid": "d&d5.0-basic-rule-slashing",
        "name": "Slashing",
        "entry_type": "basic-rule",
        "parent_guid": "d&d5.0-basic-rule-damage-types",
        "data": {
            "name": "Slashing",
            "description": "Slashing damage is dealt by swords, axes, and claws.",
            "entry_category": "definition",
            "parent_guid": "d&d5.0-basic-rule-damage-types"
        },
        "source": {"name": "PHB"}
    },
    {
        "guid": "d&d5.0-basic-rule-bludgeoning",
        "name": "Bludgeoning",
        "entry_type": "basic-rule",
        "parent_guid": "d&d5.0-basic-rule-damage-types",
        "data": {
            "name": "Bludgeoning",
            "description": "Bludgeoning damage is dealt by blunt force from hammers, clubs, and falling.",
            "entry_category": "definition",
            "parent_guid": "d&d5.0-basic-rule-damage-types"
        },
        "source": {"name": "PHB"}
    },
    {
        "guid": "d&d5.0-basic-rule-piercing",
        "name": "Piercing",
        "entry_type": "basic-rule",
        "parent_guid": "d&d5.0-basic-rule-damage-types",
        "data": {
            "name": "Piercing",
            "description": "Piercing damage is dealt by arrows, spears, and fangs.",
            "entry_category": "definition",
            "parent_guid": "d&d5.0-basic-rule-damage-types"
        },
        "source": {"name": "PHB"}
    },
    # Equipment Hierarchy
    {
        "guid": "d&d5.0-basic-rule-equipment",
        "name": "Equipment",
        "entry_type": "basic-rule",
        "data": {
            "name": "Equipment",
            "description": "# Equipment\n\nAdventurers rely on various types of equipment to survive and thrive.",
            "entry_category": "container"
        },
        "source": {"name": "PHB"}
    },
    {
        "guid": "d&d5.0-basic-rule-weapons",
        "name": "Weapons",
        "entry_type": "basic-rule",
        "parent_guid": "d&d5.0-basic-rule-equipment",
        "data": {
            "name": "Weapons",
            "description": "## Weapons\n\nWeapons are categorized by their complexity and fighting style.",
            "entry_category": "container",
            "parent_guid": "d&d5.0-basic-rule-equipment"
        },
        "source": {"name": "PHB"}
    },
    {
        "guid": "d&d5.0-basic-rule-weapon-masteries",
        "name": "Weapon Masteries",
        "entry_type": "basic-rule",
        "parent_guid": "d&d5.0-basic-rule-weapons",
        "data": {
            "name": "Weapon Masteries",
            "description": "### Weapon Masteries\n\nWeapon proficiency categories.",
            "entry_category": "container",
            "parent_guid": "d&d5.0-basic-rule-weapons"
        },
        "source": {"name": "PHB"}
    },
    {
        "guid": "d&d5.0-basic-rule-simple-melee-weapon",
        "name": "Simple Melee Weapon",
        "entry_type": "basic-rule",
        "parent_guid": "d&d5.0-basic-rule-weapon-masteries",
        "data": {
            "name": "Simple Melee Weapon",
            "description": "Simple melee weapons require minimal training and include clubs, daggers, and quarterstaffs.",
            "entry_category": "definition",
            "parent_guid": "d&d5.0-basic-rule-weapon-masteries"
        },
        "source": {"name": "PHB"}
    },
    {
        "guid": "d&d5.0-basic-rule-simple-ranged-weapon",
        "name": "Simple Ranged Weapon",
        "entry_type": "basic-rule",
        "parent_guid": "d&d5.0-basic-rule-weapon-masteries",
        "data": {
            "name": "Simple Ranged Weapon",
            "description": "Simple ranged weapons include light crossbows and shortbows.",
            "entry_category": "definition",
            "parent_guid": "d&d5.0-basic-rule-weapon-masteries"
        },
        "source": {"name": "PHB"}
    },
    {
        "guid": "d&d5.0-basic-rule-martial-melee-weapon",
        "name": "Martial Melee Weapon",
        "entry_type": "basic-rule",
        "parent_guid": "d&d5.0-basic-rule-weapon-masteries",
        "data": {
            "name": "Martial Melee Weapon",
            "description": "Martial melee weapons require specialized training and include longswords, greatswords, and glaives.",
            "entry_category": "definition",
            "parent_guid": "d&d5.0-basic-rule-weapon-masteries"
        },
        "source": {"name": "PHB"}
    },
    {
        "guid": "d&d5.0-basic-rule-martial-ranged-weapon",
        "name": "Martial Ranged Weapon",
        "entry_type": "basic-rule",
        "parent_guid": "d&d5.0-basic-rule-weapon-masteries",
        "data": {
            "name": "Martial Ranged Weapon",
            "description": "Martial ranged weapons include longbows and heavy crossbows.",
            "entry_category": "definition",
            "parent_guid": "d&d5.0-basic-rule-weapon-masteries"
        },
        "source": {"name": "PHB"}
    },
]

SCHEMAS = {
    "basic-rule": basic_rule,
    "item": item,
    "spell": spell,
    "class": character_class
}
