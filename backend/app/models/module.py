"""
功能模块相关数据模型
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ModuleStatus(str, enum.Enum):
    """模块状态枚举"""
    PLANNING = "planning"  # 规划中
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    ON_HOLD = "on_hold"  # 暂停


class ModulePriority(str, enum.Enum):
    """模块优先级枚举"""
    LOW = "low"  # 低
    MEDIUM = "medium"  # 中
    HIGH = "high"  # 高
    CRITICAL = "critical"  # 紧急


class Module(Base):
    """功能模块模型"""
    __tablename__ = "modules"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[ModulePriority] = mapped_column(Enum(ModulePriority), default=ModulePriority.MEDIUM)
    status: Mapped[ModuleStatus] = mapped_column(Enum(ModuleStatus), default=ModuleStatus.PLANNING)
    order_num: Mapped[int] = mapped_column(Integer, default=0)  # 排序序号
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    project: Mapped["Project"] = relationship("Project", back_populates="modules")
    assignments: Mapped[List["ModuleAssignment"]] = relationship("ModuleAssignment", back_populates="module", cascade="all, delete-orphan")
    requirement_files: Mapped[List["RequirementFile"]] = relationship("RequirementFile", back_populates="module")
    requirement_points: Mapped[List["RequirementPoint"]] = relationship("RequirementPoint", back_populates="module")
    test_points: Mapped[List["TestPoint"]] = relationship("TestPoint", back_populates="module")
    test_cases: Mapped[List["TestCase"]] = relationship("TestCase", back_populates="module")
    
    def __repr__(self) -> str:
        return f"Module(id={self.id!r}, name={self.name!r}, project_id={self.project_id!r})"


class ModuleAssignment(Base):
    """模块责任分配模型"""
    __tablename__ = "module_assignments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), default="owner")  # owner, member
    assigned_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    # 时间戳
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    module: Mapped["Module"] = relationship("Module", back_populates="assignments")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="module_assignments")
    assigner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_by])
    
    def __repr__(self) -> str:
        return f"ModuleAssignment(module_id={self.module_id!r}, user_id={self.user_id!r}, role={self.role!r})"

