import pytest
from pydantic import ValidationError

from core import field_types as ft
from core.schema_builder import ObjectRegistration


def build(name, field, required=True):
    reg = ObjectRegistration(system="testsys", entry_type="thing")
    reg.add_field(name, field, required=required)
    return reg.model()


class TestListOf:
    def test_accepts_list_of_items(self):
        Model = build("tags", ft.list_of(ft.short_text(20)))
        assert Model(tags=["a", "b"]).tags == ["a", "b"]

    def test_item_constraints_enforced(self):
        Model = build("tags", ft.list_of(ft.short_text(3)))
        with pytest.raises(ValidationError):
            Model(tags=["okay-not"])

    def test_min_max_items(self):
        Model = build("dmg", ft.list_of(ft.integer(0), min_items=1, max_items=2))
        assert Model(dmg=[1]).dmg == [1]
        with pytest.raises(ValidationError):
            Model(dmg=[])
        with pytest.raises(ValidationError):
            Model(dmg=[1, 2, 3])

    def test_nested_list_of_list(self):
        Model = build("grid", ft.list_of(ft.list_of(ft.integer())))
        assert Model(grid=[[1, 2], [3]]).grid == [[1, 2], [3]]

    def test_optional_defaults_none(self):
        Model = build("tags", ft.list_of(ft.short_text()), required=False)
        assert Model().tags is None

    def test_rejects_non_fieldtype_item(self):
        with pytest.raises(ValueError):
            ft.list_of(str)

    def test_form_field(self):
        f = ft.list_of(ft.integer(0, 10), min_items=1, label="Scores").to_form_field()
        assert f["type"] == "list"
        assert f["item"] == {"type": "number", "step": 1, "min": 0, "max": 10}
        assert f["minItems"] == 1
        assert f["label"] == "Scores"


class TestTable:
    def level_table(self, **kwargs):
        return ft.table({
            "level": ft.integer(1, 20),
            "feature": ft.short_text(100),
        }, **kwargs)

    def test_accepts_valid_rows(self):
        Model = build("levels", self.level_table())
        m = Model(levels=[{"level": 1, "feature": "Rage"}, {"level": 2, "feature": "Reckless"}])
        assert m.levels[0].level == 1
        assert m.levels[1].feature == "Reckless"

    def test_cell_validation_enforced(self):
        Model = build("levels", self.level_table())
        with pytest.raises(ValidationError):
            Model(levels=[{"level": 21, "feature": "Too high"}])

    def test_missing_column_rejected(self):
        Model = build("levels", self.level_table())
        with pytest.raises(ValidationError):
            Model(levels=[{"level": 1}])

    def test_min_max_rows(self):
        Model = build("levels", self.level_table(min_rows=1, max_rows=2))
        with pytest.raises(ValidationError):
            Model(levels=[])
        with pytest.raises(ValidationError):
            Model(levels=[{"level": 1, "feature": "a"}] * 3)

    def test_optional_column_via_link(self):
        Model = build("rows", ft.table({
            "text": ft.short_text(50),
            "ref": ft.compendium_link("type:item"),
        }))
        m = Model(rows=[{"text": "no ref"}])
        assert m.rows[0].ref is None

    def test_columns_as_list_of_tuples(self):
        Model = build("rows", ft.table([("a", ft.integer()), ("b", ft.boolean())]))
        assert Model(rows=[{"a": 1, "b": True}]).rows[0].a == 1

    def test_requires_columns(self):
        with pytest.raises(ValueError):
            ft.table({})

    def test_rejects_non_fieldtype_column(self):
        with pytest.raises(ValueError):
            ft.table({"bad": int})

    def test_form_field(self):
        f = self.level_table(min_rows=1, label="Levels").to_form_field()
        assert f["type"] == "table"
        assert f["minRows"] == 1
        assert f["label"] == "Levels"
        assert f["columns"][0]["name"] == "level"
        assert f["columns"][0]["type"] == "number"
        assert f["columns"][1]["name"] == "feature"
        assert f["columns"][1]["type"] == "text"

    def test_list_of_tables(self):
        Model = build("tables", ft.list_of(self.level_table()))
        m = Model(tables=[[{"level": 1, "feature": "Rage"}]])
        assert m.tables[0][0].level == 1


class TestCompositeFieldsThroughApi:
    @pytest.fixture
    def class_template(self):
        from api.schemas import SCHEMA_REGISTRY
        reg = ObjectRegistration(system="testsys", entry_type="class")
        reg.add_field("name", ft.short_text(100), required=True)
        reg.add_field("hit_die", ft.dice_expression(), required=True)
        reg.add_field("levels", ft.table({
            "level": ft.integer(1, 20),
            "feature": ft.short_text(100),
        }, min_rows=1), required=True)
        SCHEMA_REGISTRY.setdefault("testsys", {})["class"] = reg
        yield reg
        del SCHEMA_REGISTRY["testsys"]

    async def test_create_entry_with_table_and_dice(self, client, class_template):
        resp = await client.post("/api/compendium/", json={
            "system": "testsys",
            "entry_type": "class",
            "name": "Barbarian",
            "data": {
                "name": "Barbarian",
                "hit_die": "1d12",
                "levels": [{"level": 1, "feature": "Rage"}],
            },
        })
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["data"]["levels"][0]["feature"] == "Rage"
        assert body["data"]["hit_die"] == "1d12"

    async def test_nested_error_is_readable(self, client, class_template):
        resp = await client.post("/api/compendium/", json={
            "system": "testsys",
            "entry_type": "class",
            "name": "Barbarian",
            "data": {
                "name": "Barbarian",
                "hit_die": "1d12",
                "levels": [{"level": 99, "feature": "Rage"}],
            },
        })
        assert resp.status_code == 400
        error = resp.json()["error"]
        assert any(d["field"] == "levels.0.level" for d in error["details"])

    async def test_invalid_dice_rejected_via_api(self, client, class_template):
        resp = await client.post("/api/compendium/", json={
            "system": "testsys",
            "entry_type": "class",
            "name": "Barbarian",
            "data": {"name": "Barbarian", "hit_die": "banana", "levels": [{"level": 1, "feature": "Rage"}]},
        })
        assert resp.status_code == 400
        assert "hit_die" in resp.json()["error"]["message"]

    async def test_form_schema_exposes_composites(self, client, class_template):
        resp = await client.get("/api/schemas/testsys/class")
        assert resp.status_code == 200
        fields = {f["name"]: f for f in resp.json()["fields"]}
        assert fields["levels"]["type"] == "table"
        assert fields["hit_die"]["type"] == "dice_expression"


class TestDiceExpression:
    @pytest.mark.parametrize("expr", ["d20", "2d6", "2d6+3", "1d8 + 2d4 - 1", "D12+2", "3 + 1d4"])
    def test_valid_expressions(self, expr):
        Model = build("damage", ft.dice_expression())
        assert Model(damage=expr).damage == expr.strip()

    @pytest.mark.parametrize("expr", ["", "banana", "2d", "d", "2x6", "2d6+", "+2d6+", "5", "1+2", "0d6", "2d0"])
    def test_invalid_expressions(self, expr):
        Model = build("damage", ft.dice_expression())
        with pytest.raises(ValidationError):
            Model(damage=expr)

    def test_optional_defaults_none(self):
        Model = build("damage", ft.dice_expression(), required=False)
        assert Model().damage is None

    def test_form_field(self):
        f = ft.dice_expression(placeholder="2d8").to_form_field()
        assert f == {"type": "dice_expression", "placeholder": "2d8"}
