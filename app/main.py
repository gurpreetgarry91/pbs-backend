
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.dashboard.router import router as dashboard_router
from app.api.dashboard.auth import router as dashboard_auth_router
from app.api.mobile.router import router as mobile_router
from app.api.mobile.auth import router as mobile_auth_router
import os
from fastapi.staticfiles import StaticFiles
from app.models import SessionLocal
from app.config.config import init_db

app = FastAPI(title="PBS Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(dashboard_auth_router, prefix="/dashboard", tags=["Dashboard Auth"])
app.include_router(mobile_router, prefix="/mobile", tags=["Mobile"])
app.include_router(mobile_auth_router, prefix="/mobile", tags=["Mobile Auth"])

# Serve uploaded files from /uploads
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to PBS Backend API"}
