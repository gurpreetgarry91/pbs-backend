
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

class UserCreate(BaseModel):
    user_name: str
    email: EmailStr
    role: str
    password: str

def verify_password(plain_password, hashed_password):
    # bcrypt has a 72-byte input limit. Truncate the plain password to 72 bytes
    # before verifying to match how we hash stored passwords.
    pw_bytes = plain_password.encode("utf-8")[:72]
    # hashed_password is stored as a string; convert to bytes
    try:
        return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password):
    # Ensure password is no longer than 72 bytes for bcrypt
    pw_bytes = password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.user_name == username).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/add-user")
def add_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter((User.user_name == user.user_name) | (User.email == user.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    password_bytes = user.password.encode('utf-8')[:72]
    truncated_password = password_bytes.decode('utf-8', 'ignore')
    hashed_password = get_password_hash(truncated_password)
    new_user = User(
        user_name=user.user_name,
        email=user.email,
        role=user.role,
        password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"user_id": new_user.user_id, "user_name": new_user.user_name, "email": new_user.email, "role": new_user.role}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.user_name, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"user_id": str(user.user_id), "role": user.role})
    user.auth_token = token
    db.commit()
    return {"token": token, "user_id": str(user.user_id)}
