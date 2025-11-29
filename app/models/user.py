

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean
from sqlalchemy.sql import func
from app.models import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(30), nullable=True)
    role = Column(String(50), nullable=False)
    password = Column(Text, nullable=False)
    auth_token = Column(Text)
    active = Column(Boolean, nullable=False, server_default='true')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
