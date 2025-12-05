"""
AI模型管理API路由
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.models.ai_config import AIModel, Agent, AgentType
from app.schemas.user import User as UserSchema
from app.core.security import get_password_hash


router = APIRouter()


# 请求模型
class AIModelCreate(BaseModel):
    """AI模型创建请求"""
    model_config = {"protected_namespaces": ()}
    
    name: str = Field(..., min_length=1, max_length=100, description="模型显示名称")
    provider: str = Field(default="openai", description="模型提供商")
    model_id: str = Field(..., min_length=1, max_length=100, description="模型ID")
    base_url: str = Field(..., description="API基础地址")
    api_key: Optional[str] = Field(default="", description="API密钥(可选)")
    max_tokens: int = Field(default=4000, ge=100, le=128000, description="最大令牌数")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    stream_support: bool = Field(default=True, description="是否支持流式输出")
    is_active: bool = Field(default=True, description="是否激活")


class AIModelUpdate(BaseModel):
    """AI模型更新请求"""
    model_config = {"protected_namespaces": ()}
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模型显示名称")
    provider: Optional[str] = Field(None, description="模型提供商")
    model_id: Optional[str] = Field(None, min_length=1, max_length=100, description="模型ID")
    base_url: Optional[str] = Field(None, description="API基础地址")
    api_key: Optional[str] = Field(None, description="API密钥(可选)")
    max_tokens: Optional[int] = Field(None, ge=100, le=128000, description="最大令牌数")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="温度参数")
    stream_support: Optional[bool] = Field(None, description="是否支持流式输出")
    is_active: Optional[bool] = Field(None, description="是否激活")


class AIModelTest(BaseModel):
    """AI模型测试请求"""
    message: str = Field(default="Hello, this is a test message.", description="测试消息")


class AgentCreate(BaseModel):
    """智能体创建请求"""
    name: str = Field(..., description="智能体名称")
    type: str = Field(..., description="智能体类型")
    ai_model_id: int = Field(..., description="AI模型ID")
    prompt_template: Optional[str] = Field(default=None, description="提示词模板")
    system_prompt: Optional[str] = Field(default=None, description="系统提示词")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=2000, description="最大令牌数")


class AgentUpdate(BaseModel):
    """智能体更新请求"""
    name: Optional[str] = Field(default=None, description="智能体名称")
    ai_model_id: Optional[int] = Field(default=None, description="AI模型ID")
    prompt_template: Optional[str] = Field(default=None, description="提示词模板")
    system_prompt: Optional[str] = Field(default=None, description="系统提示词")
    temperature: Optional[float] = Field(default=None, description="温度参数")
    max_tokens: Optional[int] = Field(default=None, description="最大令牌数")
    is_active: Optional[bool] = Field(default=None, description="是否激活")


# 响应模型
class AIModelResponse(BaseModel):
    """AI模型响应"""
    model_config = {"protected_namespaces": ()}
    
    id: int
    name: str
    provider: str
    model_id: str
    base_url: str
    max_tokens: int
    temperature: float
    stream_support: bool
    is_active: bool
    created_at: str
    updated_at: str

class AIModelDetailResponse(BaseModel):
    """AI模型详情响应（包含API密钥）"""
    model_config = {"protected_namespaces": ()}
    
    id: int
    name: str
    provider: str
    model_id: str
    base_url: str
    api_key: str
    max_tokens: int
    temperature: float
    stream_support: bool
    is_active: bool
    created_at: str
    updated_at: str


class AIModelTestResponse(BaseModel):
    """AI模型测试响应"""
    success: bool
    message: str
    response: Optional[dict] = None
    error: Optional[str] = None


class AgentResponse(BaseModel):
    """智能体响应"""
    id: int
    name: str
    type: str
    type_display: str
    ai_model_id: Optional[int] = None
    ai_model_name: str
    temperature: float
    max_tokens: int
    system_prompt: Optional[str] = None
    prompt_template: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str


# AI模型管理API
@router.post("/models", response_model=AIModelResponse)
def create_ai_model(
    model_data: AIModelCreate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_admin_user)
) -> Any:
    """创建AI模型（仅管理员）"""
    try:
        # 检查模型ID是否已存在
        existing_model = db.query(AIModel).filter(AIModel.model_id == model_data.model_id).first()
        if existing_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="模型ID已存在"
            )
        
        # 创建AI模型
        ai_model = AIModel(
            name=model_data.name,
            provider=model_data.provider,
            model_id=model_data.model_id,
            api_key=model_data.api_key,  # 实际应用中需要加密存储
            base_url=model_data.base_url,
            max_tokens=model_data.max_tokens,
            temperature=model_data.temperature,
            stream_support=model_data.stream_support,
            is_active=model_data.is_active,
            created_by=current_user.id
        )
        
        db.add(ai_model)
        db.commit()
        db.refresh(ai_model)
        
        return AIModelResponse(
            id=ai_model.id,
            name=ai_model.name,
            provider=ai_model.provider,
            model_id=ai_model.model_id,
            base_url=ai_model.base_url,
            max_tokens=ai_model.max_tokens,
            temperature=ai_model.temperature,
            stream_support=ai_model.stream_support,
            is_active=ai_model.is_active,
            created_at=ai_model.created_at.isoformat(),
            updated_at=ai_model.updated_at.isoformat()
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建AI模型失败: {str(e)}"
        )


@router.get("/models", response_model=List[AIModelResponse])
def get_ai_models(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_admin_user)
) -> Any:
    """获取AI模型列表（仅管理员）"""
    query = db.query(AIModel)
    
    if is_active is not None:
        query = query.filter(AIModel.is_active == is_active)
        
    models = query.offset(skip).limit(limit).all()
    
    return [
        AIModelResponse(
            id=model.id,
            name=model.name,
            provider=model.provider,
            model_id=model.model_id,
            base_url=model.base_url,
            max_tokens=model.max_tokens,
            temperature=model.temperature,
            stream_support=model.stream_support,
            is_active=model.is_active,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat()
        )
        for model in models
    ]


@router.get("/models/{model_id}", response_model=AIModelDetailResponse)
def get_ai_model_detail(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_admin_user)
) -> Any:
    """获取AI模型详情（仅管理员，包含API密钥）"""
    ai_model = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not ai_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI模型不存在"
        )
    
    return AIModelDetailResponse(
        id=ai_model.id,
        name=ai_model.name,
        provider=ai_model.provider,
        model_id=ai_model.model_id,
        base_url=ai_model.base_url,
        api_key=ai_model.api_key,
        max_tokens=ai_model.max_tokens,
        temperature=ai_model.temperature,
        stream_support=ai_model.stream_support,
        is_active=ai_model.is_active,
        created_at=ai_model.created_at.isoformat(),
        updated_at=ai_model.updated_at.isoformat()
    )


@router.put("/models/{model_id}", response_model=AIModelResponse)
def update_ai_model(
    model_id: int,
    model_data: AIModelUpdate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_admin_user)
) -> Any:
    """更新AI模型（仅管理员）"""
    ai_model = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not ai_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI模型不存在"
        )
    
    try:
        # 更新字段
        update_data = model_data.dict(exclude_unset=True)
        # 如果api_key为空，则不更新该字段（保持原有密钥）
        if 'api_key' in update_data and not update_data['api_key']:
            update_data.pop('api_key')
        
        for field, value in update_data.items():
            setattr(ai_model, field, value)
        
        db.commit()
        db.refresh(ai_model)
        
        return AIModelResponse(
            id=ai_model.id,
            name=ai_model.name,
            provider=ai_model.provider,
            model_id=ai_model.model_id,
            base_url=ai_model.base_url,
            max_tokens=ai_model.max_tokens,
            temperature=ai_model.temperature,
            stream_support=ai_model.stream_support,
            is_active=ai_model.is_active,
            created_at=ai_model.created_at.isoformat(),
            updated_at=ai_model.updated_at.isoformat()
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新AI模型失败: {str(e)}"
        )


@router.delete("/models/{model_id}")
def delete_ai_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_admin_user)
) -> Any:
    """删除AI模型（仅管理员）"""
    ai_model = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not ai_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI模型不存在"
        )
    
    # 检查是否有智能体在使用此模型
    agents_using_model = db.query(Agent).filter(Agent.ai_model_id == model_id).count()
    if agents_using_model > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法删除，有 {agents_using_model} 个智能体正在使用此模型"
        )
    
    try:
        db.delete(ai_model)
        db.commit()
        return {"message": "AI模型删除成功"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除AI模型失败: {str(e)}"
        )


@router.post("/models/{model_id}/test", response_model=AIModelTestResponse)
async def test_ai_model(
    model_id: int,
    test_data: AIModelTest,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_admin_user)
) -> Any:
    """测试AI模型连接（仅管理员）"""
    ai_model = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not ai_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI模型不存在"
        )
    
    try:
        import httpx
        
        # 构建测试请求
        test_payload = {
            "model": ai_model.model_id,
            "messages": [
                {"role": "user", "content": test_data.message}
            ],
            "max_tokens": min(50, ai_model.max_tokens),
            "temperature": ai_model.temperature
        }
        
        # 设置请求头
        headers = {
            "Authorization": f"Bearer {ai_model.api_key}",
            "Content-Type": "application/json"
        }
        
        # 发送测试请求
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ai_model.base_url.rstrip('/')}/chat/completions",
                json=test_payload,
                headers=headers
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return AIModelTestResponse(
                    success=True,
                    message="模型测试成功，连接正常",
                    response=response_data
                )
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error", {}).get("message", error_detail)
                except:
                    pass
                
                return AIModelTestResponse(
                    success=False,
                    message=f"模型测试失败: HTTP {response.status_code}",
                    error=error_detail
                )
                
    except Exception as e:
        return AIModelTestResponse(
            success=False,
            message="模型测试失败: 网络错误",
            error=str(e)
        )


# 智能体管理API
@router.post("/agents", response_model=AgentResponse)
def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_active_user)
) -> Any:
    """创建智能体"""
    try:
        # 验证智能体类型
        try:
            agent_type = AgentType(agent_data.type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的智能体类型: {agent_data.type}"
            )
        
        # 验证AI模型是否存在
        ai_model = db.query(AIModel).filter(
            AIModel.id == agent_data.ai_model_id,
            AIModel.is_active == True
        ).first()
        if not ai_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的AI模型不存在或未激活"
            )
        
        # 创建智能体
        agent = Agent(
            name=agent_data.name,
            type=agent_type,
            ai_model_id=agent_data.ai_model_id,
            prompt_template=agent_data.prompt_template,
            system_prompt=agent_data.system_prompt,
            temperature=agent_data.temperature,
            max_tokens=agent_data.max_tokens,
            created_by=current_user.id
        )
        
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
        return AgentResponse(
            id=agent.id,
            name=agent.name,
            type=agent.type.value,
            type_display=_get_agent_type_display(agent.type),
            ai_model_name=ai_model.name,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            is_active=agent.is_active,
            created_at=agent.created_at.isoformat(),
            updated_at=agent.updated_at.isoformat()
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建智能体失败: {str(e)}"
        )


@router.get("/agents", response_model=List[AgentResponse])
def get_agents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_active_user)
) -> Any:
    """获取智能体列表"""
    agents = db.query(Agent).filter(Agent.is_active == True).offset(skip).limit(limit).all()
    
    result = []
    for agent in agents:
        ai_model = db.query(AIModel).filter(AIModel.id == agent.ai_model_id).first()
        
        result.append(AgentResponse(
            id=agent.id,
            name=agent.name,
            type=agent.type.value,
            type_display=_get_agent_type_display(agent.type),
            ai_model_id=agent.ai_model_id,
            ai_model_name=ai_model.name if ai_model else "未设置",
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            system_prompt=agent.system_prompt,
            prompt_template=agent.prompt_template,
            is_active=agent.is_active,
            created_at=agent.created_at.isoformat(),
            updated_at=agent.updated_at.isoformat()
        ))
    
    return result


@router.put("/agents/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_active_user)
) -> Any:
    """更新智能体"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    # 检查权限（只能修改自己创建的智能体，除非是管理员）
    if agent.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此智能体"
        )
    
    try:
        # 更新字段
        update_data = agent_data.dict(exclude_unset=True)
        
        # 验证：如果设置为激活，必须先关联模型
        if update_data.get('is_active') == True:
            # 检查是否有关联模型
            model_id = update_data.get('ai_model_id', agent.ai_model_id)
            if model_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无法激活智能体：请先关联AI模型"
                )
        
        for field, value in update_data.items():
            setattr(agent, field, value)
        
        db.commit()
        db.refresh(agent)
        
        ai_model = db.query(AIModel).filter(AIModel.id == agent.ai_model_id).first()
        
        return AgentResponse(
            id=agent.id,
            name=agent.name,
            type=agent.type.value,
            type_display=_get_agent_type_display(agent.type),
            ai_model_id=agent.ai_model_id,
            ai_model_name=ai_model.name if ai_model else "未设置",
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            system_prompt=agent.system_prompt,
            prompt_template=agent.prompt_template,
            is_active=agent.is_active,
            created_at=agent.created_at.isoformat(),
            updated_at=agent.updated_at.isoformat()
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新智能体失败: {str(e)}"
        )


def _get_agent_type_display(agent_type: AgentType) -> str:
    """获取智能体类型显示名称"""
    type_map = {
        AgentType.REQUIREMENT_SPLITTER: "需求拆分智能体",
        AgentType.TEST_POINT_GENERATOR: "测试点生成智能体",
        AgentType.TEST_CASE_DESIGNER: "测试用例设计智能体",
        AgentType.TEST_CASE_OPTIMIZER: "测试用例优化智能体"
    }
    return type_map.get(agent_type, agent_type.value)
