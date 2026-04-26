# QuantumBrain — LLM 推理适配层（支持 Function Calling / Tool Call 循环）

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from quantamind.shared.api import ChatMessage, MessageRole

_log = logging.getLogger("quantamind.brain")

# Tool Call 循环最大轮次，防止无限循环
MAX_TOOL_ROUNDS = 8
LLM_CONNECT_TIMEOUT_SECONDS = 15
LLM_TOTAL_TIMEOUT_SECONDS = 90


class BrainResponse:
    """Brain 返回：content 文本片段 或 tool_call 请求"""
    def __init__(self, type: str, **kwargs):
        self.type = type  # "content" | "tool_call" | "tool_calls_done"
        self.data = kwargs


class BaseBrain(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        stream: bool = True,
    ) -> AsyncIterator[str]:
        ...

    async def chat_with_tools(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        stream: bool = True,
    ) -> AsyncIterator[BrainResponse]:
        """支持 Tool Call 的对话（子类可覆盖；默认回退到纯文本 chat）"""
        plain = [ChatMessage(role=MessageRole(m["role"]), content=m.get("content", "")) for m in messages if m.get("content")]
        async for chunk in self.chat(plain, stream=stream):
            yield BrainResponse("content", text=chunk)


class OllamaBrain(BaseBrain):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def chat(self, messages: List[ChatMessage], stream: bool = True) -> AsyncIterator[str]:
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=LLM_TOTAL_TIMEOUT_SECONDS, connect=LLM_CONNECT_TIMEOUT_SECONDS)
        body = {
            "model": self.model,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "stream": stream,
        }
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{self.base_url}/api/chat", json=body) as resp:
                if resp.status != 200:
                    yield f"[Brain error: {resp.status}]"
                    return
                if stream:
                    async for line in resp.content:
                        if line:
                            try:
                                obj = json.loads(line)
                                if "message" in obj and "content" in obj["message"]:
                                    yield obj["message"]["content"]
                                if obj.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    data = await resp.json()
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]

    async def chat_with_tools(self, messages: List[dict], tools: Optional[List[dict]] = None,
                              stream: bool = True) -> AsyncIterator[BrainResponse]:
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=LLM_TOTAL_TIMEOUT_SECONDS, connect=LLM_CONNECT_TIMEOUT_SECONDS)
        body = {"model": self.model, "messages": messages, "stream": False}
        if tools:
            body["tools"] = tools
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{self.base_url}/api/chat", json=body) as resp:
                if resp.status != 200:
                    yield BrainResponse("content", text=f"[Ollama error: {resp.status}]")
                    return
                data = await resp.json()
                msg = data.get("message", {})
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        fn = tc.get("function", {})
                        yield BrainResponse("tool_call", name=fn.get("name", ""), arguments=fn.get("arguments", {}))
                    yield BrainResponse("tool_calls_done")
                elif msg.get("content"):
                    yield BrainResponse("content", text=msg["content"])


class OpenAICompatBrain(BaseBrain):
    def __init__(self, api_base: str, api_key: str, model: str):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def chat(self, messages: List[ChatMessage], stream: bool = True) -> AsyncIterator[str]:
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=LLM_TOTAL_TIMEOUT_SECONDS, connect=LLM_CONNECT_TIMEOUT_SECONDS)
        url = f"{self.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {
            "model": self.model,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "stream": stream,
        }
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=body, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    yield f"[LLM API 错误 {resp.status}]: {text[:200]}"
                    return
                if stream:
                    async for line in resp.content:
                        decoded = line.decode("utf-8", errors="ignore").strip()
                        if not decoded.startswith("data: "):
                            continue
                        payload = decoded[6:]
                        if payload == "[DONE]":
                            break
                        try:
                            obj = json.loads(payload)
                            delta = obj.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, IndexError, KeyError):
                            continue
                else:
                    data = await resp.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content:
                        yield content

    async def chat_with_tools(self, messages: List[dict], tools: Optional[List[dict]] = None,
                              stream: bool = False) -> AsyncIterator[BrainResponse]:
        """OpenAI 兼容 Function Calling（DeepSeek / Qwen / OpenAI / Kimi 等均支持）"""
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=LLM_TOTAL_TIMEOUT_SECONDS, connect=LLM_CONNECT_TIMEOUT_SECONDS)
        url = f"{self.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {"model": self.model, "messages": messages, "stream": False}
        if tools:
            body["tools"] = tools
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=body, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    yield BrainResponse("content", text=f"[LLM API 错误 {resp.status}]: {text[:200]}")
                    return
                data = await resp.json()
                choice = (data.get("choices") or [{}])[0]
                msg = choice.get("message", {})
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        fn = tc.get("function", {})
                        args = fn.get("arguments", "{}")
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except json.JSONDecodeError:
                                args = {}
                        yield BrainResponse("tool_call", id=tc.get("id", ""), name=fn.get("name", ""), arguments=args)
                    yield BrainResponse("tool_calls_done", raw_message=msg)
                elif msg.get("content"):
                    yield BrainResponse("content", text=msg["content"])


