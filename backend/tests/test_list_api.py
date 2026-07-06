async def create_rule(client, name, **overrides):
    payload = {
        "system": "d&d5.0",
        "entry_type": "rule",
        "name": name,
        "data": {"name": name},
    }
    payload.update(overrides)
    resp = await client.post("/api/compendium/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def seed_damage_types(client):
    root = await create_rule(client, "Damage Types")
    for name in ["Slashing", "Piercing", "Bludgeoning"]:
        await create_rule(client, name, parent_guid=root["guid"])
    return root


class TestFilters:
    async def test_guid_prefix(self, client):
        await seed_damage_types(client)
        await create_rule(client, "Conditions", guid="d&d5.0-condition-list")

        resp = await client.get("/api/compendium/", params={"guid_prefix": "d&d5.0-rule-"})
        body = resp.json()
        assert body["total"] == 4
        assert all(e["guid"].startswith("d&d5.0-rule-") for e in body["entries"])

    async def test_guid_prefix_no_match(self, client):
        await seed_damage_types(client)
        resp = await client.get("/api/compendium/", params={"guid_prefix": "other-sys-"})
        assert resp.json()["total"] == 0

    async def test_guid_prefix_wildcards_escaped(self, client):
        await seed_damage_types(client)
        resp = await client.get("/api/compendium/", params={"guid_prefix": "d&d5.0-rule-%"})
        assert resp.json()["total"] == 0

    async def test_parent_guid(self, client):
        root = await seed_damage_types(client)
        resp = await client.get("/api/compendium/", params={"parent_guid": root["guid"]})
        body = resp.json()
        assert body["total"] == 3
        assert {e["name"] for e in body["entries"]} == {
            "Slashing", "Piercing", "Bludgeoning",
        }

    async def test_parent_guid_null_for_top_level(self, client):
        await seed_damage_types(client)
        resp = await client.get("/api/compendium/", params={"parent_guid": "null"})
        body = resp.json()
        assert body["total"] == 1
        assert body["entries"][0]["name"] == "Damage Types"

    async def test_search_on_name(self, client):
        await seed_damage_types(client)
        resp = await client.get("/api/compendium/", params={"search": "slash"})
        body = resp.json()
        assert body["total"] == 1
        assert body["entries"][0]["name"] == "Slashing"

    async def test_homebrew_filter(self, client):
        await create_rule(client, "Official Rule", homebrew=False)
        await create_rule(client, "House Rule", homebrew=True)
        resp = await client.get("/api/compendium/", params={"homebrew": "true"})
        body = resp.json()
        assert body["total"] == 1
        assert body["entries"][0]["name"] == "House Rule"

    async def test_filters_combine(self, client):
        root = await seed_damage_types(client)
        resp = await client.get("/api/compendium/", params={
            "parent_guid": root["guid"],
            "search": "ing",
            "system": "d&d5.0",
        })
        assert resp.json()["total"] == 3


class TestPagination:
    async def test_limit_and_total(self, client):
        await seed_damage_types(client)
        resp = await client.get("/api/compendium/", params={"limit": 2})
        body = resp.json()
        assert len(body["entries"]) == 2
        assert body["total"] == 4
        assert body["limit"] == 2
        assert body["offset"] == 0

    async def test_offset_pages_through_ordered_names(self, client):
        await seed_damage_types(client)
        page1 = (await client.get("/api/compendium/", params={"limit": 2, "offset": 0})).json()
        page2 = (await client.get("/api/compendium/", params={"limit": 2, "offset": 2})).json()
        names = [e["name"] for e in page1["entries"] + page2["entries"]]
        assert names == ["Bludgeoning", "Damage Types", "Piercing", "Slashing"]

    async def test_offset_past_end_returns_empty(self, client):
        await seed_damage_types(client)
        resp = await client.get("/api/compendium/", params={"offset": 10})
        body = resp.json()
        assert body["entries"] == []
        assert body["total"] == 4

    async def test_invalid_limit_rejected(self, client):
        resp = await client.get("/api/compendium/", params={"limit": 0})
        assert resp.status_code == 422

    async def test_invalid_offset_rejected(self, client):
        resp = await client.get("/api/compendium/", params={"offset": -1})
        assert resp.status_code == 422
