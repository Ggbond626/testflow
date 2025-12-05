"""
项目相关的Pydantic模式
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.user import User, ProjectMember


# 基础项目模式
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, max_length=1000, description="项目描述")


# 项目创建模式
class ProjectCreate(ProjectBase):
    pass


# 项目更新模式
class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, max_length=1000, description="项目描述")


# 项目响应模式
class Project(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 项目详细信息（包含成员和统计信息）
class ProjectDetail(Project):
    owner: User
    members: List[ProjectMember] = []
    member_count: int = Field(default=0, description="成员数量")
    requirement_files_count: int = Field(default=0, description="需求文件数量")
    requirement_points_count: int = Field(default=0, description="需求点数量")
    test_cases_count: int = Field(default=0, description="测试用例数量")


# 项目列表查询参数
class ProjectListParams(BaseModel):
    skip: int = Field(default=0, ge=0, description="跳过的记录数")
    limit: int = Field(default=20, ge=1, le=100, description="返回的记录数")
    search: Optional[str] = Field(None, description="搜索项目名称或描述")
    owner_id: Optional[int] = Field(None, description="按所有者筛选")


# 项目列表响应
class ProjectListResponse(BaseModel):
    projects: List[Project]
    total: int
    skip: int
    limit: int


# 项目统计信息
class ProjectStats(BaseModel):
    total_projects: int = Field(default=0, description="总项目数")
    owned_projects: int = Field(default=0, description="拥有的项目数")
    member_projects: int = Field(default=0, description="参与的项目数")
    active_projects: int = Field(default=0, description="活跃项目数")
