# 基类：Agent 接口

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional

from quantamind.shared.api import ChatMessage, MessageRole


class BaseAgent(ABC):
    name: str = "base"
    role: str = ""

    @abstractmethod
    async def respond(
        self,
        messages: List[ChatMessage],
        context: Optional[dict] = None,
    ) -> AsyncIterator[str]:
        ...
