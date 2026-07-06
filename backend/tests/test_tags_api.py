async def create_spell(client, name="Fire Bolt", tags=None, **overrides):
    payload = {
        "system": "d&d5.0",
        "entry_type": "spell",
        "name": name,
        "data": {"name": name, "level": 0, "school": "Evocation"},
    }
    if tags is not None:
        payload["tags"] = tags
    payload.update(overrides)
    resp = await client.post("/api/compendium/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestTagWrites:
    async def test_create_with_tags_normalized(self, client):
        entry = await create_spell(client, tags=["Fire", "Area of Effect", "fire", "  "])
        assert entry["tags"] == ["fire", "area-of-effect"]

    async def test_create_without_tags_defaults_empty(self, client):
        entry = await create_spell(client)
        assert entry["tags"] == []

    async def test_put_replaces_tags(self, client):
        entry = await create_spell(client, tags=["fire"])
        resp = await client.put(f"/api/compendium/{entry['guid']}", json={
            "name": "Fire Bolt",
            "data": {"name": "Fire Bolt", "level": 0, "school": "Evocation"},
            "tags": ["Cold"],
        })
        assert resp.status_code == 200
        assert resp.json()["tags"] == ["cold"]

    async def test_put_without_tags_clears(self, client):
        entry = await create_spell(client, tags=["fire"])
        resp = await client.put(f"/api/compendium/{entry['guid']}", json={
            "name": "Fire Bolt",
            "data": {"name": "Fire Bolt", "level": 0, "school": "Evocation"},
        })
        assert resp.status_code == 200
        assert resp.json()["tags"] == []

    async def test_patch_updates_only_tags(self, client):
        entry = await create_spell(client, tags=["fire"])
        resp = await client.patch(f"/api/compendium/{entry['guid']}", json={"tags": ["fire", "cantrip"]})
        assert resp.status_code == 200
        body = resp.json()
        assert body["tags"] == ["fire", "cantrip"]
        assert body["data"]["school"] == "Evocation"

    async def test_patch_without_tags_preserves(self, client):
        entry = await create_spell(client, tags=["fire"])
        resp = await client.patch(f"/api/compendium/{entry['guid']}", json={"data": {"level": 1}})
        assert resp.status_code == 200
        assert resp.json()["tags"] == ["fire"]

    async def test_rename_preserves_tags(self, client):
        entry = await create_spell(client, tags=["fire"])
        resp = await client.post(f"/api/compendium/{entry['guid']}/rename", json={"new_name": "Frost Bolt"})
        assert resp.status_code == 200
        assert resp.json()["tags"] == ["fire"]


class TestTagFiltering:
    async def test_filter_by_single_tag(self, client):
        await create_spell(client, name="Fireball", tags=["fire", "aoe"])
        await create_spell(client, name="Ray of Frost", tags=["cold"])
        resp = await client.get("/api/compendium/", params={"tag": "fire"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["entries"][0]["name"] == "Fireball"

    async def test_filter_multiple_tags_is_and(self, client):
        await create_spell(client, name="Fireball", tags=["fire", "aoe"])
        await create_spell(client, name="Fire Bolt", tags=["fire"])
        resp = await client.get("/api/compendium/", params=[("tag", "fire"), ("tag", "aoe")])
        body = resp.json()
        assert body["total"] == 1
        assert body["entries"][0]["name"] == "Fireball"

    async def test_filter_is_exact_not_substring(self, client):
        await create_spell(client, name="Fireball", tags=["fireball"])
        resp = await client.get("/api/compendium/", params={"tag": "fire"})
        assert resp.json()["total"] == 0

    async def test_filter_input_normalized(self, client):
        await create_spell(client, name="Longsword", tags=["Martial Weapon"])
        resp = await client.get("/api/compendium/", params={"tag": "Martial Weapon"})
        assert resp.json()["total"] == 1

    async def test_combines_with_other_filters(self, client):
        await create_spell(client, name="Fireball", tags=["fire"])
        await create_spell(client, name="Flame Blade", tags=["fire"])
        resp = await client.get("/api/compendium/", params={"tag": "fire", "search": "ball"})
        body = resp.json()
        assert body["total"] == 1
        assert body["entries"][0]["name"] == "Fireball"
