"""
测试用例相关的schemas
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class Priority(str, Enum):
    """优先级枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestPointStatus(str, Enum):
    """测试点状态枚举"""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    TEST_CASE_GENERATED = "test_case_generated"
    COMPLETED = "completed"


class TestMethod(str, Enum):
    """测试方法枚举"""
    BLACK_BOX = "black_box"
    WHITE_BOX = "white_box"
    GRAY_BOX = "gray_box"


class TestCaseStatus(str, Enum):
    """测试用例状态枚举"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


# ========== 测试点 Schemas ==========

class TestPointBase(BaseModel):
    """测试点基础schema"""
    content: str
    test_type: str = "functional"  # 测试类型（动态，由系统设置管理）
    design_method: Optional[str] = None  # 测试设计方法
    priority: Priority = Priority.MEDIUM
    status: TestPointStatus = TestPointStatus.DRAFT


class TestPointCreate(TestPointBase):
    """创建测试点schema"""
    requirement_point_id: int


class TestPointUpdate(BaseModel):
    """更新测试点schema"""
    content: Optional[str] = None
    test_type: Optional[str] = None  # 测试类型（动态）
    design_method: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[TestPointStatus] = None


class TestPoint(TestPointBase):
    """测试点schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    requirement_point_id: int
    design_method: Optional[str] = None
    created_by_ai: bool
    edited_by_user: bool
    created_by: int
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# ========== 测试用例 Schemas ==========

class TestCaseBase(BaseModel):
    """测试用例基础schema"""
    title: str
    description: Optional[str] = None
    preconditions: Optional[str] = None
    test_steps: Optional[List[Dict[str, Any]]] = None
    expected_result: Optional[str] = None
    test_method: Optional[TestMethod] = TestMethod.BLACK_BOX
    test_category: Optional[str] = "functional"  # 测试类别（动态，由系统设置管理）
    status: TestCaseStatus = TestCaseStatus.DRAFT


class TestCaseCreate(BaseModel):
    """创建测试用例schema - 用于模块级别的测试用例创建"""
    title: str = Field(..., min_length=1, description="测试用例标题（必填）")
    test_point_id: int = Field(..., description="关联的测试点ID（必填）")
    description: Optional[str] = None
    preconditions: Optional[str] = None
    test_steps: Optional[List[Dict[str, Any]]] = None
    expected_result: Optional[str] = None
    design_method: Optional[str] = None  # 设计方法（等价类划分、边界值等）
    test_method: Optional[str] = "black_box"
    test_category: Optional[str] = "functional"
    status: Optional[str] = "draft"
    created_by_ai: bool = False
    
    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('标题不能为空')
        return v.strip()


class TestCaseUpdate(BaseModel):
    """更新测试用例schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    preconditions: Optional[str] = None
    test_steps: Optional[List[Dict[str, Any]]] = None
    expected_result: Optional[str] = None
    design_method: Optional[str] = None  # 设计方法
    test_method: Optional[str] = None
    test_category: Optional[str] = None
    status: Optional[str] = None
    
    @field_validator('title')
    @classmethod
    def title_not_empty_if_provided(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('标题不能为空')
        return v.strip() if v else v


class TestCase(TestCaseBase):
    """测试用例schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    test_point_id: Optional[int] = None
    module_id: Optional[int] = None
    created_by_ai: bool
    edited_by_user: bool
    created_by: int
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# ========== 测试用例响应 Schemas ==========

class TestCaseResponse(BaseModel):
    """测试用例响应schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    test_point_id: Optional[int] = None
    module_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    preconditions: Optional[str] = None
    test_steps: Optional[List[Dict[str, Any]]] = None
    expected_result: Optional[str] = None
    design_method: Optional[str] = None  # 设计方法
    test_method: Optional[str] = None
    test_category: Optional[str] = None
    status: str
    created_by_ai: bool
    edited_by_user: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class TestPointWithCasesResponse(BaseModel):
    """包含测试用例的测试点响应"""
    id: int
    content: str
    test_type: str
    priority: str
    created_by_ai: bool
    test_cases: List[TestCaseResponse] = []


class TestCaseHierarchyResponse(BaseModel):
    """测试用例层级结构响应（按测试点分组）"""
    test_points: List[TestPointWithCasesResponse]
    total_test_points: int
    total_test_cases: int


class TestCaseBatchCreate(BaseModel):
    """批量创建测试用例请求"""
    test_cases: List[TestCaseCreate]
    clear_existing: bool = False


class TestCaseBatchCreateResponse(BaseModel):
    """批量创建测试用例响应"""
    success: bool
    created_count: int
    deleted_count: int = 0
    test_cases: List[TestCaseResponse] = []


# ========== 关联查询 Schemas ==========

class TestCaseWithPoint(TestCase):
    """包含测试点信息的测试用例"""
    test_point: TestPoint


class TestPointWithCases(TestPoint):
    """包含测试用例列表的测试点"""
    test_cases: List[TestCase] = []


class RequirementPointWithTestPoints(BaseModel):
    """包含测试点列表的需求点"""
    id: int
    content: str
    order_index: int
    status: str
    test_points: List[TestPointWithCases] = []


# ========== 层级结构 Schemas ==========

class TestHierarchy(BaseModel):
    """测试层级结构"""
    project_id: int
    file_id: Optional[int] = None
    requirement_points: List[RequirementPointWithTestPoints]
    statistics: Dict[str, int]


# ========== 导出 Schemas ==========

class ExportRequest(BaseModel):
    """导出请求schema"""
    format: str = Field(..., description="导出格式: excel, csv, json, markdown")
    include_metadata: bool = Field(False, description="是否包含元数据")
    task_id: Optional[int] = Field(None, description="生成任务ID")
    file_id: Optional[int] = Field(None, description="需求文件ID")
