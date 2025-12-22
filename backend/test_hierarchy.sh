#!/bin/bash
# Test script for hierarchical compendium system using the API

API_BASE="http://localhost:8000/api/compendium"

echo "=== Creating Hierarchical Rule Structure ==="
echo

# 1. Create Equipment (top-level container)
echo "Creating Equipment (container)..."
curl -s -X POST "$API_BASE/" \
  -H "Content-Type: application/json" \
  -d '{
    "system": "d&d5.0",
    "entry_type": "basic-rule",
    "name": "Equipment",
    "data": {
      "name": "Equipment",
      "description": "# Equipment\n\nAdventurers rely on various types of equipment to survive and thrive in their quests.",
      "entry_category": "container"
    },
    "source": "PHB"
  }' | jq -r '.guid'

# 2. Create Weapons (child of Equipment)
echo "Creating Weapons (container, parent: Equipment)..."
curl -s -X POST "$API_BASE/" \
  -H "Content-Type: application/json" \
  -d '{
    "system": "d&d5.0",
    "entry_type": "basic-rule",
    "name": "Weapons",
    "parent_guid": "d&d5.0-basic-rule-equipment",
    "data": {
      "name": "Weapons",
      "description": "## Weapons\n\nWeapons are tools of combat, categorized by their complexity and fighting style.",
      "entry_category": "container",
      "parent_guid": "d&d5.0-basic-rule-equipment"
    },
    "source": "PHB"
  }' | jq -r '.guid'

# 3. Create Masteries (child of Weapons)
echo "Creating Weapon Masteries (container, parent: Weapons)..."
curl -s -X POST "$API_BASE/" \
  -H "Content-Type: application/json" \
  -d '{
    "system": "d&d5.0",
    "entry_type": "basic-rule",
    "name": "Weapon Masteries",
    "parent_guid": "d&d5.0-basic-rule-weapons",
    "data": {
      "name": "Weapon Masteries",
      "description": "### Weapon Masteries\n\nWeapon proficiency types determine how effectively a character can wield different weapons.",
      "entry_category": "container",
      "parent_guid": "d&d5.0-basic-rule-weapons"
    },
    "source": "PHB"
  }' | jq -r '.guid'

# 4. Create Simple Melee Weapon (definition)
echo "Creating Simple Melee Weapon (definition, parent: Weapon Masteries)..."
curl -s -X POST "$API_BASE/" \
  -H "Content-Type: application/json" \
  -d '{
    "system": "d&d5.0",
    "entry_type": "basic-rule",
    "name": "Simple Melee Weapon",
    "parent_guid": "d&d5.0-basic-rule-weapon-masteries",
    "data": {
      "name": "Simple Melee Weapon",
      "description": "#### Simple Melee Weapon\n\nSimple melee weapons are easy to use and require minimal training. They include clubs, daggers, and quarterstaffs.",
      "entry_category": "definition",
      "parent_guid": "d&d5.0-basic-rule-weapon-masteries"
    },
    "source": "PHB"
  }' | jq -r '.guid'

# 5. Create Bludgeoning damage type
echo "Creating Bludgeoning damage type..."
curl -s -X POST "$API_BASE/" \
  -H "Content-Type: application/json" \
  -d '{
    "system": "d&d5.0",
    "entry_type": "damage-type",
    "name": "Bludgeoning",
    "data": {
      "name": "Bludgeoning",
      "description": "Bludgeoning damage is dealt by clubs, hammers, and other blunt weapons."
    },
    "source": "PHB"
  }' | jq -r '.guid'

# 6. Create Club item that references the hierarchy
echo "Creating Club (item, links to hierarchy)..."
curl -s -X POST "$API_BASE/" \
  -H "Content-Type: application/json" \
  -d '{
    "system": "d&d5.0",
    "entry_type": "item",
    "name": "Club",
    "data": {
      "name": "Club",
      "description": "A simple wooden club, effective for bludgeoning foes.",
      "weight": 2,
      "damage_dice": "1d4",
      "damage_type": "d&d5.0-damage-type-bludgeoning",
      "item_category": "d&d5.0-basic-rule-weapons",
      "mastery_type": "d&d5.0-basic-rule-simple-melee-weapon"
    },
    "source": "PHB"
  }' | jq -r '.guid'

echo
echo "=== Testing Hierarchy Queries ==="
echo

# Test: Get children of Equipment
echo "Children of Equipment:"
curl -s "$API_BASE/d&d5.0-basic-rule-equipment/children" | jq -r '.children[] | .name'

echo
echo "Ancestors of Simple Melee Weapon:"
curl -s "$API_BASE/d&d5.0-basic-rule-simple-melee-weapon/ancestors" | jq -r '.ancestors[] | .name' | tr '\n' ' → '
echo

echo
echo "=== Testing Markdown Rendering ==="
echo

# Render the Equipment tree as markdown
echo "Rendered Equipment hierarchy:"
echo "-----------------------------------------------------------"
curl -s "$API_BASE/d&d5.0-basic-rule-equipment/render" | jq -r '.markdown'
echo "-----------------------------------------------------------"

echo
echo "✅ All tests completed!"
echo
echo "You can now:"
echo "  1. View the hierarchy in the browser at http://localhost:8000/docs"
echo "  2. Query children: GET /api/compendium/{guid}/children"
echo "  3. Get full tree: GET /api/compendium/{guid}/tree"
echo "  4. Render markdown: GET /api/compendium/{guid}/render"
