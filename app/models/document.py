from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(String(255), nullable=False)
    document_type = Column(String(100), nullable=False)          # e.g. "application/pdf"
    document_size = Column(BigInteger, nullable=False)           # bytes
    description = Column(Text, nullable=True)
    s3_key = Column(String(512), nullable=False, unique=True)    # S3 object key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    document_created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    document_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    owner = relationship("User", back_populates="documents", foreign_keys=[user_id])
