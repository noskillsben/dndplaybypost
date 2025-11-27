import pytest
import pytest_asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from httpx import AsyncClient
from typing import AsyncGenerator


from core.database import Base, get_db
from models.user import User
from models.campaign import Campaign
from models.campaign_member import CampaignMember, RoleEnum
from models.character import Character
from models.message import Message
from api.auth import pwd_context, create_access_token


# Use the same database as development for tests (will be cleaned up after each test)
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://dnd_user:dnd_password@postgres:5432/dnd_db")


@pytest_asyncio.fixture
async def test_db():
    """Create a test database and tables"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db):
    """Create a test client with database override"""
    from main import app
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(test_db):
    """Create a test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=pwd_context.hash("testpassword"),
        is_admin=False
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(test_db):
    """Create a test admin user"""
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=pwd_context.hash("adminpassword"),
        is_admin=True
    )
    test_db.add(admin)
    await test_db.commit()
    await test_db.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def test_user2(test_db):
    """Create a second test user"""
    user = User(
        username="testuser2",
        email="test2@example.com",
        password_hash=pwd_context.hash("testpassword2"),
        is_admin=False
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
def auth_token(test_user):
    """Create an auth token for test user"""
    return create_access_token(data={"sub": test_user.username, "is_admin": False})


@pytest_asyncio.fixture
def admin_token(test_admin):
    """Create an auth token for admin user"""
    return create_access_token(data={"sub": test_admin.username, "is_admin": True})


@pytest_asyncio.fixture
def auth_token2(test_user2):
    """Create an auth token for second test user"""
    return create_access_token(data={"sub": test_user2.username, "is_admin": False})


@pytest_asyncio.fixture
async def test_campaign(test_db, test_user):
    """Create a test campaign with the test user as DM"""
    campaign = Campaign(
        name="Test Campaign",
        description="A test campaign",
        settings={},
        created_by=test_user.id
    )
    test_db.add(campaign)
    await test_db.flush()
    
    # Add user as DM
    member = CampaignMember(
        campaign_id=campaign.id,
        user_id=test_user.id,
        role=RoleEnum.DM
    )
    test_db.add(member)
    await test_db.commit()
    await test_db.refresh(campaign)
    return campaign


@pytest_asyncio.fixture
async def test_character(test_db, test_user, test_campaign):
    """Create a test character"""
    character = Character(
        campaign_id=test_campaign.id,
        player_id=test_user.id,
        name="Test Character",
        sheet_data={"class": "Fighter", "level": 1},
        notes="Test notes"
    )
    test_db.add(character)
    await test_db.commit()
    await test_db.refresh(character)
    return character


@pytest_asyncio.fixture
async def test_message(test_db, test_user, test_campaign, test_character):
    """Create a test message"""
    message = Message(
        campaign_id=test_campaign.id,
        user_id=test_user.id,
        character_id=test_character.id,
        content="Test message",
        is_ic=True,
        extra_data={}
    )
    test_db.add(message)
    await test_db.commit()
    await test_db.refresh(message)
    return message
