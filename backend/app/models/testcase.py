"""
测试用例相关数据模型
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class Priority(str, enum.Enum):
    """优先级枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestPointStatus(str, enum.Enum):
    """测试点状态枚举"""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    TEST_CASE_GENERATED = "test_case_generated"
    COMPLETED = "completed"


class TestMethod(str, enum.Enum):
    """测试方法枚举"""
    BLACK_BOX = "black_box"
    WHITE_BOX = "white_box"
    GRAY_BOX = "gray_box"


class TestCaseStatus(str, enum.Enum):
    """测试用例状态枚举"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewStatus(str, enum.Enum):
    """评审状态枚举"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class TestPoint(Base):
    """测试点模型（支持新架构）"""
    __tablename__ = "test_points"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 关联到需求点（级联删除：删除需求点时自动删除测试点）
    requirement_point_id: Mapped[Optional[int]] = mapped_column(ForeignKey("requirement_points.id", ondelete="CASCADE"), index=True)
    
    # 关联到模块（新架构）
    module_id: Mapped[Optional[int]] = mapped_column(ForeignKey("modules.id", ondelete="SET NULL"), index=True)
   
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 测试点内容
    test_type: Mapped[str] = mapped_column(String(50), default="functional")  # 测试类型（动态，由系统设置管理）
    design_method: Mapped[Optional[str]] = mapped_column(String(50))  # 测试设计方法（等价类、边界值等）
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # 优先级
    
    # 状态（保留兼容性，但改为可选）
    status: Mapped[Optional[TestPointStatus]] = mapped_column(Enum(TestPointStatus), default=TestPointStatus.DRAFT)
    
    # 编辑标记（保留兼容性）
    created_by_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    edited_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 用户信息
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    module: Mapped[Optional["Module"]] = relationship("Module", back_populates="test_points")
    requirement_point: Mapped[Optional["RequirementPoint"]] = relationship("RequirementPoint", back_populates="test_points", foreign_keys=[requirement_point_id])
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    updater: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by])
    test_cases: Mapped[List["TestCase"]] = relationship("TestCase", back_populates="test_point", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"TestPoint(id={self.id!r}, content={self.content[:50]!r}...)"


class TestCase(Base):
    """测试用例模型（完全可编辑）"""
    __tablename__ = "test_cases"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 关联到测试点（级联删除：删除测试点时自动删除测试用例）
    test_point_id: Mapped[Optional[int]] = mapped_column(ForeignKey("test_points.id", ondelete="CASCADE"), index=True)
    
    # 关联到模块（新架构）
    module_id: Mapped[Optional[int]] = mapped_column(ForeignKey("modules.id", ondelete="SET NULL"), index=True)
    import_module_name: Mapped[Optional[str]] = mapped_column(String(100))  # 导入时的模块名称（当未匹配到系统模块时使用）
    
    # 直接关联到项目（用于查询未分类用例）
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    preconditions: Mapped[Optional[str]] = mapped_column(Text)
    test_steps: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # JSON格式存储步骤列表
    expected_result: Mapped[Optional[str]] = mapped_column(Text)
    
    # 设计方法（等价类划分、边界值分析等）
    design_method: Mapped[Optional[str]] = mapped_column(String(50))
    
    # 优先级（从测试点继承）
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # high/medium/low
    
    # 保留旧字段以兼容
    test_method: Mapped[Optional[TestMethod]] = mapped_column(Enum(TestMethod))
    test_category: Mapped[Optional[str]] = mapped_column(String(50))  # 测试类别（动态，由系统设置管理）
    status: Mapped[TestCaseStatus] = mapped_column(Enum(TestCaseStatus), default=TestCaseStatus.DRAFT)
    
    # 编辑标记
    created_by_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    edited_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 用户信息
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    module: Mapped[Optional["Module"]] = relationship("Module", back_populates="test_cases")
    test_point: Mapped[Optional["TestPoint"]] = relationship("TestPoint", back_populates="test_cases")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    updater: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by])
    reviews: Mapped[List["TestCaseReview"]] = relationship("TestCaseReview", back_populates="test_case")
    
    def __repr__(self) -> str:
        return f"TestCase(id={self.id!r}, title={self.title!r}, status={self.status!r})"


class TestCaseReview(Base):
    """测试用例评审模型"""
    __tablename__ = "test_case_reviews"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"), nullable=False)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.PENDING)
    comments: Mapped[Optional[str]] = mapped_column(Text)
    
    # 时间戳
    review_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    test_case: Mapped["TestCase"] = relationship("TestCase", back_populates="reviews")
    reviewer: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"TestCaseReview(id={self.id!r}, test_case_id={self.test_case_id!r}, status={self.status!r})"


class ExecutionStatus(str, enum.Enum):
    """测试执行状态枚举"""
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    IN_PROGRESS = "in_progress"


class TestCaseExecution(Base):
    """测试用例执行记录模型"""
    __tablename__ = "test_case_executions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"), nullable=False)
    executed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    execution_time: Mapped[Optional[float]] = mapped_column(Float)  # 执行耗时（秒）
    
    # 执行环境信息
    environment: Mapped[Optional[str]] = mapped_column(String(100))  # 测试环境
    build_version: Mapped[Optional[str]] = mapped_column(String(100))  # 构建版本
    
    # 时间戳
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    test_case: Mapped["TestCase"] = relationship("TestCase")
    executor: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"TestCaseExecution(id={self.id!r}, test_case_id={self.test_case_id!r}, status={self.status!r})"
