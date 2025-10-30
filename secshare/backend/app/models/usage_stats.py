from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class UsageStats(Base):
    __tablename__ = "usage_stats"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)

    secrets_created_this_month = Column(Integer, default=0, nullable=False)
    secret_requests_this_month = Column(Integer, default=0, nullable=False)
    attachment_bytes_this_month = Column(BigInteger, default=0, nullable=False)

    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="usage_stats")
