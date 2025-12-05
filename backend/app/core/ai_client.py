"""
AI客户端基础类
支持OpenAI兼容格式的所有模型
"""
import asyncio
import json
import time
from typing import Dict, Any, Optional, List, AsyncGenerator
from abc import ABC, abstractmethod
import httpx
from pydantic import BaseModel

from app.config import settings


class AIMessage(BaseModel):
    """AI消息模型"""
    role: str  # system, user, assistant
    content: str


class AIResponse(BaseModel):
    """AI响应模型"""
    content: str
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None


class BaseAIClient(ABC):
    """AI客户端基础抽象类"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            headers={"Authorization": f"Bearer {api_key}"}
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AIResponse:
        """聊天完成接口"""
        pass
    
    @abstractmethod
    async def stream_chat_completion(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成接口"""
        pass


class OpenAICompatibleClient(BaseAIClient):
    """OpenAI兼容格式客户端"""
    
    async def chat_completion(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AIResponse:
        """聊天完成"""
        try:
            # 构建请求数据
            request_data = {
                "model": self.model,
                "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            
            # 发送请求
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=request_data
            )
            response.raise_for_status()
            
            # 解析响应
            data = response.json()
            choice = data["choices"][0]
            
            return AIResponse(
                content=choice["message"]["content"],
                usage=data.get("usage"),
                model=data.get("model"),
                finish_reason=choice.get("finish_reason")
            )
            
        except httpx.HTTPError as e:
            raise Exception(f"AI API请求失败: {e}")
        except KeyError as e:
            raise Exception(f"AI API响应格式错误: {e}")
    
    async def stream_chat_completion(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        try:
            # 构建请求数据
            request_data = {
                "model": self.model,
                "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
                **kwargs
            }
            
            # 发送流式请求
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=request_data
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # 移除 "data: " 前缀
                        
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            choice = data["choices"][0]
                            
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.HTTPError as e:
            raise Exception(f"AI流式API请求失败: {e}")


class AIClientFactory:
    """AI客户端工厂"""
    
    @staticmethod
    def create_client(
        provider: str,
        api_key: str,
        model: str,
        base_url: Optional[str] = None
    ) -> BaseAIClient:
        """创建AI客户端"""
        if provider.lower() in ["openai", "anthropic", "deepseek", "zhipu", "moonshot"]:
            return OpenAICompatibleClient(
                api_key=api_key,
                base_url=base_url,
                model=model
            )
        else:
            raise ValueError(f"不支持的AI提供商: {provider}")


# 全局AI客户端管理器
class AIClientManager:
    """AI客户端管理器"""
    
    def __init__(self):
        self._clients: Dict[int, BaseAIClient] = {}
    
    async def get_client(self, model_config: Dict[str, Any]) -> BaseAIClient:
        """获取AI客户端"""
        model_id = model_config["id"]
        
        # 如果客户端已存在，直接返回
        if model_id in self._clients:
            return self._clients[model_id]
        
        # 创建新客户端
        client = AIClientFactory.create_client(
            provider=model_config["provider"],
            api_key=model_config["api_key"],
            model=model_config["model_id"],
            base_url=model_config.get("base_url")
        )
        
        self._clients[model_id] = client
        return client
    
    async def remove_client(self, model_id: int):
        """移除客户端"""
        if model_id in self._clients:
            client = self._clients.pop(model_id)
            await client.__aexit__(None, None, None)


# 全局客户端管理器实例
ai_client_manager = AIClientManager()
