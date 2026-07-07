import pytest


async def create_system(client, guid="testsys", name="Test System"):
    resp = await client.post("/api/systems", json={"guid": guid, "name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


async def create_template(client, system="testsys", entry_type="gadget", fields=None, **overrides):
    if fields is None:
        fields = [
            {"name": "name", "type": "short_text", "required": True, "base_field": True,
             "params": {"max_len": 100}},
            {"name": "charge", "type": "integer", "params": {"min_val": 0, "max_val": 5}},
        ]
    payload = {"system": system, "entry_type": entry_type, "fields": fields}
    payload.update(overrides)
    resp = await client.post("/api/templates", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestSystemsApi:
    async def test_create_system(self, client):
        body = await create_system(client)
        assert body["guid"] == "testsys"
        resp = await client.get("/api/schemas/systems")
        assert "testsys" in resp.json()["systems"]

    async def test_guid_derived_from_name(self, client):
        resp = await client.post("/api/systems", json={"name": "Lasers & Feelings"})
        assert resp.status_code == 201
        assert resp.json()["guid"] == "lasers-feelings"

    async def test_duplicate_system_conflict(self, client):
        await create_system(client)
        resp = await client.post("/api/systems", json={"guid": "testsys", "name": "Again"})
        assert resp.status_code == 409


class TestTemplateCreate:
    async def test_create_and_fetch(self, client):
        await create_system(client)
        created = await create_template(client)
        assert created["system"] == "testsys"
        assert created["entry_type"] == "gadget"
        resp = await client.get("/api/templates/testsys/gadget")
        assert resp.status_code == 200
        names = [f["name"] for f in resp.json()["fields"]]
        assert names == ["name", "charge"]

    async def test_name_field_added_when_missing(self, client):
        await create_system(client)
        created = await create_template(client, entry_type="widget", fields=[
            {"name": "size", "type": "integer"},
        ])
        first = created["fields"][0]
        assert first["name"] == "name"
        assert first["required"] is True

    async def test_unknown_system_rejected(self, client):
        resp = await client.post("/api/templates", json={
            "system": "nope", "entry_type": "thing", "fields": [],
        })
        assert resp.status_code == 400
        assert resp.json()["error"]["message"] == "System not found"

    async def test_duplicate_template_conflict(self, client):
        await create_system(client)
        await create_template(client)
        resp = await client.post("/api/templates", json={
            "system": "testsys", "entry_type": "gadget", "fields": [],
        })
        assert resp.status_code == 409

    async def test_entry_type_slugified(self, client):
        await create_system(client)
        created = await create_template(client, entry_type="Space Ship")
        assert created["entry_type"] == "space-ship"

    async def test_unknown_field_type_rejected(self, client):
        await create_system(client)
        resp = await client.post("/api/templates", json={
            "system": "testsys", "entry_type": "thing",
            "fields": [{"name": "x", "type": "hologram"}],
        })
        assert resp.status_code == 400
        assert "hologram" in resp.json()["error"]["message"]

    async def test_bad_field_name_rejected(self, client):
        await create_system(client)
        for bad in ("2bad", "class", "_private", "has space"):
            resp = await client.post("/api/templates", json={
                "system": "testsys", "entry_type": "thing",
                "fields": [{"name": bad, "type": "integer"}],
            })
            assert resp.status_code == 400, bad

    async def test_duplicate_field_name_rejected(self, client):
        await create_system(client)
        resp = await client.post("/api/templates", json={
            "system": "testsys", "entry_type": "thing",
            "fields": [
                {"name": "x", "type": "integer"},
                {"name": "x", "type": "boolean"},
            ],
        })
        assert resp.status_code == 400
        assert "duplicate" in resp.json()["error"]["message"].lower()

    async def test_unknown_param_rejected(self, client):
        await create_system(client)
        resp = await client.post("/api/templates", json={
            "system": "testsys", "entry_type": "thing",
            "fields": [{"name": "x", "type": "integer", "params": {"max_len": 5}}],
        })
        assert resp.status_code == 400

    async def test_composite_specs_round_trip(self, client):
        await create_system(client)
        fields = [
            {"name": "hit_die", "type": "dice_expression", "required": True},
            {"name": "style", "type": "select", "params": {"options": ["laser", "feeling"]}},
            {"name": "traits", "type": "grant", "params": {"query": "type:trait"}},
            {"name": "skill_choice", "type": "choice", "params": {"query": "type:skill"}},
            {"name": "notes", "type": "list_of", "params": {"item": {"type": "short_text", "params": {"max_len": 50}}}},
            {"name": "levels", "type": "table", "params": {
                "columns": [
                    {"name": "level", "type": "integer", "params": {"min_val": 1, "max_val": 10}},
                    {"name": "feature", "type": "short_text", "params": {"max_len": 100}},
                ],
                "min_rows": 1,
            }},
        ]
        await create_template(client, entry_type="klass", fields=fields)
        resp = await client.get("/api/templates/testsys/klass")
        stored = {f["name"]: f for f in resp.json()["fields"]}
        assert stored["levels"]["params"]["columns"][0]["name"] == "level"
        assert stored["notes"]["params"]["item"]["type"] == "short_text"
        form = await client.get("/api/schemas/testsys/klass")
        form_fields = {f["name"]: f for f in form.json()["fields"]}
        assert form_fields["levels"]["type"] == "table"
        assert form_fields["notes"]["type"] == "list"
        assert form_fields["traits"]["query"] == "type:trait"


class TestTemplatesDriveEntries:
    async def test_entry_validates_against_db_template(self, client):
        await create_system(client)
        await create_template(client)
        ok = await client.post("/api/compendium/", json={
            "system": "testsys", "entry_type": "gadget", "name": "Zapper",
            "data": {"name": "Zapper", "charge": 3},
        })
        assert ok.status_code == 201, ok.text
        bad = await client.post("/api/compendium/", json={
            "system": "testsys", "entry_type": "gadget", "name": "Overzapper",
            "data": {"name": "Overzapper", "charge": 99},
        })
        assert bad.status_code == 400
        assert any(d["field"] == "charge" for d in bad.json()["error"]["details"])

    async def test_unknown_entry_type_rejected(self, client):
        await create_system(client)
        resp = await client.post("/api/compendium/", json={
            "system": "testsys", "entry_type": "nope", "name": "X",
            "data": {"name": "X"},
        })
        assert resp.status_code == 400
        assert resp.json()["error"]["message"] == "Invalid entry type"

    async def test_schema_endpoints_reflect_db(self, client):
        await create_system(client)
        await create_template(client)
        types = await client.get("/api/schemas/testsys/types")
        assert types.status_code == 200
        assert "gadget" in types.json()["types"]
        form = await client.get("/api/schemas/testsys/gadget")
        assert form.status_code == 200
        fields = {f["name"]: f for f in form.json()["fields"]}
        assert fields["charge"]["type"] == "number"
        assert fields["name"]["required"] is True


class TestTemplateUpdate:
    async def test_put_changes_validation(self, client):
        await create_system(client)
        await create_template(client)
        resp = await client.post("/api/compendium/", json={
            "system": "testsys", "entry_type": "gadget", "name": "Zapper",
            "data": {"name": "Zapper", "charge": 9},
        })
        assert resp.status_code == 400
        resp = await client.put("/api/templates/testsys/gadget", json={
            "fields": [
                {"name": "name", "type": "short_text", "required": True, "base_field": True,
                 "params": {"max_len": 100}},
                {"name": "charge", "type": "integer", "params": {"min_val": 0, "max_val": 10}},
            ],
        })
        assert resp.status_code == 200, resp.text
        resp = await client.post("/api/compendium/", json={
            "system": "testsys", "entry_type": "gadget", "name": "Zapper",
            "data": {"name": "Zapper", "charge": 9},
        })
        assert resp.status_code == 201, resp.text

    async def test_put_unknown_template_404(self, client):
        await create_system(client)
        resp = await client.put("/api/templates/testsys/nope", json={"fields": []})
        assert resp.status_code == 404

    async def test_put_keeps_name_field(self, client):
        await create_system(client)
        await create_template(client)
        resp = await client.put("/api/templates/testsys/gadget", json={
            "fields": [{"name": "charge", "type": "integer"}],
        })
        assert resp.status_code == 200
        names = [f["name"] for f in resp.json()["fields"]]
        assert names[0] == "name"


class TestTemplateDelete:
    async def test_delete_blocked_while_entries_exist(self, client):
        await create_system(client)
        await create_template(client)
        resp = await client.post("/api/compendium/", json={
            "system": "testsys", "entry_type": "gadget", "name": "Zapper",
            "data": {"name": "Zapper"},
        })
        assert resp.status_code == 201
        resp = await client.delete("/api/templates/testsys/gadget")
        assert resp.status_code == 409

    async def test_delete_then_type_invalid(self, client):
        await create_system(client)
        await create_template(client)
        resp = await client.delete("/api/templates/testsys/gadget")
        assert resp.status_code == 204
        resp = await client.post("/api/compendium/", json={
            "system": "testsys", "entry_type": "gadget", "name": "X",
            "data": {"name": "X"},
        })
        assert resp.status_code == 400
        assert resp.json()["error"]["message"] == "Invalid entry type"


class TestTemplateList:
    async def test_list_filters_by_system(self, client):
        await create_system(client)
        await create_template(client)
        resp = await client.get("/api/templates", params={"system": "testsys"})
        assert resp.status_code == 200
        templates = resp.json()["templates"]
        assert len(templates) == 1
        assert templates[0]["entry_type"] == "gadget"
        assert templates[0]["field_count"] == 2

    async def test_seeded_dnd50_templates_present(self, client):
        resp = await client.get("/api/templates", params={"system": "d&d5.0"})
        types = {t["entry_type"] for t in resp.json()["templates"]}
        assert {"rule", "item", "spell", "class"} <= types

    async def test_seeded_spell_form_matches_python_definition(self, client):
        resp = await client.get("/api/schemas/d&d5.0/spell")
        assert resp.status_code == 200
        fields = {f["name"]: f for f in resp.json()["fields"]}
        assert fields["level"]["type"] == "number"
        assert fields["level"]["max"] == 9
        assert fields["level"]["required"] is True
        assert fields["description"]["type"] == "markdown"
