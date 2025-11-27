import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_character(client: AsyncClient, auth_token, test_campaign):
    """Test creating a character"""
    response = await client.post(
        "/api/characters",
        json={
            "campaign_id": str(test_campaign.id),
            "name": "Aragorn",
            "sheet_data": {
                "class": "Ranger",
                "level": 5,
                "race": "Human"
            },
            "notes": "Strider"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Aragorn"
    assert data["sheet_data"]["class"] == "Ranger"
    assert data["notes"] == "Strider"


@pytest.mark.asyncio
async def test_create_character_minimal(client: AsyncClient, auth_token, test_campaign):
    """Test creating character with minimal data"""
    response = await client.post(
        "/api/characters",
        json={
            "campaign_id": str(test_campaign.id),
            "name": "Simple Character",
            "sheet_data": {}
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Simple Character"
    assert data["sheet_data"] == {}
    assert data["notes"] is None


@pytest.mark.asyncio
async def test_create_character_campaign_not_found(client: AsyncClient, auth_token):
    """Test creating character in non-existent campaign"""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.post(
        "/api/characters",
        json={
            "campaign_id": str(fake_id),
            "name": "Test",
            "sheet_data": {}
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_character_not_member(client: AsyncClient, auth_token2, test_campaign):
    """Test creating character in campaign where user is not a member"""
    response = await client.post(
        "/api/characters",
        json={
            "campaign_id": str(test_campaign.id),
            "name": "Hacker",
            "sheet_data": {}
        },
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_character_unauthorized(client: AsyncClient, test_campaign):
    """Test creating character without auth"""
    response = await client.post(
        "/api/characters",
        json={
            "campaign_id": str(test_campaign.id),
            "name": "Test",
            "sheet_data": {}
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_characters(client: AsyncClient, auth_token, test_character):
    """Test listing user's characters"""
    response = await client.get(
        "/api/characters",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(c["id"] == str(test_character.id) for c in data)


@pytest.mark.asyncio
async def test_list_characters_empty(client: AsyncClient, auth_token2):
    """Test listing characters when user has none"""
    response = await client.get(
        "/api/characters",
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_characters_by_campaign(client: AsyncClient, auth_token, test_campaign, test_character):
    """Test listing characters filtered by campaign"""
    response = await client.get(
        f"/api/characters?campaign_id={test_campaign.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert all(c["campaign_id"] == str(test_campaign.id) for c in data)


@pytest.mark.asyncio
async def test_list_characters_by_campaign_not_member(client: AsyncClient, auth_token2, test_campaign):
    """Test listing characters for campaign where not a member"""
    response = await client.get(
        f"/api/characters?campaign_id={test_campaign.id}",
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_character(client: AsyncClient, auth_token, test_character):
    """Test getting character details"""
    response = await client.get(
        f"/api/characters/{test_character.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_character.id)
    assert data["name"] == test_character.name


@pytest.mark.asyncio
async def test_get_character_not_found(client: AsyncClient, auth_token):
    """Test getting non-existent character"""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.get(
        f"/api/characters/{fake_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_character_not_member(client: AsyncClient, auth_token2, test_character):
    """Test getting character when not campaign member"""
    response = await client.get(
        f"/api/characters/{test_character.id}",
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_character_as_owner(client: AsyncClient, auth_token, test_character):
    """Test updating character as owner"""
    response = await client.patch(
        f"/api/characters/{test_character.id}",
        json={
            "name": "Updated Name",
            "sheet_data": {"class": "Wizard", "level": 2}
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["sheet_data"]["class"] == "Wizard"


@pytest.mark.asyncio
async def test_update_character_partial(client: AsyncClient, auth_token, test_character):
    """Test partial character update"""
    response = await client.patch(
        f"/api/characters/{test_character.id}",
        json={"notes": "New notes only"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "New notes only"
    assert data["name"] == test_character.name  # Unchanged


@pytest.mark.asyncio
async def test_update_character_as_dm(client: AsyncClient, auth_token, test_character):
    """Test updating character as DM"""
    response = await client.patch(
        f"/api/characters/{test_character.id}",
        json={"notes": "DM notes added"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "DM notes added"


@pytest.mark.asyncio
async def test_update_character_not_found(client: AsyncClient, auth_token):
    """Test updating non-existent character"""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.patch(
        f"/api/characters/{fake_id}",
        json={"name": "Test"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_character_unauthorized(client: AsyncClient, auth_token2, test_character):
    """Test updating character when not authorized"""
    response = await client.patch(
        f"/api/characters/{test_character.id}",
        json={"name": "Hacked"},
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_character_as_owner(client: AsyncClient, auth_token, test_character):
    """Test deleting character as owner"""
    response = await client.delete(
        f"/api/characters/{test_character.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_character_not_found(client: AsyncClient, auth_token):
    """Test deleting non-existent character"""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.delete(
        f"/api/characters/{fake_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_character_unauthorized(client: AsyncClient, auth_token2, test_character):
    """Test deleting character when not authorized"""
    response = await client.delete(
        f"/api/characters/{test_character.id}",
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 403
