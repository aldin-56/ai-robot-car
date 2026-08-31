from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.security import sanitize_input

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterSchema(BaseModel):
    email: str
    username: str
    password: str


class LoginSchema(BaseModel):
    username: str
    password: str


class UserResponseSchema(BaseModel):
    id: str
    email: str
    username: str
    optimization_pref: str
    spending_limit: float


@router.post("/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    email = sanitize_input(data.email).lower()
    username = sanitize_input(data.username).lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email is already registered.")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username is already taken.")

    user = User(
        email=email,
        username=username,
        hashed_password=data.password  # simplified for demo auth
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "optimization_pref": user.optimization_pref,
            "spending_limit": user.spending_limit
        }
    }


@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    username = sanitize_input(data.username).lower()
    user = db.query(User).filter((User.username == username) | (User.email == username)).first()

    if not user or user.hashed_password != data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    return {
        "message": "Login successful",
        "token": f"mock_jwt_token_{user.id}",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "optimization_pref": user.optimization_pref,
            "spending_limit": user.spending_limit
        }
    }


@router.get("/me")
def get_me(user_id: str = "default_demo_user", db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Create default demo user if not existing
        user = User(
            id="default_demo_user",
            email="demo@litemind.ai",
            username="demouser",
            hashed_password="demopassword"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "optimization_pref": user.optimization_pref,
        "spending_limit": user.spending_limit,
        "privacy_mode": user.privacy_mode
    }
