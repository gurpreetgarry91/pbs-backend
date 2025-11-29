from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from app.models import SessionLocal
from app.models.user import User
from app.models.subscription import MasterSubscription
from app.models.media import Media
from fastapi import UploadFile, File, Form
from typing import List as TypingList
import os
from pathlib import Path
from datetime import datetime
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.api.dashboard.auth import get_password_hash

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    token = credentials.credentials
    user = db.query(User).filter(User.auth_token == token).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
    if user.role not in ("super_admin", "editor"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
    return user


@router.get("/ping")
def ping():
    return {"message": "Dashboard API is working"}


@router.get("/users", response_model=List[dict])
def list_users(q: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Only return users with role super_admin or editor
    allowed_roles = ("super_admin", "editor", "subscriber")
    base_query = db.query(User).filter(User.role.in_(allowed_roles))

    # If a search query `q` is provided, filter by user_name or email (case-insensitive)
    if q:
        pattern = f"%{q}%"
        users = base_query.filter((User.user_name.ilike(pattern)) | (User.email.ilike(pattern))).all()
    else:
        users = base_query.all()
    result = []
    for u in users:
        result.append({
            "user_id": u.user_id,
            "user_name": u.user_name,
            "email": u.email,
            "phone": u.phone,
            "role": u.role,
            "active": u.active,
            "created_at": u.created_at,
            "updated_at": u.updated_at,
        })
    return result


@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    u = db.query(User).filter(User.user_id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": u.user_id,
        "user_name": u.user_name,
        "email": u.email,
        "phone": getattr(u, 'phone', None),
        "role": u.role,
        "active": u.active,
        "created_at": u.created_at,
        "updated_at": u.updated_at,
    }


from pydantic import BaseModel, EmailStr


class UserCreateSchema(BaseModel):
    user_name: str
    email: EmailStr
    phone: str | None = None
    role: str
    password: str
    active: bool | None = True


class UserUpdateSchema(BaseModel):
    user_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    role: str | None = None
    password: str | None = None
    active: bool | None = None


@router.post("/users")
def create_user(payload: UserCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(User).filter((User.user_name == payload.user_name) | (User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    hashed = get_password_hash(payload.password)
    # set active flag if provided (default True)
    new_user = User(user_name=payload.user_name, email=payload.email, phone=payload.phone, role=payload.role, password=hashed, active=payload.active if payload.active is not None else True)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"user_id": new_user.user_id, "user_name": new_user.user_name, "email": new_user.email, "phone": new_user.phone, "role": new_user.role, "active": new_user.active}


@router.put("/users/{user_id}")
def update_user(user_id: int, payload: UserUpdateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    u = db.query(User).filter(User.user_id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.user_name:
        u.user_name = payload.user_name
    if payload.email:
        u.email = payload.email
    if payload.phone is not None:
        u.phone = payload.phone
    if payload.role:
        u.role = payload.role
    if payload.password:
        u.password = get_password_hash(payload.password)
    if payload.active is not None:
        u.active = payload.active
    db.commit()
    db.refresh(u)
    return {"user_id": u.user_id, "user_name": u.user_name, "email": u.email, "phone": u.phone, "role": u.role, "active": u.active}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    u = db.query(User).filter(User.user_id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(u)
    db.commit()
    return {"detail": "User deleted"}


# User subscriptions
from app.models.user_subscription import UserSubscription


class UserSubscriptionCreateSchema(BaseModel):
    user_id: int
    subscription_id: int
    start_datetime: str  # ISO datetime string
    end_date: str  # ISO date string
    payment_method: str
    subscription_status: str | None = "Active"


class UserSubscriptionUpdateSchema(BaseModel):
    user_id: int | None = None
    subscription_id: int | None = None
    start_datetime: str | None = None
    end_date: str | None = None
    payment_method: str | None = None
    subscription_status: str | None = None
    is_deleted: bool | None = None


@router.get("/user-subscriptions")
def list_user_subscriptions(q: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    base = db.query(UserSubscription)
    if q:
        pattern = f"%{q}%"
        subs = base.filter(UserSubscription.payment_method.ilike(pattern)).all()
    else:
        subs = base.all()
    result = []
    for s in subs:
        result.append({
            "id": s.id,
            "user_id": s.user_id,
            "subscription_id": s.subscription_id,
            "start_datetime": s.start_datetime,
            "end_date": s.end_date,
            "payment_method": s.payment_method,
            "is_deleted": s.is_deleted,
            "subscription_status": s.subscription_status,
            "added_by": s.added_by,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        })
    return result


@router.get("/user-subscriptions/{sub_id}")
def get_user_subscription(sub_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = db.query(UserSubscription).filter(UserSubscription.id == sub_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="User subscription not found")
    return {
        "id": s.id,
        "user_id": s.user_id,
        "subscription_id": s.subscription_id,
        "start_datetime": s.start_datetime,
        "end_date": s.end_date,
        "payment_method": s.payment_method,
        "is_deleted": s.is_deleted,
        "subscription_status": s.subscription_status,
        "added_by": s.added_by,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }


@router.post("/user-subscriptions")
def create_user_subscription(payload: UserSubscriptionCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new = UserSubscription(
        user_id=payload.user_id,
        subscription_id=payload.subscription_id,
        start_datetime=payload.start_datetime,
        end_date=payload.end_date,
        payment_method=payload.payment_method,
        subscription_status=payload.subscription_status if payload.subscription_status is not None else "Active",
        added_by=current_user.user_id,
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return {"id": new.id}


@router.put("/user-subscriptions/{sub_id}")
def update_user_subscription(sub_id: int, payload: UserSubscriptionUpdateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = db.query(UserSubscription).filter(UserSubscription.id == sub_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="User subscription not found")
    if payload.user_id is not None:
        s.user_id = payload.user_id
    if payload.subscription_id is not None:
        s.subscription_id = payload.subscription_id
    if payload.start_datetime is not None:
        s.start_datetime = payload.start_datetime
    if payload.end_date is not None:
        s.end_date = payload.end_date
    if payload.payment_method is not None:
        s.payment_method = payload.payment_method
    if payload.subscription_status is not None:
        s.subscription_status = payload.subscription_status
    if payload.is_deleted is not None:
        s.is_deleted = payload.is_deleted
    db.commit()
    db.refresh(s)
    return {"id": s.id}


@router.delete("/user-subscriptions/{sub_id}")
def delete_user_subscription(sub_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = db.query(UserSubscription).filter(UserSubscription.id == sub_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="User subscription not found")
    # soft delete
    s.is_deleted = True
    db.commit()
    return {"detail": "User subscription marked deleted"}


# Media CRUD for subscriber uploads
@router.get("/media")
def list_media(user_id: int, date: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # date expected as YYYY-MM-DD
    try:
        dt = datetime.fromisoformat(date).date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")
    medias = db.query(Media).filter(Media.user_id == user_id, Media.upload_date == dt, Media.is_deleted == False).all()
    result = []
    for m in medias:
        # construct public URL under /uploads
        rel = Path(m.stored_path)
        url = f"/uploads/{rel.as_posix()}"
        result.append({
            "id": m.id,
            "original_name": m.original_name,
            "url": url,
            "media_type": m.media_type,
            "created_at": m.created_at,
        })
    return result


def _ensure_upload_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


@router.post("/media")
def upload_media(files: TypingList[UploadFile] = File(...), user_id: int = Form(...), date: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        dt = datetime.fromisoformat(date).date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")

    base_dir = Path.cwd() / "uploads" / f"subscriber_{user_id}" / date
    _ensure_upload_dir(base_dir)
    created = []
    for upload in files:
        filename = upload.filename
        # sanitize filename
        safe_name = filename.replace("..", "").replace("/", "_")
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        stored_name = f"{timestamp}_{safe_name}"
        dest = base_dir / stored_name
        with dest.open("wb") as f:
            f.write(upload.file.read())
        ctype = (upload.content_type or "").lower()
        if ctype.startswith("image"):
            mtype = "image"
        elif ctype.startswith("video"):
            mtype = "video"
        else:
            mtype = "file"
        rel_path = Path(f"subscriber_{user_id}") / date / stored_name
        media = Media(
            user_id=user_id,
            original_name=filename,
            stored_path=str(rel_path.as_posix()),
            media_type=mtype,
            upload_date=dt,
            added_by=current_user.user_id,
        )
        db.add(media)
        db.commit()
        db.refresh(media)
        created.append({
            "id": media.id,
            "original_name": media.original_name,
            "url": f"/uploads/{rel_path.as_posix()}",
            "media_type": media.media_type,
        })
    return {"created": created}


@router.delete("/media/{media_id}")
def delete_media(media_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    m = db.query(Media).filter(Media.id == media_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Media not found")
    # delete file if exists
    try:
        file_path = Path.cwd() / "uploads" / Path(m.stored_path)
        if file_path.exists():
            file_path.unlink()
    except Exception:
        pass
    m.is_deleted = True
    db.commit()
    return {"detail": "Media deleted"}



# Subscriptions CRUD
class SubscriptionCreateSchema(BaseModel):
    subscription_name: str
    description: str | None = None
    price: float
    duration: int
    active: bool | None = True


class SubscriptionUpdateSchema(BaseModel):
    subscription_name: str | None = None
    description: str | None = None
    price: float | None = None
    duration: int | None = None
    active: bool | None = None


@router.get("/subscriptions")
def list_subscriptions(q: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # list subscriptions, optional search by name
    base = db.query(MasterSubscription)
    if q:
        pattern = f"%{q}%"
        subs = base.filter(MasterSubscription.subscription_name.ilike(pattern)).all()
    else:
        subs = base.all()
    result = []
    for s in subs:
        result.append({
            "id": s.id,
            "subscription_name": s.subscription_name,
            "description": s.description,
            "price": float(s.price),
            "duration": s.duration,
            "active": s.active,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        })
    return result


@router.get("/subscriptions/{sub_id}")
def get_subscription(sub_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = db.query(MasterSubscription).filter(MasterSubscription.id == sub_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {
        "id": s.id,
        "subscription_name": s.subscription_name,
        "description": s.description,
        "price": float(s.price),
        "duration": s.duration,
        "active": s.active,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }


@router.post("/subscriptions")
def create_subscription(payload: SubscriptionCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new = MasterSubscription(
        subscription_name=payload.subscription_name,
        description=payload.description,
        price=payload.price,
        duration=payload.duration,
        active=payload.active if payload.active is not None else True,
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return {"id": new.id, "subscription_name": new.subscription_name, "price": float(new.price), "duration": new.duration, "active": new.active}


@router.put("/subscriptions/{sub_id}")
def update_subscription(sub_id: int, payload: SubscriptionUpdateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = db.query(MasterSubscription).filter(MasterSubscription.id == sub_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if payload.subscription_name is not None:
        s.subscription_name = payload.subscription_name
    if payload.description is not None:
        s.description = payload.description
    if payload.price is not None:
        s.price = payload.price
    if payload.duration is not None:
        s.duration = payload.duration
    if payload.active is not None:
        s.active = payload.active
    db.commit()
    db.refresh(s)
    return {"id": s.id, "subscription_name": s.subscription_name, "price": float(s.price), "duration": s.duration, "active": s.active}


@router.delete("/subscriptions/{sub_id}")
def delete_subscription(sub_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = db.query(MasterSubscription).filter(MasterSubscription.id == sub_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Subscription not found")
    db.delete(s)
    db.commit()
    return {"detail": "Subscription deleted"}
