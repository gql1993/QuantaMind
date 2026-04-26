from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from quantamind.shared.api import ChatMessage, MessageRole
from quantamind_v2.contracts.run import RunState, RunType
from quantamind_v2.core.runs.coordinator import RunCoordinator


@dataclass
class ChatResult:
    content: str
    run_id: str
    pipeline_id: str | None = None


class ChatService:
    def __init__(self, coordinator: RunCoordinator) -> None:
        self.coordinator = coordinator
        self._orchestrator = None

    async def send(self, message: str, *, session_id: str | None = None) -> ChatResult:
        run_id = self._create_chat_run(message)
        try:
            reply = await self._run_orchestrator(message, session_id=session_id, run_id=run_id)
            self._complete_chat_run(run_id)
            pipeline_id = getattr(self._orchestrator, "_current_pipeline_id", None)
            return ChatResult(content=reply, run_id=run_id, pipeline_id=pipeline_id)
        except Exception as exc:
            self._fail_chat_run(run_id, exc)
            raise

    async def stream(self, message: str, *, session_id: str | None = None) -> AsyncIterator[dict]:
        run_id = self._create_chat_run(message)
        yield {"type": "run", "run_id": run_id, "session_id": session_id}
        chunks: list[str] = []
        try:
            async for chunk in self._iter_orchestrator(message, session_id=session_id, run_id=run_id):
                chunks.append(chunk)
                yield {"type": "content", "data": chunk, "run_id": run_id, "session_id": session_id}
            self._complete_chat_run(run_id)
            pipeline_id = getattr(self._orchestrator, "_current_pipeline_id", None)
            yield {
                "type": "done",
                "run_id": run_id,
                "session_id": session_id,
                "pipeline_id": pipeline_id,
                "content": "".join(chunks),
            }
        except Exception as exc:
            self._fail_chat_run(run_id, exc)
            yield {"type": "error", "run_id": run_id, "session_id": session_id, "data": str(exc)}

    async def _run_orchestrator(self, message: str, *, session_id: str | None, run_id: str) -> str:
        chunks = [chunk async for chunk in self._iter_orchestrator(message, session_id=session_id, run_id=run_id)]
        return "".join(chunks)

    async def _iter_orchestrator(
        self,
        message: str,
        *,
        session_id: str | None,
        run_id: str,
    ) -> AsyncIterator[str]:
        if self._orchestrator is None:
            from quantamind.agents.orchestrator import Orchestrator

            self._orchestrator = Orchestrator()
        context = {
            "session_id": session_id,
            "run_id": run_id,
        }
        messages = [ChatMessage(role=MessageRole.USER, content=message)]
        async for chunk in self._orchestrator.respond(messages, context):
            yield chunk

    def _create_chat_run(self, message: str) -> str:
        run = self.coordinator.create_run(
            RunType.CHAT,
            origin="frontend_chat",
            owner_agent="orchestrator",
            status_message=message[:120],
        )
        self.coordinator.transition(
            run.run_id,
            RunState.RUNNING,
            stage="responding",
            status_message="AI 工作台正在生成回复。",
        )
        return run.run_id

    def _complete_chat_run(self, run_id: str) -> None:
        self.coordinator.transition(
            run_id,
            RunState.COMPLETED,
            stage="completed",
            status_message="AI 回复已生成。",
        )

    def _fail_chat_run(self, run_id: str, exc: Exception) -> None:
        self.coordinator.transition(
            run_id,
            RunState.FAILED,
            stage="failed",
            status_message=str(exc),
        )
