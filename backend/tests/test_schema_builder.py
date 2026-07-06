import pytest
from pydantic import ValidationError

from core import field_types as ft
from core.schema_builder import ObjectRegistration, SeedEntry


@pytest.fixture
def item_registration():
    reg = ObjectRegistration(system="testsys", entry_type="item")
    reg.add_field("name", ft.short_text(100), base_field=True, required=True)
    reg.add_markdown_field("description")
    reg.add_field("weight", ft.integer(min_val=0))
    reg.add_parent_field()
    reg.add_category_field()
    return reg


class TestModelGeneration:
    def test_valid_data_passes(self, item_registration):
        Model = item_registration.model()
        obj = Model(name="Longsword", description="A sword.", weight=3)
        assert obj.name == "Longsword"
        assert obj.weight == 3

    def test_missing_required_field_fails(self, item_registration):
        Model = item_registration.model()
        with pytest.raises(ValidationError):
            Model(description="No name")

    def test_optional_fields_default_to_none(self, item_registration):
        Model = item_registration.model()
        obj = Model(name="Torch")
        assert obj.description is None
        assert obj.weight is None
        assert obj.parent_guid is None

    def test_invalid_type_fails(self, item_registration):
        Model = item_registration.model()
        with pytest.raises(ValidationError):
            Model(name="Rock", weight="heavy")

    def test_entry_category_literal(self, item_registration):
        Model = item_registration.model()
        assert Model(name="Box", entry_category="container").entry_category == "container"
        with pytest.raises(ValidationError):
            Model(name="Box", entry_category="not-a-category")

    def test_model_cache_invalidated_on_add_field(self, item_registration):
        Model1 = item_registration.model()
        item_registration.add_field("value", ft.integer(0))
        Model2 = item_registration.model()
        assert Model1 is not Model2
        assert Model2(name="Gem", value=100).value == 100


class TestFormGeneration:
    def test_form_lists_all_fields_in_order(self, item_registration):
        form = item_registration.form()
        assert form["system"] == "testsys"
        names = [f["name"] for f in form["fields"]]
        assert names == ["name", "description", "weight", "parent_guid", "entry_category"]

    def test_form_field_metadata(self, item_registration):
        form = item_registration.form()
        by_name = {f["name"]: f for f in form["fields"]}
        assert by_name["name"]["required"] is True
        assert by_name["name"]["base_field"] is True
        assert by_name["weight"]["type"] == "number"
        assert by_name["parent_guid"]["type"] == "parent_link"
        assert by_name["entry_category"]["type"] == "select"


class TestSeedEntries:
    def test_call_returns_validated_seed_entry(self, item_registration):
        entry = item_registration(guid="longsword", name="Longsword", weight=3)
        assert isinstance(entry, SeedEntry)
        assert entry.guid == "testsys-item-longsword"
        assert entry.system == "testsys"
        assert entry.entry_type == "item"
        assert entry.data["name"] == "Longsword"
        assert entry.data["weight"] == 3

    def test_call_with_invalid_data_raises(self, item_registration):
        with pytest.raises(ValueError):
            item_registration(guid="bad", name="Bad", weight=-5)

    def test_call_without_name_raises(self, item_registration):
        with pytest.raises(ValueError):
            item_registration(guid="anon", description="nameless")

    def test_parent_guid_and_source_carried(self, item_registration):
        parent = item_registration(guid="weapons", name="Weapons")
        child = item_registration(
            guid="dagger",
            name="Dagger",
            parent_guid=parent.guid,
            source={"name": "SRD", "page": 12},
        )
        assert child.parent_guid == "testsys-item-weapons"
        assert child.source == {"name": "SRD", "page": 12}

    def test_seed_entry_requires_system(self):
        reg = ObjectRegistration()
        reg.add_field("name", ft.short_text(10), required=True)
        with pytest.raises(ValueError):
            reg(guid="x", name="X")
