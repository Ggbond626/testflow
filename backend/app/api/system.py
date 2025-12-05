"""
系统信息和健康检查API
"""
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.ai_config import AIModel, Agent
from app.core.dependencies import get_current_admin_user
from app.config import settings

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> Any:
    """系统健康检查"""
    try:
        # 测试数据库连接
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
        "version": settings.app_version,
        "app_name": settings.app_name
    }


@router.get("/info")
def system_info() -> Any:
    """系统基本信息"""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
        "database_type": "sqlite" if "sqlite" in settings.database_url else "other",
        "cors_origins": settings.cors_origins,
        "max_file_size": settings.max_file_size,
        "allowed_file_types": settings.allowed_file_types
    }


@router.get("/stats")
def system_stats(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """系统统计信息（管理员专用）"""
    # 用户统计
    total_users = db.query(User).count()
    admin_users = db.query(User).filter(User.role == UserRole.ADMIN).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # 项目统计
    total_projects = db.query(Project).count()
    
    # AI配置统计
    total_ai_models = db.query(AIModel).count()
    active_ai_models = db.query(AIModel).filter(AIModel.is_active == True).count()
    total_agents = db.query(Agent).count()
    active_agents = db.query(Agent).filter(Agent.is_active == True).count()
    
    return {
        "users": {
            "total": total_users,
            "admin": admin_users,
            "active": active_users,
            "inactive": total_users - active_users
        },
        "projects": {
            "total": total_projects
        },
        "ai_config": {
            "models": {
                "total": total_ai_models,
                "active": active_ai_models,
                "inactive": total_ai_models - active_ai_models
            },
            "agents": {
                "total": total_agents,
                "active": active_agents,
                "inactive": total_agents - active_agents
            }
        }
    }


@router.get("/database/tables")
def database_tables(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """数据库表信息（管理员专用）"""
    try:
        # 获取所有表名（SQLite特定查询）
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result.fetchall()]
        
        table_info = {}
        for table in tables:
            if not table.startswith('sqlite_'):  # 排除系统表
                try:
                    count_result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.fetchone()[0]
                    table_info[table] = {"count": count}
                except Exception as e:
                    table_info[table] = {"error": str(e)}
        
        return {
            "tables": table_info,
            "total_tables": len(table_info)
        }
    except Exception as e:
        return {"error": f"无法获取数据库表信息: {str(e)}"}


@router.post("/database/backup")
def backup_database(
    admin_user: User = Depends(get_current_admin_user)
) -> Any:
    """数据库备份（管理员专用）"""
    # TODO: 实现数据库备份功能
    return {"message": "数据库备份功能待实现"}


@router.get("/logs")
def get_system_logs(
    admin_user: User = Depends(get_current_admin_user),
    lines: int = 100
) -> Any:
    """获取系统日志（管理员专用）"""
    # TODO: 实现日志读取功能
    return {
        "message": "系统日志功能待实现",
        "requested_lines": lines
    }
