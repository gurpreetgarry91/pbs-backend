# Configuration settings for PBS Backend API


from app.models import engine, Base
from app.models.user import User
from app.models.roles import *

class Settings:
    PROJECT_NAME: str = "PBS Backend API"
    API_VERSION: str = "v1"

settings = Settings()

def init_db():
    Base.metadata.create_all(bind=engine)
