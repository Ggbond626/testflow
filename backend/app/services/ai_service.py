"""
AI服务 - 调用大语言模型
只支持 OpenAI 兼容格式的 API 调用
支持流式生成，避免长时间连接超时
"""
import json
import os
import base64
from typing import Dict, Any, List, Optional
import httpx


class AIService:
    """AI服务类 - 使用 OpenAI 兼容格式调用大语言模型"""
    
    def __init__(self):
        pass
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """将图片文件编码为base64字符串"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def get_image_mime_type(self, image_path: str) -> str:
        """根据图片路径获取MIME类型"""
        ext = image_path.lower().split(".")[-1]
        mime_types = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "webp": "image/webp",
        }
        return mime_types.get(ext, "image/png")
    
    async def call_ai_stream(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        api_key: str,
        base_url: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        流式调用 OpenAI 兼容格式的 API，收集所有输出后返回
        
        Args:
            model: 模型ID
            messages: 消息列表
            api_key: API密钥
            base_url: API基础URL
            temperature: 温度参数
            max_tokens: 最大令牌数
            
        Returns:
            AI响应内容（完整收集后返回）
        """
        # 确保 base_url 格式正确
        base_url = base_url.rstrip('/')
        if not base_url.endswith('/v1'):
            base_url = f"{base_url}/v1"
        
        url = f"{base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True  # 启用流式输出
        }
        
        print(f"🤖 AI流式调用: model={model}, url={url}")
        
        collected_content = []
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:  # 增加超时时间
                async with client.stream("POST", url, headers=headers, json=data) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        print(f"❌ API调用失败: {response.status_code} - {error_text.decode()}")
                        raise Exception(f"API返回错误: {response.status_code}")
                    
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        
                        # 处理 SSE 格式
                        if line.startswith("data: "):
                            data_str = line[6:]  # 去掉 "data: " 前缀
                            
                            if data_str.strip() == "[DONE]":
                                break
                            
                            try:
                                chunk = json.loads(data_str)
                                if "choices" in chunk and chunk["choices"]:
                                    delta = chunk["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        collected_content.append(content)
                            except json.JSONDecodeError:
                                continue
            
            full_content = "".join(collected_content)
            print(f"✅ AI流式响应完成，内容长度: {len(full_content)}")
            return full_content
                    
        except httpx.TimeoutException:
            print("❌ API调用超时")
            raise Exception("API调用超时，请稍后重试")
        except Exception as e:
            print(f"❌ AI流式调用异常: {e}")
            raise
    
    async def call_ai(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        api_key: str,
        base_url: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        调用 OpenAI 兼容格式的 API（使用流式模式避免超时）
        
        Args:
            model: 模型ID
            messages: 消息列表
            api_key: API密钥
            base_url: API基础URL
            temperature: 温度参数
            max_tokens: 最大令牌数
            
        Returns:
            AI响应内容
        """
        # 默认使用流式调用
        return await self.call_ai_stream(
            model=model,
            messages=messages,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    async def call_ai_multimodal(
        self,
        model: str,
        text_content: str,
        image_paths: List[str],
        api_key: str,
        base_url: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        多模态AI调用接口 - 支持文本和图片输入（OpenAI兼容格式，流式模式）
        
        Args:
            model: 模型ID
            text_content: 文本内容
            image_paths: 图片文件路径列表
            api_key: API密钥
            base_url: API基础URL
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大令牌数
            
        Returns:
            AI响应内容
        """
        # 构建多模态消息内容
        content = [{"type": "text", "text": text_content}]
        
        # 添加图片
        for image_path in image_paths:
            try:
                image_data = self.encode_image_to_base64(image_path)
                mime_type = self.get_image_mime_type(image_path)
                
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_data}",
                        "detail": "high"
                    }
                })
            except Exception as e:
                print(f"⚠️ 无法加载图片 {image_path}: {e}")
                continue
        
        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})
        
        # 使用流式调用
        return await self.call_ai_stream(
            model=model,
            messages=messages,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens
        )


# 全局AI服务实例
ai_service = AIService()
