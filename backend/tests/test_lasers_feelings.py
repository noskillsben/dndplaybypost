"""D-12 exit test: define Lasers & Feelings (a one-page RPG) entirely through
the same API calls the in-app template editor makes — no Python schema edits."""

NAME_FIELD = {
    "name": "name",
    "type": "short_text",
    "required": True,
    "base_field": True,
    "params": {"max_len": 200},
}


async def define_system(client):
    resp = await client.post("/api/systems", json={
        "name": "Lasers & Feelings",
        "description": "A one-page sci-fi RPG by John Harper",
    })
    assert resp.status_code == 201, resp.text
    system = resp.json()["guid"]
    assert system == "lasers-feelings"
    return system


async def define_templates(client, system):
    simple = [
        NAME_FIELD,
        {"name": "description", "type": "markdown", "required": False,
         "base_field": True, "params": {"max_len": 2000}},
    ]
    for entry_type, label in (("style", "Style"), ("role", "Role"),
                              ("ship-strength", "Ship Strength")):
        resp = await client.post("/api/templates", json={
            "system": system, "entry_type": entry_type,
            "label": label, "fields": simple,
        })
        assert resp.status_code == 201, resp.text

    resp = await client.post("/api/templates", json={
        "system": system, "entry_type": "ship", "label": "Ship",
        "fields": [
            NAME_FIELD,
            {"name": "strengths", "type": "choice", "required": True,
             "params": {"query": "type:ship-strength", "label": "Strengths"}},
            {"name": "problem", "type": "long_text", "required": False,
             "params": {"max_len": 500}},
        ],
    })
    assert resp.status_code == 201, resp.text

    resp = await client.post("/api/templates", json={
        "system": system, "entry_type": "character", "label": "Character",
        "fields": [
            NAME_FIELD,
            {"name": "style", "type": "compendium_link", "required": True,
             "params": {"query": "type:style", "label": "Style"}},
            {"name": "role", "type": "compendium_link", "required": True,
             "params": {"query": "type:role", "label": "Role"}},
            {"name": "number", "type": "integer", "required": True,
             "params": {"min_val": 2, "max_val": 5}},
            {"name": "goal", "type": "short_text", "required": True,
             "params": {"max_len": 200}},
            {"name": "gear", "type": "list_of", "required": False,
             "params": {"item": {"type": "short_text",
                                 "params": {"max_len": 100}},
                        "max_items": 3}},
        ],
    })
    assert resp.status_code == 201, resp.text


async def create_entry(client, system, entry_type, name, data, guid=None):
    payload = {
        "system": system,
        "entry_type": entry_type,
        "name": name,
        "data": {"name": name, **data},
        "source": {"name": "Lasers & Feelings"},
        "homebrew": True,
    }
    if guid:
        payload["guid"] = guid
    resp = await client.post("/api/compendium/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestLasersAndFeelings:
    async def test_full_system_defined_via_api(self, client):
        system = await define_system(client)
        await define_templates(client, system)

        # Schema endpoints (what DynamicForm consumes) reflect the new system
        resp = await client.get(f"/api/schemas/{system}/types")
        assert sorted(resp.json()["types"]) == [
            "character", "role", "ship", "ship-strength", "style",
        ]
        form = (await client.get(f"/api/schemas/{system}/character")).json()
        by_name = {f["name"]: f for f in form["fields"]}
        assert by_name["number"]["min"] == 2
        assert by_name["number"]["max"] == 5
        assert by_name["style"]["type"] == "compendium_link"
        assert by_name["gear"]["type"] == "list"

        # Seed lookup content
        for style in ("Alien", "Android", "Dangerous", "Hot-Shot",
                      "Intrepid", "Savvy"):
            await create_entry(client, system, "style", style,
                               {"description": f"{style} characters."})
        for role in ("Doctor", "Envoy", "Engineer", "Explorer",
                     "Pilot", "Soldier"):
            await create_entry(client, system, "role", role,
                               {"description": f"The {role}."})
        for strength in ("Fast", "Nimble", "Well-Armed", "Powerful Shields",
                         "Superior Sensors", "Cloaking Device", "Fightercraft"):
            await create_entry(client, system, "ship-strength", strength, {})

        # The ship records a machine-readable "pick 2 strengths" choice
        ship = await create_entry(client, system, "ship", "Raptor", {
            "strengths": {"choose": 2, "query": "type:ship-strength"},
            "problem": "Our captain is smitten with an enemy agent.",
        })
        assert ship["guid"] == "lasers-feelings-ship-raptor"
        assert ship["data"]["strengths"]["choose"] == 2

        # A character links to seeded style/role and passes number bounds
        character = await create_entry(client, system, "character", "Zara Vex", {
            "style": "lasers-feelings-style-hot-shot",
            "role": "lasers-feelings-role-pilot",
            "number": 4,
            "goal": "Prove yourself to the Consortium",
            "gear": ["Blaster", "Comm bracelet"],
        })
        assert character["guid"] == "lasers-feelings-character-zara-vex"
        assert character["data"]["number"] == 4
        assert character["data"]["gear"] == ["Blaster", "Comm bracelet"]

        # Browsing works: styles listable by type filter
        resp = await client.get("/api/compendium/", params={
            "system": system, "entry_type": "style",
        })
        assert resp.json()["total"] == 6

    async def test_template_validation_enforced(self, client):
        system = await define_system(client)
        await define_templates(client, system)

        # number outside 2-5 rejected with a field-level detail
        resp = await client.post("/api/compendium/", json={
            "system": system, "entry_type": "character", "name": "Broken",
            "data": {"name": "Broken",
                     "style": "lasers-feelings-style-alien",
                     "role": "lasers-feelings-role-doctor",
                     "number": 6, "goal": "Nope"},
        })
        assert resp.status_code == 400
        details = resp.json()["error"]["details"]
        assert any(d["field"] == "number" for d in details)

        # too many gear items rejected
        resp = await client.post("/api/compendium/", json={
            "system": system, "entry_type": "character", "name": "Hoarder",
            "data": {"name": "Hoarder",
                     "style": "lasers-feelings-style-alien",
                     "role": "lasers-feelings-role-doctor",
                     "number": 3, "goal": "Carry everything",
                     "gear": ["a", "b", "c", "d"]},
        })
        assert resp.status_code == 400

        # incoherent choice (options fewer than choose) rejected
        resp = await client.post("/api/compendium/", json={
            "system": system, "entry_type": "ship", "name": "Bad Ship",
            "data": {"name": "Bad Ship",
                     "strengths": {"choose": 2,
                                   "options": ["lasers-feelings-ship-strength-fast"]}},
        })
        assert resp.status_code == 400

    async def test_templates_editable_after_creation(self, client):
        system = await define_system(client)
        await define_templates(client, system)

        # Loosen the character number range in the "editor" (PUT), like the UI does
        resp = await client.get(f"/api/templates/{system}/character")
        fields = resp.json()["fields"]
        for field in fields:
            if field["name"] == "number":
                field["params"]["max_val"] = 6
        resp = await client.put(f"/api/templates/{system}/character",
                                json={"fields": fields})
        assert resp.status_code == 200, resp.text

        await create_entry(client, system, "style", "Alien", {})
        await create_entry(client, system, "role", "Doctor", {})
        entry = await create_entry(client, system, "character", "Sixer", {
            "style": "lasers-feelings-style-alien",
            "role": "lasers-feelings-role-doctor",
            "number": 6,
            "goal": "Push the limits",
        })
        assert entry["data"]["number"] == 6
