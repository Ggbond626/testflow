"""
FastAPI主应用入口
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings, get_settings
from app.database import create_tables, SessionLocal
from app.services.settings_service import SettingsService
from app.services.async_task_manager import task_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建数据库表
    create_tables()
    print("🚀 数据库表创建完成")
    
    # 初始化默认设置（幂等操作，不会重复创建）
    db = SessionLocal()
    try:
        SettingsService.initialize_defaults(db)
        print("✅ 系统默认设置初始化完成")
        
        # 加载并发配置到任务管理器
        task_manager.load_config_from_db(db)
        print("✅ 任务管理器并发配置加载完成")
    except Exception as e:
        print(f"⚠️ 设置初始化警告: {e}")
    finally:
        db.close()
    
    yield
    # 关闭时的清理工作
    print("👋 应用关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于AI的自动化测试用例生成系统",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用AI自动测试用例生成系统",
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version
    }


@app.get("/config")
async def get_config_info(config: settings = Depends(get_settings)):
    """获取配置信息（仅显示非敏感信息）"""
    return {
        "app_name": config.app_name,
        "version": config.app_version,
        "debug": config.debug,
        "cors_origins": config.cors_origins,
        "allowed_file_types": config.allowed_file_types
    }


# 添加API路由
from app.api import (
    auth, 
    projects,
    modules,
    requirements, 
    ai_models,
    agents,
    system,
    test_data,
    settings,
    project_test_cases
)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(projects.router, prefix="/api/projects", tags=["项目管理"])
app.include_router(modules.router, prefix="/api/projects", tags=["模块管理"])
app.include_router(requirements.router, prefix="/api/projects", tags=["需求管理"])
app.include_router(project_test_cases.router, prefix="/api", tags=["项目测试用例"])
app.include_router(test_data.router, prefix="/api", tags=["测试数据管理"])
app.include_router(system.router, prefix="/api/system", tags=["系统管理"])
app.include_router(ai_models.router, prefix="/api/ai", tags=["AI模型管理"])
app.include_router(agents.router, prefix="/api/agents", tags=["智能体管理"])
app.include_router(settings.router, prefix="/api/settings", tags=["系统设置"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        reload=settings.debug
    )
