from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID


class ColorSettings(BaseModel):
    primary: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary: str = Field(default="#8B5CF6", pattern=r"^#[0-9A-Fa-f]{6}$")
    background: str = Field(default="#1F2937", pattern=r"^#[0-9A-Fa-f]{6}$")


class EmailSettings(BaseModel):
    enabled: bool = False
    provider: str = "gmail"
    from_address: str = ""
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""
    gmail_access_token: str = ""
    gmail_token_expires_at: Optional[datetime] = None
    gmail_authorized: bool = False


class UserRegistrationSettings(BaseModel):
    allow_new_users: bool = True
    registration_mode: str = Field(default="open", pattern=r"^(open|invite_only|closed)$")
    require_email: bool = True
    require_email_verification: bool = False
    new_users_can_create_campaigns: bool = True
    new_users_can_join_campaigns: bool = True


class CampaignSettings(BaseModel):
    max_per_user: int = Field(default=10, ge=0)
    max_characters_per_campaign: int = Field(default=8, ge=1)
    default_visibility: str = Field(default="private", pattern=r"^(public|private|invite_only)$")
    allow_invites: bool = True


class FeatureSettings(BaseModel):
    compendium_enabled: bool = True
    allow_homebrew: bool = False
    dice_rolling_enabled: bool = True
    messaging_enabled: bool = True


class SecuritySettings(BaseModel):
    session_timeout_minutes: int = Field(default=1440, ge=1)
    max_login_attempts: int = Field(default=5, ge=1)
    require_strong_passwords: bool = True
    password_min_length: int = Field(default=8, ge=4, le=128)


class UploadSettings(BaseModel):
    max_file_size_mb: int = Field(default=5, ge=1, le=100)
    allowed_image_types: List[str] = Field(
        default=["image/png", "image/jpeg", "image/webp", "image/gif"]
    )


class SiteSettingsSchema(BaseModel):
    """Complete site settings schema with validation"""
    site_name: str = "D&D Play-by-Post"
    site_domain: str = ""
    site_logo: str = ""
    colors: ColorSettings = Field(default_factory=ColorSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)
    user_registration: UserRegistrationSettings = Field(default_factory=UserRegistrationSettings)
    campaigns: CampaignSettings = Field(default_factory=CampaignSettings)
    features: FeatureSettings = Field(default_factory=FeatureSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    uploads: UploadSettings = Field(default_factory=UploadSettings)


class SiteSettingsUpdate(BaseModel):
    """Schema for updating site settings - all fields optional"""
    site_name: Optional[str] = None
    site_domain: Optional[str] = None
    site_logo: Optional[str] = None
    colors: Optional[ColorSettings] = None
    email: Optional[EmailSettings] = None
    user_registration: Optional[UserRegistrationSettings] = None
    campaigns: Optional[CampaignSettings] = None
    features: Optional[FeatureSettings] = None
    security: Optional[SecuritySettings] = None
    uploads: Optional[UploadSettings] = None


class SiteSettingsResponse(BaseModel):
    """Response schema including metadata"""
    settings: Dict[str, Any]
    updated_at: Optional[datetime] = None
    updated_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True
