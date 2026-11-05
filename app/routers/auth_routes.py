"""HTTP layer only: receives requests, calls services, returns responses."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, get_current_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.auth_schema import (
    ChangePasswordRequest, LoginRequest, LoginResponse, MessageResponse,
    RegisterRequest, RegisterResponse, UserOut, VerifyTokenRequest, VerifyTokenResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = auth_service.register_user(db, data)
    return RegisterResponse(message="User registered successfully", user_id=user.id,
                            full_name=user.full_name, email=user.email, is_active=user.is_active)


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user, token = auth_service.login_user(db, data)
    return LoginResponse(message="Login successful", access_token=token,
                         token_type="bearer", user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/verify-token", response_model=VerifyTokenResponse)
def verify_token(data: VerifyTokenRequest):
    payload = decode_access_token(data.token)  # raises 401 if invalid/expired
    return VerifyTokenResponse(
        valid=True,
        user_id=int(payload["sub"]),
        role=payload["role"],
        expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
    )


@router.post("/change-password", response_model=MessageResponse)
def change_password(data: ChangePasswordRequest,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    auth_service.change_user_password(db, current_user, data)
    return MessageResponse(message="Password changed successfully")
