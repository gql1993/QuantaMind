from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class InMemoryLibraryService:
    """Phase 6 minimal library ingest service for V2."""

    def __init__(self) -> None:
        self._files: Dict[str, Dict[str, Any]] = {}
        self._blobs: Dict[str, bytes] = {}

    def create_pending_file(
        self,
        filename: str,
        content: bytes,
        *,
        project_id: str = "default",
        folder_id: str = "",
    ) -> Dict[str, Any]:
        file_id = f"F-{uuid4().hex[:8]}"
        ext = os.path.splitext(filename)[1].lower()
        now = utc_now_iso()
        record = {
            "file_id": file_id,
            "filename": filename,
            "extension": ext,
            "size_bytes": len(content),
            "project_id": project_id,
            "folder_id": folder_id,
            "uploaded_at": now,
            "parsed": False,
            "parse_result": None,
            "vector_index": None,
            "file_type": self._classify_file(ext),
            "latest_ingest_job": {
                "status": "queued",
                "stage": "uploaded",
                "attempts": 0,
                "updated_at": now,
            },
            "run_id": None,
            "task_id": None,
            "artifact_id": None,
        }
        self._files[file_id] = record
        self._blobs[file_id] = content
        return self._public(record)

    def bind_runtime(
        self,
        file_id: str,
        *,
        run_id: str | None = None,
        task_id: str | None = None,
    ) -> Dict[str, Any]:
        record = self._files.get(file_id)
        if record is None:
            raise KeyError(f"file not found: {file_id}")
        if run_id:
            record["run_id"] = run_id
        if task_id:
            record["task_id"] = task_id
        return self._public(record)

    def ingest_file(self, file_id: str, *, attempts: int = 1) -> Dict[str, Any]:
        record = self._files.get(file_id)
        if record is None:
            raise KeyError(f"file not found: {file_id}")
        blob = self._blobs.get(file_id)
        if blob is None:
            raise KeyError(f"file content not found: {file_id}")

        record["latest_ingest_job"] = {
            "status": "running",
            "stage": "uploaded",
            "attempts": attempts,
            "updated_at": utc_now_iso(),
        }
        try:
            parse_result = self._parse_content(record["filename"], blob)
            record["parse_result"] = parse_result
            record["parsed"] = True
            record["latest_ingest_job"] = {
                "status": "running",
                "stage": "parsed",
                "attempts": attempts,
                "updated_at": utc_now_iso(),
            }
            chunks = int(max(1, min(32, (record["size_bytes"] // 512) + 1)))
            vector = {"backend": "inmemory", "chunks": chunks, "indexed": chunks}
            record["vector_index"] = vector
            record["latest_ingest_job"] = {
                "status": "completed",
                "stage": "indexed",
                "attempts": attempts,
                "updated_at": utc_now_iso(),
                "payload": vector,
            }
            summary = (
                f"Library ingest completed: {record['filename']} "
                f"(type={record['file_type']}, size={record['size_bytes']} bytes)"
            )
            return {
                "file": self._public(record),
                "summary": summary,
                "parse_result": parse_result,
                "vector_index": vector,
                "status": "completed",
            }
        except Exception as exc:  # noqa: BLE001
            record["parsed"] = False
            record["parse_result"] = {"error": str(exc)}
            record["vector_index"] = {"error": str(exc)}
            record["latest_ingest_job"] = {
                "status": "failed",
                "stage": "parsed",
                "attempts": attempts,
                "updated_at": utc_now_iso(),
                "error_message": str(exc),
            }
            raise

    def attach_artifact(self, file_id: str, artifact_id: str) -> Dict[str, Any]:
        record = self._files.get(file_id)
        if record is None:
            raise KeyError(f"file not found: {file_id}")
        record["artifact_id"] = artifact_id
        return self._public(record)

    def get_file(self, file_id: str) -> Dict[str, Any] | None:
        record = self._files.get(file_id)
        if record is None:
            return None
        return self._public(record)

    def list_files(self, project_id: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = list(self._files.values())
        if project_id:
            rows = [row for row in rows if row.get("project_id") == project_id]
        if search:
            q = search.lower()
            rows = [
                row
                for row in rows
                if q in str(row.get("filename", "")).lower()
                or q in str(row.get("file_type", "")).lower()
                or q in str(row.get("extension", "")).lower()
            ]
        rows.sort(key=lambda row: row.get("uploaded_at", ""), reverse=True)
        return [self._public(row) for row in rows]

    def get_stats(self) -> Dict[str, Any]:
        rows = list(self._files.values())
        by_type: Dict[str, int] = {}
        for row in rows:
            file_type = row.get("file_type", "其他")
            by_type[file_type] = by_type.get(file_type, 0) + 1
        return {
            "total_files": len(rows),
            "total_size_bytes": sum(int(row.get("size_bytes", 0) or 0) for row in rows),
            "parsed": sum(1 for row in rows if row.get("parsed")),
            "by_type": by_type,
        }

    def _public(self, row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "file_id": row.get("file_id"),
            "filename": row.get("filename"),
            "extension": row.get("extension"),
            "size_bytes": row.get("size_bytes"),
            "project_id": row.get("project_id"),
            "folder_id": row.get("folder_id"),
            "uploaded_at": row.get("uploaded_at"),
            "parsed": row.get("parsed"),
            "parse_result": row.get("parse_result"),
            "vector_index": row.get("vector_index"),
            "file_type": row.get("file_type"),
            "latest_ingest_job": row.get("latest_ingest_job"),
            "run_id": row.get("run_id"),
            "task_id": row.get("task_id"),
            "artifact_id": row.get("artifact_id"),
        }

    def _classify_file(self, ext: str) -> str:
        mapping = {
            ".docx": "设计文档",
            ".doc": "设计文档",
            ".pdf": "图纸/文档",
            ".pptx": "演示文稿",
            ".ppt": "演示文稿",
            ".xlsx": "参数表格",
            ".xls": "参数表格",
            ".csv": "数据文件",
            ".gds": "版图文件",
            ".oas": "版图文件",
            ".json": "数据文件",
            ".py": "Python 代码",
            ".ipynb": "Jupyter 笔记本",
            ".zip": "压缩包",
            ".7z": "压缩包",
            ".tar": "压缩包",
            ".gz": "压缩包",
        }
        return mapping.get(ext, "其他")

    def _parse_content(self, filename: str, blob: bytes) -> Dict[str, Any]:
        ext = os.path.splitext(filename)[1].lower()
        if ext in {".txt", ".md", ".py", ".json", ".csv", ".docx", ".pdf", ".pptx", ".ipynb"}:
            preview = blob[:2000].decode("utf-8", errors="replace")
            line_count = preview.count("\n") + 1 if preview else 0
            return {"type": ext.lstrip(".") or "text", "line_count": line_count, "text_preview": preview}
        return {"type": ext.lstrip(".") or "binary", "size_bytes": len(blob)}
