from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class SubscriptionPlan(str, enum.Enum):
    FREE = "FREE"
    PRO = "PRO"
    TEAM = "TEAM"
    ENTERPRISE = "ENTERPRISE"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CANCELED = "CANCELED"
    PAST_DUE = "PAST_DUE"
    TRIALING = "TRIALING"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True)
    plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.FREE, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)

    stripe_customer_id = Column(String, unique=True, nullable=True, index=True)
    stripe_subscription_id = Column(String, unique=True, nullable=True, index=True)
    stripe_price_id = Column(String, nullable=True)
    stripe_current_period_end = Column(DateTime(timezone=True), nullable=True)

    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=True)
    team_id = Column(String, ForeignKey("teams.id"), unique=True, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="subscription")
    team = relationship("Team", back_populates="subscription")
