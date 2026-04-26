# AI 芯片设计师 Agent（Phase 1 原型）

from typing import AsyncIterator, List, Optional

from quantamind.shared.api import ChatMessage, MessageRole
from quantamind.server import brain, memory
from quantamind.agents.base import BaseAgent


class DesignerAgent(BaseAgent):
    name = "designer_agent"
    role = "AI芯片设计师"

    def __init__(self):
        self._brain = brain.get_brain()

    async def respond(
        self,
        messages: List[ChatMessage],
        context: Optional[dict] = None,
    ) -> AsyncIterator[str]:
        project_id = (context or {}).get("project_id")
        sys_content = (
            "You are the QuantaMind Chip Designer Agent. You help with quantum chip design: "
            "transmon/xmon topology, frequency allocation, layout and routing concepts, "
            "and Q-EDA workflow. Answer in the user's language. When design decisions are made, "
            "summarize them in 1-2 lines for project memory."
        )
        system_msg = ChatMessage(role=MessageRole.SYSTEM, content=sys_content)
        full = [system_msg] + messages

        full_text = ""
        async for chunk in self._brain.chat(full, stream=True):
            full_text += chunk
            yield chunk

        # 简短结论写入项目记忆（便于后续 RAG）
        if full_text.strip() and project_id:
            memory.append_memory(
                f"[Designer] User asked about design. Summary: {full_text.strip()[:300]}...",
                project_id,
            )
