from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole


# Auth

class UserRegister(BaseModel):
    user_name: str
    user_email: EmailStr
    user_password: str
    user_role: Optional[UserRole] = UserRole.user


class UserLogin(BaseModel):
    user_email: EmailStr
    user_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: int
    user_name: str
    user_email: str
    user_role: UserRole

    model_config = {"from_attributes": True}


# Documents 

class DocumentRead(BaseModel):
    id: int
    document_name: str
    document_type: str
    document_size: int
    description: Optional[str]
    s3_key: str
    user_id: int

    model_config = {"from_attributes": True}


class PresignedURLResponse(BaseModel):
    presigned_url: str
    expires_in_seconds: int = 3600
