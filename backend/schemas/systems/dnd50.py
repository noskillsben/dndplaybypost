from core.schema_builder import ObjectRegistration
from core import field_types as ft

# Damage Type Schema
damage_type = ObjectRegistration(system="d&d5.0")
damage_type.add_field("name", ft.short_text(50), base_field=True, required=True)
damage_type.add_field("description", ft.long_text(), base_field=True)

# Item Schema
item = ObjectRegistration(system="d&d5.0")
item.add_field("name", ft.short_text(100), base_field=True, required=True)
item.add_field("description", ft.long_text(), base_field=True)
item.add_field("weight", ft.integer(min_val=0), base_field=True)
item.add_field("damage_dice", ft.short_text(20), placeholder="1d8")
item.add_field("damage_type", ft.compendium_link(
    query="d&d5.0-basic-damage-type-*",
    label="Damage Type"
))

# Spell Schema
spell = ObjectRegistration(system="d&d5.0")
spell.add_field("name", ft.short_text(100), base_field=True, required=True)
spell.add_field("description", ft.long_text(), base_field=True)
spell.add_field("level", ft.integer(min_val=0, max_val=9), required=True)
spell.add_field("school", ft.short_text(20), placeholder="Evocation")
spell.add_field("casting_time", ft.short_text(50), placeholder="1 action")
spell.add_field("range", ft.short_text(50))
spell.add_field("components", ft.short_text(50), placeholder="V, S, M")
spell.add_field("duration", ft.short_text(50))
spell.add_field("concentration", ft.short_text(5), placeholder="Yes/No") # Should use Boolean later but short_text is fine for now

# Class Schema
character_class = ObjectRegistration(system="d&d5.0")
character_class.add_field("name", ft.short_text(50), base_field=True, required=True)
character_class.add_field("description", ft.long_text(), base_field=True)
character_class.add_field("hit_die", ft.short_text(5), placeholder="d8")
character_class.add_field("primary_ability", ft.short_text(50), placeholder="Strength/Dexterity")

SCHEMAS = {
    "damage-type": damage_type,
    "item": item,
    "spell": spell,
    "class": character_class
}
