# QuantumMemory — 项目记忆（Markdown 文件，OpenClaw 风格）

from datetime import datetime
from pathlib import Path
from typing import Optional

from quantamind import config


def get_project_path(project_id: Optional[str] = None) -> Path:
    config.ensure_dirs()
    if project_id:
        return config.PROJECTS_DIR / f"{project_id}.md"
    return config.PROJECTS_DIR / "default.md"


def read_memory(project_id: Optional[str] = None) -> str:
    p = get_project_path(project_id)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def append_memory(content: str, project_id: Optional[str] = None) -> None:
    config.ensure_dirs()
    p = get_project_path(project_id)
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    block = f"\n\n---\n[{ts}]\n{content}\n"
    p.write_text((p.read_text(encoding="utf-8") if p.exists() else "") + block, encoding="utf-8")
