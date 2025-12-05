"""
应用配置管理
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    app_name: str = "AI测试用例生成系统"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 数据库配置
    database_url: str = Field(
        default="sqlite:///./autotestcase.db",
        description="数据库连接URL"
    )
    
    # JWT认证配置
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT密钥，生产环境必须修改"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30 * 24 * 60  # 30天
    
    # 文件上传配置
    upload_dir: str = "./uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: list = [".docx", ".pdf", ".xlsx", ".txt"]
    
    # AI模型配置
    default_ai_provider: str = "openai"
    default_model: str = "gpt-3.5-turbo"
    ai_request_timeout: int = 60
    max_tokens: int = 2000
    temperature: float = 0.7

    # OpenAI API配置
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API密钥"
    )
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API基础URL"
    )

    # Anthropic API配置
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API密钥"
    )
    anthropic_base_url: str = Field(
        default="https://api.anthropic.com",
        description="Anthropic API基础URL"
    )
    
    # CORS配置
    cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:9000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:9000"
    ]
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # 忽略额外字段


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例（用于FastAPI依赖注入）"""
    return settings
