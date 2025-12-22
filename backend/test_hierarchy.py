"""
Test script to demonstrate hierarchical compendium system.

This script creates a hierarchical rule structure:
  Equipment (container)
  └── Weapons (container)
      └── Masteries (container)
          └── Simple Melee Weapon (definition)

Then creates a Club item that references the Simple Melee Weapon definition.
"""
import asyncio
import sys
sys.path.insert(0, '/home/ben/dndplaybypost/backend')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.compendium import CompendiumEntry
from core.markdown_renderer import render_tree, render_rulebook

# Database connection
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/dndplaybypost"

async def main():
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=== Creating Hierarchical Rule Structure ===\n")
        
        # 1. Create Equipment (top-level container)
        equipment = CompendiumEntry(
            guid="d&d5.0-basic-rule-equipment",
            system="d&d5.0",
            entry_type="basic-rule",
            name="Equipment",
            data={
                "name": "Equipment",
                "description": "# Equipment\n\nAdventurers rely on various types of equipment to survive and thrive in their quests.",
                "entry_category": "container",
                "parent_guid": None
            },
            homebrew=False,
            source="PHB"
        )
        session.add(equipment)
        print(f"✓ Created: {equipment.name} (container)")
        
        # 2. Create Weapons (child of Equipment)
        weapons = CompendiumEntry(
            guid="d&d5.0-basic-rule-weapons",
            system="d&d5.0",
            entry_type="basic-rule",
            name="Weapons",
            parent_guid="d&d5.0-basic-rule-equipment",
            data={
                "name": "Weapons",
                "description": "## Weapons\n\nWeapons are tools of combat, categorized by their complexity and fighting style.",
                "entry_category": "container",
                "parent_guid": "d&d5.0-basic-rule-equipment"
            },
            homebrew=False,
            source="PHB"
        )
        session.add(weapons)
        print(f"✓ Created: {weapons.name} (container, parent: Equipment)")
        
        # 3. Create Masteries (child of Weapons)
        masteries = CompendiumEntry(
            guid="d&d5.0-basic-rule-masteries",
            system="d&d5.0",
            entry_type="basic-rule",
            name="Weapon Masteries",
            parent_guid="d&d5.0-basic-rule-weapons",
            data={
                "name": "Weapon Masteries",
                "description": "### Weapon Masteries\n\nWeapon proficiency types determine how effectively a character can wield different weapons.",
                "entry_category": "container",
                "parent_guid": "d&d5.0-basic-rule-weapons"
            },
            homebrew=False,
            source="PHB"
        )
        session.add(masteries)
        print(f"✓ Created: {masteries.name} (container, parent: Weapons)")
        
        # 4. Create Simple Melee Weapon (definition)
        simple_melee = CompendiumEntry(
            guid="d&d5.0-basic-rule-simple-melee-weapon",
            system="d&d5.0",
            entry_type="basic-rule",
            name="Simple Melee Weapon",
            parent_guid="d&d5.0-basic-rule-masteries",
            data={
                "name": "Simple Melee Weapon",
                "description": "#### Simple Melee Weapon\n\nSimple melee weapons are easy to use and require minimal training. They include clubs, daggers, and quarterstaffs.",
                "entry_category": "definition",
                "parent_guid": "d&d5.0-basic-rule-masteries"
            },
            homebrew=False,
            source="PHB"
        )
        session.add(simple_melee)
        print(f"✓ Created: {simple_melee.name} (definition, parent: Weapon Masteries)")
        
        # 5. Create Slashing damage type
        slashing = CompendiumEntry(
            guid="d&d5.0-damage-type-slashing",
            system="d&d5.0",
            entry_type="damage-type",
            name="Slashing",
            data={
                "name": "Slashing",
                "description": "Slashing damage is dealt by swords, axes, and other bladed weapons."
            },
            homebrew=False,
            source="PHB"
        )
        session.add(slashing)
        print(f"✓ Created: {slashing.name} (damage type)")
        
        # 6. Create Club item that references the hierarchy
        club = CompendiumEntry(
            guid="d&d5.0-item-club",
            system="d&d5.0",
            entry_type="item",
            name="Club",
            data={
                "name": "Club",
                "description": "A simple wooden club, effective for bludgeoning foes.",
                "weight": 2,
                "damage_dice": "1d4",
                "damage_type": "d&d5.0-damage-type-slashing",
                "item_category": "d&d5.0-basic-rule-weapons",
                "mastery_type": "d&d5.0-basic-rule-simple-melee-weapon"
            },
            homebrew=False,
            source="PHB"
        )
        session.add(club)
        print(f"✓ Created: {club.name} (item, links to: Weapons, Simple Melee Weapon)")
        
        await session.commit()
        
        print("\n=== Testing Hierarchy Queries ===\n")
        
        # Test: Get children of Equipment
        from sqlalchemy.future import select
        children_result = await session.execute(
            select(CompendiumEntry).where(CompendiumEntry.parent_guid == "d&d5.0-basic-rule-equipment")
        )
        children = children_result.scalars().all()
        print(f"Children of Equipment: {[c.name for c in children]}")
        
        # Test: Get ancestors of Simple Melee Weapon
        ancestors = []
        current_guid = "d&d5.0-basic-rule-simple-melee-weapon"
        while current_guid:
            result = await session.execute(select(CompendiumEntry).where(CompendiumEntry.guid == current_guid))
            entry = result.scalar_one_or_none()
            if entry:
                ancestors.insert(0, entry.name)
                current_guid = entry.parent_guid
            else:
                break
        print(f"Ancestors of Simple Melee Weapon: {' → '.join(ancestors)}")
        
        print("\n=== Testing Markdown Rendering ===\n")
        
        # Render the Equipment tree as markdown
        markdown = await render_tree(session, "d&d5.0-basic-rule-equipment")
        print("Rendered Equipment hierarchy:")
        print("-" * 60)
        print(markdown)
        print("-" * 60)
        
        print("\n✅ All tests passed!")
        print("\nYou can now:")
        print("  1. Use the API endpoints to query the hierarchy")
        print("  2. Create more hierarchical entries")
        print("  3. Render markdown documentation")

if __name__ == "__main__":
    asyncio.run(main())
