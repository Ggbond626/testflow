"""
自定义异常类
"""
from typing import Any, Optional, Dict
from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """API基础异常类"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "内部服务器错误"
    
    def __init__(
        self,
        detail: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ):
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.detail,
            headers=headers
        )


class NotFoundException(BaseAPIException):
    """资源未找到异常"""
    status_code = status.HTTP_404_NOT_FOUND
    detail = "资源不存在"


class UnauthorizedException(BaseAPIException):
    """未授权异常"""
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "未授权访问"


class ForbiddenException(BaseAPIException):
    """禁止访问异常"""
    status_code = status.HTTP_403_FORBIDDEN
    detail = "无权限访问"


class BadRequestException(BaseAPIException):
    """请求参数错误异常"""
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "请求参数错误"


class ConflictException(BaseAPIException):
    """冲突异常"""
    status_code = status.HTTP_409_CONFLICT
    detail = "资源冲突"


class ValidationException(BaseAPIException):
    """数据验证异常"""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "数据验证失败"


# 生成任务相关异常已移除（功能已迁移到 agents 系统）


# AI相关异常
class AIServiceException(BaseAPIException):
    """AI服务异常基类"""
    pass


class AIModelNotFoundException(AIServiceException, NotFoundException):
    """AI模型未找到"""
    detail = "AI模型不存在或未激活"


class AIAgentNotFoundException(AIServiceException, NotFoundException):
    """智能体未找到"""
    detail = "智能体不存在或未激活"


class AIServiceUnavailableException(AIServiceException):
    """AI服务不可用"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "AI服务暂时不可用"


class AIQuotaExceededException(AIServiceException):
    """AI配额超限"""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    detail = "AI服务调用配额已用完"


# 文件相关异常
class FileException(BaseAPIException):
    """文件异常基类"""
    pass


class FileNotFoundException(FileException, NotFoundException):
    """文件未找到"""
    detail = "文件不存在"


class FileUploadException(FileException):
    """文件上传异常"""
    detail = "文件上传失败"


class FileExtractionException(FileException):
    """文件内容提取异常"""
    detail = "文件内容提取失败"


class FileTypeNotSupportedException(FileException, BadRequestException):
    """文件类型不支持"""
    detail = "不支持的文件类型"
