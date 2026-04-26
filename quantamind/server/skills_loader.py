# QuantumSkills — YAML+Markdown 技能加载

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from quantamind import config


def _parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """解析 ---yaml--- ... --- 与正文"""
    if not content.strip().startswith("---"):
        return {}, content
    parts = re.split(r"^---\s*$", content.strip(), 2, flags=re.MULTILINE)
    if len(parts) < 3:
        return {}, content
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except Exception:
        meta = {}
    return meta, parts[2].strip()


def load_skill(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    meta["_path"] = str(path)
    meta["_body"] = body
    return meta


def _skill_dirs() -> List[Path]:
    """内置技能目录（包内）+ 用户技能目录"""
    pkg_skills = Path(__file__).resolve().parent.parent / "skills"
    dirs = [config.SKILLS_DIR]
    if pkg_skills.is_dir():
        dirs.insert(0, pkg_skills)
    return dirs


def list_skills() -> List[Dict[str, Any]]:
    config.ensure_dirs()
    skills = []
    seen = set()
    for base in _skill_dirs():
        if not base.exists():
            continue
        for f in base.rglob("*.md"):
            try:
                s = load_skill(f)
                sid = s.get("name") or f.stem
                if sid in seen:
                    continue
                seen.add(sid)
                s["_id"] = sid
                skills.append(s)
            except Exception:
                continue
    return skills


def get_skill_by_trigger(trigger_text: str) -> Optional[Dict[str, Any]]:
    """按触发词匹配技能（简单包含匹配）"""
    for s in list_skills():
        trigger = s.get("trigger") or s.get("triggers") or ""
        if isinstance(trigger, list):
            trigger = "|".join(trigger)
        if trigger and trigger_text and trigger.lower() in trigger_text.lower():
            return s
    return None
