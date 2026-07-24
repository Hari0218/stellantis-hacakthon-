"""Auth Service — handles user management and token issuance."""
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Boolean
from typing import Optional

from shared.database import Base, get_engine, get_session_factory, get_db, init_db
from shared.schemas import UserCreate, UserResponse, TokenResponse
from shared.auth_utils import hash_password, verify_password, create_token, decode_token

app = FastAPI(title="Auth Service", version="1.0.0")

DATABASE_URL = "sqlite:///./auth.db"
engine = get_engine(DATABASE_URL)
SessionFactory = get_session_factory(engine)


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="technician")
    is_active = Column(Boolean, default=True)


class Role(Base):
    __tablename__ = "role"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    permissions = Column(String, nullable=False)  # JSON string of permission list


init_db(engine)


def get_db_session():
    yield from get_db(SessionFactory)


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Fetch a user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Fetch a user by primary key."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Fetch a user by email address."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    """Register a new user with hashed password."""
    if get_user_by_username(db, user_data.username):
        raise ValueError(f"Username '{user_data.username}' is already taken")
    if get_user_by_email(db, user_data.email):
        raise ValueError(f"Email '{user_data.email}' is already registered")
    hashed = hash_password(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed,
        role=user_data.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Verify credentials and return user if valid."""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def deactivate_user(db: Session, user_id: int) -> bool:
    """Deactivate a user account."""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    user.is_active = False
    db.commit()
    return True


def issue_token(user: User) -> str:
    """Create an auth token for an authenticated user."""
    return create_token(user.id, user.role)


def verify_token_and_get_user(db: Session, token: str) -> Optional[User]:
    """Decode a token and return the corresponding user."""
    info = decode_token(token)
    if not info:
        return None
    return get_user_by_id(db, info["user_id"])


@app.post("/register", response_model=UserResponse, status_code=201)
def register_endpoint(user: UserCreate, db: Session = Depends(get_db_session)):
    try:
        return create_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/login", response_model=TokenResponse)
def login_endpoint(username: str, password: str, db: Session = Depends(get_db_session)):
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = issue_token(user)
    return TokenResponse(access_token=token)


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user_endpoint(user_id: int, db: Session = Depends(get_db_session)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/users/{user_id}/deactivate")
def deactivate_endpoint(user_id: int, db: Session = Depends(get_db_session)):
    success = deactivate_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"deactivated": True}


@app.get("/verify")
def verify_token_endpoint(token: str, db: Session = Depends(get_db_session)):
    user = verify_token_and_get_user(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"user_id": user.id, "username": user.username, "role": user.role}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "auth_service"}
