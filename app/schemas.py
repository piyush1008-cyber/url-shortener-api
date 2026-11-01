from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator


class URLBase(BaseModel):
    """Base payload schema for URL requests."""
    original_url: str = Field(..., description="Destination destination URL to shorten")
    custom_code: Optional[str] = Field(
        None,
        min_length=3,
        max_length=32,
        description="Optional custom vanity alias for the shortened URL"
    )
    expires_in_days: Optional[int] = Field(
        None,
        ge=1,
        le=365,
        description="Optional time-to-live in days before the link expires"
    )

    @field_validator("original_url")
    @classmethod
    def validate_url_format(cls, v: str) -> str:
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("custom_code")
    @classmethod
    def validate_custom_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v.isalnum() and not all(c in "-_" or c.isalnum() for c in v):
                raise ValueError("Custom code may only contain alphanumeric characters, hyphens, and underscores")
        return v


class URLCreate(URLBase):
    """Payload for creating a new short link."""
    pass


class URLResponse(BaseModel):
    """Schema returned after creating or querying a short link."""
    id: int
    original_url: str
    short_code: str
    short_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    click_count: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ClickDetail(BaseModel):
    """Telemetry detail for individual click events."""
    clicked_at: datetime
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class URLAnalytics(BaseModel):
    """Aggregated analytics data payload for a shortened link."""
    short_code: str
    original_url: str
    short_url: str
    total_clicks: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_expired: bool
    top_referrers: Dict[str, int]
    recent_clicks: List[ClickDetail]
