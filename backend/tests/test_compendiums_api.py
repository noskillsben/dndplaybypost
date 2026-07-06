async def create_compendium(client, name="Test Compendium", system="d&d5.0", **overrides):
    payload = {"name": name, "system": system}
    payload.update(overrides)
    resp = await client.post("/api/compendiums", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def create_spell(client, name="Fire Bolt", **overrides):
    payload = {
        "system": "d&d5.0",
        "entry_type": "spell",
        "name": name,
        "data": {"name": name, "level": 0, "school": "Evocation"},
    }
    payload.update(overrides)
    resp = await client.post("/api/compendium/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestCompendiumCrud:
    async def test_create_slugifies_guid(self, client):
        comp = await create_compendium(client, name="Ben's Homebrew")
        assert comp["guid"] == "ben-s-homebrew"
        assert comp["name"] == "Ben's Homebrew"
        assert comp["system"] == "d&d5.0"
        assert comp["entry_count"] == 0

    async def test_create_with_custom_guid(self, client):
        comp = await create_compendium(client, guid="srd-2014")
        assert comp["guid"] == "srd-2014"

    async def test_duplicate_guid_rejected(self, client):
        await create_compendium(client, name="Core")
        resp = await client.post("/api/compendiums", json={"name": "Core", "system": "d&d5.0"})
        assert resp.status_code == 400

    async def test_get(self, client):
        comp = await create_compendium(client, description="stuff")
        resp = await client.get(f"/api/compendiums/{comp['guid']}")
        assert resp.status_code == 200
        assert resp.json()["description"] == "stuff"

    async def test_get_missing_404(self, client):
        resp = await client.get("/api/compendiums/nope")
        assert resp.status_code == 404

    async def test_list_filters_by_system(self, client):
        await create_compendium(client, name="Five E", system="d&d5.0")
        await create_compendium(client, name="Lasers", system="lasers-and-feelings")
        resp = await client.get("/api/compendiums", params={"system": "d&d5.0"})
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()["compendiums"]]
        assert names == ["Five E"]

    async def test_patch_updates_name_and_description(self, client):
        comp = await create_compendium(client)
        resp = await client.patch(f"/api/compendiums/{comp['guid']}", json={
            "name": "Renamed", "description": "new desc",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Renamed"
        assert body["description"] == "new desc"
        assert body["guid"] == comp["guid"]

    async def test_delete_empty(self, client):
        comp = await create_compendium(client)
        resp = await client.delete(f"/api/compendiums/{comp['guid']}")
        assert resp.status_code == 204
        resp = await client.get(f"/api/compendiums/{comp['guid']}")
        assert resp.status_code == 404

    async def test_delete_nonempty_blocked(self, client):
        comp = await create_compendium(client)
        await create_spell(client, compendium_guid=comp["guid"])
        resp = await client.delete(f"/api/compendiums/{comp['guid']}")
        assert resp.status_code == 409


class TestEntryMembership:
    async def test_entry_created_in_compendium(self, client):
        comp = await create_compendium(client)
        entry = await create_spell(client, compendium_guid=comp["guid"])
        assert entry["compendium_guid"] == comp["guid"]
        resp = await client.get(f"/api/compendiums/{comp['guid']}")
        assert resp.json()["entry_count"] == 1

    async def test_entry_unknown_compendium_rejected(self, client):
        resp = await client.post("/api/compendium/", json={
            "system": "d&d5.0",
            "entry_type": "spell",
            "name": "Zap",
            "data": {"name": "Zap", "level": 0, "school": "Evocation"},
            "compendium_guid": "nope",
        })
        assert resp.status_code == 400

    async def test_list_entries_filtered_by_compendium(self, client):
        comp_a = await create_compendium(client, name="A")
        comp_b = await create_compendium(client, name="B")
        await create_spell(client, name="Alpha Bolt", compendium_guid=comp_a["guid"])
        await create_spell(client, name="Beta Bolt", compendium_guid=comp_b["guid"])
        await create_spell(client, name="Loose Bolt")

        resp = await client.get("/api/compendium/", params={"compendium": comp_a["guid"]})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["entries"][0]["name"] == "Alpha Bolt"

    async def test_patch_moves_entry_between_compendiums(self, client):
        comp_a = await create_compendium(client, name="A")
        comp_b = await create_compendium(client, name="B")
        entry = await create_spell(client, compendium_guid=comp_a["guid"])
        resp = await client.patch(f"/api/compendium/{entry['guid']}", json={
            "compendium_guid": comp_b["guid"],
        })
        assert resp.status_code == 200
        assert resp.json()["compendium_guid"] == comp_b["guid"]

    async def test_patch_can_clear_compendium(self, client):
        comp = await create_compendium(client)
        entry = await create_spell(client, compendium_guid=comp["guid"])
        resp = await client.patch(f"/api/compendium/{entry['guid']}", json={
            "compendium_guid": None,
        })
        assert resp.status_code == 200
        assert resp.json()["compendium_guid"] is None

    async def test_rename_preserves_compendium(self, client):
        comp = await create_compendium(client)
        entry = await create_spell(client, compendium_guid=comp["guid"])
        resp = await client.post(f"/api/compendium/{entry['guid']}/rename", json={
            "new_name": "Frost Bolt",
        })
        assert resp.status_code == 200
        assert resp.json()["compendium_guid"] == comp["guid"]
