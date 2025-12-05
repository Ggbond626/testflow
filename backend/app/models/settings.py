"""
系统设置相关数据模型
包含测试分类、测试设计方法和系统配置
"""
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class TestCategory(Base):
    """测试分类模型"""
    __tablename__ = "test_categories"
    __table_args__ = (
        UniqueConstraint('code', name='uq_test_categories_code'),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"TestCategory(id={self.id!r}, name={self.name!r}, code={self.code!r})"


class TestDesignMethod(Base):
    """测试设计方法模型"""
    __tablename__ = "test_design_methods"
    __table_args__ = (
        UniqueConstraint('code', name='uq_test_design_methods_code'),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"TestDesignMethod(id={self.id!r}, name={self.name!r}, code={self.code!r})"


class SystemConfig(Base):
    """系统配置模型"""
    __tablename__ = "system_configs"
    __table_args__ = (
        UniqueConstraint('config_key', name='uq_system_configs_key'),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    config_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    config_value: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"SystemConfig(id={self.id!r}, config_key={self.config_key!r})"
