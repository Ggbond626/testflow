"""
系统设置服务层
提供测试分类、测试设计方法和并发配置的CRUD操作
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models.settings import TestCategory, TestDesignMethod, SystemConfig
from app.schemas.settings import (
    TestCategoryCreate, TestCategoryUpdate, TestCategoryResponse,
    TestDesignMethodCreate, TestDesignMethodUpdate, TestDesignMethodResponse,
    ConcurrencyConfig
)


# 默认测试分类
# 默认启用的分类
DEFAULT_ACTIVE_CATEGORIES = ["functional", "performance", "security", "interface", "stress", "usability"]

DEFAULT_TEST_CATEGORIES = [
    {"name": "功能测试", "code": "functional", "description": "验证系统功能是否符合需求规格", "order_index": 0, "is_active": True},
    {"name": "性能测试", "code": "performance", "description": "验证系统性能指标是否满足要求", "order_index": 1, "is_active": True},
    {"name": "安全测试", "code": "security", "description": "验证系统安全性和数据保护能力", "order_index": 2, "is_active": True},
    {"name": "接口测试", "code": "interface", "description": "验证系统接口的正确性和稳定性", "order_index": 3, "is_active": True},
    {"name": "压力测试", "code": "stress", "description": "验证系统在极限负载下的稳定性", "order_index": 4, "is_active": True},
    {"name": "可用性测试", "code": "usability", "description": "验证系统的用户体验和易用性", "order_index": 5, "is_active": True},
    {"name": "兼容性测试", "code": "compatibility", "description": "验证系统在不同环境下的兼容性", "order_index": 6, "is_active": False},
    {"name": "安装测试", "code": "installation", "description": "验证系统安装、升级和卸载过程", "order_index": 7, "is_active": False},
    {"name": "配置测试", "code": "configuration", "description": "验证系统配置的正确性和灵活性", "order_index": 8, "is_active": False},
    {"name": "探索性测试", "code": "exploratory", "description": "通过探索发现潜在问题", "order_index": 9, "is_active": False},
    {"name": "自动化测试", "code": "automation", "description": "验证自动化测试脚本的有效性", "order_index": 10, "is_active": False},
    {"name": "灾难恢复测试", "code": "disaster_recovery", "description": "验证系统灾难恢复能力", "order_index": 11, "is_active": False},
    {"name": "本地化测试", "code": "localization", "description": "验证系统的多语言和本地化支持", "order_index": 12, "is_active": False},
    {"name": "负载测试", "code": "load", "description": "验证系统在预期负载下的表现", "order_index": 13, "is_active": False},
    {"name": "容量测试", "code": "capacity", "description": "验证系统的最大容量和扩展能力", "order_index": 14, "is_active": False},
]

# 默认测试设计方法
DEFAULT_DESIGN_METHODS = [
    {"name": "等价类划分法", "code": "equivalence_partitioning", "description": "将输入数据划分为有效等价类和无效等价类", "order_index": 0},
    {"name": "边界值分析法", "code": "boundary_value", "description": "针对输入边界值设计测试用例", "order_index": 1},
    {"name": "因果图法", "code": "cause_effect", "description": "分析输入条件和输出结果之间的因果关系", "order_index": 2},
    {"name": "判定表法", "code": "decision_table", "description": "使用判定表分析复杂的业务逻辑", "order_index": 3},
    {"name": "状态转换法", "code": "state_transition", "description": "基于状态机模型设计测试用例", "order_index": 4},
    {"name": "正交试验法", "code": "orthogonal_array", "description": "使用正交表减少测试用例数量", "order_index": 5},
    {"name": "场景法", "code": "scenario", "description": "基于用户使用场景设计测试用例", "order_index": 6},
    {"name": "错误推测法", "code": "error_guessing", "description": "基于经验推测可能的错误设计测试用例", "order_index": 7},
]

# 并发配置键
CONCURRENCY_CONFIG_KEY = "concurrency_config"


class SettingsService:
    """系统设置服务类"""
    
    # ============== Test Categories ==============
    
    @staticmethod
    def get_test_categories(db: Session, active_only: bool = False) -> List[TestCategory]:
        """获取所有测试分类
        
        Args:
            db: 数据库会话
            active_only: 是否只返回启用的分类
            
        Returns:
            测试分类列表
        """
        query = db.query(TestCategory)
        if active_only:
            query = query.filter(TestCategory.is_active == True)
        return query.order_by(TestCategory.order_index, TestCategory.id).all()
    
    @staticmethod
    def get_test_category_by_id(db: Session, category_id: int) -> Optional[TestCategory]:
        """根据ID获取测试分类"""
        return db.query(TestCategory).filter(TestCategory.id == category_id).first()
    
    @staticmethod
    def get_test_category_by_code(db: Session, code: str) -> Optional[TestCategory]:
        """根据代码获取测试分类"""
        return db.query(TestCategory).filter(TestCategory.code == code).first()
    
    @staticmethod
    def create_test_category(db: Session, data: TestCategoryCreate) -> TestCategory:
        """创建测试分类
        
        Args:
            db: 数据库会话
            data: 创建数据
            
        Returns:
            创建的测试分类
            
        Raises:
            HTTPException: 当代码重复时抛出400错误
        """
        # 检查代码是否已存在
        existing = SettingsService.get_test_category_by_code(db, data.code)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"测试分类代码 '{data.code}' 已存在"
            )
        
        category = TestCategory(
            name=data.name,
            code=data.code,
            description=data.description,
            is_active=data.is_active,
            order_index=data.order_index,
            is_default=False
        )
        
        try:
            db.add(category)
            db.commit()
            db.refresh(category)
            return category
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"测试分类代码 '{data.code}' 已存在"
            )
    
    @staticmethod
    def update_test_category(db: Session, category_id: int, data: TestCategoryUpdate) -> Optional[TestCategory]:
        """更新测试分类
        
        Args:
            db: 数据库会话
            category_id: 分类ID
            data: 更新数据
            
        Returns:
            更新后的测试分类，如果不存在返回None
            
        Raises:
            HTTPException: 当更新的代码与其他分类重复时抛出400错误
        """
        category = SettingsService.get_test_category_by_id(db, category_id)
        if not category:
            return None
        
        # 如果更新代码，检查是否与其他分类重复
        if data.code is not None and data.code != category.code:
            existing = SettingsService.get_test_category_by_code(db, data.code)
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"测试分类代码 '{data.code}' 已存在"
                )
        
        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(category, key, value)
        
        try:
            db.commit()
            db.refresh(category)
            return category
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"测试分类代码 '{data.code}' 已存在"
            )
    
    @staticmethod
    def delete_test_category(db: Session, category_id: int) -> bool:
        """删除测试分类
        
        默认数据不允许删除，非默认数据真实删除
        
        Args:
            db: 数据库会话
            category_id: 分类ID
            
        Returns:
            是否删除成功
        """
        category = SettingsService.get_test_category_by_id(db, category_id)
        if not category:
            return False
        
        # 默认数据不允许删除
        if category.is_default:
            raise ValueError("默认分类不允许删除")
        
        # 非默认数据真实删除
        db.delete(category)
        db.commit()
        return True
    
    @staticmethod
    def reset_test_categories(db: Session) -> List[TestCategory]:
        """重置测试分类为默认值
        
        删除所有非默认分类，恢复默认分类的状态
        
        Args:
            db: 数据库会话
            
        Returns:
            重置后的测试分类列表
        """
        # 删除所有非默认分类
        db.query(TestCategory).filter(TestCategory.is_default == False).delete()
        
        # 恢复默认分类的状态
        default_categories = db.query(TestCategory).filter(TestCategory.is_default == True).all()
        
        # 如果没有默认分类，重新创建
        if not default_categories:
            for cat_data in DEFAULT_TEST_CATEGORIES:
                category = TestCategory(
                    name=cat_data["name"],
                    code=cat_data["code"],
                    description=cat_data["description"],
                    order_index=cat_data["order_index"],
                    is_active=cat_data["is_active"],  # 使用配置中的 is_active 值
                    is_default=True
                )
                db.add(category)
        else:
            # 恢复默认分类的状态（根据 DEFAULT_TEST_CATEGORIES 配置）
            default_config_map = {cat["code"]: cat["is_active"] for cat in DEFAULT_TEST_CATEGORIES}
            for category in default_categories:
                category.is_active = default_config_map.get(category.code, True)
        
        db.commit()
        return SettingsService.get_test_categories(db)
    
    # ============== Test Design Methods ==============
    
    @staticmethod
    def get_design_methods(db: Session, active_only: bool = False) -> List[TestDesignMethod]:
        """获取所有测试设计方法
        
        Args:
            db: 数据库会话
            active_only: 是否只返回启用的方法
            
        Returns:
            测试设计方法列表
        """
        query = db.query(TestDesignMethod)
        if active_only:
            query = query.filter(TestDesignMethod.is_active == True)
        return query.order_by(TestDesignMethod.order_index, TestDesignMethod.id).all()
    
    @staticmethod
    def get_design_method_by_id(db: Session, method_id: int) -> Optional[TestDesignMethod]:
        """根据ID获取测试设计方法"""
        return db.query(TestDesignMethod).filter(TestDesignMethod.id == method_id).first()
    
    @staticmethod
    def get_design_method_by_code(db: Session, code: str) -> Optional[TestDesignMethod]:
        """根据代码获取测试设计方法"""
        return db.query(TestDesignMethod).filter(TestDesignMethod.code == code).first()
    
    @staticmethod
    def create_design_method(db: Session, data: TestDesignMethodCreate) -> TestDesignMethod:
        """创建测试设计方法
        
        Args:
            db: 数据库会话
            data: 创建数据
            
        Returns:
            创建的测试设计方法
            
        Raises:
            HTTPException: 当代码重复时抛出400错误
        """
        # 检查代码是否已存在
        existing = SettingsService.get_design_method_by_code(db, data.code)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"测试设计方法代码 '{data.code}' 已存在"
            )
        
        method = TestDesignMethod(
            name=data.name,
            code=data.code,
            description=data.description,
            is_active=data.is_active,
            order_index=data.order_index,
            is_default=False
        )
        
        try:
            db.add(method)
            db.commit()
            db.refresh(method)
            return method
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"测试设计方法代码 '{data.code}' 已存在"
            )
    
    @staticmethod
    def update_design_method(db: Session, method_id: int, data: TestDesignMethodUpdate) -> Optional[TestDesignMethod]:
        """更新测试设计方法
        
        Args:
            db: 数据库会话
            method_id: 方法ID
            data: 更新数据
            
        Returns:
            更新后的测试设计方法，如果不存在返回None
            
        Raises:
            HTTPException: 当更新的代码与其他方法重复时抛出400错误
        """
        method = SettingsService.get_design_method_by_id(db, method_id)
        if not method:
            return None
        
        # 如果更新代码，检查是否与其他方法重复
        if data.code is not None and data.code != method.code:
            existing = SettingsService.get_design_method_by_code(db, data.code)
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"测试设计方法代码 '{data.code}' 已存在"
                )
        
        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(method, key, value)
        
        try:
            db.commit()
            db.refresh(method)
            return method
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"测试设计方法代码 '{data.code}' 已存在"
            )
    
    @staticmethod
    def delete_design_method(db: Session, method_id: int) -> bool:
        """删除测试设计方法
        
        默认数据不允许删除，非默认数据真实删除
        
        Args:
            db: 数据库会话
            method_id: 方法ID
            
        Returns:
            是否删除成功
        """
        method = SettingsService.get_design_method_by_id(db, method_id)
        if not method:
            return False
        
        # 默认数据不允许删除
        if method.is_default:
            raise ValueError("默认方法不允许删除")
        
        # 非默认数据真实删除
        db.delete(method)
        db.commit()
        return True
    
    @staticmethod
    def reset_design_methods(db: Session) -> List[TestDesignMethod]:
        """重置测试设计方法为默认值
        
        删除所有非默认方法，恢复默认方法的状态
        
        Args:
            db: 数据库会话
            
        Returns:
            重置后的测试设计方法列表
        """
        # 删除所有非默认方法
        db.query(TestDesignMethod).filter(TestDesignMethod.is_default == False).delete()
        
        # 恢复默认方法的状态
        default_methods = db.query(TestDesignMethod).filter(TestDesignMethod.is_default == True).all()
        
        # 如果没有默认方法，重新创建
        if not default_methods:
            for method_data in DEFAULT_DESIGN_METHODS:
                method = TestDesignMethod(
                    name=method_data["name"],
                    code=method_data["code"],
                    description=method_data["description"],
                    order_index=method_data["order_index"],
                    is_active=True,
                    is_default=True
                )
                db.add(method)
        else:
            # 恢复默认方法为活动状态
            for method in default_methods:
                method.is_active = True
        
        db.commit()
        return SettingsService.get_design_methods(db)
    
    # ============== Concurrency Config ==============
    
    @staticmethod
    def get_concurrency_config(db: Session) -> ConcurrencyConfig:
        """获取并发配置
        
        Args:
            db: 数据库会话
            
        Returns:
            并发配置对象，如果不存在返回默认配置
        """
        config = db.query(SystemConfig).filter(
            SystemConfig.config_key == CONCURRENCY_CONFIG_KEY
        ).first()
        
        if config:
            return ConcurrencyConfig(**config.config_value)
        
        # 返回默认配置
        return ConcurrencyConfig()
    
    @staticmethod
    def update_concurrency_config(db: Session, config: ConcurrencyConfig) -> ConcurrencyConfig:
        """更新并发配置
        
        Args:
            db: 数据库会话
            config: 新的并发配置
            
        Returns:
            更新后的并发配置
        """
        existing = db.query(SystemConfig).filter(
            SystemConfig.config_key == CONCURRENCY_CONFIG_KEY
        ).first()
        
        config_value = config.model_dump()
        
        if existing:
            existing.config_value = config_value
        else:
            new_config = SystemConfig(
                config_key=CONCURRENCY_CONFIG_KEY,
                config_value=config_value,
                description="AI生成任务并发控制配置"
            )
            db.add(new_config)
        
        db.commit()
        return config
    
    # ============== Initialization ==============
    
    @staticmethod
    def initialize_defaults(db: Session) -> None:
        """初始化默认配置
        
        在系统启动时调用，确保默认的测试分类和设计方法存在
        此方法是幂等的，多次调用不会产生重复数据
        
        Args:
            db: 数据库会话
        """
        # 初始化默认测试分类
        existing_category_codes = {
            cat.code for cat in db.query(TestCategory).all()
        }
        
        for cat_data in DEFAULT_TEST_CATEGORIES:
            if cat_data["code"] not in existing_category_codes:
                category = TestCategory(
                    name=cat_data["name"],
                    code=cat_data["code"],
                    description=cat_data["description"],
                    order_index=cat_data["order_index"],
                    is_active=cat_data["is_active"],  # 使用配置中的 is_active 值
                    is_default=True
                )
                db.add(category)
        
        # 初始化默认测试设计方法
        existing_method_codes = {
            method.code for method in db.query(TestDesignMethod).all()
        }
        
        for method_data in DEFAULT_DESIGN_METHODS:
            if method_data["code"] not in existing_method_codes:
                method = TestDesignMethod(
                    name=method_data["name"],
                    code=method_data["code"],
                    description=method_data["description"],
                    order_index=method_data["order_index"],
                    is_active=True,
                    is_default=True
                )
                db.add(method)
        
        # 初始化默认并发配置
        existing_concurrency = db.query(SystemConfig).filter(
            SystemConfig.config_key == CONCURRENCY_CONFIG_KEY
        ).first()
        
        if not existing_concurrency:
            default_config = ConcurrencyConfig()
            new_config = SystemConfig(
                config_key=CONCURRENCY_CONFIG_KEY,
                config_value=default_config.model_dump(),
                description="AI生成任务并发控制配置"
            )
            db.add(new_config)
        
        db.commit()


# 导出服务实例
settings_service = SettingsService()
