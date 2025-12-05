"""
认证相关API路由
"""
from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    LoginRequest, LoginResponse, RefreshTokenRequest,
    UserCreate, User as UserSchema, PasswordUpdate, UserUpdate, UserListResponse
)
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, verify_refresh_token
)
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """用户注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        role=user_data.role or UserRole.USER
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> Any:
    """用户登录"""
    # 支持用户名或邮箱登录
    user = db.query(User).filter(
        (User.username == login_data.username) | 
        (User.email == login_data.username)
    ).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用"
        )
    
    # 创建访问令牌和刷新令牌
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )


@router.post("/refresh", response_model=dict)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    """刷新访问令牌"""
    payload = verify_refresh_token(refresh_data.refresh_token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )
    
    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserSchema)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """获取当前用户信息"""
    return current_user


@router.put("/me", response_model=UserSchema)
def update_current_user(
    user_update: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新当前用户信息"""
    # 只允许更新用户名和邮箱
    allowed_fields = {"username", "email"}
    update_data = {k: v for k, v in user_update.items() if k in allowed_fields}
    
    if "username" in update_data:
        # 检查用户名是否已被其他用户使用
        existing_user = db.query(User).filter(
            User.username == update_data["username"],
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
    
    if "email" in update_data:
        # 检查邮箱是否已被其他用户使用
        existing_user = db.query(User).filter(
            User.email == update_data["email"],
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
    
    # 更新用户信息
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.put("/me/password")
def change_password(
    password_data: PasswordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """修改当前用户密码"""
    # 验证当前密码
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 更新密码
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "密码修改成功"}


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """用户登出（客户端需要删除令牌）"""
    return {"message": "登出成功"}


# 管理员专用接口
@router.get("/users", response_model=UserListResponse)
def list_users(
    skip: int = 0,
    limit: int = 20,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户列表（管理员专用）"""
    query = db.query(User)

    # 角色筛选
    if role:
        query = query.filter(User.role == role)

    # 状态筛选
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    # 搜索用户名或邮箱
    if search and search.strip():
        query = query.filter(
            (User.username.contains(search.strip())) |
            (User.email.contains(search.strip()))
        )

    # 获取总数
    total = query.count()

    # 分页查询
    users = query.offset(skip).limit(limit).all()

    return UserListResponse(
        users=users,
        total=total,
        skip=skip,
        limit=limit
    )


@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    status_data: dict,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新用户状态（管理员专用）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    is_active = status_data.get("is_active")
    if is_active is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少is_active参数"
        )

    user.is_active = bool(is_active)
    db.commit()

    return {"message": f"用户状态已更新为{'激活' if is_active else '禁用'}"}


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role_data: dict,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新用户角色（管理员专用）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    role = role_data.get("role")
    if role not in ["admin", "user"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的角色"
        )

    user.role = UserRole(role)
    db.commit()

    return {"message": f"用户角色已更新为{role}"}


@router.post("/users", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """创建用户（管理员专用）"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        role=user_data.role or UserRole.USER
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.put("/users/{user_id}", response_model=UserSchema)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新用户信息（管理员专用）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 检查用户名是否已被其他用户使用
    if user_update.username and user_update.username != user.username:
        existing_user = db.query(User).filter(
            User.username == user_update.username,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

    # 检查邮箱是否已被其他用户使用
    if user_update.email and user_update.email != user.email:
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

    # 更新用户信息
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """删除用户（管理员专用）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 不能删除自己
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账号"
        )

    # 物理删除用户
    db.delete(user)
    db.commit()

    return {"message": "用户已删除"}


@router.get("/users/{user_id}", response_model=UserSchema)
def get_user(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户详情（管理员专用）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return user
