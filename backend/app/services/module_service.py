"""
功能模块服务层
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_
from fastapi import HTTPException

from app.models.module import Module, ModuleAssignment, ModuleStatus, ModulePriority
from app.models.user import User
from app.models.requirement import RequirementFile, RequirementPoint
from app.models.testcase import TestPoint, TestCase
from app.schemas.module import (
    ModuleCreate, ModuleUpdate, ModuleDetail, ModuleStats, 
    ModuleAssignee, ModuleAssignmentCreate, ProjectStatsResponse
)


class ModuleService:
    """功能模块服务"""
    
    @staticmethod
    def create_module(db: Session, project_id: int, module_data: ModuleCreate, user_id: int) -> Module:
        """创建功能模块"""
        # 获取当前项目下模块的最大order_num
        max_order = db.query(func.max(Module.order_num)).filter(
            Module.project_id == project_id
        ).scalar() or -1
        
        # 创建模块
        module = Module(
            project_id=project_id,
            name=module_data.name,
            description=module_data.description,
            priority=module_data.priority,
            status=module_data.status,
            order_num=max_order + 1
        )
        db.add(module)
        db.commit()
        db.refresh(module)
        
        return module
    
    @staticmethod
    def get_modules(db: Session, project_id: int, priority: Optional[ModulePriority] = None) -> List[ModuleDetail]:
        """获取项目的所有模块（包含统计信息）"""
        query = db.query(Module).filter(Module.project_id == project_id)
        
        if priority:
            query = query.filter(Module.priority == priority)
        
        modules = query.order_by(Module.order_num, Module.created_at).all()
        
        # 构建详细信息
        module_details = []
        for module in modules:
            stats = ModuleService._get_module_stats(db, module.id)
            assignees = ModuleService._get_module_assignees(db, module.id)
            
            module_detail = ModuleDetail(
                id=module.id,
                project_id=module.project_id,
                name=module.name,
                description=module.description,
                priority=module.priority,
                status=module.status,
                order_num=module.order_num,
                created_at=module.created_at,
                updated_at=module.updated_at,
                stats=stats,
                assignees=assignees
            )
            module_details.append(module_detail)
        
        return module_details
    
    @staticmethod
    def get_module(db: Session, module_id: int) -> Optional[ModuleDetail]:
        """获取单个模块详情"""
        module = db.query(Module).filter(Module.id == module_id).first()
        if not module:
            return None
        
        stats = ModuleService._get_module_stats(db, module.id)
        assignees = ModuleService._get_module_assignees(db, module.id)
        
        return ModuleDetail(
            id=module.id,
            project_id=module.project_id,
            name=module.name,
            description=module.description,
            priority=module.priority,
            status=module.status,
            order_num=module.order_num,
            created_at=module.created_at,
            updated_at=module.updated_at,
            stats=stats,
            assignees=assignees
        )
    
    @staticmethod
    def update_module(db: Session, module_id: int, module_data: ModuleUpdate) -> Optional[Module]:
        """更新模块信息"""
        module = db.query(Module).filter(Module.id == module_id).first()
        if not module:
            return None
        
        # 更新字段
        update_data = module_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(module, key, value)
        
        db.commit()
        db.refresh(module)
        return module
    
    @staticmethod
    def delete_module(db: Session, module_id: int) -> bool:
        """删除模块（级联删除相关数据）"""
        module = db.query(Module).filter(Module.id == module_id).first()
        if not module:
            return False
        
        db.delete(module)
        db.commit()
        return True
    
    @staticmethod
    def reorder_modules(db: Session, project_id: int, module_orders: List[dict]) -> bool:
        """调整模块顺序"""
        try:
            for item in module_orders:
                module_id = item.get('id')
                order_num = item.get('order_num')
                
                module = db.query(Module).filter(
                    Module.id == module_id,
                    Module.project_id == project_id
                ).first()
                
                if module:
                    module.order_num = order_num
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"调整顺序失败: {str(e)}")
    
    @staticmethod
    def assign_module(db: Session, module_id: int, assignment_data: ModuleAssignmentCreate, assigned_by: int) -> ModuleAssignee:
        """分配模块负责人"""
        # 检查模块是否存在
        module = db.query(Module).filter(Module.id == module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="模块不存在")
        
        # 检查用户是否存在
        user = db.query(User).filter(User.id == assignment_data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 检查是否已分配
        existing = db.query(ModuleAssignment).filter(
            ModuleAssignment.module_id == module_id,
            ModuleAssignment.user_id == assignment_data.user_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="该用户已被分配到此模块")
        
        # 创建分配
        assignment = ModuleAssignment(
            module_id=module_id,
            user_id=assignment_data.user_id,
            role=assignment_data.role,
            assigned_by=assigned_by
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        
        # 返回负责人信息
        return ModuleAssignee(
            id=assignment.id,
            user_id=assignment.user_id,
            username=user.username,
            role=assignment.role,
            assigned_at=assignment.assigned_at,
            assigned_by=assignment.assigned_by
        )
    
    @staticmethod
    def remove_assignment(db: Session, module_id: int, user_id: int) -> bool:
        """移除模块负责人"""
        assignment = db.query(ModuleAssignment).filter(
            ModuleAssignment.module_id == module_id,
            ModuleAssignment.user_id == user_id
        ).first()
        
        if not assignment:
            return False
        
        db.delete(assignment)
        db.commit()
        return True
    
    @staticmethod
    def get_assignees(db: Session, module_id: int) -> List[ModuleAssignee]:
        """获取模块的所有负责人"""
        return ModuleService._get_module_assignees(db, module_id)
    
    @staticmethod
    def _get_module_stats(db: Session, module_id: int) -> ModuleStats:
        """获取模块统计信息（内部方法）"""
        from app.models.testcase import TestCase, TestCaseStatus, TestPoint
        
        # 需求文件数量
        req_files_count = db.query(func.count(RequirementFile.id)).filter(
            RequirementFile.module_id == module_id
        ).scalar() or 0
        
        # 需求点数量（从requirement_files关联）
        req_points_count = db.query(func.count(RequirementPoint.id)).join(
            RequirementFile, RequirementPoint.requirement_file_id == RequirementFile.id
        ).filter(
            RequirementFile.module_id == module_id
        ).scalar() or 0
        
        # 测试点数量（直接从module_id查询）
        test_points_count = db.query(func.count(TestPoint.id)).filter(
            TestPoint.module_id == module_id
        ).scalar() or 0
        
        # 测试用例数量（直接从module_id查询）
        test_cases_count = db.query(func.count(TestCase.id)).filter(
            TestCase.module_id == module_id
        ).scalar() or 0
        
        # 已审核通过的测试用例数量
        test_cases_approved = db.query(func.count(TestCase.id)).filter(
            TestCase.module_id == module_id,
            TestCase.status == TestCaseStatus.APPROVED
        ).scalar() or 0
        
        # 有测试用例的测试点数量（用于计算覆盖率）
        test_points_with_cases = db.query(func.count(func.distinct(TestCase.test_point_id))).filter(
            TestCase.module_id == module_id,
            TestCase.test_point_id != None
        ).scalar() or 0
        
        # 计算完成率（基于测试点覆盖率：有测试用例的测试点 / 总测试点）
        completion_rate = 0.0
        if test_points_count > 0:
            completion_rate = (test_points_with_cases / test_points_count) * 100
        
        return ModuleStats(
            requirement_files_count=req_files_count,
            requirement_points_count=req_points_count,
            test_points_count=test_points_count,
            test_cases_count=test_cases_count,
            test_cases_approved=test_cases_approved,
            completion_rate=completion_rate
        )
    
    @staticmethod
    def _get_module_assignees(db: Session, module_id: int) -> List[ModuleAssignee]:
        """获取模块负责人列表（内部方法）"""
        assignments = db.query(ModuleAssignment, User).join(
            User, ModuleAssignment.user_id == User.id
        ).filter(
            ModuleAssignment.module_id == module_id
        ).all()
        
        return [
            ModuleAssignee(
                id=assignment.id,
                user_id=assignment.user_id,
                username=user.username,
                role=assignment.role,
                assigned_at=assignment.assigned_at,
                assigned_by=assignment.assigned_by
            )
            for assignment, user in assignments
        ]
    
    @staticmethod
    def get_project_stats(db: Session, project_id: int) -> ProjectStatsResponse:
        """获取项目统计信息"""
        # 模块数量
        module_count = db.query(func.count(Module.id)).filter(
            Module.project_id == project_id
        ).scalar() or 0
        
        # 按状态分组的模块数量
        modules_by_status = {}
        status_counts = db.query(
            Module.status,
            func.count(Module.id)
        ).filter(
            Module.project_id == project_id
        ).group_by(Module.status).all()
        
        for status, count in status_counts:
            modules_by_status[status.value] = count
        
        # 按优先级分组的模块数量
        modules_by_priority = {}
        priority_counts = db.query(
            Module.priority,
            func.count(Module.id)
        ).filter(
            Module.project_id == project_id
        ).group_by(Module.priority).all()
        
        for priority, count in priority_counts:
            modules_by_priority[priority.value] = count
        
        # 需求点数量（通过module关联）
        requirement_points_count = db.query(func.count(RequirementPoint.id)).join(
            RequirementFile, RequirementPoint.requirement_file_id == RequirementFile.id
        ).filter(
            RequirementFile.module_id.in_(
                db.query(Module.id).filter(Module.project_id == project_id)
            )
        ).scalar() or 0
        
        # 测试用例数量
        # 统计逻辑：
        # 1. 直接关联到项目的用例 (project_id matches)
        # 2. 关联到项目下模块的用例 (module.project_id matches)
        test_cases_count = db.query(func.count(TestCase.id)).outerjoin(
            Module, TestCase.module_id == Module.id
        ).filter(
            or_(
                TestCase.project_id == project_id,
                Module.project_id == project_id
            )
        ).scalar() or 0
        
        # 成员数量（从project_members表获取）
        from app.models.user import ProjectMember
        member_count = db.query(func.count(ProjectMember.id)).filter(
            ProjectMember.project_id == project_id
        ).scalar() or 0
        
        return ProjectStatsResponse(
            module_count=module_count,
            member_count=member_count,
            requirement_points_count=requirement_points_count,
            test_cases_count=test_cases_count,
            modules_by_status=modules_by_status,
            modules_by_priority=modules_by_priority,
            recent_activities=[]  # TODO: 实现最近活动
        )


# 导出服务实例
module_service = ModuleService()

