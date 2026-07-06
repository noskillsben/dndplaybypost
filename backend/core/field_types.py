import copy
import re
from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple, Union
from pydantic import AfterValidator, Field, create_model
from pydantic_core import PydanticUndefined

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
        return (int, Field(**constraints))
    
    def to_form_field(self) -> dict:
        field = {'type': 'number', 'step': 1}
        if self.min_val is not None:
            field['min'] = self.min_val
        if self.max_val is not None:
            field['max'] = self.max_val
        return field


class Decimal(FieldType):
    """Decimal/float number input"""
    
    def __init__(self, min_val: Optional[float] = None,
                 max_val: Optional[float] = None,
                 step: Optional[float] = None):
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        constraints = {}
        if self.min_val is not None:
            constraints['ge'] = self.min_val
        if self.max_val is not None:
            constraints['le'] = self.max_val
        return (float, Field(**constraints))
    
    def to_form_field(self) -> dict:
        field = {'type': 'number', 'step': self.step if self.step is not None else 'any'}
        if self.min_val is not None:
            field['min'] = self.min_val
        if self.max_val is not None:
            field['max'] = self.max_val
        return field


class Boolean(FieldType):
    """Checkbox input"""
    
    def __init__(self, label: str = ""):
        self.label = label
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        return (bool, Field())
    
    def to_form_field(self) -> dict:
        return {
            'type': 'checkbox',
            'label': self.label
        }


class Select(FieldType):
    """Dropdown with a fixed list of options"""
    
    def __init__(self, options: List[str], label: str = ""):
        if not options:
            raise ValueError("Select requires at least one option")
        self.options = list(options)
        self.label = label
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        return (Literal[tuple(self.options)], Field())
    
    def to_form_field(self) -> dict:
        return {
            'type': 'select',
            'options': self.options,
            'label': self.label
        }


def parse_link_query(query: str) -> dict:
    """
    Translate a compendium link query string into list-API filter params.
    
    Supported forms:
        "parent:<guid>"      -> {"parent_guid": <guid>}
        "type:<entry_type>"  -> {"entry_type": <entry_type>}
        "tag:<tag>"          -> {"tag": <tag>}
        "prefix:<prefix>"    -> {"guid_prefix": <prefix>}
        "<prefix>-*"         -> {"guid_prefix": <prefix>}  (legacy form)
    """
    if not query:
        return {}
    for prefix, param in (("parent:", "parent_guid"),
                          ("type:", "entry_type"),
                          ("tag:", "tag"),
                          ("prefix:", "guid_prefix")):
        if query.startswith(prefix):
            return {param: query[len(prefix):]}
    # Legacy glob form: "d&d5.0-rule-*"
    return {"guid_prefix": query[:-1] if query.endswith("*") else query}


