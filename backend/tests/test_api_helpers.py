import pytest
from unittest.mock import AsyncMock, MagicMock
from models.campaign import Campaign
from models.campaign_member import CampaignMember, RoleEnum
from models.user import User
from models.character import Character

@pytest.mark.asyncio
async def test_check_is_dm_true():
    from api.campaigns import check_is_dm
    user = User(id="user1")
    member = CampaignMember(user_id="user1", role=RoleEnum.DM)
    campaign = Campaign(members=[member])
    assert await check_is_dm(campaign, user) is True

@pytest.mark.asyncio
async def test_check_is_dm_false_player():
    from api.campaigns import check_is_dm
    user = User(id="user1")
    member = CampaignMember(user_id="user1", role=RoleEnum.PLAYER)
    campaign = Campaign(members=[member])
    assert await check_is_dm(campaign, user) is False

@pytest.mark.asyncio
async def test_check_is_dm_false_not_member():
    from api.campaigns import check_is_dm
    user = User(id="user1")
    member = CampaignMember(user_id="user2", role=RoleEnum.DM)
    campaign = Campaign(members=[member])
    assert await check_is_dm(campaign, user) is False

@pytest.mark.asyncio
async def test_check_is_dm_empty():
    from api.campaigns import check_is_dm
    user = User(id="user1")
    campaign = Campaign(members=[])
    assert await check_is_dm(campaign, user) is False

@pytest.mark.asyncio
async def test_check_is_member_true():
    from api.campaigns import check_is_member
    user = User(id="user1")
    member = CampaignMember(user_id="user1", role=RoleEnum.PLAYER)
    campaign = Campaign(members=[member])
    assert await check_is_member(campaign, user) is True

@pytest.mark.asyncio
async def test_check_is_member_false():
    from api.campaigns import check_is_member
    user = User(id="user1")
    member = CampaignMember(user_id="user2", role=RoleEnum.PLAYER)
    campaign = Campaign(members=[member])
    assert await check_is_member(campaign, user) is False

@pytest.mark.asyncio
async def test_check_can_modify_character_owner():
    from api.characters import check_can_modify_character
    user = User(id="user1")
    character = Character(player_id="user1")
    db = AsyncMock()
    assert await check_can_modify_character(character, user, db) is True

@pytest.mark.asyncio
async def test_check_can_modify_character_dm():
    from api.characters import check_can_modify_character
    user = User(id="user1")
    character = Character(player_id="user2", campaign_id="camp1")
    
    # Mock DB result for DM check
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = True # Found DM record
    db.execute.return_value = result
    
    assert await check_can_modify_character(character, user, db) is True

@pytest.mark.asyncio
async def test_check_can_modify_character_neither():
    from api.characters import check_can_modify_character
    user = User(id="user1")
    character = Character(player_id="user2", campaign_id="camp1")
    
    # Mock DB result for DM check (not found)
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result
    
    assert await check_can_modify_character(character, user, db) is False
