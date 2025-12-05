"""
需求点和测试点相关Schemas
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ==================== 需求点 Schemas ====================

class RequirementPointBase(BaseModel):
    """需求点基础Schema"""
    content: str = Field(..., min_length=1, description="需求点内容")
    priority: str = Field(default="medium", description="优先级：high/medium/low")


class RequirementPointCreate(RequirementPointBase):
    """创建需求点"""
    doc_id: Optional[int] = Field(None, description="来源文档ID")
    order_num: Optional[int] = Field(None, description="排序号")


class RequirementPointUpdate(BaseModel):
    """更新需求点"""
    content: Optional[str] = Field(None, min_length=1)
    priority: Optional[str] = None
    order_num: Optional[int] = None


class RequirementPointResponse(RequirementPointBase):
    """需求点响应"""
    model_config = {"from_attributes": True}
    
    id: int
    module_id: int
    doc_id: Optional[int]
    source: str  # ai_generated/manual
    order_num: int
    created_at: datetime
    updated_at: datetime


# ==================== 测试点 Schemas ====================

class TestPointBase(BaseModel):
    """测试点基础Schema"""
    title: str = Field(..., min_length=1, max_length=200, description="测试点标题")
    description: Optional[str] = Field(None, description="测试点描述")
    test_type: str = Field(default="functional", description="测试类型")
    priority: str = Field(default="medium", description="优先级")


class TestPointCreate(TestPointBase):
    """创建测试点"""
    requirement_id: Optional[int] = Field(None, description="关联需求点ID")
    order_num: Optional[int] = Field(None, description="排序号")


class TestPointUpdate(BaseModel):
    """更新测试点"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    test_type: Optional[str] = None
    priority: Optional[str] = None
    order_num: Optional[int] = None


class TestPointResponse(TestPointBase):
    """测试点响应"""
    model_config = {"from_attributes": True}
    
    id: int
    module_id: int
    requirement_id: Optional[int]
    source: str  # ai_generated/manual
    order_num: int
    created_at: datetime
    updated_at: datetime
