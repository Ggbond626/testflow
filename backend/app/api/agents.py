"""
AI智能体相关API路由
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.agent_service_real import agent_service_real as agent_service
from app.schemas.user import User as UserSchema


router = APIRouter()


# 请求模型
class RequirementAnalysisRequest(BaseModel):
    """需求分析请求"""
    requirement_content: str = Field(..., description="需求文档内容")
    project_context: str = Field(default="", description="项目背景信息")
    agent_id: Optional[int] = Field(default=None, description="指定智能体ID")
    image_paths: Optional[List[str]] = Field(default=None, description="图片文件路径列表（用于多模态分析）")


class TestPointGenerationRequest(BaseModel):
    """测试点生成请求
    
    测试分类和设计方法由后端从系统设置自动加载，无需前端传递
    """
    requirement_points: List[dict] = Field(..., description="需求点列表")
    agent_id: Optional[int] = Field(default=None, description="指定智能体ID")


class TestCaseDesignRequest(BaseModel):
    """测试用例设计请求"""
    test_points: List[dict] = Field(..., description="测试点列表")
    test_environment: str = Field(default="标准测试环境", description="测试环境")
    test_data_requirements: str = Field(default="使用标准测试数据", description="测试数据要求")
    agent_id: Optional[int] = Field(default=None, description="指定智能体ID")


class TestCaseOptimizationRequest(BaseModel):
    """测试用例优化请求"""
    original_test_cases: List[dict] = Field(..., description="原始测试用例")
    review_feedback: List[dict] = Field(default=[], description="评审反馈")
    optimization_requirements: str = Field(default="全面优化测试用例质量", description="优化要求")
    agent_id: Optional[int] = Field(default=None, description="指定智能体ID")


# 响应模型
class AgentTaskResponse(BaseModel):
    """智能体任务响应"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    task_id: Optional[int] = None


class AgentListResponse(BaseModel):
    """智能体列表响应"""
    agents: List[dict]
    total: int


class TaskLogResponse(BaseModel):
    """任务日志响应"""
    logs: List[dict]
    total: int


# API路由
@router.post("/requirement-analysis", response_model=AgentTaskResponse)
async def analyze_requirements(
    request: RequirementAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_active_user)
) -> Any:
    """
    需求分析
    
    支持多模态分析：如果提供了image_paths且配置的模型支持多模态，
    将同时分析文本和图片内容。
    """
    from app.models.ai_config import Agent, AgentType
    
    try:
        # 如果没有指定agent_id，自动查找需求分析类型的智能体
        agent_id = request.agent_id
        if not agent_id:
            agent = db.query(Agent).filter(
                Agent.type == AgentType.REQUIREMENT_SPLITTER,
                Agent.is_active == True
            ).first()
            if agent:
                agent_id = agent.id
        
        # 创建带数据库连接的服务实例
        from app.services.agent_service_real import AgentServiceReal
        service = AgentServiceReal(db=db)
        
        result = await service.execute_requirement_analysis(
            requirement_content=request.requirement_content,
            project_context=request.project_context,
            user_id=current_user.id,
            agent_id=agent_id,
            image_paths=request.image_paths
        )
        
        return AgentTaskResponse(
            success=result["success"],
            data=result.get("data"),
            error=result.get("error"),
            task_id=result.get("task_log_id")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"需求分析失败: {str(e)}"
        )


class AsyncTaskResponse(BaseModel):
    """异步任务响应"""
    task_id: str
    status: str
    message: str


class AsyncTaskStatusResponse(BaseModel):
    """异步任务状态响应"""
    task_id: str
    task_type: str
    status: str
    progress: int
    total_batches: int
    completed_batches: int
    result: Optional[dict] = None
    error: Optional[str] = None
    message: Optional[str] = None  # 进度消息


