"""
用户相关数据模型
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"


class ProjectRole(str, enum.Enum):
    """项目角色枚举"""
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    owned_projects: Mapped[List["Project"]] = relationship("Project", back_populates="owner")
    project_memberships: Mapped[List["ProjectMember"]] = relationship("ProjectMember", back_populates="user")
    module_assignments: Mapped[List["ModuleAssignment"]] = relationship("ModuleAssignment", back_populates="user", foreign_keys="[ModuleAssignment.user_id]")
    
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, email={self.email!r})"


class ProjectMember(Base):
    """项目成员关系模型"""
    __tablename__ = "project_members"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[ProjectRole] = mapped_column(Enum(ProjectRole), default=ProjectRole.MEMBER)
    
    # 时间戳
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    project: Mapped["Project"] = relationship("Project", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="project_memberships")
    
    def __repr__(self) -> str:
        return f"ProjectMember(project_id={self.project_id!r}, user_id={self.user_id!r}, role={self.role!r})"
