"""
Gateway API 契约测试（与详细设计 §11、ROADMAP 阶段 0 对齐）
由测试工程师智能体产出：健康检查、会话、任务列表与任务详情。
"""
import pytest
from fastapi.testclient import TestClient

from quantamind.server.gateway import app
from quantamind.server import arxiv_intel

client = TestClient(app)


def test_health():
    """GET /health 返回 ok"""
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert "QuantaMind" in data.get("service", "")


def test_sessions_create():
    """POST /api/v1/sessions 创建会话，返回 session_id"""
    r = client.post("/api/v1/sessions", json={})
    assert r.status_code == 200
    data = r.json()
    assert "session_id" in data
    assert "created_at" in data


def test_tasks_list():
    """GET /api/v1/tasks 返回任务列表，结构符合 TaskInfo"""
    r = client.get("/api/v1/tasks")
    assert r.status_code == 200
    data = r.json()
    assert "tasks" in data
    tasks = data["tasks"]
    assert isinstance(tasks, list)
    for t in tasks:
        assert "task_id" in t
        assert "status" in t
        assert t["status"] in ("pending", "running", "completed", "failed")


def test_tasks_list_filter_pending_approval():
    """GET /api/v1/tasks?filter=pending_approval 仅返回需审批任务"""
    r = client.get("/api/v1/tasks", params={"filter": "pending_approval"})
    assert r.status_code == 200
    data = r.json()
    for t in data["tasks"]:
        assert t.get("needs_approval") is True


def test_tasks_list_filter_completed():
    """GET /api/v1/tasks?filter=completed 仅返回已完成任务"""
    r = client.get("/api/v1/tasks", params={"filter": "completed"})
    assert r.status_code == 200
    data = r.json()
    for t in data["tasks"]:
        assert t["status"] == "completed"


def test_task_detail():
    """GET /api/v1/tasks/{id} 返回单任务详情"""
    r = client.get("/api/v1/tasks/t1")
    assert r.status_code == 200
    data = r.json()
    assert data["task_id"] == "t1"
    assert "status" in data
    assert "title" in data or "task_type" in data


def test_task_detail_404():
    """GET /api/v1/tasks/unknown 返回 404"""
    r = client.get("/api/v1/tasks/nonexistent-id-xxx")
    assert r.status_code == 404


def test_status_dashboard():
    """GET /api/v1/status 返回运转看板汇总"""
    r = client.get("/api/v1/status")
    assert r.status_code == 200
    data = r.json()
    assert "gateway" in data
    assert data["gateway"].get("status") == "ok"
    assert "sessions_count" in data
    assert "tasks" in data
    assert "heartbeat" in data
    assert "platforms" in data
    assert "qeda" in data["platforms"]
    assert "mes" in data["platforms"]


def test_list_taxonomy_pending_updates_api(monkeypatch):
    monkeypatch.setattr(
        arxiv_intel,
        "list_taxonomy_pending_updates",
        lambda topic_id=None: [{"update_id": "taxupd_1", "topic_id": topic_id or "measurement_control"}],
    )
    r = client.get("/api/v1/intel/taxonomy/pending-updates", params={"topic": "measurement_control"})
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert data["updates"][0]["update_id"] == "taxupd_1"


def test_approve_taxonomy_pending_update_api(monkeypatch):
    monkeypatch.setattr(
        arxiv_intel,
        "approve_taxonomy_pending_update",
        lambda update_id, reviewer=None, note=None: {"status": "approved", "update_id": update_id, "reviewer": reviewer},
    )
    r = client.post("/api/v1/intel/taxonomy/pending-updates/taxupd_1/approve", json={"reviewer": "tester"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "approved"
    assert data["update_id"] == "taxupd_1"
