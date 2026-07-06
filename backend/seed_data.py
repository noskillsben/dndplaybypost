"""
Seed foundational compendium data on startup.

This script runs after migrations and creates basic-rule entries
defined in system modules (e.g., dnd50.SEED_ENTRIES).

Automatically discovers all system modules in schemas/systems/ folder.

Uses "create or ignore" logic - safe to run multiple times.
"""
import asyncio
import sys
import os
import importlib
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

# Add parent directory to path
sys.path.insert(0, '/app')

from database import DATABASE_URL
from models.compendium import Compendium, CompendiumEntry
from models.system import System


def discover_system_modules():
    """
    Dynamically discover and import all system modules from schemas/systems/
    
    Returns a list of imported modules that have SYSTEM_INFO or SEED_ENTRIES
    """
    systems_dir = Path('/app/schemas/systems')
    system_modules = []
    
    # Find all .py files in the systems directory
    for file_path in systems_dir.glob('*.py'):
        # Skip __init__.py and any files starting with underscore
        if file_path.name.startswith('_'):
            continue
            
        # Get module name without .py extension
        module_name = file_path.stem
        
        try:
            # Dynamically import the module
            module = importlib.import_module(f'schemas.systems.{module_name}')
            
            # Check if module has the expected structure
            has_system_info = hasattr(module, 'SYSTEM_INFO')
            has_schemas = hasattr(module, 'SCHEMAS')
            has_seed_entries = hasattr(module, 'SEED_ENTRIES')
            
            # Add to list if it has at least one of the expected attributes
            if has_system_info or has_schemas or has_seed_entries:
                system_modules.append(module)
                print(f"  📦 Discovered system module: {module_name}")
            else:
                print(f"  ⚠ Skipping {module_name} (missing SYSTEM_INFO, SCHEMAS, or SEED_ENTRIES)")
                
        except Exception as e:
            print(f"  ❌ Error importing {module_name}: {e}")
    
    return system_modules


async def seed_systems(session: AsyncSession, system_modules):
    """Seed system metadata from discovered modules"""
    created_count = 0
    skipped_count = 0
    
    for system_module in system_modules:
        if not hasattr(system_module, 'SYSTEM_INFO'):
            continue
            
        system_info = system_module.SYSTEM_INFO
        guid = system_info['guid']
        
        # Check if exists
        result = await session.execute(
            select(System).where(System.guid == guid)
        )
        if result.scalar_one_or_none():
            skipped_count += 1
            continue
        
        # Create system record
        system = System(
            guid=guid,
            name=system_info['name'],
            description=system_info.get('description'),
            link=system_info.get('link')
        )
        session.add(system)
        created_count += 1
    
    if created_count > 0:
        await session.commit()
        print(f"  ✓ Created {created_count} systems")
    
    if skipped_count > 0:
        print(f"  ⊘ Skipped {skipped_count} existing systems")


async def ensure_core_compendium(session: AsyncSession, system: str) -> str:
    """Create (or reuse) the '<system>-core' compendium container for seed entries."""
    guid = f"{system}-core"
    result = await session.execute(select(Compendium).where(Compendium.guid == guid))
    if not result.scalar_one_or_none():
        session.add(Compendium(
            guid=guid,
            name=f"{system} core",
            description="Seeded core content",
            system=system,
        ))
        await session.commit()
        print(f"  ✓ Created compendium {guid}")
    return guid


async def seed_system(session: AsyncSession, system_module):
    """Seed entries for a system module"""
    # Get system name from SYSTEM_INFO or first schema
    system_name = "unknown"
    if hasattr(system_module, 'SYSTEM_INFO'):
        system_name = system_module.SYSTEM_INFO['guid']
    elif hasattr(system_module, 'SCHEMAS'):
        first_schema = next(iter(system_module.SCHEMAS.values()))
        system_name = first_schema.system
    
    if not hasattr(system_module, 'SEED_ENTRIES'):
        print(f"  No seed data defined for {system_name}")
        return
    
    created_count = 0
    skipped_count = 0
    core_compendiums = {}
    
    for entry_data in system_module.SEED_ENTRIES:
        # TODO: Remove this after all seed data is updated to use SeedEntry objects
        # Support both legacy dict and new SeedEntry object
        if isinstance(entry_data, dict):
            guid = entry_data['guid']
            name = entry_data['name']
            entry_type = entry_data.get('entry_type', 'rule')
            data = entry_data['data']
            parent_guid = entry_data.get('parent_guid')
            source = entry_data.get('source')
            # Extract system directly since legacy dicts might be dnd50-specific
            entry_system = entry_data.get('system')
        else:
            # New SeedEntry object
            guid = entry_data.guid
            name = entry_data.name
            entry_type = entry_data.entry_type
            data = entry_data.data
            parent_guid = entry_data.parent_guid
            source = entry_data.source
            entry_system = entry_data.system
        
        # Check if exists
        result = await session.execute(
            select(CompendiumEntry).where(CompendiumEntry.guid == guid)
        )
        if result.scalar_one_or_none():
            skipped_count += 1
            continue  # Already exists, skip
        
        # Determine strict system match
        final_system = entry_system or system_name
        
        if final_system not in core_compendiums:
            core_compendiums[final_system] = await ensure_core_compendium(session, final_system)
        
        # Create entry
        entry = CompendiumEntry(
            guid=guid,
            system=final_system,
            entry_type=entry_type,
            name=name,
            data=data,
            parent_guid=parent_guid,
            homebrew=False,
            source=source,
            compendium_guid=core_compendiums[final_system],
        )
        session.add(entry)
        created_count += 1
    
    if created_count > 0:
        await session.commit()
        print(f"  ✓ Created {created_count} entries for {system_name}")
    
    if skipped_count > 0:
        print(f"  ⊘ Skipped {skipped_count} existing entries for {system_name}")


async def main():
    """Seed all systems"""
    print("=" * 60)
    print("Seeding foundational compendium data...")
    print("=" * 60)
    
    # Discover all system modules
    print("\nDiscovering system modules...")
    system_modules = discover_system_modules()
    print(f"Found {len(system_modules)} system module(s)\n")
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Seed systems first
        await seed_systems(session, system_modules)
        
        # Then seed each system's compendium entries
        for system_module in system_modules:
            await seed_system(session, system_module)
    
    await engine.dispose()
    print("=" * 60)
    print("Seed data complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
