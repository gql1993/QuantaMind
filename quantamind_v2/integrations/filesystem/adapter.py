from __future__ import annotations

from pathlib import Path
from typing import Any


class FilesystemAdapter:
    """Readonly filesystem adapter scoped to a workspace root."""

    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir).resolve()

    def list_files(self, relative_path: str = ".", *, limit: int = 50) -> list[dict[str, Any]]:
        target = self._resolve(relative_path)
        if not target.exists() or not target.is_dir():
            raise FileNotFoundError(f"directory not found: {relative_path}")
        items: list[dict[str, Any]] = []
        for child in sorted(target.iterdir(), key=lambda item: item.name.lower()):
            stat = child.stat()
            items.append(
                {
                    "name": child.name,
                    "relative_path": str(child.relative_to(self.root_dir)).replace("\\", "/"),
                    "is_dir": child.is_dir(),
                    "size": stat.st_size,
                }
            )
            if len(items) >= max(limit, 1):
                break
        return items

    def read_text(self, relative_path: str, *, max_chars: int = 4000) -> str:
        target = self._resolve(relative_path)
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"file not found: {relative_path}")
        text = target.read_text(encoding="utf-8", errors="replace")
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3] + "..."

    def _resolve(self, relative_path: str) -> Path:
        target = (self.root_dir / relative_path).resolve()
        if not str(target).startswith(str(self.root_dir)):
            raise PermissionError("path escapes workspace root")
        return target
