from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from quantamind_v2.runtimes.models.providers import ModelProvider, ModelRequest, ModelResponse


def build_openai_compat_provider(
    *,
    base_url: str,
    api_key: str | None = None,
    timeout_seconds: float = 20.0,
) -> ModelProvider:
    endpoint = base_url.rstrip("/") + "/chat/completions"

    def _provider(request: ModelRequest) -> ModelResponse:
        model = request.model or "gpt-4o-mini"
        messages = [
            {"role": item.role, "content": item.content}
            for item in request.messages
            if item.content.strip()
        ]
        if not messages:
            messages = [{"role": "user", "content": request.prompt}]
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        raw_body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        req = urllib.request.Request(endpoint, data=raw_body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"openai_compat http {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"openai_compat network error: {exc}") from exc
        data = json.loads(raw) if raw else {}
        choices = data.get("choices", [])
        message = {}
        if choices:
            message = choices[0].get("message", {}) or {}
        content = str(message.get("content", "")).strip()
        return ModelResponse(
            provider="openai_compat",
            model=data.get("model") or model,
            text=content,
            usage=data.get("usage") or {},
            raw=data,
        )

    return _provider
