# Dungeons & Dragons 5e (2014) setup file.
# This file is used to define the systems, schemas and adds empty data for the system.
# Json import/export system will be added to import rules, modules, and adventures using the data layed out in this file.

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
rule = ObjectRegistration(system="d&d5.0", entry_type="rule")
rule.add_field("name", ft.short_text(100), base_field=True, required=True)
rule.add_markdown_field("description", max_len=10000, required=False)
rule.add_parent_field()
rule.add_category_field()

# Item Schema - updated to use new field types and demonstrate hierarchy
item = ObjectRegistration(system="d&d5.0", entry_type="item")
item.add_field("name", ft.short_text(100), base_field=True, required=True)
item.add_markdown_field("description", required=False)
item.add_field("weight", ft.integer(min_val=0), base_field=True)
item.add_field("damage_dice", ft.short_text(20), placeholder="1d8")
item.add_field("damage_type", ft.compendium_link(
    query="type:damage-type",
    label="Damage Type"
))
# Link to weapon category (e.g., "Simple Melee Weapon")
item.add_field("item_category", ft.compendium_link(
    query="d&d5.0-rule-*",
    label="Item Category"
))
# Link to mastery type if applicable
item.add_field("mastery_type", ft.compendium_link(
    query="d&d5.0-rule-*",
    label="Mastery Type"
))

# Spell Schema
spell = ObjectRegistration(system="d&d5.0", entry_type="spell")
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
character_class = ObjectRegistration(system="d&d5.0", entry_type="class")
character_class.add_field("name", ft.short_text(50), base_field=True, required=True)
character_class.add_markdown_field("description", required=False)
character_class.add_field("hit_die", ft.short_text(5), placeholder="d8")
character_class.add_field("primary_ability", ft.short_text(50), placeholder="Strength/Dexterity")

# Foundational lookup types (D-01) - things other templates reference by
# "type:<entry_type>" link queries (spells -> damage types, monsters ->
# conditions/sizes/creature types, skills -> abilities, ...)

ability = ObjectRegistration(system="d&d5.0", entry_type="ability")
ability.add_field("name", ft.short_text(50), base_field=True, required=True)
ability.add_field("abbreviation", ft.short_text(3), required=True)
ability.add_markdown_field("description", max_len=2000, required=False)

skill = ObjectRegistration(system="d&d5.0", entry_type="skill")
skill.add_field("name", ft.short_text(50), base_field=True, required=True)
skill.add_field("ability", ft.compendium_link(query="type:ability", label="Ability"), required=True)
skill.add_markdown_field("description", max_len=2000, required=False)

damage_type = ObjectRegistration(system="d&d5.0", entry_type="damage-type")
damage_type.add_field("name", ft.short_text(50), base_field=True, required=True)
damage_type.add_markdown_field("description", max_len=2000, required=False)

condition = ObjectRegistration(system="d&d5.0", entry_type="condition")
condition.add_field("name", ft.short_text(50), base_field=True, required=True)
condition.add_markdown_field("description", max_len=5000, required=False)

language = ObjectRegistration(system="d&d5.0", entry_type="language")
language.add_field("name", ft.short_text(50), base_field=True, required=True)
language.add_field("category", ft.select(["standard", "exotic"], label="Category"), required=True)
language.add_field("script", ft.short_text(50))
language.add_field("typical_speakers", ft.short_text(100))

creature_type = ObjectRegistration(system="d&d5.0", entry_type="creature-type")
creature_type.add_field("name", ft.short_text(50), base_field=True, required=True)
creature_type.add_markdown_field("description", max_len=2000, required=False)

size = ObjectRegistration(system="d&d5.0", entry_type="size")
size.add_field("name", ft.short_text(50), base_field=True, required=True)
size.add_field("space", ft.short_text(50), placeholder="5 by 5 ft.")
size.add_markdown_field("description", max_len=2000, required=False)

currency = ObjectRegistration(system="d&d5.0", entry_type="currency")
currency.add_field("name", ft.short_text(50), base_field=True, required=True)
currency.add_field("abbreviation", ft.short_text(5), required=True)
currency.add_field("value_in_gp", ft.decimal(min_val=0), required=True)

