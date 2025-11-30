import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
import json

from main import app
from tests.conftest import test_user, test_campaign, test_db
from core.database import get_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://dnd_user:dnd_password@postgres:5432/dnd_db")

async def override_get_db_new():
    """Create a new engine/session for WebSocket tests to avoid loop conflicts"""
    engine = create_async_engine(TEST_DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_websocket_requires_authentication(test_db):
    """Test that WebSocket connection requires authentication"""
    app.dependency_overrides[get_db] = override_get_db_new
    client = TestClient(app)
    campaign_id = uuid4()
    
    # Try to connect without token
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/campaigns/{campaign_id}/ws"):
            pass
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_websocket_requires_campaign_membership(test_db, test_user, test_campaign):
    """Test that WebSocket connection requires campaign membership"""
    app.dependency_overrides[get_db] = override_get_db_new
    from api.auth import create_access_token
    
    # Create a different campaign that user is not a member of
    other_campaign_id = uuid4()
    
    client = TestClient(app)
    token = create_access_token(data={"sub": str(test_user.id)})
    
    # Try to connect to campaign user is not a member of
    with pytest.raises(Exception):
        with client.websocket_connect(
            f"/api/campaigns/{other_campaign_id}/ws?token={token}"
        ):
            pass
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_websocket_message_broadcast(test_db, test_user, test_campaign):
    """Test that messages are broadcast to all connected clients"""
    app.dependency_overrides[get_db] = override_get_db_new
    from api.auth import create_access_token
    
    client = TestClient(app)
    token = create_access_token(data={"sub": str(test_user.id)})
    
    # Connect two clients to the same campaign
    with client.websocket_connect(
        f"/api/campaigns/{test_campaign.id}/ws?token={token}"
    ) as ws1:
        with client.websocket_connect(
            f"/api/campaigns/{test_campaign.id}/ws?token={token}"
        ) as ws2:
            # Receive "user_joined" messages
            ws1.receive_json()  # user 1 joined
            ws2.receive_json()  # user 1 joined (from ws1)
            ws2.receive_json()  # user 2 joined
            
            # Send message from client 1
            ws1.send_json({
                "type": "message",
                "content": "Hello from client 1",
                "is_ic": True
            })
            
            # Both clients should receive the message
            msg1 = ws1.receive_json()
            msg2 = ws2.receive_json()
            
            assert msg1["type"] == "message"
            assert msg1["data"]["content"] == "Hello from client 1"
            assert msg2["type"] == "message"
            assert msg2["data"]["content"] == "Hello from client 1"
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_websocket_dice_roll(test_db, test_user, test_campaign):
    """Test dice rolling through WebSocket"""
    app.dependency_overrides[get_db] = override_get_db_new
    from api.auth import create_access_token
    
    client = TestClient(app)
    token = create_access_token(data={"sub": str(test_user.id)})
    
    with client.websocket_connect(
        f"/api/campaigns/{test_campaign.id}/ws?token={token}"
    ) as ws:
        # Receive "user_joined" message
        ws.receive_json()
        
        # Send message with dice roll
        ws.send_json({
            "type": "message",
            "content": "I attack!",
            "dice_expression": "1d20+5",
            "is_ic": True
        })
        
        # Receive the message back
        msg = ws.receive_json()
        
        assert msg["type"] == "message"
        assert msg["data"]["content"] == "I attack!"
        assert "dice_roll" in msg["data"]["extra_data"]
        
        dice_roll = msg["data"]["extra_data"]["dice_roll"]
        assert dice_roll["expression"] == "1d20+5"
        assert "total" in dice_roll
        assert "breakdown" in dice_roll
        assert 6 <= dice_roll["total"] <= 25  # 1d20+5 range
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_websocket_invalid_dice_expression(test_db, test_user, test_campaign):
    """Test that invalid dice expressions return an error"""
    app.dependency_overrides[get_db] = override_get_db_new
    from api.auth import create_access_token
    
    client = TestClient(app)
    token = create_access_token(data={"sub": str(test_user.id)})
    
    with client.websocket_connect(
        f"/api/campaigns/{test_campaign.id}/ws?token={token}"
    ) as ws:
        # Receive "user_joined" message
        ws.receive_json()
        
        # Send message with invalid dice expression
        ws.send_json({
            "type": "message",
            "content": "Rolling...",
            "dice_expression": "invalid",
            "is_ic": True
        })
        
        # Should receive error message
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert "Invalid dice expression" in msg["data"]["message"]
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_websocket_user_joined_left_notifications(test_db, test_user, test_campaign):
    """Test that user join/leave notifications are sent"""
    app.dependency_overrides[get_db] = override_get_db_new
    from api.auth import create_access_token
    
    client = TestClient(app)
    token = create_access_token(data={"sub": str(test_user.id)})
    
    with client.websocket_connect(
        f"/api/campaigns/{test_campaign.id}/ws?token={token}"
    ) as ws1:
        # Receive "user_joined" for first connection
        msg = ws1.receive_json()
        assert msg["type"] == "user_joined"
        assert msg["data"]["username"] == test_user.username
        
        # Connect second client
        with client.websocket_connect(
            f"/api/campaigns/{test_campaign.id}/ws?token={token}"
        ) as ws2:
            # First client should receive "user_joined" for second connection
            msg = ws1.receive_json()
            assert msg["type"] == "user_joined"
            
            # Second client receives its own join and the existing user
            ws2.receive_json()  # Skip own join
        
        # After ws2 closes, ws1 should receive "user_left"
        msg = ws1.receive_json()
        assert msg["type"] == "user_left"
    
    app.dependency_overrides.clear()
