from __future__ import annotations

from typing import Any, Dict

from quantamind.server import hands_intel


def run_today_digest_shortcut(force: bool = False) -> Dict[str, Any]:
    """Stable V2 shortcut wrapper around the existing V1 digest shortcut."""
    return hands_intel.run_daily_digest_shortcut(force=force)