@router.post("/test-point-generation", response_model=AgentTaskResponse)
async def generate_test_points(
    request: TestPointGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_active_user)
) -> Any:
    """生成测试点（同步模式，适用于少量需求点）
    
    测试分类和设计方法由后端从系统设置自动加载
    """
    from app.models.ai_config import Agent, AgentType
    from app.services.agent_service_real import AgentServiceReal
    
    try:
        # 如果没有指定agent_id，自动查找测试点生成类型的智能体
        agent_id = request.agent_id
        if not agent_id:
            agent = db.query(Agent).filter(
                Agent.type == AgentType.TEST_POINT_GENERATOR,
                Agent.is_active == True
            ).first()
            if agent:
                agent_id = agent.id
        
        service = AgentServiceReal(db=db)
        result = await service.execute_test_point_generation(
            requirement_points=request.requirement_points,
            user_id=current_user.id,
            agent_id=agent_id
        )
        
        return AgentTaskResponse(
            success=result["success"],
            data=result.get("data"),
            error=result.get("error"),
            task_id=result.get("task_log_id")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试点生成失败: {str(e)}"
        )


@router.post("/test-point-generation/async", response_model=AsyncTaskResponse)
async def generate_test_points_async(
    request: TestPointGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_active_user)
) -> Any:
    """异步生成测试点（适用于大量需求点，支持进度轮询）
    
    测试分类、设计方法和并发配置由后端从系统设置自动加载
    """
    import asyncio
    from app.models.ai_config import Agent, AgentType
    from app.services.agent_service_real import AgentServiceReal
    from app.services.async_task_manager import task_manager
    
    # 从系统设置加载并发配置
    task_manager.load_config_from_db(db)
    
    # 计算批次数（基于系统设置的并发数）
    concurrency = task_manager.max_concurrent_tasks
    batch_size = max(2, concurrency * 2)
    total_batches = (len(request.requirement_points) + batch_size - 1) // batch_size
    
    # 创建异步任务
    task_id = task_manager.create_task("test_point_generation", total_batches)
    task_manager.start_task(task_id)
    
    # 获取agent_id
    agent_id = request.agent_id
    if not agent_id:
        agent = db.query(Agent).filter(
            Agent.type == AgentType.TEST_POINT_GENERATOR,
            Agent.is_active == True
        ).first()
        if agent:
            agent_id = agent.id
    
    # 后台执行任务
    async def run_task():
        try:
            service = AgentServiceReal(db=db)
            result = await service.execute_test_point_generation(
                requirement_points=request.requirement_points,
                user_id=current_user.id,
                agent_id=agent_id,
                task_id=task_id
            )
            
            if result["success"]:
                task_manager.complete_task(task_id, result.get("data"))
            else:
                task_manager.fail_task(task_id, result.get("error", "未知错误"))
        except Exception as e:
            task_manager.fail_task(task_id, str(e))
    
    # 启动后台任务
    asyncio_task = asyncio.create_task(run_task())
    task_manager.register_running_task(task_id, asyncio_task)
    
    return AsyncTaskResponse(
        task_id=task_id,
        status="running",
        message=f"任务已启动，共 {len(request.requirement_points)} 个需求点，分 {total_batches} 批处理（并发数: {concurrency}）"
    )


@router.get("/tasks/{task_id}/status", response_model=AsyncTaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: UserSchema = Depends(get_current_active_user)
) -> Any:
    """获取异步任务状态"""
    from app.services.async_task_manager import task_manager
    
    print(f"\n{'='*60}")
    print(f"[查询任务状态] 开始查询")
    print(f"[查询任务状态] task_id: {task_id}")
    print(f"[查询任务状态] task_manager 实例 ID: {id(task_manager)}")
    print(f"[查询任务状态] 当前所有任务: {list(task_manager._tasks.keys())}")
    print(f"[查询任务状态] 任务数量: {len(task_manager._tasks)}")
    print(f"{'='*60}\n")
    
    task_status = task_manager.get_task_status(task_id)
    if not task_status:
        print(f"[查询任务状态] ❌ 任务不存在: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务不存在: {task_id}"
        )
    
    print(f"[查询任务状态] ✅ 找到任务: {task_status}")
    return AsyncTaskStatusResponse(**task_status)


class CancelTaskResponse(BaseModel):
    """取消任务响应"""
    success: bool
    message: str


@router.post("/tasks/{task_id}/cancel", response_model=CancelTaskResponse)
async def cancel_task(
    task_id: str,
    current_user: UserSchema = Depends(get_current_active_user)
) -> Any:
    """取消异步任务"""
    from app.services.async_task_manager import task_manager
    
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    task_manager.cancel_task(task_id)
    
    return CancelTaskResponse(
        success=True,
        message="任务已取消"
    )


