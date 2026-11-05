"""Pydantic request/response models and password-strength validation."""
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


def validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes (bcrypt limit)")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain an uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain a lowercase letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain a digit")
    if not re.search(r"[^A-Za-z0-9]", value):
        raise ValueError("Password must contain a special character")
    return value


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str
    confirm_password: str

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Full name must have at least 2 characters")
        return v

    @field_validator("email")
    @classmethod
    def lower_email(cls, v: str) -> str:
        return v.lower()

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("password and confirm_password do not match")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def lower_email(cls, v: str) -> str:
        return v.lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RegisterResponse(BaseModel):
    message: str
    user_id: int
    full_name: str
    email: EmailStr
    is_active: bool


class LoginResponse(BaseModel):
    message: str
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class VerifyTokenRequest(BaseModel):
    token: str = Field(min_length=1)


class VerifyTokenResponse(BaseModel):
    valid: bool
    user_id: int
    role: str
    expires_at: datetime


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str
    confirm_new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @model_validator(mode="after")
    def check(self):
        if self.new_password != self.confirm_new_password:
            raise ValueError("new_password and confirm_new_password do not match")
        if self.new_password == self.current_password:
            raise ValueError("New password must be different from the current password")
        return self


class MessageResponse(BaseModel):
    message: str
