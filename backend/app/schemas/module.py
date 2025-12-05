"""
功能模块相关的Pydantic模式
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.module import ModuleStatus, ModulePriority


# 模块统计信息
class ModuleStats(BaseModel):
    """模块统计信息"""
    requirement_files_count: int = Field(default=0, description="需求文件数量")
    requirement_points_count: int = Field(default=0, description="需求点数量")
    test_points_count: int = Field(default=0, description="测试点数量")
    test_cases_count: int = Field(default=0, description="测试用例数量")
    test_cases_approved: int = Field(default=0, description="已审核测试用例数量")
    completion_rate: float = Field(default=0.0, description="完成率（0-100）")


# 模块负责人信息
class ModuleAssignee(BaseModel):
    """模块负责人信息"""
    id: int
    user_id: int
    username: str
    role: str = Field(description="角色：owner/member")
    assigned_at: datetime
    assigned_by: Optional[int] = None

    class Config:
        from_attributes = True


# 基础模块模式
class ModuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="模块名称")
    description: Optional[str] = Field(None, description="模块描述")
    priority: ModulePriority = Field(default=ModulePriority.MEDIUM, description="优先级")
    status: ModuleStatus = Field(default=ModuleStatus.PLANNING, description="状态")


# 模块创建模式
class ModuleCreate(ModuleBase):
    pass


# 模块更新模式
class ModuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模块名称")
    description: Optional[str] = Field(None, description="模块描述")
    priority: Optional[ModulePriority] = Field(None, description="优先级")
    status: Optional[ModuleStatus] = Field(None, description="状态")


# 模块响应模式
class Module(ModuleBase):
    id: int
    project_id: int
    order_num: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 模块详细信息（包含统计和负责人）
class ModuleDetail(Module):
    stats: ModuleStats = Field(default_factory=ModuleStats, description="统计信息")
    assignees: List[ModuleAssignee] = Field(default_factory=list, description="负责人列表")


# 模块列表响应
class ModuleListResponse(BaseModel):
    modules: List[ModuleDetail]
    total: int


# 模块排序请求
class ModuleReorderRequest(BaseModel):
    module_orders: List[dict] = Field(..., description="模块ID和排序号列表，格式：[{id: 1, order_num: 0}, ...]")


# 模块分配请求
class ModuleAssignmentCreate(BaseModel):
    user_id: int = Field(..., description="用户ID")
    role: str = Field(default="owner", description="角色：owner/member")


# 模块分配响应
class ModuleAssignmentResponse(ModuleAssignee):
    pass


# 项目统计信息（包含模块数据）
class ProjectStatsResponse(BaseModel):
    """项目统计信息响应"""
    module_count: int = Field(default=0, description="模块数量")
    member_count: int = Field(default=0, description="成员数量")
    requirement_points_count: int = Field(default=0, description="需求点数量")
    test_cases_count: int = Field(default=0, description="测试用例数量")
    modules_by_status: dict = Field(default_factory=dict, description="按状态分组的模块数量")
    modules_by_priority: dict = Field(default_factory=dict, description="按优先级分组的模块数量")
    recent_activities: List[dict] = Field(default_factory=list, description="最近的活动")

