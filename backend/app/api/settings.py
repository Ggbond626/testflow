"""
系统设置API路由
提供测试分类、测试设计方法和并发配置的管理接口
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_active_user
from app.services.settings_service import SettingsService
from app.services.async_task_manager import task_manager
from app.schemas.settings import (
    TestCategoryCreate, TestCategoryUpdate, TestCategoryResponse,
    TestDesignMethodCreate, TestDesignMethodUpdate, TestDesignMethodResponse,
    ConcurrencyConfig
)

router = APIRouter()


# ============== Test Categories Endpoints ==============

@router.get("/test-categories", response_model=List[TestCategoryResponse])
def get_test_categories(
    active_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取所有测试分类
    
    Args:
        active_only: 是否只返回启用的分类
    
    Returns:
        测试分类列表
    """
    return SettingsService.get_test_categories(db, active_only=active_only)


@router.post("/test-categories", response_model=TestCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_test_category(
    data: TestCategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建测试分类
    
    Args:
        data: 测试分类创建数据
    
    Returns:
        创建的测试分类
    
    Raises:
        HTTPException: 当代码重复时返回400错误
    """
    return SettingsService.create_test_category(db, data)


@router.put("/test-categories/{category_id}", response_model=TestCategoryResponse)
def update_test_category(
    category_id: int,
    data: TestCategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新测试分类
    
    Args:
        category_id: 分类ID
        data: 更新数据
    
    Returns:
        更新后的测试分类
    
    Raises:
        HTTPException: 当分类不存在时返回404错误，当代码重复时返回400错误
    """
    category = SettingsService.update_test_category(db, category_id, data)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"测试分类 ID {category_id} 不存在"
        )
    return category


@router.delete("/test-categories/{category_id}")
def delete_test_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除测试分类（软删除）
    
    Args:
        category_id: 分类ID
    
    Returns:
        删除成功消息
    
    Raises:
        HTTPException: 当分类不存在时返回404错误
    """
    success = SettingsService.delete_test_category(db, category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"测试分类 ID {category_id} 不存在"
        )
    return {"message": "测试分类删除成功"}


@router.post("/test-categories/reset", response_model=List[TestCategoryResponse])
def reset_test_categories(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """重置测试分类为默认值
    
    删除所有非默认分类，恢复默认分类的状态
    
    Returns:
        重置后的测试分类列表
    """
    return SettingsService.reset_test_categories(db)


# ============== Test Design Methods Endpoints ==============

@router.get("/design-methods", response_model=List[TestDesignMethodResponse])
def get_design_methods(
    active_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取所有测试设计方法
    
    Args:
        active_only: 是否只返回启用的方法
    
    Returns:
        测试设计方法列表
    """
    return SettingsService.get_design_methods(db, active_only=active_only)


@router.post("/design-methods", response_model=TestDesignMethodResponse, status_code=status.HTTP_201_CREATED)
def create_design_method(
    data: TestDesignMethodCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建测试设计方法
    
    Args:
        data: 测试设计方法创建数据
    
    Returns:
        创建的测试设计方法
    
    Raises:
        HTTPException: 当代码重复时返回400错误
    """
    return SettingsService.create_design_method(db, data)


@router.put("/design-methods/{method_id}", response_model=TestDesignMethodResponse)
def update_design_method(
    method_id: int,
    data: TestDesignMethodUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新测试设计方法
    
    Args:
        method_id: 方法ID
        data: 更新数据
    
    Returns:
        更新后的测试设计方法
    
    Raises:
        HTTPException: 当方法不存在时返回404错误，当代码重复时返回400错误
    """
    method = SettingsService.update_design_method(db, method_id, data)
    if not method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"测试设计方法 ID {method_id} 不存在"
        )
    return method


@router.delete("/design-methods/{method_id}")
def delete_design_method(
    method_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除测试设计方法（软删除）
    
    Args:
        method_id: 方法ID
    
    Returns:
        删除成功消息
    
    Raises:
        HTTPException: 当方法不存在时返回404错误
    """
    success = SettingsService.delete_design_method(db, method_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"测试设计方法 ID {method_id} 不存在"
        )
    return {"message": "测试设计方法删除成功"}


@router.post("/design-methods/reset", response_model=List[TestDesignMethodResponse])
def reset_design_methods(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """重置测试设计方法为默认值
    
    删除所有非默认方法，恢复默认方法的状态
    
    Returns:
        重置后的测试设计方法列表
    """
    return SettingsService.reset_design_methods(db)


# ============== Concurrency Config Endpoints ==============

@router.get("/concurrency", response_model=ConcurrencyConfig)
def get_concurrency_config(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取并发配置
    
    Returns:
        当前并发配置
    """
    return SettingsService.get_concurrency_config(db)


@router.put("/concurrency", response_model=ConcurrencyConfig)
def update_concurrency_config(
    config: ConcurrencyConfig,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新并发配置
    
    Args:
        config: 新的并发配置
    
    Returns:
        更新后的并发配置
    
    Note:
        配置值会自动验证范围：
        - max_concurrent_tasks: 1-10
        - task_timeout: 30-600秒
        - retry_count: 0-5
        - queue_size: 10-1000
        
        更新后会自动刷新任务管理器的配置
    """
    result = SettingsService.update_concurrency_config(db, config)
    
    # 刷新任务管理器的并发配置
    task_manager.reload_config(db)
    
    return result