# Seed data - foundational entries created on startup using Pythonic API
# ---------------------------------------------------------------------

# 1. Beyond 1rst level 
# Note: Source is applied to all of these for brevity, could be per-item
srd_source = {"name": "SRD", "link": "https://media.wizards.com/2016/downloads/DND/SRD-OGL_V5.1.pdf", "page": 1 }

beyond_1rst_level = rule(
    guid="beyond-1rst-level",
    name="Beyond 1rst Level",
    description="### Beyond 1rst Level ###\n\nAs your character goes on adventures and overcomes challenges, he or she gains experience,  represented by experience points. A character who  reaches a specified experience point total advances  in capability. This advancement is called gaining a  level. When your character gains a level, his or her class  often grants additional features, as detailed in the  class description. Some of these features allow you  to increase your ability scores, either increasing two  scores by 1 each or increasing one score by 2. You  can’t increase an ability score above 20. In addition,  every character’s proficiency bonus increases at  certain levels. Each time you gain a level, you gain 1 additional  Hit Die. Roll that Hit Die, add your Constitution  modifier to the roll, and add the total to your hit  point maximum. Alternatively, you can use the fixed  value shown in your class entry, which is the average  result of the die roll (rounded up). When your Constitution modifier increases by 1,  your hit point maximum increases by 1 for each level  you have attained. For example, if your 7th-­‐‑level  fighter has a Constitution score of 17, when he  reaches 8th level, he increases his Constitution score  from 17 to 18, thus increasing his Constitution  modifier from +3 to +4. His hit point maximum then  increases by 8. The Character Advancement table summarizes the  XP you need to advance in levels from level 1  through level 20, and the proficiency bonus for a  character of that level. Consult the information in  your character’s class description to see what other  improvements you gain at each level.",
    entry_category="container",
    source={**srd_source, "page": 56}
)






damage_types = rule(
    guid="damage-types",
    name="Damage Types",
    description="# Damage Types\n\nThe various types of damage that can be dealt in D&D 5e.",
    entry_category="container",
    source=srd_source
)

slashing = rule(
    guid="slashing",
    name="Slashing",
    parent_guid=damage_types.guid,
    description="Slashing damage is dealt by swords, axes, and claws.",
    entry_category="definition",
    source=srd_source
)

bludgeoning = rule(
    guid="bludgeoning",
    name="Bludgeoning",
    parent_guid=damage_types.guid,
    description="Bludgeoning damage is dealt by blunt force from hammers, clubs, and falling.",
    entry_category="definition",
    source=srd_source
)

piercing = rule(
    guid="piercing",
    name="Piercing",
    parent_guid=damage_types.guid,
    description="Piercing damage is dealt by arrows, spears, and fangs.",
    entry_category="definition",
    source=srd_source
)

# 2. Equipment Hierarchy
equipment = rule(
    guid="equipment",
    name="Equipment",
    description="# Equipment\n\nAdventurers rely on various types of equipment to survive and thrive.",
    entry_category="container",
    source=srd_source
)

weapons = rule(
    guid="weapons",
    name="Weapons",
    parent_guid=equipment.guid,
    description="## Weapons\n\nWeapons are categorized by their complexity and fighting style.",
    entry_category="container",
    source=srd_source
)

weapon_masteries = rule(
    guid="weapon-masteries",
    name="Weapon Masteries",
    parent_guid=weapons.guid,
    description="### Weapon Masteries\n\nWeapon proficiency categories.",
    entry_category="container",
    source=srd_source
)

simple_melee = rule(
    guid="simple-melee-weapon",
    name="Simple Melee Weapon",
    parent_guid=weapon_masteries.guid,
    description="Simple melee weapons require minimal training and include clubs, daggers, and quarterstaffs.",
    entry_category="definition",
    source=srd_source
)

