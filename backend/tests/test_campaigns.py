import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_campaign(client: AsyncClient, auth_token):
    """Test creating a campaign"""
    response = await client.post(
        "/api/campaigns",
        json={
            "name": "New Campaign",
            "description": "A new test campaign",
            "settings": {"house_rules": "No evil characters"}
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Campaign"
    assert data["description"] == "A new test campaign"
    assert len(data["members"]) == 1
    assert data["members"][0]["role"] == "dm"


@pytest.mark.asyncio
async def test_create_campaign_minimal(client: AsyncClient, auth_token):
    """Test creating campaign with minimal data"""
    response = await client.post(
        "/api/campaigns",
        json={"name": "Minimal Campaign"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Minimal Campaign"
    assert data["description"] is None
    assert data["settings"] == {}


@pytest.mark.asyncio
async def test_create_campaign_unauthorized(client: AsyncClient):
    """Test creating campaign without auth"""
    response = await client.post(
        "/api/campaigns",
        json={"name": "Test Campaign"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_campaigns(client: AsyncClient, auth_token, test_campaign):
    """Test listing user's campaigns"""
    response = await client.get(
        "/api/campaigns",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(c["id"] == str(test_campaign.id) for c in data)


@pytest.mark.asyncio
async def test_list_campaigns_empty(client: AsyncClient, auth_token2):
    """Test listing campaigns when user has none"""
    response = await client.get(
        "/api/campaigns",
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_campaign(client: AsyncClient, auth_token, test_campaign):
    """Test getting campaign details"""
    response = await client.get(
        f"/api/campaigns/{test_campaign.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_campaign.id)
    assert data["name"] == test_campaign.name


@pytest.mark.asyncio
async def test_get_campaign_not_found(client: AsyncClient, auth_token):
    """Test getting non-existent campaign"""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.get(
        f"/api/campaigns/{fake_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_campaign_not_member(client: AsyncClient, auth_token2, test_campaign):
    """Test getting campaign when not a member"""
    response = await client.get(
        f"/api/campaigns/{test_campaign.id}",
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_campaign(client: AsyncClient, auth_token, test_campaign):
    """Test updating campaign as DM"""
    response = await client.patch(
        f"/api/campaigns/{test_campaign.id}",
        json={"name": "Updated Campaign Name"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Campaign Name"


@pytest.mark.asyncio
async def test_update_campaign_all_fields(client: AsyncClient, auth_token, test_campaign):
    """Test updating all campaign fields"""
    response = await client.patch(
        f"/api/campaigns/{test_campaign.id}",
        json={
            "name": "New Name",
            "description": "New Description",
            "settings": {"new_rule": "value"}
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "New Description"
    assert data["settings"]["new_rule"] == "value"


@pytest.mark.asyncio
async def test_update_campaign_not_found(client: AsyncClient, auth_token):
    """Test updating non-existent campaign"""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.patch(
        f"/api/campaigns/{fake_id}",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_campaign_not_dm(client: AsyncClient, auth_token2, test_campaign, test_db, test_user2):
    """Test updating campaign when not DM"""
    from models.campaign_member import CampaignMember, RoleEnum
    
    # Add user2 as player
    member = CampaignMember(
        campaign_id=test_campaign.id,
        user_id=test_user2.id,
        role=RoleEnum.PLAYER
    )
    test_db.add(member)
    await test_db.commit()
    
    response = await client.patch(
        f"/api/campaigns/{test_campaign.id}",
        json={"name": "Hacked Name"},
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_campaign(client: AsyncClient, auth_token, test_campaign):
    """Test deleting campaign as DM"""
    response = await client.delete(
        f"/api/campaigns/{test_campaign.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_campaign_not_found(client: AsyncClient, auth_token):
    """Test deleting non-existent campaign"""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.delete(
        f"/api/campaigns/{fake_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_campaign_not_dm(client: AsyncClient, auth_token2, test_campaign, test_db, test_user2):
    """Test deleting campaign when not DM"""
    from models.campaign_member import CampaignMember, RoleEnum
    
    # Add user2 as player
    member = CampaignMember(
        campaign_id=test_campaign.id,
        user_id=test_user2.id,
        role=RoleEnum.PLAYER
    )
    test_db.add(member)
    await test_db.commit()
    
    response = await client.delete(
        f"/api/campaigns/{test_campaign.id}",
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_add_member(client: AsyncClient, auth_token, test_campaign, test_user2):
    """Test adding member to campaign"""
    response = await client.post(
        f"/api/campaigns/{test_campaign.id}/members",
        json={"user_id": str(test_user2.id), "role": "player"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == str(test_user2.id)
    assert data["role"] == "player"


@pytest.mark.asyncio
async def test_add_member_as_dm(client: AsyncClient, auth_token, test_campaign, test_user2):
    """Test adding member as DM role"""
    response = await client.post(
        f"/api/campaigns/{test_campaign.id}/members",
        json={"user_id": str(test_user2.id), "role": "dm"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "dm"


@pytest.mark.asyncio
async def test_add_member_not_dm(client: AsyncClient, auth_token2, test_campaign, test_user):
    """Test adding member when not DM"""
    response = await client.post(
        f"/api/campaigns/{test_campaign.id}/members",
        json={"user_id": str(test_user.id), "role": "player"},
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_add_member_user_not_found(client: AsyncClient, auth_token, test_campaign):
    """Test adding non-existent user as member"""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.post(
        f"/api/campaigns/{test_campaign.id}/members",
        json={"user_id": str(fake_id), "role": "player"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_member_already_member(client: AsyncClient, auth_token, test_campaign, test_user2, test_db):
    """Test adding user who is already a member"""
    from models.campaign_member import CampaignMember, RoleEnum
    
    # Add user2 as player first
    member = CampaignMember(
        campaign_id=test_campaign.id,
        user_id=test_user2.id,
        role=RoleEnum.PLAYER
    )
    test_db.add(member)
    await test_db.commit()
    
    # Try to add again
    response = await client.post(
        f"/api/campaigns/{test_campaign.id}/members",
        json={"user_id": str(test_user2.id), "role": "player"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "already a member" in response.json()["detail"]


@pytest.mark.asyncio
async def test_remove_member(client: AsyncClient, auth_token, test_campaign, test_user2, test_db):
    """Test removing member from campaign"""
    from models.campaign_member import CampaignMember, RoleEnum
    
    # Add user2 as player first
    member = CampaignMember(
        campaign_id=test_campaign.id,
        user_id=test_user2.id,
        role=RoleEnum.PLAYER
    )
    test_db.add(member)
    await test_db.commit()
    
    response = await client.delete(
        f"/api/campaigns/{test_campaign.id}/members/{test_user2.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_remove_member_not_found(client: AsyncClient, auth_token, test_campaign):
    """Test removing non-existent member"""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.delete(
        f"/api/campaigns/{test_campaign.id}/members/{fake_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_remove_only_dm(client: AsyncClient, auth_token, test_campaign, test_user):
    """Test that the only DM cannot be removed"""
    response = await client.delete(
        f"/api/campaigns/{test_campaign.id}/members/{test_user.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "only DM" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_member_role(client: AsyncClient, auth_token, test_campaign, test_user2, test_db):
    """Test updating member role"""
    from models.campaign_member import CampaignMember, RoleEnum
    
    # Add user2 as player first
    member = CampaignMember(
        campaign_id=test_campaign.id,
        user_id=test_user2.id,
        role=RoleEnum.PLAYER
    )
    test_db.add(member)
    await test_db.commit()
    
    response = await client.patch(
        f"/api/campaigns/{test_campaign.id}/members/{test_user2.id}",
        json={"role": "dm"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "dm"


@pytest.mark.asyncio
async def test_update_member_role_not_found(client: AsyncClient, auth_token, test_campaign):
    """Test updating role of non-existent member"""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.patch(
        f"/api/campaigns/{test_campaign.id}/members/{fake_id}",
        json={"role": "dm"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_demote_only_dm(client: AsyncClient, auth_token, test_campaign, test_user):
    """Test that the only DM cannot demote themselves"""
    response = await client.patch(
        f"/api/campaigns/{test_campaign.id}/members/{test_user.id}",
        json={"role": "player"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "only DM" in response.json()["detail"]
