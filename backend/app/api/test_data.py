"""
测试数据查询API
用于 GenerationResultsV2.vue 查询和管理测试层级数据
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.project import Project
from app.models.requirement import RequirementFile, RequirementPoint
from app.models.testcase import TestPoint, TestCase

router = APIRouter(prefix="/test-data", tags=["test-data"])


@router.get("/projects/{project_id}/test-hierarchy")
def get_test_hierarchy(
    project_id: int,
    file_id: Optional[int] = Query(None, description="需求文件ID"),
    module_id: Optional[int] = Query(None, description="模块ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取完整的测试层级结构（需求点->测试点->测试用例）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    
    # 构建查询
    if module_id:
        query = db.query(RequirementPoint).filter(RequirementPoint.module_id == module_id)
    else:
        query = db.query(RequirementPoint).join(
            RequirementFile,
            RequirementPoint.requirement_file_id == RequirementFile.id,
            isouter=True
        ).filter(
            (RequirementFile.project_id == project_id) |
            (RequirementPoint.module_id.isnot(None))
        )
    
    if file_id:
        query = query.filter(RequirementPoint.requirement_file_id == file_id)
    
    requirement_points = query.order_by(RequirementPoint.order_num).all()
    
    # 构建层级结构
    hierarchy = []
    for req_point in requirement_points:
        test_points = db.query(TestPoint).filter(
            TestPoint.requirement_point_id == req_point.id
        ).all()
        
        test_points_data = []
        for test_point in test_points:
            test_cases = db.query(TestCase).filter(
                TestCase.test_point_id == test_point.id
            ).all()
            
            test_points_data.append({
                "id": test_point.id,
                "content": test_point.content,
                "test_type": test_point.test_type.value if hasattr(test_point.test_type, 'value') else test_point.test_type,
                "priority": test_point.priority.value if hasattr(test_point.priority, 'value') else test_point.priority,
                "status": test_point.status.value if hasattr(test_point.status, 'value') else test_point.status,
                "test_cases": [
                    {
                        "id": tc.id,
                        "title": tc.title,
                        "description": tc.description,
                        "status": tc.status.value if hasattr(tc.status, 'value') else tc.status,
                        "test_method": tc.test_method.value if tc.test_method and hasattr(tc.test_method, 'value') else tc.test_method
                    }
                    for tc in test_cases
                ]
            })
        
        hierarchy.append({
            "id": req_point.id,
            "content": req_point.content,
            "order_index": req_point.order_num,
            "status": req_point.status.value if hasattr(req_point.status, 'value') else req_point.status,
            "test_points": test_points_data
        })
    
    return {
        "project_id": project_id,
        "file_id": file_id,
        "requirement_points": hierarchy,
        "statistics": {
            "total_requirement_points": len(requirement_points),
            "total_test_points": sum(len(rp["test_points"]) for rp in hierarchy),
            "total_test_cases": sum(
                len(tp["test_cases"]) 
                for rp in hierarchy 
                for tp in rp["test_points"]
            )
        }
    }


@router.put("/requirement-points/{point_id}")
def update_requirement_point(
    point_id: int,
    content: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新需求点内容"""
    req_point = db.query(RequirementPoint).filter(RequirementPoint.id == point_id).first()
    if not req_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求点不存在")
    
    req_point.content = content
    req_point.edited_by_user = True
    req_point.updated_by = current_user.id
    req_point.status = "confirmed"
    
    db.commit()
    db.refresh(req_point)
    return {"id": req_point.id, "content": req_point.content, "status": req_point.status}


@router.put("/test-points/{point_id}")
def update_test_point(
    point_id: int,
    content: str,
    test_type: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新测试点内容"""
    test_point = db.query(TestPoint).filter(TestPoint.id == point_id).first()
    if not test_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试点不存在")
    
    test_point.content = content
    if test_type:
        test_point.test_type = test_type
    if priority:
        test_point.priority = priority
    test_point.edited_by_user = True
    test_point.updated_by = current_user.id
    test_point.status = "confirmed"
    
    db.commit()
    db.refresh(test_point)
    return {"id": test_point.id, "content": test_point.content, "status": test_point.status}


@router.put("/test-cases/{case_id}")
def update_test_case(
    case_id: int,
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新测试用例"""
    test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试用例不存在")
    
    if "title" in data:
        test_case.title = data["title"]
    if "description" in data:
        test_case.description = data["description"]
    if "preconditions" in data:
        test_case.preconditions = data["preconditions"]
    if "test_steps" in data:
        test_case.test_steps = data["test_steps"]
    if "expected_result" in data:
        test_case.expected_result = data["expected_result"]
    
    test_case.edited_by_user = True
    test_case.updated_by = current_user.id
    test_case.status = "under_review"
    
    db.commit()
    db.refresh(test_case)
    return {"id": test_case.id, "title": test_case.title, "status": test_case.status, "message": "更新成功"}


@router.delete("/requirement-points/{point_id}")
def delete_requirement_point(
    point_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """删除需求点（数据库级联删除会自动删除关联的测试点和测试用例）"""
    req_point = db.query(RequirementPoint).filter(RequirementPoint.id == point_id).first()
    if not req_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求点不存在")
    
    db.delete(req_point)
    db.commit()
    return {"message": "需求点已删除"}


@router.delete("/test-points/{point_id}")
def delete_test_point(
    point_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """删除测试点（数据库级联删除会自动删除关联的测试用例）"""
    test_point = db.query(TestPoint).filter(TestPoint.id == point_id).first()
    if not test_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试点不存在")
    
    db.delete(test_point)
    db.commit()
    return {"message": "测试点已删除"}


@router.delete("/test-cases/{case_id}")
def delete_test_case(
    case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """删除测试用例"""
    test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试用例不存在")
    
    db.delete(test_case)
    db.commit()
    return {"message": "测试用例已删除"}


@router.get("/stats")
def get_test_data_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取测试数据统计信息"""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    from app.models.ai_config import Agent
    
    # 测试用例总数
    total_test_cases = db.query(func.count(TestCase.id)).scalar() or 0
    
    # 测试点总数
    total_test_points = db.query(func.count(TestPoint.id)).scalar() or 0
    
    # 需求点总数
    total_requirement_points = db.query(func.count(RequirementPoint.id)).scalar() or 0
    
    # 本周新增测试用例
    one_week_ago = datetime.now() - timedelta(days=7)
    weekly_new = db.query(func.count(TestCase.id)).filter(
        TestCase.created_at >= one_week_ago
    ).scalar() or 0
    
    # AI智能体数量（只统计活跃的）
    active_agents = db.query(func.count(Agent.id)).filter(Agent.is_active == True).scalar() or 0
    
    return {
        "total_test_cases": total_test_cases,
        "total_test_points": total_test_points,
        "total_requirement_points": total_requirement_points,
        "weekly_new": weekly_new,
        "total_agents": active_agents
    }