simple_ranged = rule(
    guid="simple-ranged-weapon",
    name="Simple Ranged Weapon",
    parent_guid=weapon_masteries.guid,
    description="Simple ranged weapons include light crossbows and shortbows.",
    entry_category="definition",
    source=srd_source
)

martial_melee = rule(
    guid="martial-melee-weapon",
    name="Martial Melee Weapon",
    parent_guid=weapon_masteries.guid,
    description="Martial melee weapons require specialized training and include longswords, greatswords, and glaives.",
    entry_category="definition",
    source=srd_source
)

martial_ranged = rule(
    guid="martial-ranged-weapon",
    name="Martial Ranged Weapon",
    parent_guid=weapon_masteries.guid,
    description="Martial ranged weapons include longbows and heavy crossbows.",
    entry_category="definition",
    source=srd_source
)

# 3. Foundational lookups (D-01)

_ABILITIES = [
    ("strength", "Strength", "STR", "Measures physical power."),
    ("dexterity", "Dexterity", "DEX", "Measures agility, reflexes, and balance."),
    ("constitution", "Constitution", "CON", "Measures endurance and vital force."),
    ("intelligence", "Intelligence", "INT", "Measures reasoning and memory."),
    ("wisdom", "Wisdom", "WIS", "Measures perception and insight."),
    ("charisma", "Charisma", "CHA", "Measures force of personality."),
]
ability_entries = [
    ability(guid=g, name=n, abbreviation=a, description=d, source=srd_source)
    for g, n, a, d in _ABILITIES
]

_SKILLS = [
    ("athletics", "Athletics", "strength"),
    ("acrobatics", "Acrobatics", "dexterity"),
    ("sleight-of-hand", "Sleight of Hand", "dexterity"),
    ("stealth", "Stealth", "dexterity"),
    ("arcana", "Arcana", "intelligence"),
    ("history", "History", "intelligence"),
    ("investigation", "Investigation", "intelligence"),
    ("nature", "Nature", "intelligence"),
    ("religion", "Religion", "intelligence"),
    ("animal-handling", "Animal Handling", "wisdom"),
    ("insight", "Insight", "wisdom"),
    ("medicine", "Medicine", "wisdom"),
    ("perception", "Perception", "wisdom"),
    ("survival", "Survival", "wisdom"),
    ("deception", "Deception", "charisma"),
    ("intimidation", "Intimidation", "charisma"),
    ("performance", "Performance", "charisma"),
    ("persuasion", "Persuasion", "charisma"),
]
skill_entries = [
    skill(guid=g, name=n, ability=f"d&d5.0-ability-{a}", source=srd_source)
    for g, n, a in _SKILLS
]

_DAMAGE_TYPES = [
    ("acid", "Acid", "Corrosive damage, like a black dragon's breath."),
    ("bludgeoning", "Bludgeoning", "Blunt force from hammers, clubs, and falling."),
    ("cold", "Cold", "The chill of an ice storm or a white dragon's breath."),
    ("fire", "Fire", "Flames from dragons and spells like fireball."),
    ("force", "Force", "Pure magical energy, like magic missile."),
    ("lightning", "Lightning", "Electrical damage from lightning bolt and blue dragons."),
    ("necrotic", "Necrotic", "Withering energy dealt by undead and dark magic."),
    ("piercing", "Piercing", "Puncturing damage from arrows, spears, and fangs."),
    ("poison", "Poison", "Venomous stings and toxic gas."),
    ("psychic", "Psychic", "Mental damage from psionic abilities."),
    ("radiant", "Radiant", "Searing divine energy."),
    ("slashing", "Slashing", "Cutting damage from swords, axes, and claws."),
    ("thunder", "Thunder", "A concussive burst of sound."),
]
damage_type_entries = [
    damage_type(guid=g, name=n, description=d, source=srd_source)
    for g, n, d in _DAMAGE_TYPES
]

