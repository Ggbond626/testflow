"""
智能体相关schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


class AgentType(str, Enum):
    """智能体类型枚举"""
    REQUIREMENT_SPLITTER = "requirement_splitter"
    TEST_POINT_GENERATOR = "test_point_generator"
    TEST_CASE_DESIGNER = "test_case_designer"
    TEST_CASE_OPTIMIZER = "test_case_optimizer"


class AgentBase(BaseModel):
    """智能体基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="智能体名称")
    type: AgentType = Field(..., description="智能体类型")
    ai_model_id: int = Field(..., description="关联的AI模型ID")
    prompt_template: Optional[str] = Field(None, description="提示词模板")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=128000, ge=100, le=128000, description="最大令牌数")
    is_active: bool = Field(default=True, description="是否激活")


class AgentCreate(AgentBase):
    """创建智能体"""
    pass


class AgentUpdate(BaseModel):
    """更新智能体"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="智能体名称")
    type: Optional[AgentType] = Field(None, description="智能体类型")
    ai_model_id: Optional[int] = Field(None, description="关联的AI模型ID")
    prompt_template: Optional[str] = Field(None, description="提示词模板")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(None, ge=100, le=128000, description="最大令牌数")
    is_active: Optional[bool] = Field(None, description="是否激活")


class AgentResponse(AgentBase):
    """智能体响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime


class AgentListResponse(BaseModel):
    """智能体列表响应"""
    agents: list[AgentResponse]
    total: int


class AgentExecuteRequest(BaseModel):
    """执行智能体请求"""
    prompt: str = Field(..., min_length=1, description="输入提示")
    context: Optional[dict] = Field(None, description="上下文信息")


class AgentExecuteResponse(BaseModel):
    """执行智能体响应"""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    usage: Optional[dict] = None
