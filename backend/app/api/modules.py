"""
功能模块管理API路由
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.module import ModulePriority
from app.schemas.module import (
    ModuleCreate, ModuleUpdate, Module as ModuleSchema,
    ModuleDetail, ModuleListResponse, ModuleReorderRequest,
    ModuleAssignmentCreate, ModuleAssignee, ProjectStatsResponse
)
from app.services.module_service import module_service
from app.core.dependencies import get_current_active_user


def check_project_access(db: Session, project_id: int, user: User) -> Project:
    """检查用户是否有项目访问权限"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查权限：所有者、管理员或项目成员
    if user.role == UserRole.ADMIN or project.owner_id == user.id:
        return project
    
    # 检查是否是项目成员
    from app.models.user import ProjectMember
    is_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id
    ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="无权访问该项目")
    
    return project


def check_project_edit_permission(db: Session, project_id: int, user: User) -> Project:
    """检查用户是否有项目编辑权限"""
    project = check_project_access(db, project_id, user)
    
    # 只有所有者和管理员可以编辑
    if user.role != UserRole.ADMIN and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权编辑该项目")
    
    return project


router = APIRouter()


@router.get("/{project_id}/stats", response_model=ProjectStatsResponse)
def get_project_stats(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取项目统计信息"""
    # 检查权限
    check_project_access(db, project_id, current_user)
    
    # 获取统计信息
    stats = module_service.get_project_stats(db, project_id)
    return stats


@router.get("/{project_id}/modules", response_model=ModuleListResponse)
def get_modules(
    project_id: int,
    priority: Optional[ModulePriority] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取项目的所有功能模块"""
    # 检查权限
    check_project_access(db, project_id, current_user)
    
    # 获取模块列表
    modules = module_service.get_modules(db, project_id, priority)
    
    return ModuleListResponse(
        modules=modules,
        total=len(modules)
    )


@router.post("/{project_id}/modules", response_model=ModuleDetail, status_code=status.HTTP_201_CREATED)
def create_module(
    project_id: int,
    module_data: ModuleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """创建功能模块"""
    # 检查权限
    check_project_edit_permission(db, project_id, current_user)
    
    # 创建模块
    module = module_service.create_module(db, project_id, module_data, current_user.id)
    
    # 返回详情
    module_detail = module_service.get_module(db, module.id)
    return module_detail


@router.get("/{project_id}/modules/{module_id}", response_model=ModuleDetail)
def get_module(
    project_id: int,
    module_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取模块详情"""
    # 检查权限
    check_project_access(db, project_id, current_user)
    
    # 获取模块
    module = module_service.get_module(db, module_id)
    if not module or module.project_id != project_id:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    return module


@router.put("/{project_id}/modules/{module_id}", response_model=ModuleDetail)
def update_module(
    project_id: int,
    module_id: int,
    module_data: ModuleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新模块信息"""
    # 检查权限
    check_project_edit_permission(db, project_id, current_user)
    
    # 检查模块是否存在
    existing_module = module_service.get_module(db, module_id)
    if not existing_module or existing_module.project_id != project_id:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    # 更新模块
    updated_module = module_service.update_module(db, module_id, module_data)
    if not updated_module:
        raise HTTPException(status_code=500, detail="更新失败")
    
    # 返回详情
    module_detail = module_service.get_module(db, module_id)
    return module_detail


@router.delete("/{project_id}/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(
    project_id: int,
    module_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    """删除模块"""
    # 检查权限
    check_project_edit_permission(db, project_id, current_user)
    
    # 检查模块是否存在
    existing_module = module_service.get_module(db, module_id)
    if not existing_module or existing_module.project_id != project_id:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    # 删除模块
    success = module_service.delete_module(db, module_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")


@router.put("/{project_id}/modules/reorder")
def reorder_modules(
    project_id: int,
    reorder_data: ModuleReorderRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """调整模块顺序"""
    # 检查权限
    check_project_edit_permission(db, project_id, current_user)
    
    # 调整顺序
    success = module_service.reorder_modules(db, project_id, reorder_data.module_orders)
    
    return {"success": success, "message": "顺序调整成功"}


@router.post("/{project_id}/modules/{module_id}/assign", response_model=ModuleAssignee, status_code=status.HTTP_201_CREATED)
def assign_module(
    project_id: int,
    module_id: int,
    assignment_data: ModuleAssignmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """分配模块负责人"""
    # 检查权限
    check_project_edit_permission(db, project_id, current_user)
    
    # 检查模块是否存在
    existing_module = module_service.get_module(db, module_id)
    if not existing_module or existing_module.project_id != project_id:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    # 分配负责人
    assignee = module_service.assign_module(db, module_id, assignment_data, current_user.id)
    
    return assignee


@router.delete("/{project_id}/modules/{module_id}/assign/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_assignment(
    project_id: int,
    module_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    """移除模块负责人"""
    # 检查权限
    check_project_edit_permission(db, project_id, current_user)
    
    # 检查模块是否存在
    existing_module = module_service.get_module(db, module_id)
    if not existing_module or existing_module.project_id != project_id:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    # 移除负责人
    success = module_service.remove_assignment(db, module_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="负责人分配不存在")


@router.get("/{project_id}/modules/{module_id}/assignees", response_model=List[ModuleAssignee])
def get_module_assignees(
    project_id: int,
    module_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取模块的所有负责人"""
    # 检查权限
    check_project_access(db, project_id, current_user)
    
    # 检查模块是否存在
    existing_module = module_service.get_module(db, module_id)
    if not existing_module or existing_module.project_id != project_id:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    # 获取负责人列表
    assignees = module_service.get_assignees(db, module_id)
    
    return assignees