class FallbackBrain(BaseBrain):
    async def chat(self, messages: List[ChatMessage], stream: bool = True) -> AsyncIterator[str]:
        last = next((m.content for m in reversed(messages) if m.role == MessageRole.USER), "")
        t = last.lower()
        if any(k in t for k in ("你好", "hello", "hi", "嗨")):
            yield "你好！我是 QuantaMind 量智大脑。当前 LLM 服务未连接，运行在内置模式。请在设置中配置 LLM 提供商（如 DeepSeek）以获得完整 AI 能力。"
        else:
            yield f"已收到：「{last[:60]}」。当前 LLM 未连接，请在设置页配置 API Key 后重试。"


class SmartBrain(BaseBrain):
    def __init__(self, primary: BaseBrain, fallback: BaseBrain):
        self._primary = primary
        self._fallback = fallback

    async def chat(self, messages: List[ChatMessage], stream: bool = True) -> AsyncIterator[str]:
        try:
            got_any = False
            async for chunk in self._primary.chat(messages, stream=stream):
                got_any = True
                yield chunk
            if got_any:
                return
        except Exception:
            pass
        async for chunk in self._fallback.chat(messages, stream=stream):
            yield chunk

    async def chat_with_tools(self, messages: List[dict], tools: Optional[List[dict]] = None,
                              stream: bool = False) -> AsyncIterator[BrainResponse]:
        try:
            got_any = False
            async for resp in self._primary.chat_with_tools(messages, tools, stream):
                got_any = True
                yield resp
            if got_any:
                return
        except Exception as e:
            _log.warning("Tool call 失败，降级: %s", e)
        async for resp in self._fallback.chat_with_tools(messages, tools, stream):
            yield resp


PROVIDER_DEFAULTS = {
    "openai":   {"api_base": "https://api.openai.com/v1",           "model": "gpt-4o-mini"},
    "deepseek": {"api_base": "https://api.deepseek.com/v1",         "model": "deepseek-chat"},
    "qwen":     {"api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"},
    "kimi":     {"api_base": "https://api.moonshot.cn/v1",           "model": "moonshot-v1-8k"},
    "zhipu":    {"api_base": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-flash"},
    "yi":       {"api_base": "https://api.lingyiwanwu.com/v1",      "model": "yi-lightning"},
}


def get_brain():
    from quantamind import config
    provider = config.LLM_PROVIDER.lower()
    if provider == "ollama":
        primary = OllamaBrain(base_url=config.LLM_API_BASE, model=config.LLM_MODEL)
    elif provider in PROVIDER_DEFAULTS or config.LLM_API_KEY:
        defaults = PROVIDER_DEFAULTS.get(provider, {})
        api_base = config.LLM_API_BASE if config.LLM_API_BASE != "http://localhost:11434" else defaults.get("api_base", config.LLM_API_BASE)
        model = config.LLM_MODEL if config.LLM_MODEL != "qwen2.5:7b" else defaults.get("model", config.LLM_MODEL)
        primary = OpenAICompatBrain(api_base=api_base, api_key=config.LLM_API_KEY, model=model)
    else:
        primary = OllamaBrain(base_url=config.LLM_API_BASE, model=config.LLM_MODEL)
    return SmartBrain(primary, FallbackBrain())
