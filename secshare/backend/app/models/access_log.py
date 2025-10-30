from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(String, primary_key=True)
    secret_id = Column(String, ForeignKey("secrets.id", ondelete="CASCADE"), nullable=False, index=True)

    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)
    accessed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    secret = relationship("Secret", back_populates="access_logs")
