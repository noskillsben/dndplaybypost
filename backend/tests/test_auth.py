import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration"""
    response = await client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "User created successfully"
    assert "is_admin" in data


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, test_user):
    """Test registering with duplicate username"""
    response = await client.post(
        "/auth/register",
        json={
            "username": test_user.username,
            "email": "different@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user):
    """Test registering with duplicate email"""
    response = await client.post(
        "/auth/register",
        json={
            "username": "differentuser",
            "email": test_user.email,
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test successful login"""
    response = await client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["is_admin"] == False


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    """Test login with wrong password"""
    response = await client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with nonexistent user"""
    response = await client.post(
        "/auth/login",
        json={
            "username": "nonexistent",
            "password": "password"
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_login(client: AsyncClient, test_admin):
    """Test admin user login"""
    response = await client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "adminpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_admin"] == True
