from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class URLItem(Base):
    """Database model for storing original URLs and generated short codes."""
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String(2048), nullable=False)
    short_code = Column(String(32), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    click_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    clicks = relationship("ClickLog", back_populates="url", cascade="all, delete-orphan")


class ClickLog(Base):
    """Database model for capturing detailed telemetry on short link redirects."""
    __tablename__ = "click_logs"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id", ondelete="CASCADE"), nullable=False)
    clicked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    referrer = Column(String(1024), nullable=True)

    url = relationship("URLItem", back_populates="clicks")


Index("idx_url_code_active", URLItem.short_code, URLItem.is_active)