_CONDITIONS = [
    ("blinded", "Blinded", "Can't see; automatically fails sight checks; attack rolls against have advantage, its attacks have disadvantage."),
    ("charmed", "Charmed", "Can't attack the charmer; charmer has advantage on social checks."),
    ("deafened", "Deafened", "Can't hear; automatically fails hearing checks."),
    ("exhaustion", "Exhaustion", "Measured in six cumulative levels, from disadvantage on ability checks to death."),
    ("frightened", "Frightened", "Disadvantage on checks and attacks while the source of fear is visible; can't willingly approach it."),
    ("grappled", "Grappled", "Speed becomes 0; ends if the grappler is incapacitated."),
    ("incapacitated", "Incapacitated", "Can't take actions or reactions."),
    ("invisible", "Invisible", "Impossible to see without magic; attacks against have disadvantage, its attacks have advantage."),
    ("paralyzed", "Paralyzed", "Incapacitated, can't move or speak; fails STR and DEX saves; melee hits are crits."),
    ("petrified", "Petrified", "Transformed to stone; incapacitated; resistance to all damage."),
    ("poisoned", "Poisoned", "Disadvantage on attack rolls and ability checks."),
    ("prone", "Prone", "Can only crawl; disadvantage on attacks; melee attacks against have advantage."),
    ("restrained", "Restrained", "Speed 0; attacks against have advantage, its attacks and DEX saves have disadvantage."),
    ("stunned", "Stunned", "Incapacitated, can't move; fails STR and DEX saves; attacks against have advantage."),
    ("unconscious", "Unconscious", "Incapacitated, prone, unaware; fails STR and DEX saves; melee hits are crits."),
]
condition_entries = [
    condition(guid=g, name=n, description=d, source=srd_source)
    for g, n, d in _CONDITIONS
]

_LANGUAGES = [
    ("common", "Common", "standard", "Common", "Humans"),
    ("dwarvish", "Dwarvish", "standard", "Dwarvish", "Dwarves"),
    ("elvish", "Elvish", "standard", "Elvish", "Elves"),
    ("giant", "Giant", "standard", "Dwarvish", "Ogres, giants"),
    ("gnomish", "Gnomish", "standard", "Dwarvish", "Gnomes"),
    ("goblin", "Goblin", "standard", "Dwarvish", "Goblinoids"),
    ("halfling", "Halfling", "standard", "Common", "Halflings"),
    ("orc", "Orc", "standard", "Dwarvish", "Orcs"),
    ("abyssal", "Abyssal", "exotic", "Infernal", "Demons"),
    ("celestial", "Celestial", "exotic", "Celestial", "Celestials"),
    ("draconic", "Draconic", "exotic", "Draconic", "Dragons, dragonborn"),
    ("deep-speech", "Deep Speech", "exotic", "", "Aboleths, cloakers"),
    ("infernal", "Infernal", "exotic", "Infernal", "Devils"),
    ("primordial", "Primordial", "exotic", "Dwarvish", "Elementals"),
    ("sylvan", "Sylvan", "exotic", "Elvish", "Fey creatures"),
    ("undercommon", "Undercommon", "exotic", "Elvish", "Underworld traders"),
]
language_entries = [
    language(guid=g, name=n, category=c, script=s, typical_speakers=t,
             source=srd_source)
    for g, n, c, s, t in _LANGUAGES
]

_CREATURE_TYPES = [
    ("aberration", "Aberration", "Utterly alien beings, such as aboleths and mind flayers."),
    ("beast", "Beast", "Nonhumanoid creatures of the natural world."),
    ("celestial", "Celestial", "Creatures native to the Upper Planes, such as angels."),
    ("construct", "Construct", "Made, not born, such as golems."),
    ("dragon", "Dragon", "Large reptilian creatures of ancient origin."),
    ("elemental", "Elemental", "Creatures native to the elemental planes."),
    ("fey", "Fey", "Creatures of magic tied to the forces of nature."),
    ("fiend", "Fiend", "Creatures of wickedness native to the Lower Planes."),
    ("giant", "Giant", "Towering humanlike creatures, such as ogres and trolls."),
    ("humanoid", "Humanoid", "The main peoples of the D&D world."),
    ("monstrosity", "Monstrosity", "Frightening creatures of unnatural origin."),
    ("ooze", "Ooze", "Gelatinous creatures like the gelatinous cube."),
    ("plant", "Plant", "Vegetable creatures, such as shambling mounds."),
    ("undead", "Undead", "Once-living creatures brought to unlife."),
]
creature_type_entries = [
    creature_type(guid=g, name=n, description=d, source=srd_source)
    for g, n, d in _CREATURE_TYPES
]

