"""
需求相关数据模型
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class RequirementStatus(str, enum.Enum):
    """需求点状态枚举"""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    COMPLETED = "completed"


class RequirementFile(Base):
    """需求文件模型"""
    __tablename__ = "requirement_files"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    module_id: Mapped[Optional[int]] = mapped_column(ForeignKey("modules.id", ondelete="SET NULL"), index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # 文件内容提取
    extracted_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_extracted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    extract_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 图片信息
    has_images: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    image_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # 时间戳
    upload_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    project: Mapped["Project"] = relationship("Project", back_populates="requirement_files")
    module: Mapped[Optional["Module"]] = relationship("Module", back_populates="requirement_files")
    uploader: Mapped["User"] = relationship("User")
    requirement_points: Mapped[List["RequirementPoint"]] = relationship("RequirementPoint", back_populates="requirement_file")
    images: Mapped[List["RequirementImage"]] = relationship("RequirementImage", back_populates="requirement_file", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"RequirementFile(id={self.id!r}, filename={self.filename!r}, project_id={self.project_id!r})"


class RequirementPoint(Base):
    """需求点模型（支持新架构）"""
    __tablename__ = "requirement_points"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 关联到需求文件（旧架构，兼容性）
    requirement_file_id: Mapped[Optional[int]] = mapped_column(ForeignKey("requirement_files.id", ondelete="SET NULL"), index=True)
    
    # 关联到模块（新架构）
    module_id: Mapped[Optional[int]] = mapped_column(ForeignKey("modules.id", ondelete="SET NULL"), index=True)
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # high/medium/low
    source: Mapped[str] = mapped_column(String(20), default="manual")  # ai_generated/manual
    order_num: Mapped[int] = mapped_column("order_index", Integer, default=0, index=True)  # 排序号，数据库列名为order_index
    
    # 状态（保留以兼容旧数据）
    status: Mapped[Optional[RequirementStatus]] = mapped_column(Enum(RequirementStatus), default=RequirementStatus.DRAFT)
    
    # 编辑标记（保留以兼容旧数据）
    created_by_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    edited_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 用户信息
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    module: Mapped[Optional["Module"]] = relationship("Module", back_populates="requirement_points")
    requirement_file: Mapped[Optional["RequirementFile"]] = relationship("RequirementFile", back_populates="requirement_points")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    updater: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by])
    test_points: Mapped[List["TestPoint"]] = relationship(
        "TestPoint", 
        back_populates="requirement_point",
        foreign_keys="[TestPoint.requirement_point_id]",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"RequirementPoint(id={self.id!r}, content={self.content[:50]!r}...)"
