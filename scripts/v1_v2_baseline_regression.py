#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_request(
    method: str,
    url: str,
    *,
    timeout: float,
    body: Dict[str, Any] | None = None,
    headers: Dict[str, str] | None = None,
) -> Tuple[int, Dict[str, Any], str]:
    data = None
    req_headers = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(url=url, method=method.upper(), data=data, headers=req_headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                payload = {}
            return int(resp.getcode()), payload, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {}
        return int(exc.code), payload, raw


def _multipart_form(fields: Dict[str, str], files: Dict[str, Tuple[str, bytes, str]]) -> Tuple[bytes, str]:
    boundary = "----QuantaMindBoundary" + str(int(time.time() * 1000))
    lines: list[bytes] = []
    for key, value in fields.items():
        lines.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )
    for key, (filename, content, mime) in files.items():
        lines.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'
                    f"Content-Type: {mime}\r\n\r\n"
                ).encode("utf-8"),
                content,
                b"\r\n",
            ]
        )
    lines.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(lines), boundary


def _multipart_request(
    url: str,
    *,
    timeout: float,
    fields: Dict[str, str],
    files: Dict[str, Tuple[str, bytes, str]],
) -> Tuple[int, Dict[str, Any], str]:
    body, boundary = _multipart_form(fields, files)
    return _send_raw_multipart(url, timeout=timeout, body=body, boundary=boundary)


def _send_raw_multipart(url: str, *, timeout: float, body: bytes, boundary: str) -> Tuple[int, Dict[str, Any], str]:
    req = urllib.request.Request(
        url=url,
        method="POST",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            payload = json.loads(raw) if raw else {}
            return int(resp.getcode()), payload, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {}
        return int(exc.code), payload, raw


def _wait_v2_task(v2_base: str, task_id: str, timeout: float) -> Dict[str, Any]:
    deadline = time.time() + timeout
    final = {}
    while time.time() < deadline:
        code, payload, _ = _json_request("GET", f"{v2_base}/api/v2/tasks/{task_id}", timeout=timeout)
        if code != 200:
            return {"ok": False, "code": code, "error": payload or "task query failed"}
        state = str(payload.get("state", ""))
        final = payload
        if state in {"completed", "failed", "cancelled", "timeout"}:
            return {"ok": True, "task": payload}
        time.sleep(0.15)
    return {"ok": False, "error": "timeout waiting task", "task": final}


def probe(v1_base: str, v2_base: str, timeout: float) -> Dict[str, Any]:
    out: Dict[str, Any] = {"timestamp": utc_now_iso(), "v1_base": v1_base, "v2_base": v2_base, "checks": []}

    def record(name: str, ok: bool, detail: Dict[str, Any]) -> None:
        out["checks"].append({"name": name, "ok": ok, "detail": detail})

    code, payload, _ = _json_request("GET", f"{v1_base}/api/v1/status", timeout=timeout)
    record("v1_status", code == 200, {"code": code, "keys": sorted(payload.keys())[:8] if isinstance(payload, dict) else []})

    code, payload, _ = _json_request("GET", f"{v2_base}/health", timeout=timeout)
    record("v2_health", code == 200, {"code": code, "service": payload.get("service") if isinstance(payload, dict) else None})

    code, payload, _ = _json_request("GET", f"{v1_base}/api/v1/library/stats", timeout=timeout)
    record("v1_library_stats", code == 200, {"code": code, "total_files": payload.get("total_files") if isinstance(payload, dict) else None})

    code, payload, _ = _json_request("GET", f"{v2_base}/api/v2/library/stats", timeout=timeout)
    record("v2_library_stats", code == 200, {"code": code, "total_files": payload.get("total_files") if isinstance(payload, dict) else None})

    code, payload, _ = _json_request("GET", f"{v2_base}/api/v2/pipelines/templates", timeout=timeout)
    templates = payload.get("items", []) if isinstance(payload, dict) else []
    record("v2_pipeline_templates", code == 200, {"code": code, "templates": [item.get("template") for item in templates]})

    upload_content = f"phase6 baseline check @ {utc_now_iso()}\n".encode("utf-8")
    code, payload, _ = _multipart_request(
        f"{v2_base}/api/v2/library/upload",
        timeout=timeout,
        fields={"project_id": "default", "origin": "baseline_regression"},
        files={"file": ("baseline_v2.txt", upload_content, "text/plain")},
    )
    upload_ok = code == 200 and isinstance(payload, dict) and payload.get("task", {}).get("task_id")
    detail = {"code": code}
    if upload_ok:
        task_id = payload["task"]["task_id"]
        wait = _wait_v2_task(v2_base, task_id, timeout=timeout)
        detail.update({"task_id": task_id, "wait": wait})
        upload_ok = upload_ok and bool(wait.get("ok")) and wait.get("task", {}).get("state") == "completed"
    else:
        detail["payload"] = payload
    record("v2_library_upload_and_ingest", upload_ok, detail)

    code, payload, _ = _json_request(
        "POST",
        f"{v2_base}/api/v2/pipelines/execute",
        timeout=timeout,
        body={"template": "standard_daily_ops", "origin": "baseline_regression", "background": True, "force": False},
    )
    pipeline_ok = code == 200 and isinstance(payload, dict) and payload.get("task", {}).get("task_id")
    detail = {"code": code}
    if pipeline_ok:
        task_id = payload["task"]["task_id"]
        wait = _wait_v2_task(v2_base, task_id, timeout=timeout)
        detail.update({"task_id": task_id, "wait": wait})
        pipeline_ok = pipeline_ok and bool(wait.get("ok"))
    else:
        detail["payload"] = payload
    record("v2_pipeline_execute", pipeline_ok, detail)

    total = len(out["checks"])
    passed = sum(1 for item in out["checks"] if item["ok"])
    out["summary"] = {"total": total, "passed": passed, "failed": total - passed}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V1/V2 baseline regression checks.")
    parser.add_argument("--v1-base", default="http://127.0.0.1:18789", help="V1 gateway base URL")
    parser.add_argument("--v2-base", default="http://127.0.0.1:18790", help="V2 gateway base URL")
    parser.add_argument("--timeout", type=float, default=20.0, help="Request timeout seconds")
    parser.add_argument(
        "--output",
        default="docs/reports/phase6_v1_v2_baseline_latest.json",
        help="Output JSON report path",
    )
    args = parser.parse_args()

    report = probe(args.v1_base.rstrip("/"), args.v2_base.rstrip("/"), timeout=args.timeout)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = report["summary"]
    print(
        f"[phase6-baseline] total={summary['total']} passed={summary['passed']} "
        f"failed={summary['failed']} report={output}"
    )
    if summary["failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