class TestCaseDesignAsyncRequest(BaseModel):
    """异步测试用例设计请求"""
    test_points: List[dict] = Field(..., description="测试点列表，每项包含 id 和 content")
    module_id: int = Field(..., description="模块ID，用于保存生成的测试用例")
    clear_existing: bool = Field(default=False, description="是否清空现有测试用例")
    agent_id: Optional[int] = Field(default=None, description="指定智能体ID")


@router.post("/test-case-design/async", response_model=AsyncTaskResponse)
async def design_test_cases_async(
    request: TestCaseDesignAsyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_active_user)
) -> Any:
    """异步设计测试用例（适用于大量测试点，支持进度轮询）
    
    测试设计方法和并发配置由后端从系统设置自动加载
    
    流程：
    1. 创建异步任务
    2. 后台批量调用AI生成测试用例
    3. 生成完成后自动保存到数据库
    4. 自动调用AI优化生成的测试用例
    5. 优化完成后更新数据库
    6. 前端通过轮询获取进度和结果
    """
    import asyncio
    from app.models.ai_config import Agent, AgentType
    from app.models.testcase import TestCase, TestCaseStatus
    from app.services.agent_service_real import AgentServiceReal
    from app.services.async_task_manager import task_manager
    
    # 从系统设置加载并发配置
    task_manager.load_config_from_db(db)
    
    # 计算批次数（生成 + 优化，各占50%进度）
    concurrency = task_manager.max_concurrent_tasks
    batch_size = max(1, concurrency)
    generation_batches = (len(request.test_points) + batch_size - 1) // batch_size
    # 总批次 = 生成批次 * 2（生成占50%，优化占50%）
    total_batches = generation_batches * 2
    
    # 创建异步任务
    task_id = task_manager.create_task("test_case_design", total_batches)
    task_manager.start_task(task_id)
    
    # 获取设计智能体ID
    design_agent_id = request.agent_id
    if not design_agent_id:
        agent = db.query(Agent).filter(
            Agent.type == AgentType.TEST_CASE_DESIGNER,
            Agent.is_active == True
        ).first()
        if agent:
            design_agent_id = agent.id
    
    # 获取优化智能体ID
    optimize_agent_id = None
    optimize_agent = db.query(Agent).filter(
        Agent.type == AgentType.TEST_CASE_OPTIMIZER,
        Agent.is_active == True
    ).first()
    if optimize_agent:
        optimize_agent_id = optimize_agent.id
    
    # 保存请求参数供后台任务使用
    module_id = request.module_id
    clear_existing = request.clear_existing
    test_points = request.test_points
    user_id = current_user.id
    
    # 后台执行任务
    async def run_task():
        from app.database import SessionLocal
        task_db = SessionLocal()
        total_saved = 0
        saved_test_cases = []  # 保存生成的测试用例，用于后续优化
        
        # 定义批次保存回调函数
        def save_batch(test_cases_data: list) -> int:
            """保存一批测试用例到数据库，返回成功保存的数量"""
            nonlocal total_saved, saved_test_cases
            saved_count = 0
            for tc_data in test_cases_data:
                try:
                    # 从agent_service继承的属性
                    test_type = tc_data.get("test_type", "functional")
                    design_method = tc_data.get("design_method")
                    priority = tc_data.get("priority", "medium")
                    
                    test_case = TestCase(
                        module_id=module_id,
                        test_point_id=tc_data.get("test_point_id"),
                        title=tc_data.get("title", "未命名测试用例"),
                        description=tc_data.get("description"),
                        preconditions=tc_data.get("preconditions"),
                        test_steps=tc_data.get("test_steps"),
                        expected_result=tc_data.get("expected_result"),
                        test_category=test_type,  # 保存测试类别
                        design_method=design_method,  # 保存设计方法
                        priority=priority,  # 保存优先级
                        status=TestCaseStatus.DRAFT,
                        created_by_ai=True,
                        edited_by_user=False,
                        created_by=user_id
                    )
                    task_db.add(test_case)
                    task_db.flush()  # 获取ID
                    saved_test_cases.append({
                        "id": test_case.id,
                        "title": test_case.title,
                        "description": test_case.description,
                        "preconditions": test_case.preconditions,
                        "test_steps": test_case.test_steps,
                        "expected_result": test_case.expected_result
                    })
                    saved_count += 1
                except Exception as e:
                    print(f"⚠️ 创建测试用例对象失败: {e}")
                    continue
            
            try:
                task_db.commit()
                total_saved += saved_count
                return saved_count
            except Exception as e:
                print(f"⚠️ 批次提交失败: {e}")
                task_db.rollback()
                return 0
        
        try:
            service = AgentServiceReal(db=task_db)
            
            # 如果需要清空现有用例
            if clear_existing:
                task_db.query(TestCase).filter(TestCase.module_id == module_id).delete()
                task_db.commit()
            
            # 阶段1：批量生成测试用例（占50%进度）
            result = await service.execute_test_case_design_batch(
                test_points=test_points,
                module_id=module_id,  # 添加module_id参数
                user_id=user_id,
                agent_id=design_agent_id,
                task_id=task_id,
                on_batch_complete=save_batch,
                progress_offset=0,
                progress_scale=0.5  # 生成阶段占50%
            )
            
            if not result["success"]:
                task_manager.fail_task(task_id, result.get("error", "生成测试用例失败"))
                return
            
            # 阶段2：自动优化生成的测试用例（占50%进度）
            if saved_test_cases and optimize_agent_id:
                print(f"🔄 开始自动优化 {len(saved_test_cases)} 个测试用例...")
                
                # 更新进度提示
                task_manager.update_progress(task_id, 50, "正在优化测试用例...")
                
                # 调用优化服务
                optimize_result = await service.execute_test_case_optimization(
                    original_test_cases=saved_test_cases,
                    review_feedback=[],
                    optimization_requirements="全面优化测试用例质量，确保测试步骤清晰、预期结果明确",
                    user_id=user_id,
                    agent_id=optimize_agent_id,
                    batch_mode=True,
                    task_id=task_id,
                    progress_offset=50,
                    progress_scale=0.5  # 优化阶段占50%
                )
                
                # 应用优化结果到数据库
                optimized_count = 0
                if optimize_result.get("success") and optimize_result.get("data"):
                    optimized_results = optimize_result["data"].get("optimized_results", [])
                    for opt_result in optimized_results:
                        if opt_result.get("success") and opt_result.get("optimized"):
                            original_id = opt_result.get("original", {}).get("id")
                            if original_id:
                                try:
                                    optimized = opt_result["optimized"]
                                    tc = task_db.query(TestCase).filter(TestCase.id == original_id).first()
                                    if tc:
                                        tc.title = optimized.get("title", tc.title)
                                        tc.description = optimized.get("description", tc.description)
                                        tc.preconditions = optimized.get("preconditions", tc.preconditions)
                                        tc.test_steps = optimized.get("test_steps", tc.test_steps)
                                        tc.expected_result = optimized.get("expected_result", tc.expected_result)
                                        optimized_count += 1
                                except Exception as e:
                                    print(f"⚠️ 更新优化结果失败: {e}")
                    
                    task_db.commit()
                    print(f"✅ 成功优化 {optimized_count} 个测试用例")
            
            task_manager.complete_task(task_id, {
                "saved_count": total_saved,
                "optimized_count": optimized_count if 'optimized_count' in dir() else 0,
                "total_generated": result.get("data", {}).get("total_generated", 0)
            })
        except Exception as e:
            task_manager.fail_task(task_id, str(e))
        finally:
            task_db.close()
    
    # 启动后台任务
    asyncio_task = asyncio.create_task(run_task())
    task_manager.register_running_task(task_id, asyncio_task)
    
    return AsyncTaskResponse(
        task_id=task_id,
        status="running",
        message=f"任务已启动，共 {len(request.test_points)} 个测试点（生成+优化）"
    )


