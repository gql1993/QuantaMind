from __future__ import annotations

from typing import Any, Dict, Optional

from quantamind.server import arxiv_intel


def run_daily_digest(force: bool = False) -> Dict[str, Any]:
    return arxiv_intel.run_daily_digest(force=force)


def run_daily_digest_shortcut(force: bool = False) -> Dict[str, Any]:
    return arxiv_intel.run_daily_digest_shortcut(force=force)


def list_recent_papers(limit: int = 20, topic: Optional[str] = None) -> Dict[str, Any]:
    records = arxiv_intel.list_recent_papers(limit=limit, topic=topic)
    return {"count": len(records), "records": records}


def list_reports(limit: int = 10) -> Dict[str, Any]:
    records = arxiv_intel.list_reports(limit=limit)
    return {"count": len(records), "records": records}


def capabilities() -> Dict[str, Any]:
    return {
        "service": "arxiv_intel",
        "topics": [topic["id"] for topic in arxiv_intel.TOPIC_QUERIES],
        "features": [
            "daily_digest",
            "daily_digest_shortcut",
            "arxiv_search",
            "structured_summary",
            "knowledge_ingestion",
            "feishu_delivery",
        ],
    }
