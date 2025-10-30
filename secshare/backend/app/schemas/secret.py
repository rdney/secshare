from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SecretCreate(BaseModel):
    content: str
    max_views: int = 1
    expires_in_hours: int = 24


class SecretResponse(BaseModel):
    id: str
    max_views: int
    current_views: int
    expires_at: datetime
    has_attachment: bool
    attachment_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SecretView(BaseModel):
    id: str
    content: str
    current_views: int
    max_views: int
    expires_at: datetime
    has_attachment: bool
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
