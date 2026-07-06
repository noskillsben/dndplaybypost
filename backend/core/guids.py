"""GUID service for compendium entries.

GUID convention: {system}-{entry_type}-{slug}[-{suffix}][-{n}]

Responsibilities:
- slugify: turn arbitrary names into url/guid-safe slugs
- build_guid / generate_unique_guid: construct guids with collision handling
- rename_entry: rename = new guid + redirect record so old links keep working
- resolve_guid: follow redirect records (flattened chains) to the live guid
"""

import re
import unicodedata
from typing import Optional

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.compendium import CompendiumEntry, GuidRedirect


def slugify(name: str) -> str:
    """Lowercase, ascii-fold, and hyphenate a name for use in a GUID."""
    value = unicodedata.normalize("NFKD", name)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "entry"


def build_guid(system: str, entry_type: str, name: str, suffix: Optional[str] = None) -> str:
    guid = f"{system}-{entry_type}-{slugify(name)}"
    if suffix:
        guid = f"{guid}-{slugify(suffix)}"
    return guid


async def guid_in_use(db: AsyncSession, guid: str, exclude: Optional[str] = None) -> bool:
    """A guid is taken if a live entry or a redirect record already uses it."""
    if guid == exclude:
        return False
    entry = await db.execute(
        select(CompendiumEntry.guid).where(CompendiumEntry.guid == guid)
    )
    if entry.scalar_one_or_none():
        return True
    redirect = await db.execute(
        select(GuidRedirect.old_guid).where(GuidRedirect.old_guid == guid)
    )
    return redirect.scalar_one_or_none() is not None


async def generate_unique_guid(
    db: AsyncSession,
    system: str,
    entry_type: str,
    name: str,
    suffix: Optional[str] = None,
    exclude: Optional[str] = None,
) -> str:
    """Build a guid and append -2, -3, ... until it doesn't collide."""
    base = build_guid(system, entry_type, name, suffix)
    guid = base
    counter = 2
    while await guid_in_use(db, guid, exclude=exclude):
        guid = f"{base}-{counter}"
        counter += 1
    return guid


async def resolve_guid(db: AsyncSession, guid: str) -> str:
    """Follow a redirect record if one exists; chains are flattened on rename."""
    result = await db.execute(
        select(GuidRedirect.new_guid).where(GuidRedirect.old_guid == guid)
    )
    target = result.scalar_one_or_none()
    return target if target else guid


async def rename_entry(
    db: AsyncSession,
    entry: CompendiumEntry,
    new_name: str,
    suffix: Optional[str] = None,
) -> CompendiumEntry:
    """Rename an entry: new guid derived from the new name, redirect from the old.

    Children are re-parented to the new guid and any redirects pointing at the
    old guid are re-targeted so chains stay one hop long. Caller commits.
    """
    old_guid = entry.guid
    new_guid = await generate_unique_guid(
        db, entry.system, entry.entry_type, new_name, suffix, exclude=old_guid
    )

    if new_guid == old_guid:
        entry.name = new_name
        return entry

    # Insert the renamed copy first so FK-holding rows can be repointed.
    await db.execute(
        insert(CompendiumEntry.__table__).values(
            guid=new_guid,
            system=entry.system,
            entry_type=entry.entry_type,
            name=new_name,
            data=entry.data,
            parent_guid=entry.parent_guid,
            homebrew=entry.homebrew,
            source=entry.source,
            compendium_guid=entry.compendium_guid,
            created_at=entry.created_at,
        )
    )
    await db.execute(
        update(CompendiumEntry.__table__)
        .where(CompendiumEntry.parent_guid == old_guid)
        .values(parent_guid=new_guid)
    )
    await db.execute(
        delete(CompendiumEntry.__table__).where(CompendiumEntry.guid == old_guid)
    )

    # Flatten existing chains, then record the new redirect.
    await db.execute(
        update(GuidRedirect.__table__)
        .where(GuidRedirect.new_guid == old_guid)
        .values(new_guid=new_guid)
    )
    db.add(GuidRedirect(old_guid=old_guid, new_guid=new_guid))

    result = await db.execute(
        select(CompendiumEntry).where(CompendiumEntry.guid == new_guid)
    )
    return result.scalar_one()
