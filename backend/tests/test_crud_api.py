async def create_spell(client, name="Fire Bolt", level=0, **overrides):
    payload = {
        "system": "d&d5.0",
        "entry_type": "spell",
        "name": name,
        "data": {"name": name, "level": level, "school": "Evocation"},
        "homebrew": True,
        "source": {"name": "Test Suite"},
    }
    payload.update(overrides)
    resp = await client.post("/api/compendium/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestPut:
    async def test_replaces_content(self, client):
        entry = await create_spell(client)
        resp = await client.put(f"/api/compendium/{entry['guid']}", json={
            "name": "Fire Bolt",
            "data": {"name": "Fire Bolt", "level": 1, "school": "Conjuration"},
            "homebrew": False,
            "source": {"name": "SRD"},
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["guid"] == entry["guid"]
        assert body["data"]["level"] == 1
        assert body["data"]["school"] == "Conjuration"
        assert body["homebrew"] is False
        assert body["source"] == {"name": "SRD"}

    async def test_invalid_data_rejected(self, client):
        entry = await create_spell(client)
        resp = await client.put(f"/api/compendium/{entry['guid']}", json={
            "name": "Fire Bolt",
            "data": {"name": "Fire Bolt", "level": 99},
        })
        assert resp.status_code == 400
        assert "level" in resp.json()["error"]["message"]

    async def test_missing_required_field_rejected(self, client):
        entry = await create_spell(client)
        resp = await client.put(f"/api/compendium/{entry['guid']}", json={
            "name": "Fire Bolt",
            "data": {"name": "Fire Bolt"},
        })
        assert resp.status_code == 400

    async def test_unknown_parent_rejected(self, client):
        entry = await create_spell(client)
        resp = await client.put(f"/api/compendium/{entry['guid']}", json={
            "name": "Fire Bolt",
            "data": {"name": "Fire Bolt", "level": 0},
            "parent_guid": "d&d5.0-spell-nope",
        })
        assert resp.status_code == 400

    async def test_self_parent_rejected(self, client):
        entry = await create_spell(client)
        resp = await client.put(f"/api/compendium/{entry['guid']}", json={
            "name": "Fire Bolt",
            "data": {"name": "Fire Bolt", "level": 0},
            "parent_guid": entry["guid"],
        })
        assert resp.status_code == 400

    async def test_missing_entry_404(self, client):
        resp = await client.put("/api/compendium/d&d5.0-spell-nope", json={
            "name": "X",
            "data": {"name": "X", "level": 0},
        })
        assert resp.status_code == 404


class TestPatch:
    async def test_partial_data_merge(self, client):
        entry = await create_spell(client)
        resp = await client.patch(f"/api/compendium/{entry['guid']}", json={
            "data": {"level": 3}
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["level"] == 3
        assert body["data"]["school"] == "Evocation"
        assert body["name"] == "Fire Bolt"

    async def test_name_only(self, client):
        entry = await create_spell(client)
        resp = await client.patch(f"/api/compendium/{entry['guid']}", json={
            "name": "Firebolt"
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Firebolt"
        assert body["data"]["name"] == "Firebolt"
        assert body["guid"] == entry["guid"]

    async def test_metadata_only(self, client):
        entry = await create_spell(client)
        resp = await client.patch(f"/api/compendium/{entry['guid']}", json={
            "homebrew": False,
            "source": {"name": "SRD", "page": 12},
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["homebrew"] is False
        assert body["source"] == {"name": "SRD", "page": 12}
        assert body["data"]["level"] == 0

    async def test_invalid_merged_data_rejected(self, client):
        entry = await create_spell(client)
        resp = await client.patch(f"/api/compendium/{entry['guid']}", json={
            "data": {"level": -1}
        })
        assert resp.status_code == 400

    async def test_parent_can_be_cleared(self, client):
        parent = await create_spell(client, name="Parent Spell", level=1)
        child = await create_spell(client, name="Child Spell", level=1,
                                   parent_guid=parent["guid"])
        assert child["parent_guid"] == parent["guid"]
        resp = await client.patch(f"/api/compendium/{child['guid']}", json={
            "parent_guid": None
        })
        assert resp.status_code == 200
        assert resp.json()["parent_guid"] is None

    async def test_follows_rename_redirect(self, client):
        entry = await create_spell(client)
        await client.post(
            f"/api/compendium/{entry['guid']}/rename", json={"new_name": "Scorch"}
        )
        resp = await client.patch(f"/api/compendium/{entry['guid']}", json={
            "data": {"level": 2}
        })
        assert resp.status_code == 200
        assert resp.json()["guid"] == "d&d5.0-spell-scorch"
        assert resp.json()["data"]["level"] == 2

    async def test_missing_entry_404(self, client):
        resp = await client.patch("/api/compendium/d&d5.0-spell-nope", json={
            "name": "X"
        })
        assert resp.status_code == 404


class TestDelete:
    async def test_delete_removes_entry(self, client):
        entry = await create_spell(client)
        resp = await client.delete(f"/api/compendium/{entry['guid']}")
        assert resp.status_code == 204
        get_resp = await client.get(f"/api/compendium/{entry['guid']}")
        assert get_resp.status_code == 404

    async def test_delete_missing_404(self, client):
        resp = await client.delete("/api/compendium/d&d5.0-spell-nope")
        assert resp.status_code == 404
