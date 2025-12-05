"""
异步任务管理器
用于管理后台异步任务，支持并发处理和状态轮询
支持从系统设置加载并发配置
"""
import asyncio
import uuid
from typing import Dict, Any, Optional, List, Callable, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class AsyncTaskStatus(str, Enum):
    """异步任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class AsyncTask:
    """异步任务数据类"""
    task_id: str
    task_type: str
    status: AsyncTaskStatus = AsyncTaskStatus.PENDING
    progress: int = 0
    total_batches: int = 0
    completed_batches: int = 0
    result: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None  # 进度消息
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "progress": self.progress,
            "total_batches": self.total_batches,
            "completed_batches": self.completed_batches,
            "result": self.result,
            "error": self.error,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class AsyncTaskManager:
    """异步任务管理器
    
    支持从系统设置加载并发配置，包括：
    - max_concurrent_tasks: 最大并发任务数
    - task_timeout: 任务超时时间（秒）
    - retry_count: 失败重试次数
    - queue_size: 任务队列大小
    """
    
    # 默认配置值
    DEFAULT_MAX_CONCURRENT_TASKS = 3
    DEFAULT_TASK_TIMEOUT = 300  # 秒（与 httpx 超时保持一致）
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_QUEUE_SIZE = 100
    
    def __init__(self):
        self._tasks: Dict[str, AsyncTask] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._pending_queue: List[str] = []  # 等待执行的任务队列
        
        # 并发配置（从系统设置加载）
        self._max_concurrent_tasks: int = self.DEFAULT_MAX_CONCURRENT_TASKS
        self._task_timeout: int = self.DEFAULT_TASK_TIMEOUT
        self._retry_count: int = self.DEFAULT_RETRY_COUNT
        self._queue_size: int = self.DEFAULT_QUEUE_SIZE
        
        # 配置是否已加载
        self._config_loaded: bool = False
    
    def load_config_from_db(self, db: "Session") -> None:
        """从数据库加载并发配置
        
        Args:
            db: 数据库会话
        """
        try:
            from app.services.settings_service import SettingsService
            
            config = SettingsService.get_concurrency_config(db)
            self._max_concurrent_tasks = config.max_concurrent_tasks
            self._task_timeout = config.task_timeout
            self._retry_count = config.retry_count
            self._queue_size = config.queue_size
            self._config_loaded = True
            
            print(f"[AsyncTaskManager] 已加载并发配置: "
                  f"max_concurrent_tasks={self._max_concurrent_tasks}, "
                  f"task_timeout={self._task_timeout}s, "
                  f"retry_count={self._retry_count}, "
                  f"queue_size={self._queue_size}")
        except Exception as e:
            print(f"[AsyncTaskManager] 加载并发配置失败，使用默认值: {e}")
            self._config_loaded = False
    
    def reload_config(self, db: "Session") -> None:
        """重新加载并发配置
        
        当系统设置更新时调用此方法刷新配置
        
        Args:
            db: 数据库会话
        """
        self.load_config_from_db(db)
    
    @property
    def max_concurrent_tasks(self) -> int:
        """获取最大并发任务数"""
        return self._max_concurrent_tasks
    
    @property
    def task_timeout(self) -> int:
        """获取任务超时时间（秒）"""
        return self._task_timeout
    
    @property
    def retry_count(self) -> int:
        """获取失败重试次数"""
        return self._retry_count
    
    @property
    def queue_size(self) -> int:
        """获取任务队列大小"""
        return self._queue_size
    
    @property
    def config_loaded(self) -> bool:
        """配置是否已从数据库加载"""
        return self._config_loaded
    
    def get_running_task_count(self) -> int:
        """获取当前正在运行的任务数"""
        return sum(1 for task in self._tasks.values() 
                   if task.status == AsyncTaskStatus.RUNNING)
    
    def get_pending_task_count(self) -> int:
        """获取等待执行的任务数"""
        return len(self._pending_queue)
    
    def can_start_new_task(self) -> bool:
        """检查是否可以启动新任务
        
        基于当前运行的任务数和配置的最大并发数判断
        
        Returns:
            是否可以启动新任务
        """
        return self.get_running_task_count() < self._max_concurrent_tasks
    
    def is_queue_full(self) -> bool:
        """检查任务队列是否已满
        
        Returns:
            队列是否已满
        """
        return len(self._pending_queue) >= self._queue_size
    
    def create_task(self, task_type: str, total_batches: int = 1) -> str:
        """创建新任务，返回任务ID
        
        如果达到并发限制，任务将被加入等待队列
        
        Args:
            task_type: 任务类型
            total_batches: 总批次数
            
        Returns:
            任务ID
            
        Raises:
            ValueError: 当队列已满时抛出
        """
        # 检查队列是否已满
        if self.is_queue_full():
            raise ValueError(f"任务队列已满（最大{self._queue_size}个），请稍后重试")
        
        task_id = str(uuid.uuid4())
        task = AsyncTask(
            task_id=task_id,
            task_type=task_type,
            total_batches=total_batches
        )
        self._tasks[task_id] = task
        
        # 如果达到并发限制，加入等待队列
        if not self.can_start_new_task():
            self._pending_queue.append(task_id)
            print(f"[AsyncTaskManager] 任务 {task_id} 已加入等待队列 "
                  f"(当前运行: {self.get_running_task_count()}/{self._max_concurrent_tasks})")
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[AsyncTask]:
        """获取任务信息"""
        return self._tasks.get(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self._tasks.get(task_id)
        if task:
            status_dict = task.to_dict()
            # 添加队列位置信息
            if task_id in self._pending_queue:
                status_dict["queue_position"] = self._pending_queue.index(task_id) + 1
            return status_dict
        return None
    
    def update_task_progress(self, task_id: str, completed_batches: int):
        """更新任务进度（基于批次数）"""
        task = self._tasks.get(task_id)
        if task:
            task.completed_batches = completed_batches
            if task.total_batches > 0:
                # 进度范围：5% ~ 95%（留5%给启动，5%给保存）
                raw_progress = (completed_batches / task.total_batches) * 90
                task.progress = int(5 + raw_progress)
    
    def update_progress(self, task_id: str, progress: int, message: str = None):
        """直接设置任务进度百分比
        
        Args:
            task_id: 任务ID
            progress: 进度百分比（0-100）
            message: 可选的进度消息
        """
        task = self._tasks.get(task_id)
        if task:
            task.progress = min(max(progress, 0), 100)
            if message:
                task.message = message
    
    def start_task(self, task_id: str) -> bool:
        """标记任务开始
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功启动（如果达到并发限制则返回False）
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        # 检查是否可以启动
        if not self.can_start_new_task() and task_id not in self._pending_queue:
            # 如果不能启动且不在队列中，加入队列
            self._pending_queue.append(task_id)
            return False
        
        # 从等待队列中移除
        if task_id in self._pending_queue:
            self._pending_queue.remove(task_id)
        
        task.status = AsyncTaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        task.progress = 5  # 设置初始进度，表示任务已开始
        return True
    
    def complete_task(self, task_id: str, result: Any):
        """标记任务完成"""
        task = self._tasks.get(task_id)
        if task:
            task.status = AsyncTaskStatus.COMPLETED
            task.progress = 100
            task.result = result
            task.completed_at = datetime.utcnow()
        
        # 清理运行中的任务
        if task_id in self._running_tasks:
            del self._running_tasks[task_id]
        
        # 尝试启动等待队列中的下一个任务
        self._process_pending_queue()
    
    def fail_task(self, task_id: str, error: str):
        """标记任务失败"""
        task = self._tasks.get(task_id)
        if task:
            task.status = AsyncTaskStatus.FAILED
            task.error = error
            task.completed_at = datetime.utcnow()
        
        # 清理运行中的任务
        if task_id in self._running_tasks:
            del self._running_tasks[task_id]
        
        # 尝试启动等待队列中的下一个任务
        self._process_pending_queue()
    
    def timeout_task(self, task_id: str):
        """标记任务超时
        
        当任务执行时间超过配置的超时时间时调用
        
        Args:
            task_id: 任务ID
        """
        task = self._tasks.get(task_id)
        if task:
            task.status = AsyncTaskStatus.TIMEOUT
            task.error = f"任务执行超时（超过{self._task_timeout}秒）"
            task.completed_at = datetime.utcnow()
        
        # 取消正在运行的asyncio任务
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]
        
        # 尝试启动等待队列中的下一个任务
        self._process_pending_queue()
    
    def cancel_task(self, task_id: str):
        """取消任务"""
        task = self._tasks.get(task_id)
        if task:
            task.status = AsyncTaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
        
        # 从等待队列中移除
        if task_id in self._pending_queue:
            self._pending_queue.remove(task_id)
        
        # 取消正在运行的asyncio任务
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]
        
        # 尝试启动等待队列中的下一个任务
        self._process_pending_queue()
    
    def register_running_task(self, task_id: str, asyncio_task: asyncio.Task):
        """注册正在运行的asyncio任务"""
        self._running_tasks[task_id] = asyncio_task
    
    async def execute_with_timeout(self, task_id: str, coro) -> Any:
        """执行任务并应用超时限制
        
        Args:
            task_id: 任务ID
            coro: 要执行的协程
            
        Returns:
            协程的返回值
            
        Raises:
            asyncio.TimeoutError: 当任务超时时抛出
        """
        try:
            result = await asyncio.wait_for(coro, timeout=self._task_timeout)
            return result
        except asyncio.TimeoutError:
            self.timeout_task(task_id)
            raise
    
    def _process_pending_queue(self):
        """处理等待队列中的任务
        
        当有任务完成时调用，尝试启动等待队列中的下一个任务
        """
        while self._pending_queue and self.can_start_new_task():
            next_task_id = self._pending_queue[0]
            task = self._tasks.get(next_task_id)
            if task and task.status == AsyncTaskStatus.PENDING:
                # 任务仍在等待，可以启动
                self._pending_queue.pop(0)
                print(f"[AsyncTaskManager] 从队列启动任务 {next_task_id}")
                # 注意：实际启动需要外部调用者处理
                break
            else:
                # 任务已被取消或状态改变，从队列移除
                self._pending_queue.pop(0)
    
    def get_next_pending_task(self) -> Optional[str]:
        """获取下一个等待执行的任务ID
        
        Returns:
            下一个等待执行的任务ID，如果队列为空或达到并发限制则返回None
        """
        if not self._pending_queue or not self.can_start_new_task():
            return None
        
        # 查找第一个仍在等待状态的任务
        for task_id in self._pending_queue:
            task = self._tasks.get(task_id)
            if task and task.status == AsyncTaskStatus.PENDING:
                return task_id
        
        return None
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        now = datetime.utcnow()
        to_delete = []
        for task_id, task in self._tasks.items():
            if task.completed_at:
                age = (now - task.completed_at).total_seconds() / 3600
                if age > max_age_hours:
                    to_delete.append(task_id)
        
        for task_id in to_delete:
            del self._tasks[task_id]
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
            if task_id in self._pending_queue:
                self._pending_queue.remove(task_id)
    
    def get_config_info(self) -> Dict[str, Any]:
        """获取当前配置信息
        
        Returns:
            配置信息字典
        """
        return {
            "max_concurrent_tasks": self._max_concurrent_tasks,
            "task_timeout": self._task_timeout,
            "retry_count": self._retry_count,
            "queue_size": self._queue_size,
            "config_loaded": self._config_loaded,
            "running_tasks": self.get_running_task_count(),
            "pending_tasks": self.get_pending_task_count()
        }


# 全局任务管理器实例
task_manager = AsyncTaskManager()
