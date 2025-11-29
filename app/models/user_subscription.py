from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.models import Base


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("public.users.user_id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("public.master_subscriptions.id"), nullable=False)
    start_datetime = Column(TIMESTAMP, nullable=False)
    end_date = Column(TIMESTAMP, nullable=False)
    payment_method = Column(String(50), nullable=False)
    is_deleted = Column(Boolean, nullable=False, server_default='false')
    subscription_status = Column(String(50), nullable=False, server_default='Active')
    added_by = Column(Integer, ForeignKey("public.users.user_id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
