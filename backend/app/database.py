"""
数据库连接和会话管理
"""
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from app.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    #echo=settings.debug,  # 开发模式下显示SQL语句
    echo=False,  # 临时关闭SQL日志，方便调试
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# 为 SQLite 启用外键约束
if "sqlite" in settings.database_url:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话（用于FastAPI依赖注入）
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    创建所有数据库表
    """
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    删除所有数据库表（仅用于开发测试）
    """
    Base.metadata.drop_all(bind=engine)
