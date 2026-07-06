async def test_health(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}


async def test_root(client):
    res = await client.get("/")
    assert res.status_code == 200
    assert "running" in res.json()["message"]


async def test_schemas_listed(client):
    res = await client.get("/api/schemas/systems")
    assert res.status_code == 200
    assert "d&d5.0" in res.json()["systems"]
