"""
初始化数据脚本
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.user import User, UserRole
from app.models.ai_config import AIModel, Agent, AgentType
from app.core.security import get_password_hash
from app.config import settings
from app.prompts import (
    REQUIREMENT_SPLITTER_SYSTEM,
    TEST_POINT_GENERATOR_SYSTEM,
    TEST_CASE_DESIGNER_SYSTEM,
    TEST_CASE_OPTIMIZER_SYSTEM
)


def create_admin_user(db: Session) -> User:
    """创建管理员用户"""
    # 检查是否已存在管理员
    admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    if admin:
        print(f"✅ 管理员用户已存在: {admin.username}")
        return admin
    
    # 创建默认管理员
    admin_user = User(
        username="admin",
        email="admin@autotestcase.com",
        password_hash=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    print(f"✅ 管理员用户创建成功: {admin_user.username}")
    print(f"   邮箱: {admin_user.email}")
    print(f"   默认密码: admin123")
    print(f"   ⚠️  请及时修改默认密码！")
    
    return admin_user


def create_demo_user(db: Session) -> User:
    """创建演示用户"""
    # 检查是否已存在演示用户
    demo_user = db.query(User).filter(User.username == "demo").first()
    if demo_user:
        print(f"✅ 演示用户已存在: {demo_user.username}")
        return demo_user
    
    # 创建演示用户
    demo_user = User(
        username="demo",
        email="demo@autotestcase.com",
        password_hash=get_password_hash("demo123"),
        role=UserRole.USER,
        is_active=True
    )
    
    db.add(demo_user)
    db.commit()
    db.refresh(demo_user)
    
    print(f"✅ 演示用户创建成功: {demo_user.username}")
    print(f"   邮箱: {demo_user.email}")
    print(f"   密码: demo123")
    
    return demo_user


def create_default_ai_models(db: Session, admin_user: User) -> list[AIModel]:
    """创建默认AI模型配置（仅在没有任何模型时创建）"""
    # 检查是否已有任何模型配置
    existing_model_count = db.query(AIModel).count()
    if existing_model_count > 0:
        print(f"✅ 已有 {existing_model_count} 个AI模型配置，跳过默认模型创建")
        # 返回所有现有模型供智能体使用
        return db.query(AIModel).all()
    
    # 首次启动，创建默认模型
    print("🔄 首次启动，创建默认AI模型...")
    
    ai_model = AIModel(
        name="OpenAI GPT-4",
        provider="openai",
        model_id="gpt-4",
        api_key="your-openai-api-key-here",
        base_url="https://api.openai.com/v1",
        is_active=False,  # 默认不激活，需要配置真实API密钥后激活
        created_by=admin_user.id
    )
    
    db.add(ai_model)
    db.commit()
    db.refresh(ai_model)
    
    print(f"✅ 默认AI模型创建成功: {ai_model.name}")
    return [ai_model]


def create_default_agents(db: Session, admin_user: User, ai_models: list[AIModel]) -> list[Agent]:
    """创建默认智能体配置"""
    if not ai_models:
        print("⚠️  没有可用的AI模型，跳过智能体创建")
        return []
    
    # 使用第一个模型作为默认模型
    default_model = ai_models[0]
    agents = []
    
    # 默认智能体配置（system_prompt从prompts.py中引用，便于统一管理）
    # 名称与前端实际使用的保持一致
    default_agents = [
        {
            "name": "需求拆分专家",
            "type": AgentType.REQUIREMENT_SPLITTER,
            "system_prompt": REQUIREMENT_SPLITTER_SYSTEM
        },
        {
            "name": "测试分析专家",
            "type": AgentType.TEST_POINT_GENERATOR,
            "system_prompt": TEST_POINT_GENERATOR_SYSTEM
        },
        {
            "name": "测试用例设计专家",
            "type": AgentType.TEST_CASE_DESIGNER,
            "system_prompt": TEST_CASE_DESIGNER_SYSTEM
        },
        {
            "name": "测试用例优化专家",
            "type": AgentType.TEST_CASE_OPTIMIZER,
            "system_prompt": TEST_CASE_OPTIMIZER_SYSTEM
        }
    ]
    
    for agent_config in default_agents:
        # 按AgentType检查是否已存在（而非按名称，避免名称修改后重复创建）
        existing_agent = db.query(Agent).filter(
            Agent.type == agent_config["type"]
        ).first()
        
        if existing_agent:
            print(f"✅ 智能体已存在: {existing_agent.name} (类型: {existing_agent.type.value})")
            agents.append(existing_agent)
            continue
        
        # 创建新智能体
        agent = Agent(
            name=agent_config["name"],
            type=agent_config["type"],
            ai_model_id=default_model.id,
            system_prompt=agent_config["system_prompt"],
            temperature=0.7,
            max_tokens=128000,  # 128k tokens，支持大批量生成
            is_active=False,  # 默认不激活，需要配置AI模型后激活
            created_by=admin_user.id
        )
        
        db.add(agent)
        agents.append(agent)
        print(f"✅ 智能体创建成功: {agent.name}")
    
    db.commit()
    return agents


def init_database():
    """初始化数据库数据"""
    print("🔄 开始初始化数据库数据...")
    
    db = SessionLocal()
    try:
        # 创建管理员用户
        admin_user = create_admin_user(db)
        
        # 创建演示用户
        demo_user = create_demo_user(db)
        
        # 创建默认AI模型
        ai_models = create_default_ai_models(db, admin_user)
        
        # 创建默认智能体
        agents = create_default_agents(db, admin_user, ai_models)
        
        print("\n🎉 数据库初始化完成！")
        print("\n📋 初始化摘要:")
        print(f"   👤 管理员用户: admin (密码: admin123)")
        print(f"   👤 演示用户: demo (密码: demo123)")
        print(f"   🤖 AI模型: {len(ai_models)} 个")
        print(f"   🧠 智能体: {len(agents)} 个")
        print("\n⚠️  重要提醒:")
        print("   1. 请及时修改默认密码")
        print("   2. 请配置真实的AI模型API密钥")
        print("   3. 配置完成后激活AI模型和智能体")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
