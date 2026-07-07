"""Convert stored entry-type template specs (JSON) into FieldType instances
and ObjectRegistrations.

The `entry_templates` table is the runtime source of truth for entry-type
schemas — users create and edit types in the browser. Python definitions
under schemas/systems/ are only seed data written into that table
(see seed_data.py).

Field spec format (recursive):
    {"name": "level", "type": "integer", "required": true,
     "base_field": false, "params": {"min_val": 1, "max_val": 20}}

Composite params:
    list_of: {"item": <spec without name>, "min_items", "max_items", "label"}
    table:   {"columns": [<spec with name>, ...], "min_rows", "max_rows", "label"}
"""
import keyword
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core import field_types as ft
from core.schema_builder import ObjectRegistration
from models.template import EntryTemplate


class TemplateSpecError(ValueError):
    """A stored or submitted template field spec is invalid."""


_SIMPLE_TYPES = {
    "short_text": ft.ShortText,
    "long_text": ft.LongText,
    "markdown": ft.Markdown,
    "integer": ft.Integer,
    "decimal": ft.Decimal,
    "boolean": ft.Boolean,
    "select": ft.Select,
    "compendium_link": ft.CompendiumLink,
    "compendium_link_list": ft.CompendiumLinkList,
    "parent_link": ft.ParentLink,
    "entry_category": ft.EntryCategory,
    "dice_expression": ft.DiceExpression,
    "choice": ft.Choice,
    "grant": ft.Grant,
}

_ALLOWED_PARAMS = {
    "short_text": {"max_len", "placeholder"},
    "long_text": {"max_len", "placeholder"},
    "markdown": {"max_len", "placeholder"},
    "integer": {"min_val", "max_val"},
    "decimal": {"min_val", "max_val", "step"},
    "boolean": {"label"},
    "select": {"options", "label"},
    "compendium_link": {"query", "label"},
    "compendium_link_list": {"query", "label"},
    "parent_link": {"label"},
    "entry_category": set(),
    "dice_expression": {"placeholder"},
    "list_of": {"item", "min_items", "max_items", "label"},
    "table": {"columns", "min_rows", "max_rows", "label"},
    "choice": {"query", "label"},
    "grant": {"query", "label", "min_items", "max_items"},
}

_PARAM_TYPES = {
    "max_len": int,
    "placeholder": str,
    "min_val": (int, float),
    "max_val": (int, float),
    "step": (int, float),
    "label": str,
    "options": list,
    "query": str,
    "min_items": int,
    "max_items": int,
    "min_rows": int,
    "max_rows": int,
}

TYPE_NAMES = sorted(_ALLOWED_PARAMS)


def check_field_name(name: Any, path: str) -> str:
    if not name or not isinstance(name, str):
        raise TemplateSpecError(f"{path}: a field name is required")
    if not name.isidentifier() or keyword.iskeyword(name) or name.startswith("_"):
        raise TemplateSpecError(
            f"{path}: '{name}' is not a valid field name (use letters, digits "
            f"and underscores; can't start with a digit or underscore or be a "
            f"Python keyword)"
        )
    return name


def _check_params(type_name: str, params: Any, path: str) -> None:
    if not isinstance(params, dict):
        raise TemplateSpecError(f"{path}: 'params' must be an object")
    unknown = set(params) - _ALLOWED_PARAMS[type_name]
    if unknown:
        raise TemplateSpecError(
            f"{path}: unknown params for {type_name}: {', '.join(sorted(unknown))}"
        )
    for key, value in params.items():
        if key in ("item", "columns"):
            continue  # validated recursively in field_from_spec
        expected = _PARAM_TYPES[key]
        if isinstance(value, bool) or not isinstance(value, expected):
            raise TemplateSpecError(f"{path}: param '{key}' has the wrong type")


def field_from_spec(spec: Any, path: str = "field") -> ft.FieldType:
    """Build a FieldType instance from a stored field spec (recursive)."""
    if not isinstance(spec, dict):
        raise TemplateSpecError(f"{path}: field spec must be an object")
    type_name = spec.get("type")
    if type_name not in _ALLOWED_PARAMS:
        raise TemplateSpecError(
            f"{path}: unknown field type '{type_name}' (known: {', '.join(TYPE_NAMES)})"
        )
    params = spec.get("params") or {}
    _check_params(type_name, params, path)
    kwargs = {k: v for k, v in params.items() if k not in ("item", "columns")}
    try:
        if type_name == "list_of":
            item_spec = params.get("item")
            if item_spec is None:
                raise TemplateSpecError(f"{path}: list_of requires an 'item' spec in params")
            item = field_from_spec(item_spec, path=f"{path}.item")
            return ft.ListOf(item, **kwargs)
        if type_name == "table":
            column_specs = params.get("columns")
            if not isinstance(column_specs, list) or not column_specs:
                raise TemplateSpecError(
                    f"{path}: table requires a non-empty 'columns' list in params"
                )
            columns = []
            seen = set()
            for i, col in enumerate(column_specs):
                col_path = f"{path}.columns.{i}"
                if not isinstance(col, dict):
                    raise TemplateSpecError(f"{col_path}: column spec must be an object")
                col_name = check_field_name(col.get("name"), col_path)
                if col_name in seen:
                    raise TemplateSpecError(f"{col_path}: duplicate column name '{col_name}'")
                seen.add(col_name)
                columns.append((col_name, field_from_spec(col, path=col_path)))
            return ft.Table(columns, **kwargs)
        return _SIMPLE_TYPES[type_name](**kwargs)
    except TemplateSpecError:
        raise
    except (TypeError, ValueError) as e:
        raise TemplateSpecError(f"{path}: {e}")


