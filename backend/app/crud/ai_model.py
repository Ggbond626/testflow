from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.models.ai_model import AIModel
from app.schemas.ai_model import AIModelCreate, AIModelUpdate


class CRUDAIModel:
    """AI模型CRUD操作"""

    def get(self, db: Session, id: int) -> Optional[AIModel]:
        """根据ID获取AI模型"""
        return db.query(AIModel).filter(AIModel.id == id).first()

    def get_by_model_id(self, db: Session, model_id: str) -> Optional[AIModel]:
        """根据模型ID获取AI模型"""
        return db.query(AIModel).filter(AIModel.model_id == model_id).first()

    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[AIModel]:
        """获取AI模型列表"""
        query = db.query(AIModel)
        
        if is_active is not None:
            query = query.filter(AIModel.is_active == is_active)
            
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: AIModelCreate) -> AIModel:
        """创建AI模型"""
        db_obj = AIModel(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, 
        db: Session, 
        db_obj: AIModel, 
        obj_in: AIModelUpdate
    ) -> AIModel:
        """更新AI模型"""
        update_data = obj_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, id: int) -> Optional[AIModel]:
        """删除AI模型"""
        obj = db.query(AIModel).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def get_active_models(self, db: Session) -> List[AIModel]:
        """获取所有激活的AI模型"""
        return db.query(AIModel).filter(AIModel.is_active == True).all()

    def count(self, db: Session, is_active: Optional[bool] = None) -> int:
        """统计AI模型数量"""
        query = db.query(AIModel)
        
        if is_active is not None:
            query = query.filter(AIModel.is_active == is_active)
            
        return query.count()


ai_model = CRUDAIModel()