class CompendiumLink(FieldType):
    """Dropdown that links to a single compendium entry"""
    
    def __init__(self, query: str, label: str = "Select..."):
        """
        Args:
            query: Link query, e.g. "parent:d&d5.0-rule-damage-types",
                   "type:item", "prefix:d&d5.0-rule-" (see parse_link_query)
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


class CompendiumLinkList(FieldType):
    """Multi-select that links to several compendium entries"""
    
    def __init__(self, query: str, label: str = "Select..."):
        """
        Args:
            query: Link query (see parse_link_query)
            label: Default label for the multi-select
        """
        self.query = query
        self.label = label
    
    def to_pydantic_field(self) -> Tuple[type, Any]:
        # Store as a list of GUID strings
        return (List[str], Field())
    
    def to_form_field(self) -> dict:
        return {
            'type': 'compendium_link_list',
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


def _item_annotation(field: FieldType):
    """Turn a FieldType into an Annotated type usable inside List[...] /
    row models, stripping any default so item-level constraints still apply."""
    py_type, field_obj = field.to_pydantic_field()
    field_obj = copy.deepcopy(field_obj)
    field_obj.default = PydanticUndefined
    return Annotated[py_type, field_obj]


class ListOf(FieldType):
    """Repeatable list of a single inner field type (which may itself be
    composite, e.g. list_of(table(...)))"""

    def __init__(self, item: FieldType, min_items: Optional[int] = None,
                 max_items: Optional[int] = None, label: str = ""):
        if not isinstance(item, FieldType):
            raise ValueError("list_of requires a FieldType item")
        self.item = item
        self.min_items = min_items
        self.max_items = max_items
        self.label = label

    def to_pydantic_field(self) -> Tuple[type, Any]:
        constraints = {}
        if self.min_items is not None:
            constraints['min_length'] = self.min_items
        if self.max_items is not None:
            constraints['max_length'] = self.max_items
        return (List[_item_annotation(self.item)], Field(**constraints))

    def to_form_field(self) -> dict:
        field = {
            'type': 'list',
            'item': self.item.to_form_field(),
            'label': self.label,
        }
        if self.min_items is not None:
            field['minItems'] = self.min_items
        if self.max_items is not None:
            field['maxItems'] = self.max_items
        return field


class Table(FieldType):
    """Rows of typed columns (class level tables, rollable tables, ...).

    Columns are given as a dict {name: FieldType} or list of (name, FieldType).
    Every row must provide a value for each column unless the column's own
    type is optional (e.g. compendium_link defaults to None).
    """

    def __init__(self, columns: Union[Dict[str, FieldType], List[Tuple[str, FieldType]]],
                 min_rows: Optional[int] = None, max_rows: Optional[int] = None,
                 label: str = ""):
        items = list(columns.items()) if isinstance(columns, dict) else list(columns)
        if not items:
            raise ValueError("table requires at least one column")
        for name, col in items:
            if not isinstance(col, FieldType):
                raise ValueError(f"table column '{name}' must be a FieldType")
        self.columns = items
        self.min_rows = min_rows
        self.max_rows = max_rows
        self.label = label
        self._row_model = None

    def row_model(self):
        if self._row_model is None:
            fields = {}
            for name, col in self.columns:
                py_type, field_obj = col.to_pydantic_field()
                fields[name] = (py_type, field_obj)
            self._row_model = create_model('TableRow', **fields)
        return self._row_model

    def to_pydantic_field(self) -> Tuple[type, Any]:
        constraints = {}
        if self.min_rows is not None:
            constraints['min_length'] = self.min_rows
        if self.max_rows is not None:
            constraints['max_length'] = self.max_rows
        return (List[self.row_model()], Field(**constraints))

    def to_form_field(self) -> dict:
        columns = []
        for name, col in self.columns:
            col_form = col.to_form_field()
            col_form['name'] = name
            columns.append(col_form)
        field = {
            'type': 'table',
            'columns': columns,
            'label': self.label,
        }
        if self.min_rows is not None:
            field['minRows'] = self.min_rows
        if self.max_rows is not None:
            field['maxRows'] = self.max_rows
        return field


_DICE_EXPR_RE = re.compile(r"^\s*(\d*[dD]\d+|\d+)(\s*[+-]\s*(\d*[dD]\d+|\d+))*\s*$")
_DICE_TERM_RE = re.compile(r"\d*[dD]\d+")


def validate_dice_expression(value: str) -> str:
    """Validate expressions like 'd20', '2d6+3', '1d8 + 2d4 - 1'."""
    if not _DICE_EXPR_RE.match(value):
        raise ValueError(f"Invalid dice expression: '{value}'")
    terms = _DICE_TERM_RE.findall(value)
    if not terms:
        raise ValueError("Dice expression must contain at least one die term (e.g. 'd6')")
    for term in terms:
        count, faces = term.lower().split("d")
        if count and int(count) < 1:
            raise ValueError(f"Die count must be at least 1 in '{term}'")
        if int(faces) < 1:
            raise ValueError(f"Die must have at least 1 face in '{term}'")
    return value.strip()


class DiceExpression(FieldType):
    """Validated dice expression string, e.g. '2d6+3'"""

    def __init__(self, placeholder: str = "e.g. 2d6+3"):
        self.placeholder = placeholder

    def to_pydantic_field(self) -> Tuple[type, Any]:
        return (Annotated[str, AfterValidator(validate_dice_expression)], Field())

    def to_form_field(self) -> dict:
        return {
            'type': 'dice_expression',
            'placeholder': self.placeholder,
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

def decimal(min_val: float = None, max_val: float = None, step: float = None) -> Decimal:
    return Decimal(min_val, max_val, step)

def boolean(label: str = "") -> Boolean:
    return Boolean(label)

def select(options: List[str], label: str = "") -> Select:
    return Select(options, label)

def compendium_link(query: str, label: str = "Select...") -> CompendiumLink:
    return CompendiumLink(query, label)

def compendium_link_list(query: str, label: str = "Select...") -> CompendiumLinkList:
    return CompendiumLinkList(query, label)

def parent_link(label: str = "Parent Entry") -> ParentLink:
    return ParentLink(label)

def markdown(max_len: int = 10000, placeholder: str = "") -> Markdown:
    return Markdown(max_len, placeholder)

def entry_category() -> EntryCategory:
    return EntryCategory()

def list_of(item: FieldType, min_items: int = None, max_items: int = None, label: str = "") -> ListOf:
    return ListOf(item, min_items, max_items, label)

def table(columns, min_rows: int = None, max_rows: int = None, label: str = "") -> Table:
    return Table(columns, min_rows, max_rows, label)

def dice_expression(placeholder: str = "e.g. 2d6+3") -> DiceExpression:
    return DiceExpression(placeholder)
