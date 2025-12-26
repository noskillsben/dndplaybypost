from core.schema_builder import ObjectRegistration
from core import field_types as ft

# System metadata
SYSTEM_INFO = {
    "guid": "d&d5.2",
    "name": "Dungeons & Dragons 5e (2024)",
    "description": "The 2024 revised edition of D&D 5e with updated rules and weapon masteries.",
    "link": "https://www.dndbeyond.com/"
}

# In 5.2 (2024), we have Weapon Masteries.
# Let's show how the schema can differ.

# Item Schema (5.2)
item = ObjectRegistration(system="d&d5.2")
item.add_field("name", ft.short_text(100), base_field=True, required=True)
item.add_field("description", ft.long_text(), base_field=True)
item.add_field("weight", ft.integer(min_val=0), base_field=True)
item.add_field("damage_dice", ft.short_text(20), placeholder="1d8")

# Difference: Added Weapon Mastery field
item.add_field("mastery", ft.short_text(50), placeholder="Grazing, Topple, etc.")

SCHEMAS = {
    "item": item
}
