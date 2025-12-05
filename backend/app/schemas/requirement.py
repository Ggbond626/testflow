"""
需求相关的Pydantic schemas
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.requirement import RequirementStatus


# 需求文件相关schemas
class RequirementFileBase(BaseModel):
    """需求文件基础schema"""
    filename: str
    file_type: str


class RequirementFileCreate(RequirementFileBase):
    """创建需求文件schema"""
    pass


class RequirementFile(RequirementFileBase):
    """需求文件schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    file_path: str
    file_size: int
    uploaded_by: int
    upload_time: datetime
    
    # 文件内容提取
    extracted_content: Optional[str] = None
    is_extracted: bool = False
    extract_error: Optional[str] = None
    
    # 图片信息
    has_images: bool = False
    image_count: int = 0
    
    # 关联数据
    uploader: Optional["User"] = None


class RequirementFileList(BaseModel):
    """需求文件列表响应schema"""
    files: List[RequirementFile]
    total: int


# 需求点相关schemas - 移到前面定义
class RequirementPointBase(BaseModel):
    """需求点基础schema"""
    content: str
    priority: Optional[str] = "medium"  # high/medium/low
    order_index: Optional[int] = 0
    status: Optional[RequirementStatus] = RequirementStatus.DRAFT


class RequirementPointCreate(RequirementPointBase):
    """创建需求点schema"""
    created_by_ai: Optional[bool] = False


class RequirementPointUpdate(BaseModel):
    """更新需求点schema"""
    content: Optional[str] = None
    priority: Optional[str] = None  # high/medium/low
    order_index: Optional[int] = None
    status: Optional[RequirementStatus] = None


class RequirementPoint(RequirementPointBase):
    """需求点schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    requirement_file_id: Optional[int] = None
    module_id: Optional[int] = None
    source: Optional[str] = "manual"  # ai_generated/manual
    created_by_ai: bool = False
    edited_by_user: bool = False
    created_by: int
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # 关联数据
    creator: Optional["User"] = None
    updater: Optional["User"] = None


class RequirementPointList(BaseModel):
    """需求点列表响应schema"""
    points: List[RequirementPoint]
    total: int


# 需求文件内容响应schema - 移到RequirementPoint定义之后
class RequirementFileContent(BaseModel):
    """需求文件内容响应schema"""
    id: int
    filename: str
    file_type: str
    extracted_content: Optional[str] = None
    is_extracted: bool = False
    extract_error: Optional[str] = None
    has_images: bool = False
    image_count: int = 0
    requirement_points: Optional[List[RequirementPoint]] = []
    images: Optional[List["RequirementImage"]] = []


# 需求文档图片相关schemas
class RequirementImageBase(BaseModel):
    """需求文档图片基础schema"""
    image_path: str
    image_format: str
    image_size: int
    position_index: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    alt_text: Optional[str] = None


class RequirementImageCreate(RequirementImageBase):
    """创建需求文档图片schema"""
    requirement_file_id: int


class RequirementImage(RequirementImageBase):
    """需求文档图片schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    requirement_file_id: int
    created_at: datetime


# 需求分析相关schemas
class RequirementAnalysisRequest(BaseModel):
    """需求分析请求schema"""
    file_id: int
    ai_config_id: Optional[int] = None
    extract_mode: str = "auto"  # auto, manual, hybrid


class RequirementAnalysisResponse(BaseModel):
    """需求分析响应schema"""
    file_id: int
    extracted_points: List[RequirementPointCreate]
    analysis_summary: str
    confidence_score: float


# 批量操作schemas
class RequirementPointBatchCreate(BaseModel):
    """批量创建需求点schema"""
    points: List[RequirementPointCreate]


class RequirementPointBatchCreateResponse(BaseModel):
    """批量创建需求点响应schema"""
    success: bool
    created_count: int
    points: List[RequirementPoint]


class RequirementPointBatchUpdate(BaseModel):
    """批量更新需求点schema"""
    point_updates: List[dict]  # {id: int, **RequirementPointUpdate}


class RequirementPointBatchDelete(BaseModel):
    """批量删除需求点schema"""
    point_ids: List[int]


# 导入User schema以避免循环导入
from app.schemas.user import User

# 更新forward references
RequirementFile.model_rebuild()
RequirementPoint.model_rebuild()
RequirementImage.model_rebuild()
RequirementFileContent.model_rebuild()
