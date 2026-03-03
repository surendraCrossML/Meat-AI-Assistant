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


class DocumentSearchRequest(BaseModel):
    query: str
    description: Optional[str] = None


class KeywordExtractionResponse(BaseModel):
    keywords: list[str]
    recipe_related_keywords: list[str]
    beef_related_keywords: list[str]
    query_summary: str


class DocumentQueryRequest(BaseModel):
    query: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the best beef recipes for a healthy diet?"
            }
        }


class DocumentQueryResponse(BaseModel):
    user_query: str
    extracted_keywords: KeywordExtractionResponse
    matching_documents: list[DocumentRead]
    summary: str
    agent_response: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_query": "What are the best beef recipes for a healthy diet?",
                "extracted_keywords": {
                    "keywords": ["beef", "recipes", "healthy"],
                    "recipe_related_keywords": ["recipes", "cooking"],
                    "beef_related_keywords": ["beef"],
                    "query_summary": "Looking for healthy beef recipes"
                },
                "matching_documents": [],
                "summary": "Found 0 documents matching your search",
                "agent_response": "No documents found to answer your query."
            }
        }