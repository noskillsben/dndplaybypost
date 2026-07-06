def assert_envelope(body):
    assert set(body.keys()) == {"error"}
    assert set(body["error"].keys()) == {"code", "message", "details"}


class TestErrorEnvelope:
    async def test_404_envelope(self, client):
        resp = await client.get("/api/compendium/nope-nope-nope")
        assert resp.status_code == 404
        body = resp.json()
        assert_envelope(body)
        assert body["error"]["code"] == "not_found"
        assert body["error"]["message"] == "Entry not found"

    async def test_schema_validation_envelope_with_field_details(self, client):
        resp = await client.post("/api/compendium/", json={
            "system": "d&d5.0",
            "entry_type": "spell",
            "name": "Broken Spell",
            "data": {"name": "Broken Spell", "level": 99},
        })
        assert resp.status_code == 400
        body = resp.json()
        assert_envelope(body)
        assert body["error"]["code"] == "validation_error"
        fields = [d["field"] for d in body["error"]["details"]]
        assert "level" in fields
        assert "level" in body["error"]["message"]

    async def test_missing_required_field_named_in_details(self, client):
        resp = await client.post("/api/compendium/", json={
            "system": "d&d5.0",
            "entry_type": "spell",
            "name": "No Level",
            "data": {"name": "No Level"},
        })
        assert resp.status_code == 400
        details = resp.json()["error"]["details"]
        assert any(d["field"] == "level" for d in details)

    async def test_request_validation_envelope(self, client):
        resp = await client.get("/api/compendium/", params={"limit": 0})
        assert resp.status_code == 422
        body = resp.json()
        assert_envelope(body)
        assert body["error"]["code"] == "validation_error"
        assert any(d["field"] == "query.limit" for d in body["error"]["details"])

    async def test_bad_request_envelope(self, client):
        resp = await client.post("/api/compendium/", json={
            "system": "not-a-system",
            "entry_type": "spell",
            "name": "X",
            "data": {"name": "X"},
        })
        assert resp.status_code == 400
        body = resp.json()
        assert_envelope(body)
        assert body["error"]["code"] == "bad_request"
        assert body["error"]["message"] == "Invalid system"
