from app.models import engine, Base
from app.models.user import User
from app.models.roles import *
from app.models.subscription import MasterSubscription
from app.models.user_subscription import UserSubscription
from app.models.media import Media

def create_all_tables():
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")

if __name__ == "__main__":
    create_all_tables()