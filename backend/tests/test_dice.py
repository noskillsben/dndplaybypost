import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_roll_simple_die(client: AsyncClient):
    """Test rolling a simple die"""
    response = await client.post(
        "/api/dice/roll",
        json={"expression": "1d20"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["expression"] == "1d20"
    assert 1 <= data["total"] <= 20
    assert len(data["rolls"]) == 1
    assert 1 <= data["rolls"][0] <= 20
    assert "breakdown" in data


@pytest.mark.asyncio
async def test_roll_with_positive_modifier(client: AsyncClient):
    """Test rolling with positive modifier"""
    response = await client.post(
        "/api/dice/roll",
        json={"expression": "1d20+5"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["expression"] == "1d20+5"
    assert 6 <= data["total"] <= 25
    assert "+5" in data["breakdown"]


@pytest.mark.asyncio
async def test_roll_with_negative_modifier(client: AsyncClient):
    """Test rolling with negative modifier"""
    response = await client.post(
        "/api/dice/roll",
        json={"expression": "1d20-2"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["expression"] == "1d20-2"
    assert -1 <= data["total"] <= 18
    assert "-2" in data["breakdown"]


@pytest.mark.asyncio
async def test_roll_multiple_dice(client: AsyncClient):
    """Test rolling multiple dice"""
    response = await client.post(
        "/api/dice/roll",
        json={"expression": "2d6"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["expression"] == "2d6"
    assert 2 <= data["total"] <= 12
    assert len(data["rolls"]) == 2
    assert all(1 <= roll <= 6 for roll in data["rolls"])


@pytest.mark.asyncio
async def test_roll_invalid_expression(client: AsyncClient):
    """Test rolling with invalid expression"""
    response = await client.post(
        "/api/dice/roll",
        json={"expression": "invalid"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_roll_too_many_dice(client: AsyncClient):
    """Test rolling too many dice"""
    response = await client.post(
        "/api/dice/roll",
        json={"expression": "101d6"}
    )
    assert response.status_code == 400
    assert "Number of dice" in response.json()["detail"]


@pytest.mark.asyncio
async def test_roll_invalid_die_size(client: AsyncClient):
    """Test rolling invalid die size"""
    response = await client.post(
        "/api/dice/roll",
        json={"expression": "1d1001"}
    )
    assert response.status_code == 400
    assert "Die size" in response.json()["detail"]


@pytest.mark.asyncio
async def test_roll_multiple_expressions(client: AsyncClient):
    """Test rolling multiple expressions at once"""
    response = await client.post(
        "/api/dice/roll/multiple",
        json={"expressions": ["1d20+5", "2d6", "1d8+3"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["expression"] == "1d20+5"
    assert data[1]["expression"] == "2d6"
    assert data[2]["expression"] == "1d8+3"
