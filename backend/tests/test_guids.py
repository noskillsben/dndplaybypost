import pytest
from sqlalchemy import select

from core import guids
from models.compendium import CompendiumEntry, GuidRedirect


def rule_payload(name, **overrides):
    payload = {
        "system": "d&d5.0",
        "entry_type": "rule",
        "name": name,
        "data": {"name": name},
    }
    payload.update(overrides)
    return payload


class TestSlugify:
    def test_basic(self):
        assert guids.slugify("Slashing") == "slashing"

    def test_spaces_and_case(self):
        assert guids.slugify("Damage Types") == "damage-types"

    def test_special_characters(self):
        assert guids.slugify("Mage's Hand (v2)!") == "mage-s-hand-v2"

    def test_unicode_folded(self):
        assert guids.slugify("Café Noël") == "cafe-noel"

    def test_collapses_runs_and_trims(self):
        assert guids.slugify("  --Fire  //  Ball--  ") == "fire-ball"

    def test_empty_falls_back(self):
        assert guids.slugify("!!!") == "entry"


class TestBuildGuid:
    def test_basic(self):
        assert guids.build_guid("d&d5.0", "rule", "Slashing") == "d&d5.0-rule-slashing"

    def test_with_suffix(self):
        assert (
            guids.build_guid("d&d5.0", "item", "Longsword", suffix="SRD")
            == "d&d5.0-item-longsword-srd"
        )


class TestGenerateUniqueGuid:
    async def test_no_collision(self, db_session):
        guid = await guids.generate_unique_guid(db_session, "sys", "thing", "Foo")
        assert guid == "sys-thing-foo"

    async def test_collision_appends_counter(self, db_session):
        db_session.add(CompendiumEntry(
            guid="sys-thing-foo", system="sys", entry_type="thing",
            name="Foo", data={},
        ))
        await db_session.commit()
        guid = await guids.generate_unique_guid(db_session, "sys", "thing", "Foo")
        assert guid == "sys-thing-foo-2"

    async def test_redirect_records_count_as_collisions(self, db_session):
        db_session.add(GuidRedirect(old_guid="sys-thing-foo", new_guid="sys-thing-bar"))
        await db_session.commit()
        guid = await guids.generate_unique_guid(db_session, "sys", "thing", "Foo")
        assert guid == "sys-thing-foo-2"


class TestCreateEndpointGuids:
    async def test_auto_generated_guid_is_slugified(self, client):
        resp = await client.post("/api/compendium/", json=rule_payload("Bludgeoning (Special)"))
        assert resp.status_code == 201
        assert resp.json()["guid"] == "d&d5.0-rule-bludgeoning-special"

    async def test_custom_suffix(self, client):
        resp = await client.post(
            "/api/compendium/", json=rule_payload("Slashing", guid_suffix="srd")
        )
        assert resp.status_code == 201
        assert resp.json()["guid"] == "d&d5.0-rule-slashing-srd"

    async def test_collision_auto_increments(self, client):
        first = await client.post("/api/compendium/", json=rule_payload("Slashing"))
        second = await client.post("/api/compendium/", json=rule_payload("Slashing"))
        assert first.json()["guid"] == "d&d5.0-rule-slashing"
        assert second.status_code == 201
        assert second.json()["guid"] == "d&d5.0-rule-slashing-2"

    async def test_custom_guid_conflict_rejected(self, client):
        await client.post("/api/compendium/", json=rule_payload("Slashing"))
        resp = await client.post(
            "/api/compendium/", json=rule_payload("Other", guid="d&d5.0-rule-slashing")
        )
        assert resp.status_code == 400


class TestRename:
    async def test_rename_creates_redirect_and_new_guid(self, client, db_session):
        created = await client.post("/api/compendium/", json=rule_payload("Slashing"))
        old_guid = created.json()["guid"]

        resp = await client.post(
            f"/api/compendium/{old_guid}/rename", json={"new_name": "Slicing"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["guid"] == "d&d5.0-rule-slicing"
        assert body["name"] == "Slicing"

        redirect = (await db_session.execute(
            select(GuidRedirect).where(GuidRedirect.old_guid == old_guid)
        )).scalar_one()
        assert redirect.new_guid == "d&d5.0-rule-slicing"

    async def test_old_guid_still_resolves_via_get(self, client):
        created = await client.post("/api/compendium/", json=rule_payload("Slashing"))
        old_guid = created.json()["guid"]
        await client.post(f"/api/compendium/{old_guid}/rename", json={"new_name": "Slicing"})

        resp = await client.get(f"/api/compendium/{old_guid}")
        assert resp.status_code == 200
        assert resp.json()["guid"] == "d&d5.0-rule-slicing"

    async def test_children_are_reparented(self, client):
        parent = await client.post("/api/compendium/", json=rule_payload("Damage Types"))
        parent_guid = parent.json()["guid"]
        child = await client.post(
            "/api/compendium/", json=rule_payload("Slashing", parent_guid=parent_guid)
        )
        assert child.status_code == 201

        await client.post(
            f"/api/compendium/{parent_guid}/rename", json={"new_name": "Damage Kinds"}
        )
        resp = await client.get(f"/api/compendium/{child.json()['guid']}")
        assert resp.json()["parent_guid"] == "d&d5.0-rule-damage-kinds"

    async def test_redirect_chains_are_flattened(self, client, db_session):
        created = await client.post("/api/compendium/", json=rule_payload("One"))
        guid_one = created.json()["guid"]
        await client.post(f"/api/compendium/{guid_one}/rename", json={"new_name": "Two"})
        await client.post("/api/compendium/d&d5.0-rule-two/rename", json={"new_name": "Three"})

        redirect = (await db_session.execute(
            select(GuidRedirect).where(GuidRedirect.old_guid == guid_one)
        )).scalar_one()
        assert redirect.new_guid == "d&d5.0-rule-three"

        resp = await client.get(f"/api/compendium/{guid_one}")
        assert resp.json()["guid"] == "d&d5.0-rule-three"

    async def test_rename_missing_entry_404(self, client):
        resp = await client.post(
            "/api/compendium/d&d5.0-rule-nope/rename", json={"new_name": "X"}
        )
        assert resp.status_code == 404

    async def test_rename_same_name_keeps_guid(self, client, db_session):
        created = await client.post("/api/compendium/", json=rule_payload("Slashing"))
        guid = created.json()["guid"]
        resp = await client.post(f"/api/compendium/{guid}/rename", json={"new_name": "Slashing"})
        assert resp.status_code == 200
        assert resp.json()["guid"] == guid
        redirects = (await db_session.execute(select(GuidRedirect))).scalars().all()
        assert redirects == []
