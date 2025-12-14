from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID


# ============================================================================
# Compendium Item Schemas
# ============================================================================

class CompendiumItemBase(BaseModel):
    """Base schema for compendium items"""
    type: str = Field(..., description="Type of compendium item (race, class, spell, item, feature, background, etc.)")
    name: str = Field(..., max_length=255, description="Name of the item")
    system: str = Field(default="D&D 5e", max_length=100, description="Game system (e.g., 'D&D 5e', 'D&D 5.2', 'Pathfinder 2e')")
    data: Dict[str, Any] = Field(..., description="Type-specific data structure")
    tags: List[str] = Field(default_factory=list, description="Tags for search and filtering")
    is_official: bool = Field(default=False, description="Whether this is official SRD content")


class CompendiumItemCreate(CompendiumItemBase):
    """Schema for creating a new compendium item"""
    pass


class CompendiumItemUpdate(BaseModel):
    """Schema for updating a compendium item"""
    name: Optional[str] = Field(None, max_length=255)
    data: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class CompendiumItemResponse(CompendiumItemBase):
    """Schema for compendium item responses"""
    id: UUID
    version: datetime
    created_at: datetime
    created_by: Optional[UUID] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class CompendiumItemList(BaseModel):
    """Schema for paginated compendium item lists"""
    items: List[CompendiumItemResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# Component Template Schemas
# ============================================================================

class ComponentTemplateBase(BaseModel):
    """Base schema for component templates"""
    component_type: str = Field(..., max_length=50, description="Type of component (resource, modifier, attack, etc.)")
    name: str = Field(..., max_length=255, description="Display name of the template")
    description: Optional[str] = Field(None, description="Description of what this component does")
    schema: Dict[str, Any] = Field(..., description="JSON Schema for validation")
    for_types: List[str] = Field(default_factory=list, description="Which compendium item types can use this template")


class ComponentTemplateCreate(ComponentTemplateBase):
    """Schema for creating a new component template"""
    pass


class ComponentTemplateUpdate(BaseModel):
    """Schema for updating a component template"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None
    for_types: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ComponentTemplateResponse(ComponentTemplateBase):
    """Schema for component template responses"""
    id: UUID
    version: datetime
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Type-Specific Schemas (for validation and documentation)
# ============================================================================

class AbilityScoreIncrease(BaseModel):
    """Schema for ability score increases"""
    applies_to: str = Field(..., description="Which ability score (or 'ability_choice')")
    choices: Optional[List[str]] = Field(None, description="Available choices if this is a choice")
    choose_count: Optional[int] = Field(None, description="How many to choose")
    value: int = Field(..., description="Bonus value")
    description: Optional[str] = None
    exclude_previous: Optional[bool] = Field(False, description="Must be different from previous choice")


class ResourceComponent(BaseModel):
    """Schema for resource components (uses, spell slots, etc.)"""
    name: str
    current: int = Field(..., ge=0)
    maximum: Union[int, str] = Field(..., description="Max uses or formula")
    recovery: str = Field(..., description="When resource refreshes (short_rest, long_rest, etc.)")
    partial_recovery: Optional[Dict[str, int]] = None


class ModifierComponent(BaseModel):
    """Schema for modifier components"""
    type: str = Field(..., description="Type of modifier (damage_bonus, advantage, etc.)")
    applies_to: Union[str, List[str]] = Field(..., description="What this modifies")
    value: Optional[Union[int, str]] = Field(None, description="Numeric bonus or formula")
    while_active: Optional[bool] = Field(False, description="Only applies when parent feature is active")
    conditional: Optional[str] = Field(None, description="Condition for when this applies")


class AttackComponent(BaseModel):
    """Schema for attack components"""
    name: str
    type: str = Field(..., description="Attack type (melee_weapon, ranged_weapon, etc.)")
    attack_bonus: Dict[str, int] = Field(..., description="Breakdown of attack bonus")
    damage: Dict[str, Any] = Field(..., description="Damage information")
    properties: List[str] = Field(default_factory=list)
    range: Optional[Dict[str, int]] = None


class FeatureData(BaseModel):
    """Schema for feature data"""
    name: str
    source_type: Optional[str] = Field(None, description="Source type (class, race, feat, etc.)")
    source_name: Optional[str] = Field(None, description="Source name")
    level_requirement: Optional[int] = Field(None, ge=1, le=20)
    description: str
    activation: Optional[Dict[str, Any]] = None
    duration: Optional[Dict[str, Any]] = None
    resource: Optional[ResourceComponent] = None
    effects: List[ModifierComponent] = Field(default_factory=list)


class SpellData(BaseModel):
    """Schema for spell data"""
    name: str
    level: int = Field(..., ge=0, le=9, description="Spell level (0 for cantrips)")
    school: str = Field(..., description="School of magic")
    casting_time: Dict[str, Any]
    range: Dict[str, Any]
    components: Dict[str, Any]
    duration: Dict[str, Any]
    description: str
    area_of_effect: Optional[Dict[str, Any]] = None
    saving_throw: Optional[Dict[str, Any]] = None
    damage: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)
    classes: List[str] = Field(default_factory=list)
    ritual: bool = False
    concentration: bool = False


class RaceData(BaseModel):
    """Schema for race/species data"""
    description: str
    size: str
    speed: int
    creature_type: Optional[str] = "Humanoid"
    age: Optional[Dict[str, int]] = None
    ability_score_increases: List[AbilityScoreIncrease] = Field(default_factory=list)
    traits: List[Dict[str, Any]] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    darkvision: Optional[int] = None


class ClassData(BaseModel):
    """Schema for class data"""
    description: str
    hit_die: str = Field(..., pattern=r"^d\d+$")
    primary_abilities: List[str]
    saving_throw_proficiencies: List[str]
    skill_proficiencies: Dict[str, Any]
    weapon_proficiencies: List[str] = Field(default_factory=list)
    armor_training: List[str] = Field(default_factory=list)
    starting_equipment: Dict[str, Any]
    features_by_level: Dict[str, List[Dict[str, Any]]]
    subclasses: Optional[Dict[str, Any]] = None
    spellcasting: Optional[Dict[str, Any]] = None


class ItemData(BaseModel):
    """Schema for item/equipment data"""
    name: str
    category: str = Field(..., description="Item category (weapon, armor, gear, etc.)")
    subcategory: Optional[str] = None
    rarity: Optional[str] = "common"
    requires_attunement: bool = False
    description: str
    cost: Optional[Dict[str, int]] = None
    weight_lbs: Optional[float] = None
    properties: List[str] = Field(default_factory=list)
    damage: Optional[Dict[str, Any]] = None
    magic_properties: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)


class BackgroundData(BaseModel):
    """Schema for background data"""
    description: str
    ability_score_increases: Optional[Dict[str, Any]] = None
    feat_guid: Optional[str] = None
    skill_proficiencies: List[str] = Field(default_factory=list)
    tool_proficiency: Optional[Dict[str, Any]] = None
    equipment_options: Optional[Dict[str, Any]] = None


# ============================================================================
# Search and Filter Schemas
# ============================================================================

class CompendiumSearchParams(BaseModel):
    """Schema for search parameters"""
    query: Optional[str] = Field(None, description="Search query")
    type: Optional[str] = Field(None, description="Filter by type")
    system: Optional[str] = Field(None, description="Filter by game system")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    is_official: Optional[bool] = Field(None, description="Filter by official/homebrew")
    is_active: Optional[bool] = Field(True, description="Filter by active status")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field("name", description="Sort field")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$")
