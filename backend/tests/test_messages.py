import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_create_message(client: AsyncClient, auth_token, test_campaign, test_character):
    """Test creating a message"""
    response = await client.post(
        f"/api/campaigns/{test_campaign.id}/messages",
        json={
            "content": "I attack the goblin!",
            "character_id": str(test_character.id),
            "is_ic": True,
            "extra_data": {"action": "attack"}
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "I attack the goblin!"
    assert data["character_id"] == str(test_character.id)
    assert data["is_ic"] == True


@pytest.mark.asyncio
async def test_create_message_ooc(client: AsyncClient, auth_token, test_campaign):
    """Test creating an out-of-character message"""
    response = await client.post(
        f"/api/campaigns/{test_campaign.id}/messages",
        json={
            "content": "Hey everyone, I'll be late next session",
            "is_ic": False
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["is_ic"] == False
    assert data["character_id"] is None


@pytest.mark.asyncio
async def test_create_message_minimal(client: AsyncClient, auth_token, test_campaign):
    """Test creating message with minimal data"""
    response = await client.post(
        f"/api/campaigns/{test_campaign.id}/messages",
        json={"content": "Simple message"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Simple message"
    assert data["is_ic"] == True  # Default
    assert data["extra_data"] == {}


@pytest.mark.asyncio
async def test_create_message_not_member(client: AsyncClient, auth_token2, test_campaign):
    """Test creating message when not campaign member"""
    response = await client.post(
        f"/api/campaigns/{test_campaign.id}/messages",
        json={"content": "Hacker message"},
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_message_campaign_not_found(client: AsyncClient, auth_token):
    """Test creating message in non-existent campaign"""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.post(
        f"/api/campaigns/{fake_id}/messages",
        json={"content": "Test"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_message_wrong_character(client: AsyncClient, auth_token, test_campaign, test_character, test_db, test_user2):
    """Test creating message with character not owned by user"""
    from models.character import Character
    
    # Create character owned by user2
    other_char = Character(
        campaign_id=test_campaign.id,
        player_id=test_user2.id,
        name="Other Character",
        sheet_data={}
    )
    test_db.add(other_char)
    await test_db.commit()
    await test_db.refresh(other_char)
    
    response = await client.post(
        f"/api/campaigns/{test_campaign.id}/messages",
        json={
            "content": "Trying to post as someone else's character",
            "character_id": str(other_char.id)
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 403
    assert "not owned by you" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_message_character_wrong_campaign(client: AsyncClient, auth_token, test_campaign, test_db, test_user):
    """Test creating message with character from different campaign"""
    from models.character import Character
    from models.campaign import Campaign
    from models.campaign_member import CampaignMember, RoleEnum
    
    # Create another campaign
    other_campaign = Campaign(
        name="Other Campaign",
        description="Another campaign",
        settings={},
        created_by=test_user.id
    )
    test_db.add(other_campaign)
    await test_db.flush()
    
    # Add user as member
    member = CampaignMember(
        campaign_id=other_campaign.id,
        user_id=test_user.id,
        role=RoleEnum.DM
    )
    test_db.add(member)
    
    # Create character in other campaign
    other_char = Character(
        campaign_id=other_campaign.id,
        player_id=test_user.id,
        name="Wrong Campaign Character",
        sheet_data={}
    )
    test_db.add(other_char)
    await test_db.commit()
    await test_db.refresh(other_char)
    
    # Try to post in test_campaign with character from other_campaign
    response = await client.post(
        f"/api/campaigns/{test_campaign.id}/messages",
        json={
            "content": "Wrong campaign character",
            "character_id": str(other_char.id)
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_messages(client: AsyncClient, auth_token, test_campaign, test_message):
    """Test listing messages in a campaign"""
    response = await client.get(
        f"/api/campaigns/{test_campaign.id}/messages",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(m["id"] == str(test_message.id) for m in data)


@pytest.mark.asyncio
async def test_list_messages_pagination(client: AsyncClient, auth_token, test_campaign):
    """Test message pagination"""
    response = await client.get(
        f"/api/campaigns/{test_campaign.id}/messages?limit=10&offset=0",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 10


@pytest.mark.asyncio
async def test_list_messages_custom_limit(client: AsyncClient, auth_token, test_campaign):
    """Test custom pagination limit"""
    response = await client.get(
        f"/api/campaigns/{test_campaign.id}/messages?limit=5",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5


@pytest.mark.asyncio
async def test_list_messages_not_member(client: AsyncClient, auth_token2, test_campaign):
    """Test listing messages when not campaign member"""
    response = await client.get(
        f"/api/campaigns/{test_campaign.id}/messages",
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_message(client: AsyncClient, auth_token, test_message):
    """Test updating a message within time limit"""
    response = await client.patch(
        f"/api/messages/{test_message.id}",
        json={"content": "Updated message content"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated message content"


@pytest.mark.asyncio
async def test_update_message_not_found(client: AsyncClient, auth_token):
    """Test updating non-existent message"""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.patch(
        f"/api/messages/{fake_id}",
        json={"content": "Test"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_message_not_owner(client: AsyncClient, auth_token2, test_message):
    """Test updating message when not the owner"""
    response = await client.patch(
        f"/api/messages/{test_message.id}",
        json={"content": "Hacked content"},
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_message_time_limit(client: AsyncClient, auth_token, test_db, test_campaign, test_user):
    """Test updating message after time limit"""
    from models.message import Message
    
    # Create old message
    old_message = Message(
        campaign_id=test_campaign.id,
        user_id=test_user.id,
        content="Old message",
        is_ic=True,
        extra_data={}
    )
    test_db.add(old_message)
    await test_db.commit()
    await test_db.refresh(old_message)
    
    # Manually set created_at to 20 minutes ago
    old_message.created_at = datetime.utcnow() - timedelta(minutes=20)
    await test_db.commit()
    
    response = await client.patch(
        f"/api/messages/{old_message.id}",
        json={"content": "Too late to edit"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 403
    assert "time limit" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_message_as_owner(client: AsyncClient, auth_token, test_message):
    """Test deleting message as owner"""
    response = await client.delete(
        f"/api/messages/{test_message.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_message_not_found(client: AsyncClient, auth_token):
    """Test deleting non-existent message"""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.delete(
        f"/api/messages/{fake_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_message_as_dm(client: AsyncClient, auth_token, test_db, test_campaign, test_user2):
    """Test deleting message as DM"""
    from models.message import Message
    from models.campaign_member import CampaignMember, RoleEnum
    
    # Add user2 as player
    member = CampaignMember(
        campaign_id=test_campaign.id,
        user_id=test_user2.id,
        role=RoleEnum.PLAYER
    )
    test_db.add(member)
    await test_db.commit()
    
    # Create message from user2
    message = Message(
        campaign_id=test_campaign.id,
        user_id=test_user2.id,
        content="Player message",
        is_ic=True,
        extra_data={}
    )
    test_db.add(message)
    await test_db.commit()
    await test_db.refresh(message)
    
    # DM (test_user) deletes player's message
    response = await client.delete(
        f"/api/messages/{message.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_message_unauthorized(client: AsyncClient, auth_token2, test_message):
    """Test deleting message when not authorized"""
    response = await client.delete(
        f"/api/messages/{test_message.id}",
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_message_not_dm_not_owner(client: AsyncClient, auth_token2, test_db, test_campaign, test_user, test_user2):
    """Test deleting message when neither owner nor DM"""
    from models.message import Message
    from models.campaign_member import CampaignMember, RoleEnum
    
    # Add user2 as player
    member = CampaignMember(
        campaign_id=test_campaign.id,
        user_id=test_user2.id,
        role=RoleEnum.PLAYER
    )
    test_db.add(member)
    await test_db.commit()
    
    # Create message from test_user (DM)
    message = Message(
        campaign_id=test_campaign.id,
        user_id=test_user.id,
        content="DM message",
        is_ic=True,
        extra_data={}
    )
    test_db.add(message)
    await test_db.commit()
    await test_db.refresh(message)
    
    # user2 (player) tries to delete DM's message
    response = await client.delete(
        f"/api/messages/{message.id}",
        headers={"Authorization": f"Bearer {auth_token2}"}
    )
    assert response.status_code == 403
