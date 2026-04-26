"""First-batch integration adapters for QuantaMind V2."""

from .filesystem import FilesystemAdapter
from .knowledge import KnowledgeAdapter, KnowledgeEntry

__all__ = [
    "FilesystemAdapter",
    "KnowledgeAdapter",
    "KnowledgeEntry",
]
