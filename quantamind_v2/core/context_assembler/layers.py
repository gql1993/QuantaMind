from __future__ import annotations

from typing import Dict, Optional

from quantamind_v2.contracts.context import ContextLayer, ContextLayerType


def make_context_layer(
    layer_type: ContextLayerType,
    content: str,
    metadata: Optional[Dict[str, str]] = None,
) -> ContextLayer:
    return ContextLayer(
        layer_type=layer_type,
        content=content.strip(),
        metadata=metadata or {},
    )


def system_layer(content: str) -> ContextLayer:
    return make_context_layer(ContextLayerType.SYSTEM, content)


def agent_identity_layer(agent_name: str, content: str) -> ContextLayer:
    return make_context_layer(
        ContextLayerType.AGENT_IDENTITY,
        content,
        metadata={"agent_name": agent_name},
    )


def project_memory_layer(project_id: str, content: str) -> ContextLayer:
    return make_context_layer(
        ContextLayerType.PROJECT_MEMORY,
        content,
        metadata={"project_id": project_id},
    )


def recent_conversation_layer(content: str) -> ContextLayer:
    return make_context_layer(ContextLayerType.RECENT_CONVERSATION, content)
