"""
智能体管理服务
支持重试机制、超时控制和并发配置
"""
import json
import re
import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.ai_config import Agent, AIModel
from app.services.ai_service import ai_service
from app.services.settings_service import SettingsService
from app.prompts import (
    render_prompt,
    REQUIREMENT_ANALYSIS_USER,
    TEST_POINT_USER,
    TEST_CASE_DESIGN_USER,
    TEST_CASE_BATCH_OPTIMIZE_USER
)


class AgentServiceReal:
    """智能体服务类
    
    支持从系统设置加载配置：
    - retry_count: 失败重试次数
    - task_timeout: 单次AI调用超时时间
    - max_concurrent_tasks: 最大并发数
    """
    
    # 默认配置
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_TASK_TIMEOUT = 300  # 秒（与 httpx 和系统设置保持一致）
    DEFAULT_RETRY_DELAY = 1  # 重试延迟基数（秒）
    
    @staticmethod
    def _normalize_priority(priority: str) -> str:
        """标准化优先级值
        
        将 P0/P1/P2/HIGH/MEDIUM/LOW 等格式统一转换为 high/medium/low
        """
        if not priority:
            return "medium"
        
        priority_map = {
            "P0": "high",
            "HIGH": "high",
            "H": "high",
            "P1": "medium",
            "MEDIUM": "medium",
            "M": "medium",
            "P2": "low",
            "LOW": "low",
            "L": "low"
        }
        return priority_map.get(priority.upper(), "medium")
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        # 配置参数（从系统设置加载）
        self._retry_count = self.DEFAULT_RETRY_COUNT
        self._task_timeout = self.DEFAULT_TASK_TIMEOUT
        self._retry_delay = self.DEFAULT_RETRY_DELAY
        self._config_loaded = False
    
    def _load_config(self) -> None:
        """从系统设置加载配置"""
        if self._config_loaded:
            return
        
        try:
            if self.db:
                config = SettingsService.get_concurrency_config(self.db)
                self._retry_count = config.retry_count
                self._task_timeout = config.task_timeout
                self._config_loaded = True
                print(f"🔧 [AgentService] 已加载配置: retry_count={self._retry_count}, task_timeout={self._task_timeout}s")
        except Exception as e:
            print(f"⚠️ [AgentService] 加载配置失败，使用默认值: {e}")
    
    def reload_config(self) -> None:
        """强制重新加载配置"""
        self._config_loaded = False
        self._load_config()
    
    def _get_test_categories_text(self) -> str:
        """获取测试类别文本"""
        if not self.db:
            return "- functional: 功能测试\n- performance: 性能测试\n- security: 安全测试"
        categories = SettingsService.get_test_categories(self.db, active_only=True)
        if not categories:
            return "- functional: 功能测试\n- performance: 性能测试\n- security: 安全测试"
        return "\n".join([f"- {c.code}: {c.name}" for c in categories])
    
    def _get_design_methods_text(self) -> str:
        """获取测试设计方法文本（包含code和name，便于AI返回正确的code）"""
        if not self.db:
            return "- equivalence_partitioning: 等价类划分法\n- boundary_value: 边界值分析法\n- scenario: 场景法"
        methods = SettingsService.get_design_methods(self.db, active_only=True)
        if not methods:
            return "- equivalence_partitioning: 等价类划分法\n- boundary_value: 边界值分析法\n- scenario: 场景法"
        return "\n".join([f"- {m.code}: {m.name}" for m in methods])
    
    async def _get_agent_config(self, agent_id: int) -> Dict[str, Any]:
        """获取智能体配置"""
        if not self.db:
            raise Exception("数据库连接未初始化")
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise Exception(f"智能体不存在: {agent_id}")
        if not agent.is_active:
            raise Exception(f"智能体未激活: {agent.name}")
        if not agent.system_prompt:
            raise Exception(f"智能体 {agent.name} 未配置系统提示词")
        
        ai_model = self.db.query(AIModel).filter(AIModel.id == agent.ai_model_id).first()
        if not ai_model:
            raise Exception("智能体关联的AI模型不存在")
        if not ai_model.api_key:
            raise Exception(f"AI模型 {ai_model.name} 未配置API密钥")
        
        return {
            "model": ai_model.model_id,
            "api_key": ai_model.api_key,
            "base_url": ai_model.base_url,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "system_prompt": agent.system_prompt
        }
    
    async def _call_ai_once(self, config: Dict[str, Any], user_prompt: str, image_paths: Optional[List[str]] = None) -> str:
        """单次调用AI（不带重试）"""
        if image_paths:
            return await ai_service.call_ai_multimodal(
                model=config["model"], text_content=user_prompt, image_paths=image_paths,
                api_key=config["api_key"], base_url=config["base_url"],
                system_prompt=config["system_prompt"], temperature=config["temperature"], max_tokens=config["max_tokens"]
            )
        messages = [{"role": "system", "content": config["system_prompt"]}, {"role": "user", "content": user_prompt}]
        return await ai_service.call_ai(
            model=config["model"], messages=messages, api_key=config["api_key"],
            base_url=config["base_url"], temperature=config["temperature"], max_tokens=config["max_tokens"]
        )
    
    async def _call_ai(self, config: Dict[str, Any], user_prompt: str, image_paths: Optional[List[str]] = None) -> str:
        """调用AI（带重试和超时机制）
        
        使用系统设置中的 retry_count 和 task_timeout 参数
        采用指数退避策略进行重试
        """
        # 确保配置已加载
        self._load_config()
        
        last_error = None
        max_attempts = self._retry_count + 1  # 重试次数 + 首次尝试
        
        for attempt in range(max_attempts):
            try:
                # 使用超时控制
                result = await asyncio.wait_for(
                    self._call_ai_once(config, user_prompt, image_paths),
                    timeout=self._task_timeout
                )
                
                if attempt > 0:
                    print(f"✅ AI调用成功 (第 {attempt + 1} 次尝试)")
                
                return result
                
            except asyncio.TimeoutError:
                last_error = f"AI调用超时（超过{self._task_timeout}秒）"
                print(f"⏱️ AI调用超时 (尝试 {attempt + 1}/{max_attempts}): {last_error}")
                
            except Exception as e:
                last_error = str(e)
                print(f"❌ AI调用失败 (尝试 {attempt + 1}/{max_attempts}): {last_error}")
            
            # 如果还有重试机会，等待后重试
            if attempt < max_attempts - 1:
                # 指数退避：1s, 2s, 4s, 8s...
                delay = self._retry_delay * (2 ** attempt)
                print(f"⏳ 等待 {delay} 秒后重试...")
                await asyncio.sleep(delay)
        
        # 所有重试都失败
        raise Exception(f"AI调用失败（已重试{self._retry_count}次）: {last_error}")
    
    async def _call_ai_with_parse(self, config: Dict[str, Any], user_prompt: str, image_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """调用AI并解析JSON（带重试机制）
        
        整合了 AI 调用和 JSON 解析，任何环节失败都会触发重试
        这样可以处理：
        - 网络错误
        - API 超时
        - JSON 格式错误
        - 响应截断
        """
        # 确保配置已加载
        self._load_config()
        
        last_error = None
        max_attempts = self._retry_count + 1
        
        for attempt in range(max_attempts):
            try:
                # 调用 AI
                response = await asyncio.wait_for(
                    self._call_ai_once(config, user_prompt, image_paths),
                    timeout=self._task_timeout
                )
                
                # 解析 JSON
                result = self._parse_json(response)
                
                if attempt > 0:
                    print(f"✅ AI调用并解析成功 (第 {attempt + 1} 次尝试)")
                
                return result
                
            except asyncio.TimeoutError:
                last_error = f"AI调用超时（超过{self._task_timeout}秒）"
                print(f"⏱️ AI调用超时 (尝试 {attempt + 1}/{max_attempts}): {last_error}")
                
            except Exception as e:
                last_error = str(e)
                error_type = "JSON解析失败" if "无法解析JSON" in str(e) else "AI调用失败"
                print(f"❌ {error_type} (尝试 {attempt + 1}/{max_attempts}): {last_error}")
            
            # 如果还有重试机会，等待后重试
            if attempt < max_attempts - 1:
                delay = self._retry_delay * (2 ** attempt)
                print(f"⏳ 等待 {delay} 秒后重试...")
                await asyncio.sleep(delay)
        
        # 所有重试都失败
        raise Exception(f"AI调用失败（已重试{self._retry_count}次）: {last_error}")
    
    async def _call_ai_with_parse(self, config: Dict[str, Any], user_prompt: str, image_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """调用AI并解析JSON（带重试机制）
        
        如果JSON解析失败，会重新调用AI（因为可能是AI返回格式错误）
        """
        # 确保配置已加载
        self._load_config()
        
        last_error = None
        max_attempts = self._retry_count + 1
        
        for attempt in range(max_attempts):
            try:
                # 调用AI（已包含网络重试）
                response = await self._call_ai(config, user_prompt, image_paths)
                
                # 尝试解析JSON
                result = self._parse_json(response)
                
                if attempt > 0:
                    print(f"✅ JSON解析成功 (第 {attempt + 1} 次尝试)")
                
                return result
                
            except Exception as e:
                error_msg = str(e)
                
                # 判断是否是JSON解析错误
                if "无法解析JSON" in error_msg:
                    last_error = f"JSON解析失败: {error_msg}"
                    print(f"📝 JSON解析失败 (尝试 {attempt + 1}/{max_attempts}): AI返回格式错误")
                else:
                    # 其他错误（网络、超时等）已经在 _call_ai 中重试过了
                    raise
                
                # 如果还有重试机会，等待后重试
                if attempt < max_attempts - 1:
                    delay = self._retry_delay * (2 ** attempt)
                    print(f"⏳ 等待 {delay} 秒后重新请求AI...")
                    await asyncio.sleep(delay)
        
        # 所有重试都失败
        raise Exception(f"AI响应解析失败（已重试{self._retry_count}次）: {last_error}")
    
    def _parse_json(self, response: str) -> Dict[str, Any]:
        """解析JSON，支持提取```json```代码块"""
        # 1. 直接解析
        try:
            return json.loads(response)
        except Exception as e1:
            print(f"⚠️ 直接JSON解析失败: {str(e1)[:100]}")
        
        # 2. 提取 ```json ... ``` 代码块
        match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception as e2:
                print(f"⚠️ 代码块JSON解析失败: {str(e2)[:100]}")
        
        # 3. 提取第一个 {...} 块
        match = re.search(r'\{[\s\S]*\}', response)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception as e3:
                print(f"⚠️ 花括号块JSON解析失败: {str(e3)[:100]}")
        
        # 保存完整响应到日志文件
        from pathlib import Path
        from datetime import datetime
        
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        log_file = log_dir / f"failed_response_{timestamp}.txt"
        
        try:
            log_file.write_text(
                f"{'='*80}\n"
                f"AI响应JSON解析失败\n"
                f"{'='*80}\n\n"
                f"响应长度: {len(response)} 字符\n\n"
                f"完整响应内容:\n"
                f"{'-'*80}\n"
                f"{response}\n"
                f"{'-'*80}\n",
                encoding='utf-8'
            )
            print(f"📁 完整响应已保存到: {log_file}")
        except Exception as save_err:
            print(f"⚠️ 保存日志文件失败: {save_err}")
        
        # 打印原始响应用于调试
        print(f"\n{'='*80}")
        print(f"❌ JSON解析完全失败")
        print(f"{'='*80}")
        print(f"响应长度: {len(response)} 字符")
        print(f"原始响应 (前1000字符):")
        print(response[:1000])
        if len(response) > 1000:
            print(f"\n... (省略 {len(response) - 1000} 字符) ...\n")
            print(f"原始响应 (最后500字符):")
            print(response[-500:])
        print(f"{'='*80}\n")
        
        raise Exception(f"无法解析JSON: {response[:200]}...")

    # ==================== 核心方法 ====================
    
    async def analyze_requirements(self, agent_id: int, content: str, image_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """分析需求"""
        config = await self._get_agent_config(agent_id)
        user_prompt = render_prompt(REQUIREMENT_ANALYSIS_USER, content=content)
        return await self._call_ai_with_parse(config, user_prompt, image_paths)
    
    async def generate_test_points(self, agent_id: int, requirement_content: str) -> Dict[str, Any]:
        """生成测试点"""
        config = await self._get_agent_config(agent_id)
        user_prompt = render_prompt(
            TEST_POINT_USER, 
            content=requirement_content, 
            test_categories=self._get_test_categories_text(),
            design_methods=self._get_design_methods_text()
        )
        return await self._call_ai_with_parse(config, user_prompt)
    
    async def design_test_case(
        self, 
        agent_id: int, 
        test_point: dict,  # 完整的测试点JSON对象
        requirement_content: str = ""  # 原始需求文档内容
    ) -> Dict[str, Any]:
        """设计测试用例（兼容单个和批量）
        
        Args:
            agent_id: 智能体ID
            test_point: 完整的测试点对象，包含 id, content, test_type, design_method, priority 等
            requirement_content: 原始需求文档内容，提供业务上下文
            
        Returns:
            单个测试用例对象
            
        Note:
            内部调用统一的批量接口，传入长度为1的数组
        """
        # 调用批量接口，传入单个测试点
        cases = await self.design_test_cases_batch(
            agent_id=agent_id,
            test_points=[test_point],
            requirement_content=requirement_content
        )
        
        # 返回第一个测试用例
        return cases[0] if cases else {}
    
    async def design_test_cases_batch(
        self, 
        agent_id: int, 
        test_points: List[dict],  # 测试点数组（1个或多个）
        requirement_content: str = ""
    ) -> List[Dict[str, Any]]:
        """批量设计测试用例（统一接口）
        
        Args:
            agent_id: 智能体ID
            test_points: 测试点数组（可以是1个或多个）
            requirement_content: 原始需求文档内容
            
        Returns:
            测试用例数组（与输入一一对应）
        """
        config = await self._get_agent_config(agent_id)
        
        # 将测试点数组转换为JSON字符串
        test_points_json = json.dumps(test_points, ensure_ascii=False, indent=2)
        
        user_prompt = render_prompt(
            TEST_CASE_DESIGN_USER,
            test_points=test_points_json,
            requirement_content=requirement_content or "（无需求文档）"
        )
        
        count = len(test_points)
        print(f"\n🎯 测试用例设计: {count} 个测试点")
        if count <= 3:
            for tp in test_points:
                preview = tp.get('content', '')[:40]
                print(f"   - {preview}... (方法: {tp.get('design_method', 'N/A')})")
        
        result = await self._call_ai_with_parse(config, user_prompt)
        
        # 打印完整原始输出
        print(f"\n{'='*80}")
        print(f"📋 批量生成原始输出 (测试点数量: {count})")
        print(f"{'='*80}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"{'='*80}\n")
        
        # 提取测试用例数组
        test_cases = result.get('test_cases', [])
        
        # 验证数量匹配
        if len(test_cases) != len(test_points):
            print(f"⚠️ 警告：测试用例数量不匹配（期望{len(test_points)}，实际{len(test_cases)}）")
            # 如果数量不匹配，尝试补齐或截断
            if len(test_cases) < len(test_points):
                print(f"⚠️ 测试用例数量不足，将使用空对象补齐")
                while len(test_cases) < len(test_points):
                    test_cases.append({})
            elif len(test_cases) > len(test_points):
                print(f"⚠️ 测试用例数量过多，将截断")
                test_cases = test_cases[:len(test_points)]
        
        print(f"✅ 生成 {len(test_cases)} 个测试用例")
        
        return test_cases
    
    async def optimize_test_cases(self, agent_id: int, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量优化测试用例"""
        config = await self._get_agent_config(agent_id)
        user_prompt = render_prompt(TEST_CASE_BATCH_OPTIMIZE_USER, test_cases=json.dumps(test_cases, ensure_ascii=False, indent=2))
        return await self._call_ai_with_parse(config, user_prompt)

    # ==================== 执行方法 ====================
    
    # ==================== 执行方法（用于异步任务） ====================
    
    async def execute_requirement_analysis(
        self,
        requirement_content: str,
        project_context: str = "",
        user_id: int = 1,
        agent_id: Optional[int] = None,
        image_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """执行需求分析（同步模式）
        
        Args:
            requirement_content: 需求文档内容
            project_context: 项目上下文
            user_id: 用户ID
            agent_id: 智能体ID
            image_paths: 图片路径列表
            
        Returns:
            包含 success, data, error 的字典
        """
        try:
            # 加载配置
            if self.db:
                from app.services.async_task_manager import task_manager
                task_manager.load_config_from_db(self.db)
                self._load_config()
            
            # 调用分析方法
            result = await self.analyze_requirements(
                agent_id=agent_id,
                content=requirement_content,
                image_paths=image_paths
            )
            
            return {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            print(f"❌ 需求分析失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_test_point_generation(
        self, 
        requirement_points: List[dict], 
        user_id: int = 1, 
        agent_id: Optional[int] = None, 
        task_id: Optional[str] = None,
        progress_offset: float = 0,
        progress_scale: float = 1.0
    ) -> Dict[str, Any]:
        """并发生成测试点
        
        每个需求点单独调用AI生成测试点，使用系统设置的并发数控制同时执行的任务数
        
        Args:
            requirement_points: 需求点列表
            user_id: 用户ID
            agent_id: 智能体ID
            task_id: 任务ID（用于进度更新）
            progress_offset: 进度偏移（0-100）
            progress_scale: 进度缩放比例（0-1）
        """
        from app.services.async_task_manager import task_manager
        if self.db:
            task_manager.load_config_from_db(self.db)
            self._load_config()  # 同步加载配置
        
        concurrency = task_manager.max_concurrent_tasks
        
        print(f"\n🚀 并发测试点生成: {len(requirement_points)} 个需求点")
        print(f"🔧 配置: 并发={concurrency}, 重试={self._retry_count}次, 超时={self._task_timeout}s")
        
        # 清空这些需求点相关的旧测试点（级联删除测试用例）
        if self.db and requirement_points:
            from app.models.testcase import TestPoint
            req_point_ids = [rp.get("id") for rp in requirement_points if rp.get("id")]
            if req_point_ids:
                old_test_points = self.db.query(TestPoint).filter(
                    TestPoint.requirement_point_id.in_(req_point_ids)
                ).all()
                
                if old_test_points:
                    print(f"🗑️  清空 {len(old_test_points)} 个旧测试点（及其关联的测试用例）")
                    for tp in old_test_points:
                        self.db.delete(tp)
                    self.db.flush()
        
        try:
            all_points = []
            completed = 0
            lock = asyncio.Lock()
            semaphore = asyncio.Semaphore(concurrency)  # 控制并发数
            
            async def process_requirement(req_point, idx):
                """处理单个需求点"""
                nonlocal completed
                
                async with semaphore:  # 控制并发
                    try:
                        # 单个需求点生成测试点
                        result = await self.generate_test_points(agent_id, req_point.get('content', str(req_point)))
                        
                        test_points = result.get("test_points", [])
                        # 关联需求点ID
                        for tp in test_points:
                            tp["requirement_point_id"] = req_point.get("id")
                        
                        print(f"✅ [{idx+1}/{len(requirement_points)}] 需求点生成 {len(test_points)} 个测试点")
                        
                        # 更新进度（线程安全）
                        async with lock:
                            completed += 1
                            all_points.extend(test_points)
                            if task_id:
                                raw_progress = (completed / len(requirement_points)) * 100
                                scaled_progress = progress_offset + raw_progress * progress_scale
                                task_manager.update_progress(task_id, int(scaled_progress))
                        
                        return test_points
                        
                    except Exception as e:
                        print(f"❌ [{idx+1}/{len(requirement_points)}] 需求点生成失败: {e}")
                        # 更新进度（即使失败也要更新）
                        async with lock:
                            completed += 1
                            if task_id:
                                raw_progress = (completed / len(requirement_points)) * 100
                                scaled_progress = progress_offset + raw_progress * progress_scale
                                task_manager.update_progress(task_id, int(scaled_progress))
                        return []
            
            # 并发处理所有需求点
            await asyncio.gather(*[process_requirement(rp, i) for i, rp in enumerate(requirement_points)])
            
            print(f"🎉 测试点生成完成, 共生成 {len(all_points)} 个测试点")
            
            return {"success": True, "data": {"test_points": all_points}}
            
        except Exception as e:
            print(f"❌ 测试点生成失败: {e}")
            return {"success": False, "error": str(e)}
    

    
    async def execute_test_case_design_batch(
        self, 
        test_points: List[dict],
        module_id: int,  # 新增：模块ID，用于查询需求文档
        user_id: int = 1, 
        agent_id: Optional[int] = None, 
        task_id: Optional[str] = None,
        on_batch_complete: Optional[callable] = None,  # 批次完成回调，用于实时保存
        progress_offset: float = 0,  # 进度偏移（0-100）
        progress_scale: float = 1.0  # 进度缩放比例（0-1）
    ) -> Dict[str, Any]:
        """批量生成测试用例（批次生成：每6个测试点为一批）
        
        Args:
            test_points: 测试点列表（完整的JSON对象，包含id, content, test_type, design_method, priority等）
            module_id: 模块ID，用于查询原始需求文档
            user_id: 用户ID
            agent_id: 智能体ID
            task_id: 任务ID（用于进度更新）
            on_batch_complete: 批次完成回调函数，签名: (test_cases: List[dict]) -> int
            progress_offset: 进度偏移量（用于多阶段任务）
            progress_scale: 进度缩放比例（用于多阶段任务）
        """
        from app.services.async_task_manager import task_manager
        from app.models.requirement import RequirementFile
        
        if self.db:
            task_manager.load_config_from_db(self.db)
            self._load_config()  # 同步加载配置
        concurrency = task_manager.max_concurrent_tasks
        
        print(f"\n🚀 批量测试用例设计: {len(test_points)} 个测试点 (批次生成)")
        print(f"🔧 配置: 并发={concurrency}, 重试={self._retry_count}次, 超时={self._task_timeout}s")
        
        # 查询该模块的所有需求文档
        requirement_content = ""
        if self.db:
            try:
                requirement_files = self.db.query(RequirementFile).filter(
                    RequirementFile.module_id == module_id,
                    RequirementFile.is_extracted == True
                ).all()
                
                if requirement_files:
                    content_parts = []
                    for file in requirement_files:
                        if file.extracted_content:
                            content_parts.append(f"【需求文档：{file.filename}】\n{file.extracted_content}")
                    requirement_content = "\n\n---\n\n".join(content_parts)
                    print(f"📄 已加载 {len(requirement_files)} 个需求文档作为上下文")
                else:
                    print(f"⚠️ 模块 {module_id} 没有找到需求文档")
            except Exception as e:
                print(f"⚠️ 查询需求文档失败: {e}")
        
        try:
            all_cases = []
            total_saved = 0
            semaphore = asyncio.Semaphore(concurrency)
            completed = 0
            lock = asyncio.Lock()
            
            # 智能分组：将测试点分成批次（每批最多3个）
            BATCH_SIZE = 3
            batches = [
                test_points[i:i+BATCH_SIZE] 
                for i in range(0, len(test_points), BATCH_SIZE)
            ]
            
            print(f"📦 智能分组: {len(test_points)} 个测试点 → {len(batches)} 个批次（每批最多{BATCH_SIZE}个）")
            
            async def process_batch(batch, batch_idx):
                nonlocal completed, total_saved
                async with semaphore:
                    try:
                        batch_size = len(batch)
                        print(f"\n🔄 批次 {batch_idx+1}/{len(batches)}: 处理 {batch_size} 个测试点")
                        
                        # 批量调用AI（一次生成多个）
                        cases = await self.design_test_cases_batch(
                            agent_id=agent_id,
                            test_points=batch,
                            requirement_content=requirement_content
                        )
                        
                        # 继承测试点的属性
                        for i, case in enumerate(cases):
                            if i < len(batch):
                                tp = batch[i]
                                case["test_point_id"] = tp.get('id')
                                case["test_type"] = tp.get('test_type', 'functional')
                                case["design_method"] = tp.get('design_method')
                                case["priority"] = tp.get('priority', 'medium')
                                case["created_by_ai"] = True
                                
                                if batch_size <= 3:  # 小批次显示详细信息
                                    print(f"   📝 用例: {case.get('title', '')[:30]}... (继承: {case['test_type']}/{case['design_method']}/{case['priority']})")
                        
                        # 保存到数据库
                        saved_count = 0
                        if on_batch_complete and cases:
                            try:
                                saved_count = on_batch_complete(cases)
                                print(f"💾 批次 {batch_idx+1}: 已保存 {saved_count} 个用例到数据库")
                            except Exception as save_err:
                                print(f"⚠️ 批次 {batch_idx+1}: 保存失败 - {save_err}")
                        
                        async with lock:
                            completed += batch_size
                            total_saved += saved_count
                            all_cases.extend(cases)
                            if task_id:
                                # 计算带偏移的进度
                                raw_progress = (completed / len(test_points)) * 100
                                scaled_progress = progress_offset + raw_progress * progress_scale
                                task_manager.update_progress(task_id, int(scaled_progress))
                        
                        print(f"✅ 批次 {batch_idx+1}/{len(batches)}: 完成，生成 {len(cases)} 个用例")
                        return cases
                        
                    except Exception as e:
                        import traceback
                        print(f"\n{'='*80}")
                        print(f"❌ 批次 {batch_idx+1}/{len(batches)}: 失败")
                        print(f"{'='*80}")
                        print(f"错误类型: {type(e).__name__}")
                        print(f"错误信息: {str(e)}")
                        print(f"测试点数量: {len(batch)}")
                        print(f"测试点内容:")
                        for i, tp in enumerate(batch):
                            print(f"  {i+1}. {tp.get('content', 'N/A')[:50]}... (方法: {tp.get('design_method', 'N/A')})")
                        print(f"\n完整堆栈:")
                        traceback.print_exc()
                        print(f"{'='*80}\n")
                        # 标记批次失败，但继续处理其他批次
                        async with lock:
                            completed += len(batch)
                            if task_id:
                                raw_progress = (completed / len(test_points)) * 100
                                scaled_progress = progress_offset + raw_progress * progress_scale
                                task_manager.update_progress(task_id, int(scaled_progress))
                        return []
            
            # 并发处理所有批次
            await asyncio.gather(*[process_batch(batch, i) for i, batch in enumerate(batches)])
            
            print(f"🎉 完成, 共 {len(all_cases)} 个用例, 已保存 {total_saved} 个")
            return {
                "success": True, 
                "data": {
                    "test_cases": all_cases,
                    "saved_count": total_saved,
                    "total_generated": len(all_cases)
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _normalize_test_case(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化测试用例格式，确保与数据库Schema一致"""
        if not data:
            return data
        
        # 数组转字符串
        def to_string(val):
            if isinstance(val, list):
                return '\n'.join(str(v) for v in val)
            return val
        
        # 标准化test_steps格式
        def normalize_steps(steps):
            if not steps or not isinstance(steps, list):
                return steps
            result = []
            for i, s in enumerate(steps):
                if isinstance(s, dict):
                    result.append({
                        "step": s.get("step", i + 1),
                        "action": s.get("action") or s.get("操作", ""),
                        "expected": s.get("expected") or s.get("预期结果") or s.get("expected_result", "")
                    })
                elif isinstance(s, str):
                    result.append({"step": i + 1, "action": s, "expected": ""})
            return result
        
        return {
            "title": data.get("title"),
            "description": to_string(data.get("description")),
            "preconditions": to_string(data.get("preconditions")),
            "test_steps": normalize_steps(data.get("test_steps")),
            "expected_result": to_string(data.get("expected_result")),
            "design_method": data.get("design_method"),
            "test_type": data.get("test_type"),
            "priority": data.get("priority"),
        }
    
    def _simplify_test_case(self, tc: Dict[str, Any]) -> Dict[str, Any]:
        """简化测试用例，只保留核心字段传给AI"""
        return {
            "id": tc.get("id"),
            "test_point_id": tc.get("test_point_id"),
            "module_id": tc.get("module_id"),
            "title": tc.get("title"),
            "description": tc.get("description"),
            "preconditions": tc.get("preconditions"),
            "test_steps": tc.get("test_steps"),
        }
    
    async def execute_test_case_optimization(
        self, 
        original_test_cases: List[dict], 
        review_feedback: List[dict] = None, 
        optimization_requirements: str = "", 
        user_id: int = 1, 
        agent_id: Optional[int] = None, 
        batch_mode: bool = False, 
        task_id: Optional[str] = None,
        progress_offset: float = 0,  # 进度偏移（0-100）
        progress_scale: float = 1.0  # 进度缩放比例（0-1）
    ) -> Dict[str, Any]:
        """批量优化测试用例（并发批量处理）
        
        每批次最多6个用例，使用系统设置的并发数控制同时执行的批次数
        
        Args:
            progress_offset: 进度偏移量（用于多阶段任务）
            progress_scale: 进度缩放比例（用于多阶段任务）
        """
        from app.services.async_task_manager import task_manager
        if self.db:
            task_manager.load_config_from_db(self.db)
            self._load_config()  # 同步加载配置
        
        BATCH_SIZE = 3  # 每批次最多3个用例（减小批次大小，避免超时）
        concurrency = task_manager.max_concurrent_tasks  # 使用系统设置的并发数
        
        # 分批
        batches = [original_test_cases[i:i+BATCH_SIZE] for i in range(0, len(original_test_cases), BATCH_SIZE)]
        total_batches = len(batches)
        
        print(f"\n🚀 批量测试用例优化: {len(original_test_cases)} 个用例, 分 {total_batches} 批处理")
        print(f"🔧 配置: 并发={concurrency}, 重试={self._retry_count}次, 超时={self._task_timeout}s")
        
        try:
            all_results = []
            completed = 0
            lock = asyncio.Lock()
            semaphore = asyncio.Semaphore(concurrency)  # 控制并发数
            
            async def process_batch(batch_idx: int, batch: List[dict]):
                """处理单个批次"""
                nonlocal completed
                
                async with semaphore:  # 控制并发
                    # 简化传给AI的数据
                    simplified_batch = [self._simplify_test_case(tc) for tc in batch]
                    
                    print(f"📦 处理第 {batch_idx+1}/{total_batches} 批，共 {len(batch)} 个用例")
                    
                    batch_results = []
                    
                    try:
                        # 一次AI调用处理整批
                        result = await self.optimize_test_cases(agent_id, simplified_batch)
                        optimized_cases = result.get("optimized_cases", [])
                        
                        # 创建id到原始用例的映射
                        original_map = {tc.get("id"): tc for tc in batch}
                        
                        # 处理返回的优化结果
                        for opt in optimized_cases:
                            tc_id = opt.get("id")
                            original = original_map.get(tc_id)
                            if original:
                                normalized = self._normalize_test_case(opt)
                                if normalized and normalized.get("title"):
                                    normalized["id"] = tc_id
                                    batch_results.append({
                                        "original": original,
                                        "optimized": normalized,
                                        "success": True,
                                        "improvements": []
                                    })
                                    print(f"   ✅ [{batch_idx+1}] 优化成功: {normalized.get('title', '')[:30]}...")
                                else:
                                    batch_results.append({
                                        "original": original,
                                        "optimized": None,
                                        "success": False,
                                        "error": "优化结果无效"
                                    })
                        
                        # 检查是否有遗漏的用例
                        returned_ids = {opt.get("id") for opt in optimized_cases}
                        for tc in batch:
                            if tc.get("id") not in returned_ids:
                                batch_results.append({
                                    "original": tc,
                                    "optimized": None,
                                    "success": False,
                                    "error": "AI未返回该用例的优化结果"
                                })
                                print(f"   ⚠️ [{batch_idx+1}] 用例 {tc.get('id')} 未被优化")
                        
                    except Exception as e:
                        print(f"❌ 第 {batch_idx+1} 批处理失败: {e}")
                        for tc in batch:
                            batch_results.append({
                                "original": tc,
                                "optimized": None,
                                "success": False,
                                "error": str(e)
                            })
                    
                    # 更新进度（线程安全）
                    async with lock:
                        completed += 1
                        all_results.extend(batch_results)
                        if task_id:
                            raw_progress = (completed / total_batches) * 100
                            scaled_progress = progress_offset + raw_progress * progress_scale
                            # 更新进度和消息
                            success_in_batch = sum(1 for r in batch_results if r.get("success"))
                            total_success = sum(1 for r in all_results if r.get("success"))
                            task_manager.update_progress(
                                task_id, 
                                int(scaled_progress), 
                                f"正在优化测试用例... ({total_success}/{len(original_test_cases)})"
                            )
                    
                    return batch_results
            
            # 并发处理所有批次
            await asyncio.gather(*[process_batch(i, batch) for i, batch in enumerate(batches)])
            
            success_count = sum(1 for r in all_results if r.get("success"))
            print(f"🎉 优化完成, 成功 {success_count}/{len(original_test_cases)} 个")
            
            return {"success": True, "data": {
                "optimized_results": all_results,
                "optimized_cases": [r["optimized"] for r in all_results if r.get("optimized")],
                "statistics": {"total": len(original_test_cases), "success_count": success_count}
            }}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute_full_generation_pipeline(
        self,
        requirement_content: str,
        file_id: int,
        module_id: int,
        user_id: int,
        agent_ids: Dict[str, int],
        image_paths: Optional[List[str]] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行完整的生成流程：需求点 → 测试点 → 测试用例 → 优化
        
        Args:
            requirement_content: 需求文档内容
            file_id: 需求文件ID
            module_id: 模块ID
            user_id: 用户ID
            agent_ids: 智能体ID字典 {"requirement": id, "test_point": id, "test_case": id, "optimizer": id}
            image_paths: 图片路径列表
            task_id: 任务ID
            
        Returns:
            包含所有生成结果的字典
        """
        from app.services.async_task_manager import task_manager
        from app.models.requirement import RequirementPoint
        from app.models.testcase import TestPoint, TestCase
        
        if self.db:
            task_manager.load_config_from_db(self.db)
            self._load_config()
        
        try:
            # ========== 阶段1：生成需求点 (0-25%) ==========
            if task_id:
                task_manager.update_progress(task_id, 0, "正在分析需求文档...")
            
            print("\n" + "="*60)
            print("🚀 开始完整生成流程")
            print("="*60)
            print(f"📄 需求文件ID: {file_id}")
            print(f"📦 模块ID: {module_id}")
            print(f"👤 用户ID: {user_id}")
            
            # ========== 清空现有数据 ==========
            # 清空该需求文件相关的所有需求点（级联删除会自动删除关联的测试点和测试用例）
            existing_points = self.db.query(RequirementPoint).filter(
                RequirementPoint.requirement_file_id == file_id
            ).all()
            
            if existing_points:
                print(f"\n🗑️  清空现有数据: {len(existing_points)} 个需求点（及其关联的测试点和测试用例）")
                for point in existing_points:
                    self.db.delete(point)
                self.db.flush()
            
            # 生成需求点
            req_result = await self.analyze_requirements(
                agent_id=agent_ids.get("requirement"),
                content=requirement_content,
                image_paths=image_paths
            )
            
            requirement_points_data = req_result.get("requirement_points", [])
            print(f"\n✅ [1/4] 需求点生成完成: {len(requirement_points_data)} 个")
            
            # 调试：输出前3个需求点的原始数据
            if requirement_points_data:
                print(f"\n📊 [调试] 前3个需求点的原始数据:")
                for i, rp in enumerate(requirement_points_data[:3]):
                    print(f"  需求点 {i+1}: priority={rp.get('priority')}, content={rp.get('content', '')[:50]}...")
            
            if not requirement_points_data:
                raise Exception("未生成任何需求点")
            
            # 保存需求点到数据库
            requirement_points = []
            for idx, rp_data in enumerate(requirement_points_data):
                # 标准化优先级
                raw_priority = rp_data.get("priority", "medium")
                normalized_priority = self._normalize_priority(raw_priority)
                
                rp = RequirementPoint(
                    requirement_file_id=file_id,
                    module_id=module_id,
                    content=rp_data.get("content", ""),
                    order_num=rp_data.get("order_index", idx),
                    priority=normalized_priority,
                    source="ai_generated",
                    created_by_ai=True,
                    created_by=user_id
                )
                self.db.add(rp)
                requirement_points.append(rp)
            
            self.db.flush()
            for rp in requirement_points:
                self.db.refresh(rp)
            
            if task_id:
                task_manager.update_progress(task_id, 25, f"需求点生成完成，共 {len(requirement_points)} 个")
            
            # ========== 阶段2：生成测试点 (25-50%) ==========
            print(f"\n🔄 [2/4] 开始生成测试点...")
            
            req_points_for_generation = [{"id": rp.id, "content": rp.content} for rp in requirement_points]
            
            tp_result = await self.execute_test_point_generation(
                requirement_points=req_points_for_generation,
                user_id=user_id,
                agent_id=agent_ids.get("test_point"),
                task_id=task_id,  # 传入task_id以支持批次级进度更新
                progress_offset=25,  # 从25%开始
                progress_scale=0.25  # 占25%进度
            )
            
            if not tp_result.get("success"):
                raise Exception(f"测试点生成失败: {tp_result.get('error')}")
            
            test_points_data = tp_result.get("data", {}).get("test_points", [])
            print(f"✅ [2/4] 测试点生成完成: {len(test_points_data)} 个")
            
            # 保存测试点到数据库
            test_points = []
            for tp_data in test_points_data:
                # 标准化优先级
                raw_priority = tp_data.get("priority", "medium")
                normalized_priority = self._normalize_priority(raw_priority)
                
                tp = TestPoint(
                    requirement_point_id=tp_data.get("requirement_point_id"),
                    module_id=module_id,
                    content=tp_data.get("content", ""),
                    test_type=tp_data.get("test_type", "functional"),
                    design_method=tp_data.get("design_method"),  # 测试设计方法
                    priority=normalized_priority,
                    created_by_ai=True,
                    created_by=user_id
                )
                self.db.add(tp)
                test_points.append(tp)
            
            self.db.flush()
            for tp in test_points:
                self.db.refresh(tp)
            
            if task_id:
                task_manager.update_progress(task_id, 50, f"测试点生成完成，共 {len(test_points)} 个")
            
            # ========== 阶段3：生成测试用例 (50-85%) ==========
            print(f"\n🔄 [3/4] 开始生成测试用例...")
            
            # 传递完整的测试点数据（包含所有必要字段）
            test_points_for_generation = [{
                "id": tp.id, 
                "content": tp.content,
                "test_type": tp.test_type,
                "design_method": tp.design_method,
                "priority": tp.priority,
                "requirement_point_id": tp.requirement_point_id
            } for tp in test_points]
            
            # 用于收集所有保存的测试用例（字典格式，用于优化）
            saved_test_cases_for_optimization = []
            
            # 定义保存回调
            def save_test_cases(cases: List[dict]) -> int:
                """保存测试用例到数据库，并收集数据用于优化"""
                nonlocal saved_test_cases_for_optimization
                saved_count = 0
                batch_objects = []  # 当前批次的对象
                
                print(f"   📥 收到 {len(cases)} 个用例待保存")
                
                for case_data in cases:
                    try:
                        tc = TestCase(
                            test_point_id=case_data.get("test_point_id"),
                            module_id=module_id,
                            title=case_data.get("title", ""),
                            description=case_data.get("description", ""),
                            preconditions=case_data.get("preconditions", ""),
                            test_steps=case_data.get("test_steps", ""),
                            expected_result=case_data.get("expected_result", ""),
                            design_method=case_data.get("design_method", ""),
                            test_category=case_data.get("test_type", "functional"),  # 测试类别
                            priority=case_data.get("priority", "medium"),
                            created_by_ai=True,
                            created_by=user_id
                        )
                        self.db.add(tc)
                        batch_objects.append(tc)
                        saved_count += 1
                    except Exception as e:
                        print(f"   ⚠️ 创建测试用例对象失败: {e}")
                        continue
                
                # 立即flush并commit当前批次
                try:
                    self.db.flush()
                    for tc in batch_objects:
                        self.db.refresh(tc)
                        # 保存为字典格式（与直接生成测试用例的方式一致）
                        saved_test_cases_for_optimization.append({
                            "id": tc.id,
                            "title": tc.title,
                            "description": tc.description,
                            "preconditions": tc.preconditions,
                            "test_steps": tc.test_steps,
                            "expected_result": tc.expected_result
                        })
                    # 每批次提交，确保数据持久化
                    self.db.commit()
                    print(f"   💾 批次保存成功: {saved_count} 个用例，总计: {len(saved_test_cases_for_optimization)} 个")
                except Exception as e:
                    print(f"   ❌ 批次提交失败: {e}")
                    self.db.rollback()
                    return 0
                
                return saved_count
            
            tc_result = await self.execute_test_case_design_batch(
                test_points=test_points_for_generation,
                module_id=module_id,
                user_id=user_id,
                agent_id=agent_ids.get("test_case"),
                task_id=task_id,
                on_batch_complete=save_test_cases,
                progress_offset=50,
                progress_scale=0.25  # 改为占25%进度（原来是0.35）
            )
            
            if not tc_result.get("success"):
                raise Exception(f"测试用例生成失败: {tc_result.get('error')}")
            
            generated_cases = tc_result.get("data", {}).get("test_cases", [])
            print(f"✅ [3/4] 测试用例生成完成: {len(generated_cases)} 个")
            print(f"💾 已保存到数据库: {len(saved_test_cases_for_optimization)} 个测试用例")
            
            if task_id:
                task_manager.update_progress(task_id, 75, f"测试用例生成完成，共 {len(generated_cases)} 个")
            
            # ========== 阶段4：优化测试用例 (75-100%) ==========
            print(f"\n🔄 [4/4] 开始优化测试用例...")
            
            # 检查是否有测试用例需要优化
            if not saved_test_cases_for_optimization:
                print(f"⚠️ 没有找到已保存的测试用例，跳过优化阶段")
                # 直接提交并完成
                self.db.commit()
                if task_id:
                    task_manager.update_progress(task_id, 100, "生成完成！")
                    task_manager.complete_task(task_id, {
                        "requirement_points_count": len(requirement_points),
                        "test_points_count": len(test_points),
                        "test_cases_count": len(generated_cases)
                    })
                return {
                    "success": True,
                    "data": {
                        "requirement_points_count": len(requirement_points),
                        "test_points_count": len(test_points),
                        "test_cases_count": len(generated_cases)
                    }
                }
            
            print(f"📋 准备优化 {len(saved_test_cases_for_optimization)} 个测试用例")
            
            # 更新进度消息，进入优化阶段
            if task_id:
                task_manager.update_progress(task_id, 75, f"正在优化测试用例...")
            
            opt_result = await self.execute_test_case_optimization(
                original_test_cases=saved_test_cases_for_optimization,
                user_id=user_id,
                agent_id=agent_ids.get("optimizer"),
                batch_mode=True,
                task_id=task_id,
                progress_offset=75,
                progress_scale=0.25
            )
            
            # 应用优化结果到数据库
            optimized_count = 0
            if opt_result.get("success"):
                optimized_results = opt_result.get("data", {}).get("optimized_results", [])
                print(f"📝 收到 {len(optimized_results)} 个优化结果")
                
                for opt_result_item in optimized_results:
                    if opt_result_item.get("success") and opt_result_item.get("optimized"):
                        original_id = opt_result_item.get("original", {}).get("id")
                        if original_id:
                            try:
                                optimized = opt_result_item["optimized"]
                                tc = self.db.query(TestCase).filter(TestCase.id == original_id).first()
                                if tc:
                                    tc.title = optimized.get("title", tc.title)
                                    tc.description = optimized.get("description", tc.description)
                                    tc.preconditions = optimized.get("preconditions", tc.preconditions)
                                    tc.test_steps = optimized.get("test_steps", tc.test_steps)
                                    tc.expected_result = optimized.get("expected_result", tc.expected_result)
                                    optimized_count += 1
                            except Exception as e:
                                print(f"⚠️ 更新优化结果失败 (ID={original_id}): {e}")
                
                print(f"✅ [4/4] 测试用例优化完成: 成功优化 {optimized_count} 个用例")
            else:
                print(f"⚠️ [4/4] 测试用例优化失败，跳过此步骤")
            
            # 先提交所有数据库更改
            print(f"\n💾 正在提交所有数据到数据库...")
            self.db.commit()
            print(f"✅ 数据库提交成功")
            
            # 验证数据是否真的保存了
            saved_count = self.db.query(TestCase).filter(TestCase.module_id == module_id).count()
            print(f"📊 数据库验证: 模块 {module_id} 共有 {saved_count} 个测试用例")
            
            # 然后标记任务完成
            if task_id:
                task_manager.update_progress(task_id, 100, "生成完成！")
                result_data = {
                    "requirement_points_count": len(requirement_points),
                    "test_points_count": len(test_points),
                    "test_cases_count": len(saved_test_cases_for_optimization),
                    "optimized_count": optimized_count
                }
                task_manager.complete_task(task_id, result_data)
                print(f"✅ 任务状态已更新为完成")
                print(f"📋 任务结果: {result_data}")
                
                # 验证任务状态
                task_status = task_manager.get_task_status(task_id)
                print(f"🔍 任务状态验证: {task_status}")
            
            print("\n" + "="*60)
            print("🎉 完整生成流程执行成功！")
            print(f"   需求点: {len(requirement_points)} 个")
            print(f"   测试点: {len(test_points)} 个")
            print(f"   测试用例: {len(saved_test_cases_for_optimization)} 个（已保存到数据库）")
            if optimized_count > 0:
                print(f"   优化用例: {optimized_count} 个")
            print("="*60)
            
            return {
                "success": True,
                "data": {
                    "requirement_points_count": len(requirement_points),
                    "test_points_count": len(test_points),
                    "test_cases_count": len(saved_test_cases_for_optimization),
                    "optimized_count": optimized_count
                }
            }
            
        except Exception as e:
            print(f"\n❌ 完整生成流程失败: {e}")
            if task_id:
                task_manager.fail_task(task_id, str(e))
            # 即使失败也提交已保存的数据
            try:
                self.db.commit()
            except:
                self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }


# 全局实例
agent_service_real = AgentServiceReal()
