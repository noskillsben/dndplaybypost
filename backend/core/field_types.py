from typing import Any, Tuple, Optional
from pydantic import Field

class FieldType:
    """Base class for all field types"""
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        """Return (python_type, pydantic.Field) for model generation"""
        raise NotImplementedError
    
    def to_form_field(self) -> dict:
        """Return dict for frontend form generation"""
        raise NotImplementedError


class ShortText(FieldType):
    """Single-line text input"""
    
    def __init__(self, max_len: int = 100, placeholder: str = ""):
        self.max_len = max_len
        self.placeholder = placeholder
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        return (str, Field(max_length=self.max_len))
    
    def to_form_field(self) -> dict:
        return {
            'type': 'text',
            'maxLength': self.max_len,
            'placeholder': self.placeholder
        }


class LongText(FieldType):
    """Multi-line text area"""
    
    def __init__(self, max_len: int = 5000, placeholder: str = ""):
        self.max_len = max_len
        self.placeholder = placeholder
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        return (str, Field(max_length=self.max_len))
    
    def to_form_field(self) -> dict:
        return {
            'type': 'textarea',
            'maxLength': self.max_len,
            'placeholder': self.placeholder
        }


class Integer(FieldType):
    """Integer number input"""
    
    def __init__(self, min_val: Optional[int] = None, 
                 max_val: Optional[int] = None):
        self.min_val = min_val
        self.max_val = max_val
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        constraints = {}
        if self.min_val is not None:
            constraints['ge'] = self.min_val
        if self.max_val is not None:
            constraints['le'] = self.max_val
        return (int, Field(default=None, **constraints))
    
    def to_form_field(self) -> dict:
        field = {'type': 'number', 'step': 1}
        if self.min_val is not None:
            field['min'] = self.min_val
        if self.max_val is not None:
            field['max'] = self.max_val
        return field


class CompendiumLink(FieldType):
    """Dropdown that links to compendium entries"""
    
    def __init__(self, query: str, label: str = "Select..."):
        """
        Args:
            query: GUID pattern to match, e.g., "d&d5.0-basic-damage-type-*"
            label: Default label for the dropdown
        """
        self.query = query
        self.label = label
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        # Store as string GUID
        return (str, Field(default=None))
    
    def to_form_field(self) -> dict:
        return {
            'type': 'compendium_link',
            'query': self.query,
            'label': self.label
        }


class ParentLink(FieldType):
    """Reference to parent compendium entry for hierarchical structures"""
    
    def __init__(self, label: str = "Parent Entry"):
        """
        Args:
            label: Label for the parent selector
        """
        self.label = label
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        # Store as optional string GUID
        return (Optional[str], Field(default=None))
    
    def to_form_field(self) -> dict:
        return {
            'type': 'parent_link',
            'label': self.label
        }


class Markdown(FieldType):
    """Rich text field that supports markdown formatting"""
    
    def __init__(self, max_len: int = 10000, placeholder: str = ""):
        self.max_len = max_len
        self.placeholder = placeholder
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        return (str, Field(max_length=self.max_len))
    
    def to_form_field(self) -> dict:
        return {
            'type': 'markdown',
            'maxLength': self.max_len,
            'placeholder': self.placeholder
        }


class EntryCategory(FieldType):
    """Enum field for entry categorization (container/definition/item)"""
    
    def __init__(self):
        self.options = ["container", "definition", "item"]
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        from typing import Literal
        return (Literal["container", "definition", "item"], Field(default="item"))
    
    def to_form_field(self) -> dict:
        return {
            'type': 'select',
            'options': self.options,
            'label': 'Entry Category'
        }


# Convenience factory functions
def short_text(max_len: int = 100, placeholder: str = "") -> ShortText:
    return ShortText(max_len, placeholder)

def long_text(max_len: int = 5000, placeholder: str = "") -> LongText:
    return LongText(max_len, placeholder)

def integer(min_val: int = None, max_val: int = None) -> Integer:
    return Integer(min_val, max_val)

def compendium_link(query: str, label: str = "Select...") -> CompendiumLink:
    return CompendiumLink(query, label)

def parent_link(label: str = "Parent Entry") -> ParentLink:
    return ParentLink(label)

def markdown(max_len: int = 10000, placeholder: str = "") -> Markdown:
    return Markdown(max_len, placeholder)

def entry_category() -> EntryCategory:
    return EntryCategory()
