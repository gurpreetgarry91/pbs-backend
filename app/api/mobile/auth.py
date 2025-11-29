
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import SessionLocal
from app.models.user import User
import bcrypt
import jwt
import os
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    user_name: str
    password: str

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"


class UserCreate(BaseModel):
    user_name: str
    email: EmailStr
    role: str
    password: str

def verify_password(plain_password, hashed_password):
    # Truncate plain password to 72 bytes to match bcrypt limit
    pw_bytes = plain_password.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password):
    pw_bytes = password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.user_name == username).first()
    if not user or not verify_password(password, user.password):
        return None
    return user

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

# Registration endpoint removed from mobile API. Use dashboard `/add-user` for registration.


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # Use the authenticate_user helper to verify password
    user = db.query(User).filter(User.user_name == payload.user_name).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"user_id": str(user.user_id), "role": user.role})
    user.auth_token = token
    db.commit()
    return {"token": token, "user_id": str(user.user_id)}
