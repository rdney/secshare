from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    team_id = Column(String, ForeignKey("teams.id"), nullable=True)

    # Relationships
    secrets = relationship("Secret", back_populates="created_by", cascade="all, delete-orphan")
    team = relationship("Team", foreign_keys=[team_id], back_populates="members")
    owned_teams = relationship("Team", foreign_keys="Team.owner_id", back_populates="owner")
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    usage_stats = relationship("UsageStats", back_populates="user", uselist=False)
