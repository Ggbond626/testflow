"""
项目管理API路由
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.database import get_db
from app.models.user import User, ProjectMember, ProjectRole, UserRole
from app.models.project import Project
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, Project as ProjectSchema,
    ProjectDetail, ProjectListParams, ProjectListResponse
)
from app.schemas.user import ProjectMemberCreate, ProjectMember as ProjectMemberSchema
from app.core.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter()


def check_project_permission(
    project: Project,
    user: User,
    required_roles: List[ProjectRole] = None
) -> bool:
    """检查用户对项目的权限"""
    # 项目所有者拥有所有权限
    if project.owner_id == user.id:
        return True
    
    # 管理员拥有所有权限
    if user.role == UserRole.ADMIN:
        return True
    
    # 检查项目成员权限
    if required_roles:
        member = next(
            (m for m in project.members if m.user_id == user.id),
            None
        )
        if member and member.role in required_roles:
            return True
    
    return False


def get_user_projects(user: User, db: Session):
    """获取用户可访问的项目"""
    if user.role == UserRole.ADMIN:
        # 管理员可以看到所有项目
        return db.query(Project).all()
    else:
        # 普通用户只能看到自己拥有的和参与的项目
        return db.query(Project).filter(
            or_(
                Project.owner_id == user.id,
                Project.id.in_(
                    db.query(ProjectMember.project_id).filter(
                        ProjectMember.user_id == user.id
                    )
                )
            )
        ).all()


@router.post("/admin", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
def create_project_admin(
    project_data: ProjectCreate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """创建新项目（管理员）"""
    db_project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=admin_user.id
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project


@router.post("/", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """创建新项目"""
    db_project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=current_user.id
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project


@router.get("/admin", response_model=ProjectListResponse)
def list_all_projects_admin(
    skip: int = 0,
    limit: int = 20,
    search: str = "",
    owner_id: Optional[int] = None,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取所有项目列表（管理员专用）"""
    # 构建查询
    query = db.query(Project)

    # 搜索过滤
    if search:
        query = query.filter(
            or_(
                Project.name.contains(search),
                Project.description.contains(search)
            )
        )

    # 所有者过滤
    if owner_id:
        query = query.filter(Project.owner_id == owner_id)

    # 获取总数
    total = query.count()

    # 分页
    projects = query.offset(skip).limit(limit).all()

    return ProjectListResponse(
        projects=projects,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/", response_model=ProjectListResponse)
def list_projects(
    skip: int = 0,
    limit: int = 20,
    search: str = "",
    owner_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取项目列表"""
    # 构建查询
    query = db.query(Project)

    # 权限过滤：管理员可以看到所有项目，普通用户只能看到自己的项目
    if current_user.role != UserRole.ADMIN:
        query = query.filter(
            or_(
                Project.owner_id == current_user.id,
                Project.id.in_(
                    db.query(ProjectMember.project_id).filter(
                        ProjectMember.user_id == current_user.id
                    )
                )
            )
        )
    
    # 搜索过滤
    if search:
        query = query.filter(
            or_(
                Project.name.contains(search),
                Project.description.contains(search)
            )
        )

    # 所有者过滤
    if owner_id:
        query = query.filter(Project.owner_id == owner_id)

    # 获取总数
    total = query.count()

    # 分页
    projects = query.offset(skip).limit(limit).all()

    return ProjectListResponse(
        projects=projects,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/admin/{project_id}", response_model=ProjectDetail)
def get_project_admin(
    project_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取项目详情（管理员）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 计算统计信息
    member_count = len(project.members)
    requirement_files_count = len(project.requirement_files)

    # 计算需求点数量（从需求文件中统计）
    requirement_points_count = 0
    for req_file in project.requirement_files:
        requirement_points_count += len(req_file.requirement_points)

    # 计算测试用例数量（从需求点的测试点中统计）
    test_cases_count = 0
    for req_file in project.requirement_files:
        for req_point in req_file.requirement_points:
            for test_point in req_point.test_points:
                test_cases_count += len(test_point.test_cases)

    # 构建详细信息
    project_detail = ProjectDetail(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        owner=project.owner,
        members=project.members,
        member_count=member_count,
        requirement_files_count=requirement_files_count,
        requirement_points_count=requirement_points_count,
        test_cases_count=test_cases_count
    )

    return project_detail


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取项目详情"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查权限
    if not check_project_permission(project, current_user, [ProjectRole.VIEWER, ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此项目"
        )
    
    # 计算统计信息
    member_count = len(project.members)
    requirement_files_count = len(project.requirement_files)

    # 计算需求点数量（从需求文件中统计）
    requirement_points_count = 0
    for req_file in project.requirement_files:
        requirement_points_count += len(req_file.requirement_points)

    # 计算测试用例数量（从需求点的测试点中统计）
    test_cases_count = 0
    for req_file in project.requirement_files:
        for req_point in req_file.requirement_points:
            for test_point in req_point.test_points:
                test_cases_count += len(test_point.test_cases)

    # 构建详细信息
    project_detail = ProjectDetail(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        owner=project.owner,
        members=project.members,
        member_count=member_count,
        requirement_files_count=requirement_files_count,
        requirement_points_count=requirement_points_count,
        test_cases_count=test_cases_count
    )
    
    return project_detail


@router.put("/{project_id}", response_model=ProjectSchema)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新项目信息"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查权限（只有所有者和管理员可以更新）
    if not check_project_permission(project, current_user, [ProjectRole.OWNER]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此项目"
        )
    
    # 更新项目信息
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/admin/{project_id}")
def delete_project_admin(
    project_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """删除项目（管理员）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    db.delete(project)
    db.commit()

    return {"message": "项目删除成功"}


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """删除项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查权限（只有所有者和管理员可以删除）
    if not check_project_permission(project, current_user, [ProjectRole.OWNER]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此项目"
        )
    
    db.delete(project)
    db.commit()
    
    return {"message": "项目删除成功"}


# 项目成员管理（管理员版本）
@router.post("/admin/{project_id}/members", response_model=ProjectMemberSchema)
def add_project_member_admin(
    project_id: int,
    member_data: ProjectMemberCreate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """添加项目成员（管理员）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 检查用户是否存在
    user = db.query(User).filter(User.id == member_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 检查是否已经是成员
    existing_member = db.query(ProjectMember).filter(
        and_(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == member_data.user_id
        )
    ).first()

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已经是项目成员"
        )

    # 添加成员
    db_member = ProjectMember(
        project_id=project_id,
        user_id=member_data.user_id,
        role=member_data.role
    )

    db.add(db_member)
    db.commit()
    db.refresh(db_member)

    return db_member


# 项目成员管理
@router.post("/{project_id}/members", response_model=ProjectMemberSchema)
def add_project_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """添加项目成员"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查权限
    if not check_project_permission(project, current_user, [ProjectRole.OWNER]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权添加项目成员"
        )
    
    # 检查用户是否存在
    user = db.query(User).filter(User.id == member_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查是否已经是成员
    existing_member = db.query(ProjectMember).filter(
        and_(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == member_data.user_id
        )
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已经是项目成员"
        )
    
    # 添加成员
    db_member = ProjectMember(
        project_id=project_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    
    return db_member


@router.get("/admin/{project_id}/members", response_model=List[ProjectMemberSchema])
def list_project_members_admin(
    project_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取项目成员列表（管理员）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    return project.members


@router.get("/{project_id}/members", response_model=List[ProjectMemberSchema])
def list_project_members(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取项目成员列表"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查权限
    if not check_project_permission(project, current_user, [ProjectRole.VIEWER, ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看项目成员"
        )
    
    return project.members


@router.delete("/admin/{project_id}/members/{user_id}")
def remove_project_member_admin(
    project_id: int,
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """移除项目成员（管理员）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 查找成员
    member = db.query(ProjectMember).filter(
        and_(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        )
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在"
        )

    db.delete(member)
    db.commit()

    return {"message": "成员移除成功"}


@router.delete("/{project_id}/members/{user_id}")
def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """移除项目成员"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查权限
    if not check_project_permission(project, current_user, [ProjectRole.OWNER]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权移除项目成员"
        )
    
    # 查找成员
    member = db.query(ProjectMember).filter(
        and_(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        )
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在"
        )
    
    db.delete(member)
    db.commit()
    
    return {"message": "成员移除成功"}
