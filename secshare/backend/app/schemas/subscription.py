from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.subscription import SubscriptionPlan, SubscriptionStatus


class SubscriptionResponse(BaseModel):
    id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    stripe_current_period_end: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CreateCheckoutSession(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str


class UsageResponse(BaseModel):
    secrets_created_this_month: int
    secret_requests_this_month: int
    attachment_bytes_this_month: int
    limit_secrets: int
    limit_attachments: int
    limit_team_size: int
