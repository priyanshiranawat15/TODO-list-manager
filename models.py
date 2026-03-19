from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP
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
    
class Task(Base):
    __tablename__ ="tasks"
    
    id = Column(Integer,index=True, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"),nullable=False)
    description = Column(String(100), nullable=False)
    status = Column(String(20))
    create_at = Column(TIMESTAMP, server_default=func.now())
    update_at = Column(TIMESTAMP, server_default=func.now())
    assignee_id = Column(Integer, nullable=True)
    
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
    
    
    
    
