from datetime import datetime, timezone

from quantamind.server import heartbeat


def test_should_run_startup_intel_catchup_false_before_schedule(monkeypatch) -> None:
    now = datetime.fromisoformat("2026-03-31T08:30:00+08:00")
    monkeypatch.setattr(heartbeat.config, "INTEL_SCHEDULE_HOUR", 9)
    monkeypatch.setattr(heartbeat.config, "INTEL_SCHEDULE_MINUTE", 0)
    monkeypatch.setattr(heartbeat.state_store, "get_intel_report", lambda _report_id: None)
    monkeypatch.setattr(heartbeat, "_last_intel_report_id", None)
    assert heartbeat._should_run_startup_intel_catchup(now) is False


def test_should_run_startup_intel_catchup_true_after_schedule_without_report(monkeypatch) -> None:
    now = datetime.fromisoformat("2026-03-31T10:15:00+08:00")
    monkeypatch.setattr(heartbeat.config, "INTEL_SCHEDULE_HOUR", 9)
    monkeypatch.setattr(heartbeat.config, "INTEL_SCHEDULE_MINUTE", 0)
    monkeypatch.setattr(heartbeat.state_store, "get_intel_report", lambda _report_id: None)
    monkeypatch.setattr(heartbeat, "_last_intel_report_id", None)
    assert heartbeat._should_run_startup_intel_catchup(now) is True


def test_should_run_startup_intel_catchup_false_when_report_exists(monkeypatch) -> None:
    now = datetime.fromisoformat("2026-03-31T10:15:00+08:00")
    monkeypatch.setattr(heartbeat.config, "INTEL_SCHEDULE_HOUR", 9)
    monkeypatch.setattr(heartbeat.config, "INTEL_SCHEDULE_MINUTE", 0)
    monkeypatch.setattr(heartbeat.state_store, "get_intel_report", lambda _report_id: {"report_id": "intel-2026-03-31"})
    monkeypatch.setattr(heartbeat, "_last_intel_report_id", None)
    assert heartbeat._should_run_startup_intel_catchup(now) is False


def test_should_run_startup_intel_catchup_false_when_already_sent_in_memory(monkeypatch) -> None:
    now = datetime.fromisoformat("2026-03-31T10:15:00+08:00")
    monkeypatch.setattr(heartbeat.config, "INTEL_SCHEDULE_HOUR", 9)
    monkeypatch.setattr(heartbeat.config, "INTEL_SCHEDULE_MINUTE", 0)
    monkeypatch.setattr(heartbeat.state_store, "get_intel_report", lambda _report_id: None)
    monkeypatch.setattr(heartbeat, "_last_intel_report_id", "intel-2026-03-31")
    assert heartbeat._should_run_startup_intel_catchup(now) is False