def _params(**values) -> Dict[str, Any]:
    return {k: v for k, v in values.items() if v is not None and v != ""}


def spec_from_field(field: ft.FieldType) -> Dict[str, Any]:
    """Serialize a FieldType instance back into a stored spec (recursive).
    Used to turn Python-defined built-ins into seed data."""
    if isinstance(field, ft.ShortText):
        return {"type": "short_text", "params": _params(max_len=field.max_len, placeholder=field.placeholder)}
    if isinstance(field, ft.LongText):
        return {"type": "long_text", "params": _params(max_len=field.max_len, placeholder=field.placeholder)}
    if isinstance(field, ft.Markdown):
        return {"type": "markdown", "params": _params(max_len=field.max_len, placeholder=field.placeholder)}
    if isinstance(field, ft.Integer):
        return {"type": "integer", "params": _params(min_val=field.min_val, max_val=field.max_val)}
    if isinstance(field, ft.Decimal):
        return {"type": "decimal", "params": _params(min_val=field.min_val, max_val=field.max_val, step=field.step)}
    if isinstance(field, ft.Boolean):
        return {"type": "boolean", "params": _params(label=field.label)}
    if isinstance(field, ft.Select):
        return {"type": "select", "params": _params(options=list(field.options), label=field.label)}
    if isinstance(field, ft.CompendiumLinkList):
        return {"type": "compendium_link_list", "params": _params(query=field.query, label=field.label)}
    if isinstance(field, ft.CompendiumLink):
        return {"type": "compendium_link", "params": _params(query=field.query, label=field.label)}
    if isinstance(field, ft.ParentLink):
        return {"type": "parent_link", "params": _params(label=field.label)}
    if isinstance(field, ft.EntryCategory):
        return {"type": "entry_category", "params": {}}
    if isinstance(field, ft.DiceExpression):
        return {"type": "dice_expression", "params": _params(placeholder=field.placeholder)}
    if isinstance(field, ft.Choice):
        return {"type": "choice", "params": _params(query=field.query, label=field.label)}
    if isinstance(field, ft.Grant):
        return {"type": "grant", "params": _params(query=field.query, label=field.label,
                                                   min_items=field.min_items, max_items=field.max_items)}
    if isinstance(field, ft.ListOf):
        params = _params(min_items=field.min_items, max_items=field.max_items, label=field.label)
        params["item"] = spec_from_field(field.item)
        return {"type": "list_of", "params": params}
    if isinstance(field, ft.Table):
        params = _params(min_rows=field.min_rows, max_rows=field.max_rows, label=field.label)
        params["columns"] = [{"name": name, **spec_from_field(col)} for name, col in field.columns]
        return {"type": "table", "params": params}
    raise TemplateSpecError(f"Cannot serialize field type {type(field).__name__}")


def registration_from_fields(system: str, entry_type: str,
                             field_specs: Any) -> ObjectRegistration:
    """Build an ObjectRegistration (validation model + form schema) from a
    template's stored field spec list."""
    if not isinstance(field_specs, list) or not field_specs:
        raise TemplateSpecError("'fields' must be a non-empty list of field specs")
    registration = ObjectRegistration(system=system, entry_type=entry_type)
    seen = set()
    for i, spec in enumerate(field_specs):
        path = f"fields.{i}"
        if not isinstance(spec, dict):
            raise TemplateSpecError(f"{path}: field spec must be an object")
        name = check_field_name(spec.get("name"), path)
        if name in seen:
            raise TemplateSpecError(f"{path}: duplicate field name '{name}'")
        seen.add(name)
        field = field_from_spec(spec, path=f"{path} ({name})")
        registration.add_field(
            name, field,
            base_field=bool(spec.get("base_field", False)),
            required=bool(spec.get("required", False)),
        )
    return registration


def fields_from_registration(registration: ObjectRegistration) -> List[Dict[str, Any]]:
    """Serialize an ObjectRegistration's fields into stored spec form."""
    specs = []
    for name, field_def in registration.fields.items():
        spec = spec_from_field(field_def["type"])
        out = {
            "name": name,
            "type": spec["type"],
            "required": bool(field_def["required"]),
            "base_field": bool(field_def["base_field"]),
        }
        if spec.get("params"):
            out["params"] = spec["params"]
        specs.append(out)
    return specs


async def get_template(db: AsyncSession, system: str,
                       entry_type: str) -> Optional[EntryTemplate]:
    result = await db.execute(
        select(EntryTemplate).where(
            EntryTemplate.system == system,
            EntryTemplate.entry_type == entry_type,
        )
    )
    return result.scalar_one_or_none()


async def get_registration(db: AsyncSession, system: str,
                           entry_type: str) -> Optional[ObjectRegistration]:
    template = await get_template(db, system, entry_type)
    if template is None:
        return None
    return registration_from_fields(system, entry_type, template.fields)
