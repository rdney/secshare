from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_teams")
    members = relationship("User", foreign_keys="User.team_id", back_populates="team")
    secrets = relationship("Secret", back_populates="team", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="team", uselist=False)
