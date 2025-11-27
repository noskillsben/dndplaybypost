import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_users_as_admin(client: AsyncClient, admin_token, test_user):
    """Test listing all users as admin"""
    response = await client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # At least admin and test_user


@pytest.mark.asyncio
async def test_list_users_as_non_admin(client: AsyncClient, auth_token):
    """Test that non-admin cannot list users"""
    response = await client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_users_unauthorized(client: AsyncClient):
    """Test that unauthorized user cannot list users"""
    response = await client.get("/admin/users")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_stats_as_admin(client: AsyncClient, admin_token):
    """Test getting stats as admin"""
    response = await client.get(
        "/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_count" in data
    assert data["user_count"] >= 1


@pytest.mark.asyncio
async def test_get_stats_as_non_admin(client: AsyncClient, auth_token):
    """Test that non-admin cannot get stats"""
    response = await client.get(
        "/admin/stats",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 403
