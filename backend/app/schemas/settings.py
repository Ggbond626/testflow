"""
系统设置相关的Pydantic模式
包含测试分类、测试设计方法和并发配置的数据验证模式
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ============== Test Category Schemas ==============

class TestCategoryBase(BaseModel):
    """测试分类基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="测试分类名称")
    code: str = Field(..., min_length=1, max_length=50, description="测试分类代码（唯一标识）")
    description: Optional[str] = Field(None, max_length=500, description="测试分类描述")
    is_active: bool = Field(default=True, description="是否启用")
    order_index: int = Field(default=0, ge=0, description="排序索引")


class TestCategoryCreate(TestCategoryBase):
    """测试分类创建模式"""
    pass


class TestCategoryUpdate(BaseModel):
    """测试分类更新模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="测试分类名称")
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="测试分类代码")
    description: Optional[str] = Field(None, max_length=500, description="测试分类描述")
    is_active: Optional[bool] = Field(None, description="是否启用")
    order_index: Optional[int] = Field(None, ge=0, description="排序索引")


class TestCategoryResponse(TestCategoryBase):
    """测试分类响应模式"""
    id: int
    is_default: bool = Field(description="是否为系统默认")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Test Design Method Schemas ==============

class TestDesignMethodBase(BaseModel):
    """测试设计方法基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="测试设计方法名称")
    code: str = Field(..., min_length=1, max_length=50, description="测试设计方法代码（唯一标识）")
    description: Optional[str] = Field(None, max_length=500, description="测试设计方法描述")
    is_active: bool = Field(default=True, description="是否启用")
    order_index: int = Field(default=0, ge=0, description="排序索引")


class TestDesignMethodCreate(TestDesignMethodBase):
    """测试设计方法创建模式"""
    pass


class TestDesignMethodUpdate(BaseModel):
    """测试设计方法更新模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="测试设计方法名称")
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="测试设计方法代码")
    description: Optional[str] = Field(None, max_length=500, description="测试设计方法描述")
    is_active: Optional[bool] = Field(None, description="是否启用")
    order_index: Optional[int] = Field(None, ge=0, description="排序索引")


class TestDesignMethodResponse(TestDesignMethodBase):
    """测试设计方法响应模式"""
    id: int
    is_default: bool = Field(description="是否为系统默认")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Concurrency Config Schema ==============

class ConcurrencyConfig(BaseModel):
    """并发配置模式
    
    用于控制AI生成任务的并发执行参数
    """
    max_concurrent_tasks: int = Field(
        default=3,
        ge=1,
        le=10,
        description="最大并发任务数（范围：1-10）"
    )
    task_timeout: int = Field(
        default=300,
        ge=60,
        le=600,
        description="任务超时时间，单位秒（范围：60-600）"
    )
    retry_count: int = Field(
        default=3,
        ge=0,
        le=5,
        description="失败重试次数（范围：0-5）"
    )
    queue_size: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="任务队列大小（范围：10-1000）"
    )


# ============== System Config Schemas ==============

class SystemConfigBase(BaseModel):
    """系统配置基础模式"""
    config_key: str = Field(..., min_length=1, max_length=100, description="配置键")
    config_value: dict = Field(..., description="配置值（JSON格式）")
    description: Optional[str] = Field(None, max_length=500, description="配置描述")


class SystemConfigCreate(SystemConfigBase):
    """系统配置创建模式"""
    pass


class SystemConfigUpdate(BaseModel):
    """系统配置更新模式"""
    config_value: Optional[dict] = Field(None, description="配置值（JSON格式）")
    description: Optional[str] = Field(None, max_length=500, description="配置描述")


class SystemConfigResponse(SystemConfigBase):
    """系统配置响应模式"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
