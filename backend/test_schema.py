from core.schema_builder import ObjectRegistration
from core import field_types as ft
import json

# Define a simple item schema for D&D 5.0
item = ObjectRegistration(system="d&d5.0")
item.add_field("name", ft.short_text(max_len=50), base_field=True, required=True)
item.add_field("description", ft.long_text(), base_field=True, required=False)
item.add_field("weight", ft.integer(min_val=0), base_field=True, required=False)
item.add_field("damage_dice", ft.short_text(max_len=20, placeholder="1d8"))
item.add_field("damage_type", ft.compendium_link(
    query="d&d5.0-basic-damage-type-*",
    label="Damage Type"
))

# Test model generation
ItemModel = item.model()
print("Generated Pydantic Model JSON Schema:")
print(json.dumps(ItemModel.model_json_schema(), indent=2))

# Test form generation
form_schema = item.form()
print("\nGenerated Form Schema:")
print(json.dumps(form_schema, indent=2))

# Test validation
valid_data = {
    "name": "Longsword",
    "description": "A versatile sword",
    "weight": 3,
    "damage_dice": "1d8",
    "damage_type": "d&d5.0-basic-damage-type-slashing"
}

print("\nValidating data...")
try:
    validated = ItemModel(**valid_data)
    print("Validation passed!")
    print(validated.model_dump_json(indent=2))
except Exception as e:
    print(f"Validation failed: {e}")

# Test invalid data
invalid_data = {
    "name": "A" * 100,  # Too long
    "weight": -1       # Too small
}

print("\nValidating invalid data (should fail)...")
try:
    ItemModel(**invalid_data)
    print("Error: Validation passed for invalid data!")
except Exception as e:
    print(f"Validation failed as expected: {len(e.errors())} errors found.")
    for err in e.errors():
        print(f"  - {err['loc'][0]}: {err['msg']}")