@router.post("/test-case-optimization", response_model=AgentTaskResponse)
async def optimize_test_cases(
    request: TestCaseOptimizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_active_user)
) -> Any:
    """优化测试用例（同步模式，适用于单个或少量用例）
    
    返回优化前后的对比信息，包括：
    - optimized_results: 每个用例的原始和优化后对比
    - optimized_cases: 所有优化后的用例列表
    - improvements: 所有改进点汇总
    - statistics: 优化统计信息
    """
    from app.models.ai_config import Agent, AgentType
    from app.services.agent_service_real import AgentServiceReal
    
    try:
        # 如果没有指定agent_id，自动查找测试用例优化类型的智能体
        agent_id = request.agent_id
        if not agent_id:
            agent = db.query(Agent).filter(
                Agent.type == AgentType.TEST_CASE_OPTIMIZER,
                Agent.is_active == True
            ).first()
            if agent:
                agent_id = agent.id
        
        service = AgentServiceReal(db=db)
        result = await service.execute_test_case_optimization(
            original_test_cases=request.original_test_cases,
            review_feedback=request.review_feedback,
            optimization_requirements=request.optimization_requirements,
            user_id=current_user.id,
            agent_id=agent_id,
            batch_mode=False  # 同步模式不使用并发
        )
        
        return AgentTaskResponse(
            success=result["success"],
            data=result.get("data"),
            error=result.get("error"),
            task_id=result.get("task_log_id")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试用例优化失败: {str(e)}"
        )


