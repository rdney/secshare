from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, BigInteger, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Secret(Base):
    __tablename__ = "secrets"

    id = Column(String, primary_key=True)
    encrypted_content = Column(Text, nullable=False)
    encrypted_key = Column(String, nullable=False)
    iv = Column(String, nullable=False)

    max_views = Column(Integer, default=1, nullable=False)
    current_views = Column(Integer, default=0, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    has_attachment = Column(Boolean, default=False, nullable=False)
    attachment_url = Column(String, nullable=True)
    attachment_name = Column(String, nullable=True)
    attachment_size = Column(BigInteger, nullable=True)

    created_by_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    created_by = relationship("User", back_populates="secrets")
    team = relationship("Team", back_populates="secrets")
    access_logs = relationship("AccessLog", back_populates="secret", cascade="all, delete-orphan")
