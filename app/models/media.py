from sqlalchemy import Column, Integer, String, Date, TIMESTAMP, Boolean
from sqlalchemy.sql import func
from app.models import Base


class Media(Base):
    __tablename__ = "media"
    __table_args__ = {"schema": "public"}
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    original_name = Column(String(255), nullable=False)
    stored_path = Column(String(1024), nullable=False)
    media_type = Column(String(50), nullable=False)
    upload_date = Column(Date, nullable=False)
    added_by = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, nullable=False, server_default='false')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