class TestCaseOptimizationBatchRequest(BaseModel):
    """批量测试用例优化请求"""
    test_cases: List[dict] = Field(..., description="测试用例列表，每项包含完整的测试用例信息")
    module_id: int = Field(..., description="模块ID，用于更新优化后的测试用例")
    review_feedback: List[dict] = Field(default=[], description="评审反馈")
    optimization_requirements: str = Field(default="全面优化测试用例质量", description="优化要求")
    auto_save: bool = Field(default=False, description="是否自动保存优化结果到数据库")
    agent_id: Optional[int] = Field(default=None, description="指定智能体ID")


@router.post("/test-case-optimization/batch", response_model=AsyncTaskResponse)
async def optimize_test_cases_batch(
    request: TestCaseOptimizationBatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_active_user)
) -> Any:
    """批量优化测试用例（异步模式，支持进度轮询）
    
    流程：
    1. 创建异步任务
    2. 后台批量调用AI优化测试用例
    3. 返回优化前后的对比信息
    4. 如果auto_save=True，自动更新数据库中的测试用例
    5. 前端通过轮询获取进度和结果
    """
    import asyncio
    from app.models.ai_config import Agent, AgentType
    from app.models.testcase import TestCase
    from app.services.agent_service_real import AgentServiceReal
    from app.services.async_task_manager import task_manager
    
    # 从系统设置加载并发配置
    task_manager.load_config_from_db(db)
    
    # 计算批次数（每个用例作为一个批次）
    total_batches = len(request.test_cases)
    
    # 创建异步任务
    task_id = task_manager.create_task("test_case_optimization", total_batches)
    task_manager.start_task(task_id)
    
    # 获取agent_id
    agent_id = request.agent_id
    if not agent_id:
        agent = db.query(Agent).filter(
            Agent.type == AgentType.TEST_CASE_OPTIMIZER,
            Agent.is_active == True
        ).first()
        if agent:
            agent_id = agent.id
    
    # 保存请求参数供后台任务使用
    module_id = request.module_id
    test_cases = request.test_cases
    review_feedback = request.review_feedback
    optimization_requirements = request.optimization_requirements
    auto_save = request.auto_save
    user_id = current_user.id
    
    # 后台执行任务
    async def run_task():
        # 创建新的数据库会话用于后台任务
        from app.database import SessionLocal
        task_db = SessionLocal()
        
        try:
            service = AgentServiceReal(db=task_db)
            
            # 批量优化测试用例
            result = await service.execute_test_case_optimization(
                original_test_cases=test_cases,
                review_feedback=review_feedback,
                optimization_requirements=optimization_requirements,
                user_id=user_id,
                agent_id=agent_id,
                batch_mode=True,
                task_id=task_id
            )
            
            if result["success"]:
                data = result.get("data", {})
                optimized_results = data.get("optimized_results", [])
                
                # 如果auto_save=True，更新数据库中的测试用例
                updated_count = 0
                if auto_save:
                    for opt_result in optimized_results:
                        if opt_result.get("success") and opt_result.get("optimized"):
                            original = opt_result.get("original", {})
                            optimized = opt_result.get("optimized", {})
                            case_id = original.get("id")
                            
                            if case_id:
                                try:
                                    test_case = task_db.query(TestCase).filter(
                                        TestCase.id == case_id
                                    ).first()
                                    
                                    if test_case:
                                        # 更新测试用例字段
                                        if optimized.get("title"):
                                            test_case.title = optimized["title"]
                                        if optimized.get("description"):
                                            test_case.description = optimized["description"]
                                        if optimized.get("preconditions"):
                                            test_case.preconditions = optimized["preconditions"]
                                        if optimized.get("test_steps"):
                                            test_case.test_steps = optimized["test_steps"]
                                        if optimized.get("expected_result"):
                                            test_case.expected_result = optimized["expected_result"]
                                        
                                        test_case.edited_by_user = True
                                        test_case.updated_by = user_id
                                        updated_count += 1
                                except Exception as e:
                                    print(f"⚠️ 更新测试用例 {case_id} 失败: {e}")
                                    continue
                    
                    task_db.commit()
                
                # 添加更新统计到结果
                data["updated_count"] = updated_count
                
                task_manager.complete_task(task_id, data)
            else:
                task_manager.fail_task(task_id, result.get("error", "未知错误"))
        except Exception as e:
            task_manager.fail_task(task_id, str(e))
        finally:
            task_db.close()
    
    # 启动后台任务
    asyncio_task = asyncio.create_task(run_task())
    task_manager.register_running_task(task_id, asyncio_task)
    
    concurrency = task_manager.max_concurrent_tasks
    return AsyncTaskResponse(
        task_id=task_id,
        status="running",
        message=f"批量优化任务已启动，共 {len(request.test_cases)} 个测试用例（并发数: {concurrency}）"
    )


