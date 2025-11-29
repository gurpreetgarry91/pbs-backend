# Add your SQLAlchemy models and DB connection here
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123456@localhost:5432/sgp")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
def check_db_connection():
	try:
		with engine.connect() as connection:
			connection.execute("SELECT 1")
		return True
	except Exception as e:
		print(f"Database connection failed: {e}")
		return False
