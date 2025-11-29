from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean, Numeric
from sqlalchemy.sql import func
from app.models import Base


class MasterSubscription(Base):
    __tablename__ = "master_subscriptions"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    duration = Column(Integer, nullable=False)
    active = Column(Boolean, nullable=False, server_default='true')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
