"""
LifeOS Auth Router — Hardened Authentication
==============================================
Secure signup, login, and session management with
structured logging, role support, and input validation.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
from beanie import PydanticObjectId
from models import User, UserRole
from auth import (
    get_password_hash, verify_password, create_access_token,
    decode_access_token, ACCESS_TOKEN_EXPIRE_MINUTES,
)
from utils.logger import get_logger
from utils.security import sanitize_string, MAX_NAME_LENGTH

log = get_logger("router.auth")

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=MAX_NAME_LENGTH)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class AuthResponse(BaseModel):
    user_id: str
    token: str
    role: str = "user"


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Extracts and validates the current user from the JWT token."""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    user_str_id: str = payload.get("sub")

    try:
        oid = PydanticObjectId(user_str_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session ID (Please login again)",
        )

    user = await User.get(oid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    log.info(f"Signup attempt: email={request.email}")

    existing_user = await User.find_one(User.email == request.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pwd = get_password_hash(request.password)
    user = User(
        name=sanitize_string(request.name, MAX_NAME_LENGTH),
        email=request.email,
        hashed_password=hashed_pwd,
        role=UserRole.USER,
    )
    await user.insert()

    token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    log.info(f"User registered: id={user.id}")
    return {"user_id": str(user.id), "token": token, "role": user.role}


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    log.info(f"Login attempt: email={request.email}")

    user = await User.find_one(User.email == request.email)
    if not user:
        log.warning(f"Login failed: email not found — {request.email}")
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not verify_password(request.password, user.hashed_password):
        log.warning(f"Login failed: password mismatch — user={user.id}")
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    log.info(f"Login successful: user={user.id}")
    return {"user_id": str(user.id), "token": token, "role": user.role}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "user_id": str(current_user.id),
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "timezone": current_user.timezone,
    }
