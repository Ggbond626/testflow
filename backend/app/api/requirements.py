"""
需求文件和模块数据管理API
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User, UserRole, ProjectRole
from app.models.project import Project
from app.models.module import Module
from app.models.requirement import RequirementFile, RequirementPoint, RequirementStatus
from app.models.requirement_image import RequirementImage
from app.models.testcase import TestPoint, TestCase
from app.schemas.requirement import (
    RequirementFile as RequirementFileSchema,
    RequirementFileContent,
    RequirementPoint as RequirementPointSchema,
    RequirementImage as RequirementImageSchema
)
from app.core.dependencies import get_current_active_user
from app.utils.file_extractor import extract_text_from_file, extract_images_from_docx
import os
import uuid
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# 文件上传配置
UPLOAD_DIR = Path("uploads/requirements")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_UPLOAD_DIR = Path("uploads/requirement_images")
IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".txt", ".docx", ".md"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


# ========== 请求模型 ==========

class RequirementPointCreate(BaseModel):
    """创建需求点的请求模型"""
    content: str
    order_index: int = 0
    priority: str = "medium"
    created_by_ai: bool = False


class BatchCreateRequirementPointsRequest(BaseModel):
    """批量创建需求点的请求模型"""
    points: List[RequirementPointCreate]


def check_project_permission(project: Project, user: User, required_roles: List[ProjectRole] = None) -> bool:
    """检查用户对项目的权限"""
    # 项目所有者拥有所有权限
    if project.owner_id == user.id:
        return True
    
    # 管理员拥有所有权限
    if user.role == UserRole.ADMIN or str(user.role) == "admin" or \
       (hasattr(user.role, 'value') and user.role.value == "admin"):
        return True
    
    # 检查项目成员权限
    if required_roles and project.members:
        member = next((m for m in project.members if m.user_id == user.id), None)
        if member and member.role in required_roles:
            return True
    
    return False


# ========== 需求文件管理 ==========

@router.post("/{project_id}/modules/{module_id}/requirements/files", response_model=RequirementFileSchema)
async def upload_requirement_file(
    project_id: int,
    module_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """上传需求文件到指定模块"""
    module = db.query(Module).filter(Module.id == module_id, Module.project_id == project_id).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模块不存在或不属于该项目")
    
    project = db.query(Project).options(joinedload(Project.members)).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权上传需求文件")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                          detail=f"不支持的文件类型，支持：{', '.join(ALLOWED_EXTENSIONS)}")
    
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                          detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）")
    
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件保存失败: {str(e)}")
    
    file_type_clean = file_ext.lstrip('.')
    extracted_content, extract_error = extract_text_from_file(str(file_path), file_type_clean)
    
    db_file = RequirementFile(
        project_id=project_id,
        module_id=module_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        file_type=file_type_clean,
        uploaded_by=current_user.id,
        extracted_content=extracted_content if not extract_error else None,
        is_extracted=not bool(extract_error),
        extract_error=extract_error
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    # 对于DOCX文件，提取图片
    if file_type_clean == 'docx':
        try:
            image_output_dir = IMAGE_UPLOAD_DIR / str(db_file.id)
            images, image_error = extract_images_from_docx(str(file_path), str(image_output_dir))
            
            if images and not image_error:
                for img_info in images:
                    db_image = RequirementImage(
                        requirement_file_id=db_file.id,
                        image_path=img_info['path'],
                        image_format=img_info['format'],
                        image_size=img_info['size'],
                        position_index=img_info['position_index'],
                        width=img_info.get('width'),
                        height=img_info.get('height')
                    )
                    db.add(db_image)
                
                db_file.has_images = True
                db_file.image_count = len(images)
                db.commit()
                db.refresh(db_file)
        except Exception as e:
            logger.error(f"处理DOCX图片时发生异常: {str(e)}")
    
    return db_file


@router.get("/{project_id}/modules/{module_id}/requirements/files", response_model=List[RequirementFileSchema])
def list_requirement_files(
    project_id: int,
    module_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取模块的需求文件列表"""
    module = db.query(Module).filter(Module.id == module_id, Module.project_id == project_id).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模块不存在或不属于该项目")
    
    project = db.query(Project).options(joinedload(Project.members)).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.VIEWER, ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看需求文件")
    
    files = db.query(RequirementFile).filter(
        RequirementFile.project_id == project_id,
        RequirementFile.module_id == module_id
    ).order_by(RequirementFile.upload_time.desc()).all()
    
    return files


