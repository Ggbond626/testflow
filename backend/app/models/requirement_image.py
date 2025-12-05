"""
需求文档图片模型
"""
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class RequirementImage(Base):
    """需求文档图片模型 - 存储从DOCX文档中提取的图片信息"""
    __tablename__ = "requirement_images"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    requirement_file_id: Mapped[int] = mapped_column(
        ForeignKey("requirement_files.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # 图片存储信息
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    image_format: Mapped[str] = mapped_column(String(10), nullable=False)  # png/jpg/gif
    image_size: Mapped[int] = mapped_column(Integer, nullable=False)  # 字节大小
    
    # 图片位置和尺寸
    position_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 在文档中的位置顺序
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # 图片描述
    alt_text: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    # 关系
    requirement_file: Mapped["RequirementFile"] = relationship(
        "RequirementFile", 
        back_populates="images"
    )
    
    def __repr__(self) -> str:
        return f"RequirementImage(id={self.id!r}, file_id={self.requirement_file_id!r}, path={self.image_path!r})"
