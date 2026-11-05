"""Business logic + database operations for authentication."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user_model import User
from app.schemas.auth_schema import ChangePasswordRequest, LoginRequest, RegisterRequest

DEFAULT_ROLE = "user"


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email.lower()).first()


def register_user(db: Session, data: RegisterRequest) -> User:
    if get_user_by_email(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email is already registered")
    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=DEFAULT_ROLE,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, data: LoginRequest):
    user = get_user_by_email(db, data.email)
    # same message for unknown email and wrong password -> no user enumeration
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is inactive")
    token = create_access_token(user.id, user.role)
    return user, token


def change_user_password(db: Session, user: User, data: ChangePasswordRequest) -> None:
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    user.password_hash = hash_password(data.new_password)
    db.commit()