@router.get("/list", response_model=AgentListResponse)
def get_agent_list(
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_active_user)
) -> Any:
    """获取智能体列表"""
    try:
        agents = agent_service.get_agent_list(db, user_id=current_user.id)
        
        return AgentListResponse(
            agents=agents,
            total=len(agents)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取智能体列表失败: {str(e)}"
        )


@router.get("/task-logs", response_model=TaskLogResponse)
def get_task_logs(
    agent_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_active_user)
) -> Any:
    """获取任务执行日志"""
    try:
        logs = agent_service.get_task_logs(
            db=db,
            user_id=current_user.id,
            agent_id=agent_id,
            limit=limit
        )
        
        return TaskLogResponse(
            logs=logs,
            total=len(logs)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务日志失败: {str(e)}"
        )


@router.get("/types")
def get_agent_types() -> Any:
    """获取智能体类型列表"""
    return {
        "agent_types": [
            {
                "value": "requirement_splitter",
                "label": "需求拆分智能体",
                "description": "将需求文档自动拆分为结构化需求点"
            },
            {
                "value": "test_point_generator",
                "label": "测试点生成智能体",
                "description": "基于需求点和测试类型生成测试点"
            },
            {
                "value": "test_case_designer",
                "label": "测试用例设计智能体",
                "description": "根据测试点生成完整测试用例"
            },
            {
                "value": "test_case_optimizer",
                "label": "测试用例优化智能体",
                "description": "基于评审反馈自动优化测试用例"
            }
        ]
    }


@router.get("/test-types")
def get_test_types(
    db: Session = Depends(get_db)
) -> Any:
    """获取测试类型列表（从系统设置加载启用的测试分类）"""
    from app.services.settings_service import SettingsService
    
    # 从数据库获取启用的测试分类
    categories = SettingsService.get_test_categories(db, active_only=True)
    
    test_types = [
        {
            "value": cat.code,
            "label": cat.name,
            "description": cat.description or ""
        }
        for cat in categories
    ]
    
    return {"test_types": test_types}


@router.get("/design-methods")
def get_design_methods(
    db: Session = Depends(get_db)
) -> Any:
    """获取测试设计方法列表（从系统设置加载启用的设计方法）"""
    from app.services.settings_service import SettingsService
    
    # 从数据库获取启用的测试设计方法
    methods = SettingsService.get_design_methods(db, active_only=True)
    
    design_methods = [
        {
            "value": m.code,
            "label": m.name,
            "description": m.description or ""
        }
        for m in methods
    ]
    
    return {"design_methods": design_methods}
