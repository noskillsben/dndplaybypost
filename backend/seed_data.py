"""
Seed foundational compendium data on startup.

This script runs after migrations and creates basic-rule entries
defined in system modules (e.g., dnd50.SEED_ENTRIES).

Uses "create or ignore" logic - safe to run multiple times.
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

# Add parent directory to path
sys.path.insert(0, '/app')

from database import DATABASE_URL
from models.compendium import CompendiumEntry
from schemas.systems import dnd50, dnd52


async def seed_system(session: AsyncSession, system_name: str, system_module):
    """Seed entries for a system if they don't exist"""
    if not hasattr(system_module, 'SEED_ENTRIES'):
        print(f"  No seed data defined for {system_name}")
        return
    
    created_count = 0
    skipped_count = 0
    
    for entry_data in system_module.SEED_ENTRIES:
        guid = entry_data['guid']
        
        # Check if exists
        result = await session.execute(
            select(CompendiumEntry).where(CompendiumEntry.guid == guid)
        )
        if result.scalar_one_or_none():
            skipped_count += 1
            continue  # Already exists, skip
        
        # Extract system from GUID or use first schema's system
        system = entry_data.get('system')
        if not system and hasattr(system_module, 'SCHEMAS'):
            # Get system from first schema
            first_schema = next(iter(system_module.SCHEMAS.values()))
            system = first_schema.system
        
        # Create entry
        entry = CompendiumEntry(
            guid=guid,
            system=system or system_name,
            entry_type=entry_data.get('entry_type', 'basic-rule'),
            name=entry_data['name'],
            data=entry_data['data'],
            parent_guid=entry_data.get('parent_guid'),
            homebrew=False,
            source=entry_data.get('source', 'Core Rules')
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
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Seed each system
        await seed_system(session, "d&d5.0", dnd50)
        await seed_system(session, "d&d5.2", dnd52)
    
    await engine.dispose()
    print("=" * 60)
    print("Seed data complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