@router.delete("/{project_id}/modules/{module_id}/requirements/files/{file_id}")
def delete_requirement_file(
    project_id: int,
    module_id: int,
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """删除需求文件"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除需求文件")
    
    req_file = db.query(RequirementFile).filter(
        RequirementFile.id == file_id,
        RequirementFile.project_id == project_id
    ).first()
    
    if not req_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求文件不存在")
    
    # 删除物理文件
    try:
        if os.path.exists(req_file.file_path):
            os.remove(req_file.file_path)
    except Exception as e:
        logger.warning(f"删除物理文件失败: {e}")
    
    # 删除关联的图片文件和目录
    try:
        image_dir = IMAGE_UPLOAD_DIR / str(req_file.id)
        if image_dir.exists():
            import shutil
            shutil.rmtree(str(image_dir))
    except Exception as e:
        logger.warning(f"删除图片目录失败: {e}")
    
    db.delete(req_file)
    db.commit()
    
    return {"message": "需求文件删除成功"}


@router.get("/{project_id}/requirements/files/{file_id}/download")
async def download_requirement_file(
    project_id: int,
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """下载需求文件"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.VIEWER, ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权下载需求文件")
    
    req_file = db.query(RequirementFile).filter(
        RequirementFile.id == file_id,
        RequirementFile.project_id == project_id
    ).first()
    
    if not req_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求文件不存在")
    
    if not os.path.exists(req_file.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件已丢失")
    
    return FileResponse(path=req_file.file_path, filename=req_file.filename, media_type='application/octet-stream')


@router.get("/{project_id}/requirements/files/{file_id}/images/{image_id}")
async def get_requirement_image(
    project_id: int,
    file_id: int,
    image_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取需求文档中的图片"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.VIEWER, ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看图片")
    
    image = db.query(RequirementImage).filter(
        RequirementImage.id == image_id,
        RequirementImage.requirement_file_id == file_id
    ).first()
    
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    
    if not os.path.exists(image.image_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片文件已丢失")
    
    mime_types = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 
                  'gif': 'image/gif', 'webp': 'image/webp', 'bmp': 'image/bmp'}
    media_type = mime_types.get(image.image_format.lower(), 'application/octet-stream')
    
    return FileResponse(path=image.image_path, media_type=media_type)


@router.put("/{project_id}/requirements/files/{file_id}/rename")
def rename_requirement_file(
    project_id: int,
    file_id: int,
    new_filename: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """重命名需求文件"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权重命名需求文件")
    
    req_file = db.query(RequirementFile).filter(
        RequirementFile.id == file_id,
        RequirementFile.project_id == project_id
    ).first()
    
    if not req_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求文件不存在")
    
    if not new_filename or new_filename.strip() == "":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件名不能为空")
    
    req_file.filename = new_filename.strip()
    db.commit()
    db.refresh(req_file)
    
    return req_file


@router.get("/{project_id}/requirements/files/{file_id}/content", response_model=RequirementFileContent)
def get_requirement_file_content(
    project_id: int,
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取需求文件的提取内容"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.VIEWER, ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看需求文件内容")
    
    req_file = db.query(RequirementFile).filter(
        RequirementFile.id == file_id,
        RequirementFile.project_id == project_id
    ).first()
    
    if not req_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求文件不存在")
    
    # 如果文件内容未提取，尝试重新提取
    if not req_file.is_extracted and not req_file.extract_error:
        if os.path.exists(req_file.file_path):
            file_ext = Path(req_file.filename).suffix.lower().lstrip('.')
            extracted_content, extract_error = extract_text_from_file(req_file.file_path, file_ext)
            
            if not extract_error:
                req_file.extracted_content = extracted_content
                req_file.is_extracted = True
            else:
                req_file.extract_error = extract_error
            
            db.commit()
            db.refresh(req_file)
    
    requirement_points = db.query(RequirementPoint).filter(
        RequirementPoint.requirement_file_id == file_id
    ).order_by(RequirementPoint.order_num, RequirementPoint.created_at).all()
    
    images = db.query(RequirementImage).filter(
        RequirementImage.requirement_file_id == file_id
    ).order_by(RequirementImage.position_index).all()
    
    return RequirementFileContent(
        id=req_file.id,
        filename=req_file.filename,
        file_type=req_file.file_type,
        extracted_content=req_file.extracted_content,
        is_extracted=req_file.is_extracted,
        extract_error=req_file.extract_error,
        has_images=req_file.has_images,
        image_count=req_file.image_count,
        requirement_points=requirement_points,
        images=images
    )



# ========== 按模块管理需求点 ==========

@router.get("/{project_id}/modules/{module_id}/requirement-points", response_model=List[RequirementPointSchema])
def list_module_requirement_points(
    project_id: int,
    module_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取模块的需求点列表"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.VIEWER, ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看需求点")
    
    module = db.query(Module).filter(Module.id == module_id, Module.project_id == project_id).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模块不存在")
    
    points = db.query(RequirementPoint).filter(
        RequirementPoint.module_id == module_id
    ).order_by(RequirementPoint.order_num, RequirementPoint.created_at).all()
    
    return points


@router.post("/{project_id}/modules/{module_id}/requirement-points", response_model=RequirementPointSchema)
def create_module_requirement_point(
    project_id: int,
    module_id: int,
    content: str,
    priority: str = "medium",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """手动创建需求点"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权创建需求点")
    
    module = db.query(Module).filter(Module.id == module_id, Module.project_id == project_id).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模块不存在")
    
    # 获取当前最大排序号
    max_order = db.query(RequirementPoint).filter(
        RequirementPoint.module_id == module_id
    ).count()
    
    point = RequirementPoint(
        module_id=module_id,
        content=content,
        priority=priority,
        order_num=max_order,
        source="manual",
        created_by_ai=False,
        created_by=current_user.id
    )
    
    db.add(point)
    db.commit()
    db.refresh(point)
    
    return point


def _normalize_priority(priority: str) -> str:
    """标准化优先级值
    
    将 P0/P1/P2 等格式转换为 high/medium/low
    """
    priority_map = {
        "P0": "high",
        "P1": "medium", 
        "P2": "low",
        "HIGH": "high",
        "MEDIUM": "medium",
        "LOW": "low",
        "H": "high",
        "M": "medium",
        "L": "low"
    }
    return priority_map.get(priority.upper() if priority else "", "medium")


@router.post("/{project_id}/modules/{module_id}/requirements/files/{file_id}/points/batch")
def batch_create_requirement_points(
    project_id: int,
    module_id: int,
    file_id: int,
    request: BatchCreateRequirementPointsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """批量创建需求点（从AI生成结果）
    
    注意：此操作会先删除该需求文件之前生成的所有需求点，然后创建新的需求点
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权创建需求点")
    
    module = db.query(Module).filter(Module.id == module_id, Module.project_id == project_id).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模块不存在")
    
    # 验证需求文件存在
    req_file = db.query(RequirementFile).filter(
        RequirementFile.id == file_id,
        RequirementFile.project_id == project_id
    ).first()
    if not req_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求文件不存在")
    
    # 删除该需求文件之前生成的所有需求点
    # 注意：这会级联删除关联的测试点和测试用例（如果数据库设置了级联删除）
    old_points = db.query(RequirementPoint).filter(
        RequirementPoint.requirement_file_id == file_id,
        RequirementPoint.module_id == module_id
    ).all()
    
    deleted_count = len(old_points)
    if deleted_count > 0:
        logger.info(f"删除需求文件 {file_id} 的 {deleted_count} 个旧需求点")
        for old_point in old_points:
            db.delete(old_point)
        db.flush()  # 先刷新删除操作
    
    # 创建新的需求点
    created_points = []
    for point_data in request.points:
        # 标准化优先级
        normalized_priority = _normalize_priority(point_data.priority)
        
        point = RequirementPoint(
            requirement_file_id=file_id,
            module_id=module_id,
            content=point_data.content,
            order_num=point_data.order_index,
            priority=normalized_priority,
            source="ai_generated",
            created_by_ai=point_data.created_by_ai,
            created_by=current_user.id
        )
        db.add(point)
        created_points.append(point)
    
    db.commit()
    
    # 刷新所有创建的需求点并转换为字典
    points_data = []
    for point in created_points:
        db.refresh(point)
        points_data.append({
            "id": point.id,
            "requirement_file_id": point.requirement_file_id,
            "module_id": point.module_id,
            "content": point.content,
            "priority": point.priority,
            "source": point.source,
            "order_index": point.order_num,
            "created_by_ai": point.created_by_ai,
            "created_by": point.created_by,
            "created_at": point.created_at.isoformat() if point.created_at else None,
            "updated_at": point.updated_at.isoformat() if point.updated_at else None
        })
    
    return {
        "message": f"成功创建 {len(created_points)} 个需求点",
        "count": len(created_points),
        "points": points_data
    }


@router.put("/{project_id}/modules/{module_id}/requirement-points/{point_id}", response_model=RequirementPointSchema)
def update_module_requirement_point(
    project_id: int,
    module_id: int,
    point_id: int,
    content: str,
    priority: str = "medium",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新需求点"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改需求点")
    
    point = db.query(RequirementPoint).filter(
        RequirementPoint.id == point_id,
        RequirementPoint.module_id == module_id
    ).first()
    
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求点不存在")
    
    point.content = content
    point.priority = priority
    point.edited_by_user = True
    point.updated_by = current_user.id
    
    db.commit()
    db.refresh(point)
    
    return point


@router.delete("/{project_id}/modules/{module_id}/requirement-points/{point_id}")
def delete_module_requirement_point(
    project_id: int,
    module_id: int,
    point_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """删除需求点（数据库级联删除会自动删除关联的测试点和测试用例）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除需求点")
    
    point = db.query(RequirementPoint).filter(
        RequirementPoint.id == point_id,
        RequirementPoint.module_id == module_id
    ).first()
    
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求点不存在")
    
    db.delete(point)
    db.commit()
    
    return {"message": "需求点已删除", "id": point_id}


# ========== 一键生成测试用例 ==========

@router.post("/{project_id}/modules/{module_id}/requirements/files/{file_id}/generate-all")
async def generate_all_test_artifacts(
    project_id: int,
    module_id: int,
    file_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """一键生成：需求点 → 测试点 → 测试用例 → 优化
    
    执行完整的测试用例生成流程：
    1. 分析需求文档，生成需求点
    2. 基于需求点生成测试点
    3. 基于测试点生成测试用例
    4. 优化生成的测试用例
    
    整个过程在后台异步执行，支持进度跟踪和取消操作。
    """
    from app.services.async_task_manager import task_manager
    from app.services.agent_service_real import AgentServiceReal
    from app.models.ai_config import Agent
    
    # 权限检查
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权执行此操作")
    
    module = db.query(Module).filter(Module.id == module_id, Module.project_id == project_id).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模块不存在")
    
    # 验证需求文件存在
    req_file = db.query(RequirementFile).filter(
        RequirementFile.id == file_id,
        RequirementFile.project_id == project_id
    ).first()
    if not req_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求文件不存在")
    
    if not req_file.is_extracted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="需求文件内容尚未提取")
    
    # 获取需求文件内容
    try:
        content_response = get_requirement_file_content(project_id, file_id, current_user, db)
        requirement_content = content_response.extracted_content
        # 获取图片路径列表
        image_paths = [img.image_path for img in content_response.images] if content_response.images else []
        
        if not requirement_content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="需求文件内容为空")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取需求文件内容失败: {str(e)}")
    
    # 获取各阶段的智能体配置
    from app.models.ai_config import AgentType
    
    # 为每个阶段选择对应类型的智能体
    requirement_agent = db.query(Agent).filter(
        Agent.is_active == True,
        Agent.type == AgentType.REQUIREMENT_SPLITTER
    ).first()
    
    test_point_agent = db.query(Agent).filter(
        Agent.is_active == True,
        Agent.type == AgentType.TEST_POINT_GENERATOR
    ).first()
    
    test_case_agent = db.query(Agent).filter(
        Agent.is_active == True,
        Agent.type == AgentType.TEST_CASE_DESIGNER
    ).first()
    
    optimizer_agent = db.query(Agent).filter(
        Agent.is_active == True,
        Agent.type == AgentType.TEST_CASE_OPTIMIZER
    ).first()
    
    # 如果某个类型的智能体不存在，使用第一个可用的智能体作为后备
    fallback_agent = db.query(Agent).filter(Agent.is_active == True).first()
    if not fallback_agent:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="没有可用的智能体")
    
    agent_ids = {
        "requirement": requirement_agent.id if requirement_agent else fallback_agent.id,
        "test_point": test_point_agent.id if test_point_agent else fallback_agent.id,
        "test_case": test_case_agent.id if test_case_agent else fallback_agent.id,
        "optimizer": optimizer_agent.id if optimizer_agent else fallback_agent.id
    }
    
    # 创建异步任务
    task_id = task_manager.create_task("one_click_generation", total_batches=100)
    task_manager.start_task(task_id)
    
    print(f"\n{'='*60}")
    print(f"[一键生成] 任务已创建: {task_id}")
    print(f"[一键生成] task_manager 实例 ID: {id(task_manager)}")
    print(f"[一键生成] 当前所有任务: {list(task_manager._tasks.keys())}")
    print(f"[一键生成] 任务数量: {len(task_manager._tasks)}")
    print(f"{'='*60}\n")
    
    # 异步执行完整流程
    async def execute_pipeline():
        # 创建新的数据库会话用于后台任务
        from app.database import SessionLocal
        db_session = SessionLocal()
        try:
            print(f"[一键生成] 开始执行后台任务: {task_id}")
            service = AgentServiceReal(db=db_session)
            await service.execute_full_generation_pipeline(
                requirement_content=requirement_content,
                file_id=file_id,
                module_id=module_id,
                user_id=current_user.id,
                agent_ids=agent_ids,
                image_paths=image_paths,
                task_id=task_id
            )
        except Exception as e:
            print(f"[一键生成] 后台任务执行失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db_session.close()
    
    background_tasks.add_task(execute_pipeline)
    
    return {
        "task_id": task_id,
        "message": "一键生成任务已创建，正在后台执行",
        "estimated_time": "预计需要 3-5 分钟"
    }


# ========== 按模块管理测试点 ==========

@router.get("/{project_id}/modules/{module_id}/test-points")
def list_module_test_points(
    project_id: int,
    module_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取模块的测试点列表（按需求点分组）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.VIEWER, ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看测试点")
    
    # 获取模块的需求点
    requirement_points = db.query(RequirementPoint).filter(
        RequirementPoint.module_id == module_id
    ).order_by(RequirementPoint.order_num).all()
    
    result = []
    total_test_points = 0
    
    for rp in requirement_points:
        test_points = db.query(TestPoint).filter(
            TestPoint.requirement_point_id == rp.id
        ).order_by(TestPoint.id).all()
        
        total_test_points += len(test_points)
        
        result.append({
            "id": rp.id,
            "content": rp.content,
            "priority": rp.priority,
            "created_by_ai": rp.created_by_ai,
            "test_points": [
                {
                    "id": tp.id,
                    "content": tp.content,
                    "test_type": tp.test_type,
                    "design_method": tp.design_method,
                    "priority": tp.priority,
                    "created_by_ai": tp.created_by_ai
                }
                for tp in test_points
            ]
        })
    
    return {
        "requirement_points": result,
        "statistics": {
            "total_requirement_points": len(requirement_points),
            "total_test_points": total_test_points
        }
    }


@router.post("/{project_id}/modules/{module_id}/test-points")
def create_module_test_point(
    project_id: int,
    module_id: int,
    content: str,
    requirement_point_id: int,
    test_type: str = "functional",
    design_method: Optional[str] = None,
    priority: str = "medium",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """手动创建测试点"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权创建测试点")
    
    # 验证需求点存在
    req_point = db.query(RequirementPoint).filter(
        RequirementPoint.id == requirement_point_id,
        RequirementPoint.module_id == module_id
    ).first()
    if not req_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求点不存在")
    
    test_point = TestPoint(
        module_id=module_id,
        requirement_point_id=requirement_point_id,
        content=content,
        test_type=test_type,
        design_method=design_method,
        priority=priority,
        created_by_ai=False,
        created_by=current_user.id
    )
    
    db.add(test_point)
    db.commit()
    db.refresh(test_point)
    
    return {
        "id": test_point.id,
        "content": test_point.content,
        "test_type": test_point.test_type,
        "design_method": test_point.design_method,
        "priority": test_point.priority
    }


@router.post("/{project_id}/modules/{module_id}/test-points/batch")
def batch_create_module_test_points(
    project_id: int,
    module_id: int,
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """批量创建测试点（支持先清空现有测试点）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权创建测试点")
    
    points_data = data.get("points", [])
    clear_existing = data.get("clear_existing", False)
    deleted_count = 0
    
    # 如果需要清空现有测试点
    if clear_existing:
        deleted_count = db.query(TestPoint).filter(
            TestPoint.module_id == module_id
        ).delete(synchronize_session=False)
        logger.info(f"清空模块 {module_id} 的测试点，删除 {deleted_count} 个（级联删除关联的测试用例）")
    
    created_points = []
    
    for point_data in points_data:
        test_point = TestPoint(
            module_id=module_id,
            requirement_point_id=point_data.get("requirement_point_id"),
            content=point_data.get("content", ""),
            test_type=point_data.get("test_type", "functional"),
            design_method=point_data.get("design_method"),  # 测试设计方法
            priority=point_data.get("priority", "medium"),
            created_by_ai=point_data.get("created_by_ai", False),
            created_by=current_user.id
        )
        db.add(test_point)
        created_points.append(test_point)
    
    db.commit()
    
    return {
        "success": True,
        "created_count": len(created_points),
        "deleted_count": deleted_count,
        "points": [
            {
                "id": tp.id,
                "content": tp.content,
                "test_type": tp.test_type,
                "design_method": tp.design_method,
                "priority": tp.priority
            }
            for tp in created_points
        ]
    }


@router.put("/{project_id}/modules/{module_id}/test-points/{point_id}")
def update_module_test_point(
    project_id: int,
    module_id: int,
    point_id: int,
    content: str,
    test_type: Optional[str] = None,
    design_method: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新测试点"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改测试点")
    
    test_point = db.query(TestPoint).filter(TestPoint.id == point_id).first()
    if not test_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试点不存在")
    
    test_point.content = content
    if test_type:
        test_point.test_type = test_type
    if design_method is not None:
        test_point.design_method = design_method
    if priority:
        test_point.priority = priority
    test_point.edited_by_user = True
    test_point.updated_by = current_user.id
    
    db.commit()
    db.refresh(test_point)
    
    return {
        "id": test_point.id,
        "content": test_point.content,
        "test_type": test_point.test_type,
        "design_method": test_point.design_method,
        "priority": test_point.priority
    }


@router.delete("/{project_id}/modules/{module_id}/test-points/{point_id}")
def delete_module_test_point(
    project_id: int,
    module_id: int,
    point_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """删除测试点（数据库级联删除会自动删除关联的测试用例）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除测试点")
    
    test_point = db.query(TestPoint).filter(TestPoint.id == point_id).first()
    if not test_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试点不存在")
    
    db.delete(test_point)
    db.commit()
    
    return {"message": "测试点已删除", "id": point_id}



# ========== 按模块管理测试用例 ==========

class TestCaseCreate(BaseModel):
    """测试用例创建Schema"""
    title: str
    test_point_id: int
    description: Optional[str] = None
    preconditions: Optional[str] = None
    test_steps: Optional[List[dict]] = None
    expected_result: Optional[str] = None
    design_method: Optional[str] = None
    test_method: Optional[str] = None
    status: Optional[str] = "draft"
    created_by_ai: bool = False


class TestCaseUpdate(BaseModel):
    """测试用例更新Schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    preconditions: Optional[str] = None
    test_steps: Optional[List[dict]] = None
    expected_result: Optional[str] = None
    design_method: Optional[str] = None
    test_method: Optional[str] = None
    status: Optional[str] = None


@router.get("/{project_id}/modules/{module_id}/test-cases")
def list_module_test_cases(
    project_id: int,
    module_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取模块的测试用例列表（按测试点分组）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.VIEWER, ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看测试用例")
    
    # 获取模块的测试点（按需求点顺序排序）
    test_points = db.query(TestPoint).join(
        RequirementPoint, TestPoint.requirement_point_id == RequirementPoint.id
    ).filter(
        TestPoint.module_id == module_id
    ).order_by(
        RequirementPoint.order_num,  # 先按需求点顺序
        TestPoint.id                  # 同一需求点内按ID
    ).all()
    
    result = []
    total_test_cases = 0
    
    for tp in test_points:
        test_cases = db.query(TestCase).filter(
            TestCase.test_point_id == tp.id
        ).order_by(TestCase.id).all()
        total_test_cases += len(test_cases)
        
        result.append({
            "id": tp.id,
            "content": tp.content,
            "test_type": tp.test_type,
            "design_method": tp.design_method,  # 添加设计方法字段
            "priority": tp.priority,
            "created_by_ai": tp.created_by_ai,
            "test_cases": [
                {
                    "id": tc.id,
                    "test_point_id": tc.test_point_id,
                    "module_id": tc.module_id,
                    "title": tc.title,
                    "description": tc.description,
                    "preconditions": tc.preconditions,
                    "test_steps": tc.test_steps,
                    "expected_result": tc.expected_result,
                    "design_method": tc.design_method,
                    "test_method": tc.test_method.value if tc.test_method and hasattr(tc.test_method, 'value') else tc.test_method,
                    "test_category": tc.test_category,  # 已改为字符串类型，直接返回
                    "priority": tc.priority,  # 添加优先级字段
                    "status": tc.status.value if hasattr(tc.status, 'value') else tc.status,
                    "created_by_ai": tc.created_by_ai,
                    "edited_by_user": tc.edited_by_user,
                    "created_at": tc.created_at.isoformat() if tc.created_at else None,
                    "updated_at": tc.updated_at.isoformat() if tc.updated_at else None
                }
                for tc in test_cases
            ]
        })
    
    return {
        "test_points": result,
        "total_test_points": len(test_points),
        "total_test_cases": total_test_cases
    }


@router.post("/{project_id}/modules/{module_id}/test-cases")
def create_module_test_case(
    project_id: int,
    module_id: int,
    data: TestCaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """创建测试用例"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权创建测试用例")
    
    # 验证测试点存在
    test_point = db.query(TestPoint).filter(TestPoint.id == data.test_point_id).first()
    if not test_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试点不存在")
    
    test_case = TestCase(
        test_point_id=data.test_point_id,
        module_id=module_id,
        title=data.title,
        description=data.description,
        preconditions=data.preconditions,
        test_steps=data.test_steps,
        expected_result=data.expected_result,
        design_method=data.design_method,
        test_method=data.test_method,
        status=data.status or "draft",
        created_by_ai=data.created_by_ai,
        created_by=current_user.id
    )
    
    db.add(test_case)
    db.commit()
    db.refresh(test_case)
    
    return {
        "id": test_case.id,
        "title": test_case.title,
        "test_point_id": test_case.test_point_id,
        "module_id": test_case.module_id,
        "status": test_case.status.value if hasattr(test_case.status, 'value') else test_case.status
    }


@router.put("/{project_id}/modules/{module_id}/test-cases/{case_id}")
def update_module_test_case(
    project_id: int,
    module_id: int,
    case_id: int,
    data: TestCaseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新测试用例"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改测试用例")
    
    test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试用例不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(test_case, field, value)
    
    test_case.edited_by_user = True
    test_case.updated_by = current_user.id
    
    db.commit()
    db.refresh(test_case)
    
    return {
        "id": test_case.id,
        "title": test_case.title,
        "description": test_case.description,
        "preconditions": test_case.preconditions,
        "test_steps": test_case.test_steps,
        "expected_result": test_case.expected_result,
        "design_method": test_case.design_method,
        "test_method": test_case.test_method.value if test_case.test_method and hasattr(test_case.test_method, 'value') else test_case.test_method,
        "status": test_case.status.value if hasattr(test_case.status, 'value') else test_case.status
    }


@router.delete("/{project_id}/modules/{module_id}/test-cases/{case_id}")
def delete_module_test_case(
    project_id: int,
    module_id: int,
    case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """删除测试用例"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除测试用例")
    
    test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试用例不存在")
    
    db.delete(test_case)
    db.commit()
    
    return {"message": "测试用例已删除", "id": case_id}


@router.post("/{project_id}/modules/{module_id}/test-cases/batch")
def batch_create_module_test_cases(
    project_id: int,
    module_id: int,
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """批量创建测试用例"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    if not check_project_permission(project, current_user, [ProjectRole.MEMBER, ProjectRole.OWNER]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权创建测试用例")
    
    test_cases_data = data.get("test_cases", [])
    clear_existing = data.get("clear_existing", False)
    deleted_count = 0
    
    # 如果需要清空现有测试用例
    if clear_existing:
        deleted_count = db.query(TestCase).filter(TestCase.module_id == module_id).delete(synchronize_session=False)
        logger.info(f"清空模块 {module_id} 的测试用例，删除 {deleted_count} 个")
    
    created_cases = []
    
    for tc_data in test_cases_data:
        test_case = TestCase(
            test_point_id=tc_data.get("test_point_id"),
            module_id=module_id,
            title=tc_data.get("title", ""),
            description=tc_data.get("description"),
            preconditions=tc_data.get("preconditions"),
            test_steps=tc_data.get("test_steps"),
            expected_result=tc_data.get("expected_result"),
            design_method=tc_data.get("design_method"),
            test_method=tc_data.get("test_method"),
            status=tc_data.get("status", "draft"),
            created_by_ai=tc_data.get("created_by_ai", False),
            created_by=current_user.id
        )
        db.add(test_case)
        created_cases.append(test_case)
    
    db.commit()
    
    return {
        "success": True,
        "created_count": len(created_cases),
        "deleted_count": deleted_count,
        "test_cases": [
            {"id": tc.id, "title": tc.title, "test_point_id": tc.test_point_id}
            for tc in created_cases
        ]
    }