_SIZES = [
    ("tiny", "Tiny", "2 1/2 by 2 1/2 ft."),
    ("small", "Small", "5 by 5 ft."),
    ("medium", "Medium", "5 by 5 ft."),
    ("large", "Large", "10 by 10 ft."),
    ("huge", "Huge", "15 by 15 ft."),
    ("gargantuan", "Gargantuan", "20 by 20 ft. or larger"),
]
size_entries = [
    size(guid=g, name=n, space=s, source=srd_source)
    for g, n, s in _SIZES
]

_CURRENCIES = [
    ("copper", "Copper piece", "cp", 0.01),
    ("silver", "Silver piece", "sp", 0.1),
    ("electrum", "Electrum piece", "ep", 0.5),
    ("gold", "Gold piece", "gp", 1.0),
    ("platinum", "Platinum piece", "pp", 10.0),
]
currency_entries = [
    currency(guid=g, name=n, abbreviation=a, value_in_gp=v, source=srd_source)
    for g, n, a, v in _CURRENCIES
]

# Collect all seed entries
SEED_ENTRIES = [
    # Damage Types (legacy rules-hierarchy demo entries)
    damage_types,
    slashing,
    bludgeoning,
    piercing,
    # Equipment
    equipment,
    weapons,
    weapon_masteries,
    simple_melee,
    simple_ranged,
    martial_melee,
    martial_ranged,
    # Foundational lookups (D-01)
    *ability_entries,
    *skill_entries,
    *damage_type_entries,
    *condition_entries,
    *language_entries,
    *creature_type_entries,
    *size_entries,
    *currency_entries,
]

SCHEMAS = {
    "rule": rule,
    "item": item,
    "spell": spell,
    "class": character_class,
    "ability": ability,
    "skill": skill,
    "damage-type": damage_type,
    "condition": condition,
    "language": language,
    "creature-type": creature_type,
    "size": size,
    "currency": currency,
}

# Logic Definitions for Baking Engine
LOGIC_DEFINITIONS = {
    # Base Stats (usually present in raw_data, but defined here for baked access)
    "stats.strength.total": "stats.strength.base",
    "stats.dexterity.total": "stats.dexterity.base",
    
    # Derived Modifiers
    "stats.strength.mod": "(stats.strength.total - 10) // 2",
    "stats.dexterity.mod": "(stats.dexterity.total - 10) // 2",
    
    # Skills
    "skills.athletics.total": "stats.strength.mod + (proficiency_bonus if skills.athletics.prof else 0)",
    "skills.acrobatics.total": "stats.dexterity.mod + (proficiency_bonus if skills.acrobatics.prof else 0)",
    
    # Combat
    "combat.ac.total": "10 + stats.dexterity.mod", # Basic calculation, armor modifiers will override/add
}

# Layout Tree for Character Sheet UI
LAYOUT_TREE = {
    "type": "tabs",
    "children": [
        {
            "label": "Main",
            "type": "grid",
            "columns": 3,
            "children": [
                {
                    "type": "column",
                    "label": "Attributes",
                    "children": [
                        {"type": "number", "label": "Strength", "bind": "stats.strength.total", "sublabel": "stats.strength.mod"},
                        {"type": "number", "label": "Dexterity", "bind": "stats.dexterity.total", "sublabel": "stats.dexterity.mod"},
                    ]
                },
                {
                    "type": "column",
                    "label": "Vitals",
                    "children": [
                        {"type": "number", "label": "Armor Class", "bind": "combat.ac.total"},
                    ]
                }
            ]
        },
        {
            "label": "Inventory",
            "type": "list",
            "bind": "inventory"
        }
    ]
}
