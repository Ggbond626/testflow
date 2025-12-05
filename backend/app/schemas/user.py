"""
用户相关的Pydantic模式
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole, ProjectRole


# 基础用户模式
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")


# 用户创建模式
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    role: Optional[UserRole] = Field(default=UserRole.USER, description="用户角色")


# 用户更新模式
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    is_active: Optional[bool] = Field(None, description="是否激活")
    role: Optional[UserRole] = Field(None, description="用户角色")


# 密码更新模式
class PasswordUpdate(BaseModel):
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


# 用户响应模式
class User(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 用户详细信息（包含项目信息）
class UserDetail(User):
    owned_projects_count: int = Field(default=0, description="拥有的项目数量")
    member_projects_count: int = Field(default=0, description="参与的项目数量")


# 登录请求模式
class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


# 登录响应模式
class LoginResponse(BaseModel):
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user: User = Field(..., description="用户信息")


# 刷新令牌请求模式
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="刷新令牌")


# 项目成员模式
class ProjectMemberBase(BaseModel):
    user_id: int = Field(..., description="用户ID")
    role: ProjectRole = Field(default=ProjectRole.MEMBER, description="项目角色")


class ProjectMemberCreate(ProjectMemberBase):
    pass


class ProjectMemberUpdate(BaseModel):
    role: ProjectRole = Field(..., description="项目角色")


class ProjectMember(ProjectMemberBase):
    id: int
    project_id: int
    joined_at: datetime
    user: User

    class Config:
        from_attributes = True


# 用户列表查询参数
class UserListParams(BaseModel):
    skip: int = Field(default=0, ge=0, description="跳过的记录数")
    limit: int = Field(default=20, ge=1, le=100, description="返回的记录数")
    role: Optional[UserRole] = Field(None, description="按角色筛选")
    is_active: Optional[bool] = Field(None, description="按激活状态筛选")
    search: Optional[str] = Field(None, description="搜索用户名或邮箱")


# 用户列表响应
class UserListResponse(BaseModel):
    users: List[User]
    total: int
    skip: int
    limit: int
