import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(100), nullable=False)
    user_email = Column(String(255), unique=True, index=True, nullable=False)
    user_password = Column(String(255), nullable=False)  # stored as bcrypt hash
    user_role = Column(Enum(UserRole), nullable=False, default=UserRole.user)
    user_created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
