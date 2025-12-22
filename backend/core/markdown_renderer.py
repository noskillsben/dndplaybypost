"""
Markdown renderer for compendium entries.

Generates rulebook-style markdown documentation from hierarchical compendium entries.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.compendium import CompendiumEntry


async def render_entry(
    db: AsyncSession,
    guid: str,
    depth: int = 0,
    include_categories: Optional[List[str]] = None
) -> str:
    """
    Render a single entry as markdown with proper heading level.
    
    Args:
        db: Database session
        guid: Entry GUID to render
        depth: Current depth in hierarchy (0 = top level)
        include_categories: Optional list of entry categories to include (e.g., ["container", "definition"])
    
    Returns:
        Markdown string for this entry
    """
    result = await db.execute(select(CompendiumEntry).where(CompendiumEntry.guid == guid))
    entry = result.scalar_one_or_none()
    if not entry:
        return ""
    
    # Filter by category if specified
    entry_category = entry.data.get("entry_category", "item")
    if include_categories and entry_category not in include_categories:
        return ""
    
    # Determine heading level (# for depth 0, ## for depth 1, etc.)
    # Cap at 6 levels (markdown max)
    heading_level = min(depth + 1, 6)
    heading = "#" * heading_level
    
    # Build markdown output
    lines = []
    lines.append(f"{heading} {entry.name}")
    lines.append("")
    
    # Add metadata
    if entry.source and entry.source != "Unknown":
        lines.append(f"*Source: {entry.source}*")
        lines.append("")
    
    # Add description if it exists in data
    description = entry.data.get("description", "")
    if description:
        lines.append(description)
        lines.append("")
    
    # Add other relevant fields from data
    for key, value in entry.data.items():
        if key in ["name", "description", "entry_category", "parent_guid"]:
            continue  # Skip already rendered fields
        
        # Format field name nicely
        field_name = key.replace("_", " ").title()
        
        # Handle different value types
        if isinstance(value, str) and value.startswith("d&d"):
            # This is likely a compendium link - format as reference
            lines.append(f"**{field_name}:** *{value}*")
        elif value is not None and value != "":
            lines.append(f"**{field_name}:** {value}")
    
    lines.append("")
    return "\n".join(lines)


async def render_tree(
    db: AsyncSession,
    guid: str,
    max_depth: Optional[int] = None,
    current_depth: int = 0,
    include_categories: Optional[List[str]] = None
) -> str:
    """
    Recursively render an entry and its entire subtree as markdown.
    
    Args:
        db: Database session
        guid: Root entry GUID to start rendering from
        max_depth: Maximum depth to render (None = unlimited)
        current_depth: Current depth in recursion
        include_categories: Optional list of entry categories to include
    
    Returns:
        Markdown string for entire tree
    """
    # Render current entry
    entry_md = await render_entry(db, guid, current_depth, include_categories)
    if not entry_md:
        return ""
    
    lines = [entry_md]
    
    # Recursively render children if not at max depth
    if max_depth is None or current_depth < max_depth:
        children_result = await db.execute(
            select(CompendiumEntry)
            .where(CompendiumEntry.parent_guid == guid)
            .order_by(CompendiumEntry.name)
        )
        children = children_result.scalars().all()
        
        for child in children:
            child_md = await render_tree(
                db, child.guid, max_depth, current_depth + 1, include_categories
            )
            if child_md:
                lines.append(child_md)
    
    return "\n".join(lines)


async def render_rulebook(
    db: AsyncSession,
    system: str,
    entry_type: Optional[str] = None,
    include_categories: Optional[List[str]] = None
) -> str:
    """
    Render all top-level entries for a system as a complete rulebook.
    
    Args:
        db: Database session
        system: System identifier (e.g., "d&d5.0")
        entry_type: Optional filter by entry type
        include_categories: Optional list of entry categories to include
    
    Returns:
        Complete markdown rulebook
    """
    # Build query for top-level entries (no parent)
    stmt = select(CompendiumEntry).where(
        CompendiumEntry.system == system,
        CompendiumEntry.parent_guid.is_(None)
    ).order_by(CompendiumEntry.name)
    
    if entry_type:
        stmt = stmt.where(CompendiumEntry.entry_type == entry_type)
    
    result = await db.execute(stmt)
    top_level_entries = result.scalars().all()
    
    # Render title
    lines = [f"# {system.upper()} Compendium", ""]
    
    # Render each top-level entry and its tree
    for entry in top_level_entries:
        tree_md = await render_tree(db, entry.guid, include_categories=include_categories)
        if tree_md:
            lines.append(tree_md)
            lines.append("---")  # Horizontal rule between top-level sections
            lines.append("")
    
    return "\n".join(lines)
