from quantamind_v2.artifacts import InMemoryArtifactStore, render_artifact_text
from quantamind_v2.artifacts.renderers import register_renderer, unregister_renderer
from quantamind_v2.artifacts.renderers.loader import load_and_register_renderers
from quantamind_v2.contracts.artifact import ArtifactRecord, ArtifactType


def test_artifact_store_put_and_get():
    store = InMemoryArtifactStore()
    artifact = ArtifactRecord(
        artifact_id="artifact-001",
        run_id="run-001",
        artifact_type=ArtifactType.INTEL_REPORT,
        title="Intel Report",
        summary="today digest",
        payload={"papers": 12},
    )
    store.put(artifact)

    assert store.get("artifact-001") is artifact
    assert store.list_for_run("run-001") == [artifact]


def test_render_artifact_text_returns_view():
    artifact = ArtifactRecord(
        artifact_id="artifact-002",
        run_id="run-xyz",
        artifact_type=ArtifactType.DB_HEALTH_REPORT,
        title="Database Health",
        summary="all systems normal",
        payload={"design_postgres": "ok", "pgvector": "ok"},
    )
    view = render_artifact_text(artifact)

    assert view.artifact_id == "artifact-002"
    assert view.render_type.value == "text"
    assert "Database Health" in view.content
    assert "design_postgres" in view.content


def test_render_coordination_report_has_structured_sections():
    artifact = ArtifactRecord(
        artifact_id="artifact-003",
        run_id="run-coord-1",
        artifact_type=ArtifactType.COORDINATION_REPORT,
        title="coordination merged result",
        summary="agent_a and agent_b finished",
        payload={
            "route_result": {"mode": "multi_agent_plan", "reason": "contains collaboration intent"},
            "plan": {"steps": [{"owner_agent": "design_engineer"}, {"owner_agent": "process_engineer"}]},
            "merged": {
                "count": 2,
                "summary": "design and process both completed",
                "outputs": [
                    {"owner_agent": "design_engineer", "summary": "design step done"},
                    {"owner_agent": "process_engineer", "summary": "process step done"},
                ],
            },
        },
    )
    view = render_artifact_text(artifact)

    assert view.artifact_id == "artifact-003"
    assert "## Coordination" in view.content
    assert "mode: multi_agent_plan" in view.content
    assert "## Child Outputs" in view.content
    assert "[design_engineer] design step done" in view.content


def test_renderer_registry_supports_dynamic_override():
    artifact = ArtifactRecord(
        artifact_id="artifact-004",
        run_id="run-override-1",
        artifact_type=ArtifactType.DB_HEALTH_REPORT,
        title="Database Health",
        summary="healthy",
        payload={"ok": True},
    )

    def _custom_renderer(_: ArtifactRecord) -> str:
        return "# custom db renderer"

    register_renderer(ArtifactType.DB_HEALTH_REPORT, _custom_renderer, replace=True)
    try:
        view = render_artifact_text(artifact)
        assert "# custom db renderer" in view.content
    finally:
        unregister_renderer(ArtifactType.DB_HEALTH_REPORT)


def test_renderer_registry_loads_from_config_file(tmp_path):
    config_path = tmp_path / "renderer_registry.json"
    config_path.write_text(
        """
{
  "renderers": {
    "db_health_report": "quantamind_v2.artifacts.renderers.generic:render_generic_report"
  }
}
""".strip(),
        encoding="utf-8",
    )
    report = load_and_register_renderers(config_path)
    assert report["loaded"] is True
    assert any(item["artifact_type"] == "db_health_report" for item in report["registered"])

    artifact = ArtifactRecord(
        artifact_id="artifact-005",
        run_id="run-db-1",
        artifact_type=ArtifactType.DB_HEALTH_REPORT,
        title="db report",
        summary="ok",
        payload={"db": "ok"},
    )
    view = render_artifact_text(artifact)
    assert "db report" in view.content
    unregister_renderer(ArtifactType.DB_HEALTH_REPORT)
