import pytest
from pydantic import ValidationError

from core import field_types as ft
from core.schema_builder import ObjectRegistration


def build(name, field, required=True):
    reg = ObjectRegistration(system="testsys", entry_type="thing")
    reg.add_field(name, field, required=required)
    return reg.model()


class TestChoice:
    def test_accepts_options_list(self):
        Model = build("skills", ft.choice("type:skill"))
        m = Model(skills={"choose": 2, "options": ["skill-a", "skill-b", "skill-c"]})
        assert m.skills.choose == 2
        assert m.skills.options == ["skill-a", "skill-b", "skill-c"]

    def test_accepts_query_source(self):
        Model = build("skills", ft.choice())
        m = Model(skills={"choose": 1, "query": "type:skill"})
        assert m.skills.query == "type:skill"

    def test_accepts_both_sources(self):
        Model = build("skills", ft.choice())
        m = Model(skills={"choose": 1, "options": ["a"], "query": "type:skill"})
        assert m.skills.options == ["a"]

    def test_requires_a_source(self):
        Model = build("skills", ft.choice())
        with pytest.raises(ValidationError):
            Model(skills={"choose": 2})

    def test_choose_must_be_positive(self):
        Model = build("skills", ft.choice())
        with pytest.raises(ValidationError):
            Model(skills={"choose": 0, "options": ["a"]})

    def test_options_must_cover_choose(self):
        Model = build("skills", ft.choice())
        with pytest.raises(ValidationError):
            Model(skills={"choose": 3, "options": ["a", "b"]})

    def test_optional_defaults_none(self):
        Model = build("skills", ft.choice(), required=False)
        assert Model().skills is None

    def test_form_field(self):
        f = ft.choice("type:skill", label="Skill Proficiencies").to_form_field()
        assert f == {"type": "choice", "query": "type:skill", "label": "Skill Proficiencies"}


class TestGrant:
    def test_accepts_guid_list(self):
        Model = build("traits", ft.grant("type:trait"))
        m = Model(traits=["d&d5.0-trait-darkvision", "d&d5.0-trait-dwarven-resilience"])
        assert len(m.traits) == 2

    def test_min_max_items(self):
        Model = build("traits", ft.grant(min_items=1, max_items=2))
        with pytest.raises(ValidationError):
            Model(traits=[])
        with pytest.raises(ValidationError):
            Model(traits=["a", "b", "c"])

    def test_rejects_non_string_items(self):
        Model = build("traits", ft.grant())
        with pytest.raises(ValidationError):
            Model(traits=[{"guid": "nope"}])

    def test_optional_defaults_none(self):
        Model = build("traits", ft.grant(), required=False)
        assert Model().traits is None

    def test_form_field(self):
        f = ft.grant("type:trait", label="Racial Traits", min_items=1).to_form_field()
        assert f == {"type": "grant", "query": "type:trait", "label": "Racial Traits", "minItems": 1}


class TestChoiceGrantThroughApi:
    @pytest.fixture
    async def race_template(self, client):
        resp = await client.post("/api/systems", json={"guid": "testsys", "name": "Test System"})
        assert resp.status_code == 201, resp.text
        resp = await client.post("/api/templates", json={
            "system": "testsys",
            "entry_type": "race",
            "fields": [
                {"name": "name", "type": "short_text", "required": True,
                 "params": {"max_len": 100}},
                {"name": "traits", "type": "grant", "required": True,
                 "params": {"query": "type:trait", "label": "Traits"}},
                {"name": "skill_choice", "type": "choice", "required": False,
                 "params": {"query": "type:skill", "label": "Skills"}},
            ],
        })
        assert resp.status_code == 201, resp.text
        return resp.json()

    async def test_create_race_with_grants_and_choice(self, client, race_template):
        resp = await client.post("/api/compendium/", json={
            "system": "testsys",
            "entry_type": "race",
            "name": "Half-Elf",
            "data": {
                "name": "Half-Elf",
                "traits": ["testsys-trait-darkvision"],
                "skill_choice": {"choose": 2, "query": "type:skill"},
            },
        })
        assert resp.status_code == 201, resp.text
        data = resp.json()["data"]
        assert data["traits"] == ["testsys-trait-darkvision"]
        assert data["skill_choice"]["choose"] == 2

    async def test_invalid_choice_spec_rejected(self, client, race_template):
        resp = await client.post("/api/compendium/", json={
            "system": "testsys",
            "entry_type": "race",
            "name": "Half-Elf",
            "data": {
                "name": "Half-Elf",
                "traits": [],
                "skill_choice": {"choose": 2},
            },
        })
        assert resp.status_code == 400
        assert "skill_choice" in resp.json()["error"]["message"]

    async def test_form_schema_exposes_choice_grant(self, client, race_template):
        resp = await client.get("/api/schemas/testsys/race")
        assert resp.status_code == 200
        fields = {f["name"]: f for f in resp.json()["fields"]}
        assert fields["traits"]["type"] == "grant"
        assert fields["traits"]["query"] == "type:trait"
        assert fields["skill_choice"]["type"] == "choice"
