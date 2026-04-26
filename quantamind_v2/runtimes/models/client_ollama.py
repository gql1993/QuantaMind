from __future__ import annotations

import json
import urllib.error
import urllib.request

from quantamind_v2.runtimes.models.providers import ModelProvider, ModelRequest, ModelResponse


def build_ollama_provider(
    *,
    base_url: str = "http://127.0.0.1:11434",
    timeout_seconds: float = 20.0,
) -> ModelProvider:
    endpoint = base_url.rstrip("/") + "/api/generate"

    def _provider(request: ModelRequest) -> ModelResponse:
        model = request.model or "qwen2.5:7b"
        prompt = request.prompt
        if not prompt and request.messages:
            prompt = request.messages[-1].content
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": request.temperature},
        }
        if request.max_tokens is not None:
            payload["options"]["num_predict"] = request.max_tokens
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"ollama http {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"ollama network error: {exc}") from exc
        data = json.loads(raw) if raw else {}
        return ModelResponse(
            provider="ollama",
            model=data.get("model") or model,
            text=str(data.get("response", "")),
            usage={
                "prompt_eval_count": data.get("prompt_eval_count"),
                "eval_count": data.get("eval_count"),
            },
            raw=data,
        )

    return _provider
