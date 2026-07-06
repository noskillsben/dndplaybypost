import pytest
from pydantic import ValidationError

from core import field_types as ft
from core.field_types import parse_link_query
from core.schema_builder import ObjectRegistration


def build(name, field, required=False):
    reg = ObjectRegistration(system="testsys", entry_type="thing")
    reg.add_field(name, field, required=required)
    return reg.model()


class TestParseLinkQuery:
    def test_parent_query(self):
        assert parse_link_query("parent:d&d5.0-rule-damage-types") == {
            "parent_guid": "d&d5.0-rule-damage-types"
        }

    def test_type_query(self):
        assert parse_link_query("type:item") == {"entry_type": "item"}

    def test_tag_query(self):
        assert parse_link_query("tag:martial") == {"tag": "martial"}

    def test_prefix_query(self):
        assert parse_link_query("prefix:d&d5.0-rule-") == {"guid_prefix": "d&d5.0-rule-"}

    def test_legacy_glob_query(self):
        assert parse_link_query("d&d5.0-rule-*") == {"guid_prefix": "d&d5.0-rule-"}

    def test_empty_query(self):
        assert parse_link_query("") == {}


class TestCompendiumLink:
    def test_stores_guid_string(self):
        Model = build("damage_type", ft.compendium_link("parent:x"))
        assert Model(damage_type="d&d5.0-rule-slashing").damage_type == "d&d5.0-rule-slashing"

    def test_optional_by_default(self):
        Model = build("damage_type", ft.compendium_link("parent:x"))
        assert Model().damage_type is None

    def test_form_field(self):
        f = ft.compendium_link("type:item", label="Item").to_form_field()
        assert f == {"type": "compendium_link", "query": "type:item", "label": "Item"}


class TestCompendiumLinkList:
    def test_stores_list_of_guids(self):
        Model = build("proficiencies", ft.compendium_link_list("type:skill"))
        obj = Model(proficiencies=["a-skill-1", "a-skill-2"])
        assert obj.proficiencies == ["a-skill-1", "a-skill-2"]

    def test_rejects_non_list(self):
        Model = build("proficiencies", ft.compendium_link_list("type:skill"))
        with pytest.raises(ValidationError):
            Model(proficiencies="a-skill-1")

    def test_optional_defaults_none(self):
        Model = build("proficiencies", ft.compendium_link_list("type:skill"))
        assert Model().proficiencies is None

    def test_required_enforced(self):
        Model = build("proficiencies", ft.compendium_link_list("type:skill"), required=True)
        with pytest.raises(ValidationError):
            Model()

    def test_form_field(self):
        f = ft.compendium_link_list("parent:root", label="Skills").to_form_field()
        assert f == {"type": "compendium_link_list", "query": "parent:root", "label": "Skills"}


class TestParentLink:
    def test_optional_guid(self):
        Model = build("parent_guid", ft.parent_link())
        assert Model().parent_guid is None
        assert Model(parent_guid="testsys-thing-root").parent_guid == "testsys-thing-root"

    def test_form_field(self):
        assert ft.parent_link("Parent").to_form_field() == {
            "type": "parent_link",
            "label": "Parent",
        }
