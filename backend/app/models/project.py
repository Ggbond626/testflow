"""
项目相关数据模型
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Project(Base):
    """项目模型"""
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    owner: Mapped["User"] = relationship("User", back_populates="owned_projects")
    members: Mapped[List["ProjectMember"]] = relationship("ProjectMember", back_populates="project")
    modules: Mapped[List["Module"]] = relationship("Module", back_populates="project", cascade="all, delete-orphan")
    requirement_files: Mapped[List["RequirementFile"]] = relationship("RequirementFile", back_populates="project")
    
    def __repr__(self) -> str:
        return f"Project(id={self.id!r}, name={self.name!r}, owner_id={self.owner_id!r})"
