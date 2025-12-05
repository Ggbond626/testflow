from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional


class AIModelBase(BaseModel):
    """AI模型基础模型"""
    model_config = {"protected_namespaces": ()}
    
    name: str = Field(..., min_length=1, max_length=100, description="模型显示名称")
    model_id: str = Field(..., min_length=1, max_length=100, description="模型ID")
    base_url: str = Field(..., description="API基础地址")
    api_key: str = Field(..., min_length=10, description="API密钥")
    max_tokens: int = Field(default=4000, ge=100, le=128000, description="最大令牌数")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    is_active: bool = Field(default=True, description="是否激活")


class AIModelCreate(AIModelBase):
    """创建AI模型"""
    pass


class AIModelUpdate(BaseModel):
    """更新AI模型"""
    model_config = {"protected_namespaces": ()}
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模型显示名称")
    model_id: Optional[str] = Field(None, min_length=1, max_length=100, description="模型ID")
    base_url: Optional[str] = Field(None, description="API基础地址")
    api_key: Optional[str] = Field(None, min_length=10, description="API密钥")
    max_tokens: Optional[int] = Field(None, ge=100, le=128000, description="最大令牌数")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="温度参数")
    is_active: Optional[bool] = Field(None, description="是否激活")


class AIModelResponse(AIModelBase):
    """AI模型响应"""
    model_config = {"protected_namespaces": (), "from_attributes": True}
    
    id: int
    created_at: datetime
    updated_at: datetime


class AIModelTest(BaseModel):
    """AI模型测试"""
    message: str = Field(default="Hello, this is a test message.", description="测试消息")


class AIModelTestResponse(BaseModel):
    """AI模型测试响应"""
    success: bool
    message: str
    response: Optional[dict] = None
    error: Optional[str] = None
