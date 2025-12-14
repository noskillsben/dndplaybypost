import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_settings_as_admin(client: AsyncClient, admin_token):
    """Test getting site settings as admin"""
    response = await client.get(
        "/api/admin/settings",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check that default settings are present
    assert "site_name" in data
    assert "colors" in data
    assert "email" in data
    assert "user_registration" in data
    assert "campaigns" in data
    assert "features" in data
    assert "security" in data
    assert "uploads" in data
    
    # Check some default values
    assert data["site_name"] == "D&D Play-by-Post"
    assert data["colors"]["primary"] == "#3B82F6"
    assert data["user_registration"]["allow_new_users"] is True


@pytest.mark.asyncio
async def test_get_settings_as_non_admin(client: AsyncClient, auth_token):
    """Test that non-admin cannot get settings"""
    response = await client.get(
        "/api/admin/settings",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_settings_unauthorized(client: AsyncClient):
    """Test that unauthorized user cannot get settings"""
    response = await client.get("/api/admin/settings")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_settings_as_admin(client: AsyncClient, admin_token):
    """Test updating site settings as admin"""
    new_settings = {
        "site_name": "My Custom D&D Site",
        "site_domain": "dnd.example.com",
        "site_logo": "/uploads/logo.png",
        "colors": {
            "primary": "#FF5733",
            "secondary": "#33FF57",
            "background": "#333333"
        },
        "email": {
            "enabled": True,
            "provider": "gmail",
            "from_address": "admin@example.com",
            "gmail_client_id": "test_client_id",
            "gmail_client_secret": "test_secret",
            "gmail_refresh_token": "",
            "gmail_access_token": "",
            "gmail_token_expires_at": None,
            "gmail_authorized": False
        },
        "user_registration": {
            "allow_new_users": False,
            "registration_mode": "invite_only",
            "require_email": True,
            "require_email_verification": True,
            "new_users_can_create_campaigns": False,
            "new_users_can_join_campaigns": True
        },
        "campaigns": {
            "max_per_user": 5,
            "max_characters_per_campaign": 6,
            "default_visibility": "public",
            "allow_invites": True
        },
        "features": {
            "compendium_enabled": True,
            "allow_homebrew": True,
            "dice_rolling_enabled": True,
            "messaging_enabled": True
        },
        "security": {
            "session_timeout_minutes": 720,
            "max_login_attempts": 3,
            "require_strong_passwords": True,
            "password_min_length": 10
        },
        "uploads": {
            "max_file_size_mb": 10,
            "allowed_image_types": ["image/png", "image/jpeg"]
        }
    }
    
    response = await client.put(
        "/api/admin/settings",
        json=new_settings,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Verify the updates
    assert data["site_name"] == "My Custom D&D Site"
    assert data["site_domain"] == "dnd.example.com"
    assert data["colors"]["primary"] == "#FF5733"
    assert data["user_registration"]["allow_new_users"] is False
    assert data["user_registration"]["registration_mode"] == "invite_only"
    assert data["campaigns"]["max_per_user"] == 5
    assert data["security"]["password_min_length"] == 10
    
    # Verify settings persist by fetching again
    response = await client.get(
        "/api/admin/settings",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["site_name"] == "My Custom D&D Site"


@pytest.mark.asyncio
async def test_update_settings_as_non_admin(client: AsyncClient, auth_token):
    """Test that non-admin cannot update settings"""
    new_settings = {
        "site_name": "Hacked Site"
    }
    
    response = await client.put(
        "/api/admin/settings",
        json=new_settings,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_settings_unauthorized(client: AsyncClient):
    """Test that unauthorized user cannot update settings"""
    new_settings = {
        "site_name": "Hacked Site"
    }
    
    response = await client.put(
        "/api/admin/settings",
        json=new_settings
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_partial_settings_update(client: AsyncClient, admin_token):
    """Test updating only some settings fields"""
    # First get current settings
    response = await client.get(
        "/api/admin/settings",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    original_settings = response.json()
    
    # Update only site_name and one color
    partial_update = {
        **original_settings,
        "site_name": "Partially Updated Site",
        "colors": {
            **original_settings["colors"],
            "primary": "#ABCDEF"
        }
    }
    
    response = await client.put(
        "/api/admin/settings",
        json=partial_update,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["site_name"] == "Partially Updated Site"
    assert data["colors"]["primary"] == "#ABCDEF"
    # Other settings should remain unchanged
    assert data["colors"]["secondary"] == original_settings["colors"]["secondary"]

