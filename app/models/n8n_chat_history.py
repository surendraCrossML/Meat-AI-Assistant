from sqlalchemy import Column, Integer, String, Text
from app.db.base import Base


class N8nChatHistory(Base):
    __tablename__ = "n8n_chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    message = Column(Text, nullable=False)   # stores JSON string of role + content
