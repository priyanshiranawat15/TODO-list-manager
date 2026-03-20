from sqlalchemy import Boolean, Column, Integer, String, Text, ForeignKey, TIMESTAMP, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__="users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    password = Column(Text, nullable=False)
    create_at = Column(TIMESTAMP, server_default=func.now())
    update_at = Column(TIMESTAMP, server_default=func.now())
    
    tasks = relationship("Task",back_populates="user")
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    agent_session = relationship("AgentSession", back_populates="user", uselist=False)
    messages = relationship("Message", back_populates="user")
    
class Task(Base):
    __tablename__ ="tasks"
    
    id = Column(Integer,index=True, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"),nullable=False)
    description = Column(String(100), nullable=False)
    status = Column(String(20))
    create_at = Column(TIMESTAMP, server_default=func.now())
    update_at = Column(TIMESTAMP, server_default=func.now())
    assignee_id = Column(Integer, nullable=True)
    isDeleted = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    deletedAt = Column(TIMESTAMP, nullable=True)
    
    user= relationship("User",back_populates="tasks")
class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer , ForeignKey("users.id"), nullable=False, unique=True)
    first_name = Column(String(50),nullable=False)
    last_name = Column(String(50),nullable=False)
    profile_picture = Column(String(255), nullable=True)
    create_at = Column(TIMESTAMP, server_default=func.now())
    update_at = Column(TIMESTAMP, server_default=func.now())
    
    user = relationship("User", back_populates="profile")
    
class AgentSession(Base):
    __tablename__ = "agent_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    last_response_id = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="agent_session")
    
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("agent_sessions.id"), nullable=False)
    role = Column(String(20))  
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    agent_session = relationship("AgentSession", back_populates="messages")

