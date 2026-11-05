"""Password hashing, JWT creation/validation and the reusable auth dependency."""
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import get_db
from app.models.user_model import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)  # we raise our own 401


# ---------- passwords ----------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


# ---------- JWT ----------
def create_access_token(user_id: int, role: str, expires_minutes: Optional[int] = None) -> str:
    minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES if expires_minutes is None else expires_minutes
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Validate signature + expiry. Raises 401 for anything wrong."""
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token has expired",
                            headers={"WWW-Authenticate": "Bearer"})
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token",
                            headers={"WWW-Authenticate": "Bearer"})


# ---------- reusable dependencies (other services/routes can reuse these) ----------
def get_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated: Bearer token missing",
                            headers={"WWW-Authenticate": "Bearer"})
    return decode_access_token(credentials.credentials)


def get_current_user(payload: dict = Depends(get_token_payload),
                     db: Session = Depends(get_db)) -> User:
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token claims")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is inactive")
    return user
