"""
AI配置相关数据模型
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class AgentType(str, enum.Enum):
    """智能体类型枚举"""
    REQUIREMENT_SPLITTER = "requirement_splitter"
    TEST_POINT_GENERATOR = "test_point_generator"
    TEST_CASE_DESIGNER = "test_case_designer"
    TEST_CASE_OPTIMIZER = "test_case_optimizer"


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AIModel(Base):
    """AI模型配置模型"""
    __tablename__ = "ai_models"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="openai")  # 模型提供商
    model_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)  # gpt-4-turbo-preview, etc
    api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default="")  # 可选，支持空值
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)  # API基础URL
    max_tokens: Mapped[int] = mapped_column(Integer, default=4000)  # 最大令牌数
    temperature: Mapped[float] = mapped_column(Float, default=0.7)  # 温度参数
    stream_support: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否支持流式输出
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 用户信息
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    creator: Mapped["User"] = relationship("User")
    agents: Mapped[List["Agent"]] = relationship("Agent", back_populates="ai_model")
    
    def __repr__(self) -> str:
        return f"AIModel(id={self.id!r}, name={self.name!r}, provider={self.provider!r})"


class Agent(Base):
    """智能体配置模型"""
    __tablename__ = "agents"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    type: Mapped[AgentType] = mapped_column(Enum(AgentType), nullable=False)
    ai_model_id: Mapped[int] = mapped_column(ForeignKey("ai_models.id"), nullable=False)
    
    # AI参数配置
    prompt_template: Mapped[Optional[str]] = mapped_column(Text)  # 提示词模板
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)  # 系统提示词
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=128000)  # 128k tokens
    
    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 用户信息
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    ai_model: Mapped["AIModel"] = relationship("AIModel", back_populates="agents")
    creator: Mapped["User"] = relationship("User")
    task_logs: Mapped[List["TaskLog"]] = relationship("TaskLog", back_populates="agent")
    
    def __repr__(self) -> str:
        return f"Agent(id={self.id!r}, name={self.name!r}, type={self.type!r})"


class TaskLog(Base):
    """任务执行日志模型"""
    __tablename__ = "task_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    input_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    execution_time: Mapped[Optional[float]] = mapped_column(Float)  # 执行时间（秒）
    
    # 用户信息
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    agent: Mapped["Agent"] = relationship("Agent", back_populates="task_logs")
    creator: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"TaskLog(id={self.id!r}, task_type={self.task_type!r}, status={self.status!r})"
