from __future__ import annotations

import asyncio
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from quantamind_v2.contracts.approval import ApprovalRequest, ApprovalStatus, utc_now_iso
from quantamind_v2.contracts.artifact import ArtifactRecord, ArtifactType
from quantamind_v2.contracts.run import RunState, RunType
from quantamind_v2.core.coordination import (
    CoordinationConflictStrategy,
    CoordinationMode,
    decide_coordination_conflict,
    detect_active_coordination_conflict,
)
from quantamind_v2.core.gateway.deps import GatewayDeps, infer_artifact_type
from quantamind_v2.core.gateway.schemas import (
    ApprovalCreateRequest,
    CoordinationConflictPolicyUpdateRequest,
    CoordinationCutoverControlUpdateRequest,
    ApprovalResolveRequest,
    CoordinationRunRequest,
    PipelineExecuteRequest,
    ShortcutRunRequest,
    ShortcutTaskRequest,
)


def build_workflows_router(deps: GatewayDeps) -> APIRouter:
    router = APIRouter()

    def _resolve_conflict_strategy(
        *,
        profile_id: str,
        raw_value: str | None,
    ) -> tuple[CoordinationConflictStrategy, str]:
        policy_override = deps.coordination_policy.get_strategy(profile_id)
        selected = raw_value or policy_override or deps.settings.coordination.default_conflict_strategy
        source = "request" if raw_value else ("policy_override" if policy_override else "settings_default")
        try:
            return CoordinationConflictStrategy(str(selected).strip().lower()), source
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"invalid conflict_strategy: {selected}") from exc

    def _append_coordination_audit(
        *,
        event_type: str,
        profile_id: str,
        strategy: str,
        outcome: str,
        reason: str,
        run_id: str | None = None,
        conflict_run_id: str | None = None,
        route_mode: str | None = None,
        payload: dict | None = None,
    ) -> None:
        deps.coordination_audit.append(
            event_type=event_type,
            profile_id=profile_id,
            strategy=strategy,
            outcome=outcome,
            reason=reason,
            run_id=run_id,
            conflict_run_id=conflict_run_id,
            route_mode=route_mode,
            payload=dict(payload or {}),
        )

    @router.get("/api/v2/shortcuts")
    async def list_shortcuts() -> dict:
        return {
            "items": [
                {
                    "name": shortcut.name,
                    "description": shortcut.description,
                    "triggers": list(shortcut.triggers),
                    "run_type": shortcut.run_type.value,
                    "owner_agent": shortcut.owner_agent,
                }
                for shortcut in deps.shortcuts.list()
            ]
        }

    def _execute_shortcut(
        shortcut_name: str,
        force: bool,
        origin: str,
        *,
        parent_run_id: str | None = None,
        raise_on_failure: bool = False,
    ):
        shortcut = deps.shortcuts.get(shortcut_name)
        if shortcut is None:
            raise ValueError(f"shortcut not found: {shortcut_name}")

        run = deps.coordinator.create_run(
            shortcut.run_type,
            origin=origin,
            parent_run_id=parent_run_id,
            owner_agent=shortcut.owner_agent,
            status_message=f"Shortcut `{shortcut.name}` queued.",
        )
        deps.coordinator.transition(
            run.run_id,
            RunState.RUNNING,
            stage="shortcut_running",
            status_message=f"Running shortcut `{shortcut.name}`...",
        )
        try:
            result = shortcut.handler(force)
            summary = result.get("summary") or f"Shortcut `{shortcut.name}` completed."
            report = result.get("report") or {}
            metadata = {"result": result}
            artifact_id = report.get("report_id") or f"artifact-{uuid4().hex[:12]}"
            artifact = ArtifactRecord(
                artifact_id=artifact_id,
                run_id=run.run_id,
                artifact_type=ArtifactType(infer_artifact_type(shortcut.name)),
                title=f"{shortcut.name} result",
                summary=summary,
                payload={
                    "shortcut": shortcut.name,
                    "status": result.get("status", "ok"),
                    "report": report,
                    "result": result,
                },
            )
            deps.artifacts.put(artifact)
            deps.coordinator.attach_artifact(run.run_id, artifact.artifact_id)
            metadata["artifact_id"] = artifact.artifact_id
            if report.get("report_id"):
                metadata["report_id"] = report["report_id"]
            run = deps.coordinator.update_run(
                run.run_id,
                stage="shortcut_completed",
                status_message=summary,
                metadata=metadata,
            )
            run = deps.coordinator.transition(
                run.run_id,
                RunState.COMPLETED,
                stage=run.stage,
                status_message=run.status_message,
            )
        except Exception as exc:  # noqa: BLE001
            run = deps.coordinator.update_run(
                run.run_id,
                stage="shortcut_failed",
                status_message=f"Shortcut `{shortcut.name}` failed: {exc}",
                metadata={"error": str(exc)},
            )
            run = deps.coordinator.transition(
                run.run_id,
                RunState.FAILED,
                stage=run.stage,
                status_message=run.status_message,
            )
            if raise_on_failure:
                raise RuntimeError(run.status_message) from exc
        return run

    @router.post("/api/v2/shortcuts/{shortcut_name}")
    async def run_shortcut(shortcut_name: str, body: ShortcutRunRequest) -> dict:
        try:
            run = await asyncio.to_thread(_execute_shortcut, shortcut_name, body.force, body.origin)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"run": run.model_dump()}

    @router.post("/api/v2/tasks/shortcuts/{shortcut_name}")
    async def run_shortcut_in_background(shortcut_name: str, body: ShortcutTaskRequest) -> dict:
        if deps.shortcuts.get(shortcut_name) is None:
            raise HTTPException(status_code=404, detail=f"shortcut not found: {shortcut_name}")
        task = deps.tasks.submit(
            task_name=f"shortcut:{shortcut_name}",
            handler=_execute_shortcut,
            shortcut_name=shortcut_name,
            force=body.force,
            origin=body.origin,
            raise_on_failure=True,
            budget_seconds=body.budget_seconds,
            max_retries=body.max_retries,
        )
        return {"task": task.model_dump()}

    @router.get("/api/v2/library/files")
    async def list_library_files(project_id: str | None = Query(default=None), search: str | None = Query(default=None)) -> dict:
        files = deps.library.list_files(project_id=project_id, search=search)
        return {"files": files, "count": len(files)}

    @router.get("/api/v2/library/files/{file_id}")
    async def get_library_file(file_id: str) -> dict:
        record = deps.library.get_file(file_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"file not found: {file_id}")
        return record

    @router.get("/api/v2/library/stats")
    async def get_library_stats() -> dict:
        return deps.library.get_stats()

    @router.post("/api/v2/library/upload")
    async def upload_library_file(
        file: UploadFile = File(...),
        project_id: str = Form("default"),
        folder_id: str = Form(""),
        origin: str = Form("library_upload"),
    ) -> dict:
        content = await file.read()
        if not file.filename:
            raise HTTPException(status_code=400, detail="filename is required")
        record = deps.library.create_pending_file(file.filename, content, project_id=project_id, folder_id=folder_id)
        run = deps.coordinator.create_run(
            RunType.IMPORT,
            origin=origin,
            owner_agent="knowledge_engineer",
            status_message=f"Library ingest queued: {record['filename']}",
        )
        run = deps.coordinator.transition(
            run.run_id,
            RunState.RUNNING,
            stage="import_queued",
            status_message=f"Library ingest queued: {record['filename']}",
        )

        def _execute_library_ingest(file_id: str, ingest_run_id: str) -> dict:
            ingest = deps.library.ingest_file(file_id, attempts=1)
            current_file = ingest["file"]
            artifact = ArtifactRecord(
                artifact_id=f"artifact-{uuid4().hex[:12]}",
                run_id=ingest_run_id,
                artifact_type=ArtifactType.LIBRARY_INGEST_REPORT,
                title=f"library ingest: {current_file['filename']}",
                summary=ingest["summary"],
                payload={
                    "status": ingest.get("status", "completed"),
                    "file": current_file,
                    "parse_result": ingest.get("parse_result"),
                    "vector_index": ingest.get("vector_index"),
                },
            )
            deps.artifacts.put(artifact)
            deps.library.attach_artifact(file_id, artifact.artifact_id)
            deps.coordinator.attach_artifact(ingest_run_id, artifact.artifact_id)
            deps.coordinator.update_run(
                ingest_run_id,
                stage="import_indexed",
                status_message=ingest["summary"],
                metadata={
                    "library_file_id": file_id,
                    "library_artifact_id": artifact.artifact_id,
                },
            )
            return {
                "file_id": file_id,
                "artifact_id": artifact.artifact_id,
                "summary": ingest["summary"],
            }

        task = deps.tasks.submit(
            task_name=f"library_ingest:{record['filename']}",
            handler=_execute_library_ingest,
            run_id=run.run_id,
            file_id=record["file_id"],
            ingest_run_id=run.run_id,
        )
        deps.library.bind_runtime(record["file_id"], run_id=run.run_id, task_id=task.task_id)
        return {"file": deps.library.get_file(record["file_id"]), "run": run.model_dump(), "task": task.model_dump()}

    @router.get("/api/v2/approvals")
    async def list_approvals(status: str | None = Query(default=None)) -> dict:
        parsed_status = None
        if status:
            try:
                parsed_status = ApprovalStatus(status.strip().lower())
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=f"invalid approval status: {status}") from exc
        items = deps.approvals.list(parsed_status)
        items = sorted(items, key=lambda item: item.created_at, reverse=True)
        return {"items": [item.model_dump() for item in items]}

    @router.post("/api/v2/approvals")
    async def create_approval(body: ApprovalCreateRequest) -> dict:
        try:
            run = deps.coordinator.get_run(body.run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        approval = ApprovalRequest(
            approval_id=f"approval-{uuid4().hex[:12]}",
            run_id=body.run_id,
            approval_type=body.approval_type,
            summary=body.summary,
            details=dict(body.details or {}),
        )
        deps.approvals.put(approval)
        deps.coordinator.update_run(
            run.run_id,
            stage="approval_pending",
            status_message=f"Approval pending: {approval.summary}",
            metadata={"pending_approval_id": approval.approval_id},
        )
        deps.coordinator.append_event(
            run.run_id,
            "approval_requested",
            {
                "approval_id": approval.approval_id,
                "approval_type": approval.approval_type.value,
                "summary": approval.summary,
            },
        )
        return {"approval": approval.model_dump()}

    @router.get("/api/v2/approvals/{approval_id}")
    async def get_approval(approval_id: str) -> dict:
        approval = deps.approvals.get(approval_id)
        if approval is None:
            raise HTTPException(status_code=404, detail=f"approval not found: {approval_id}")
        return approval.model_dump()

    def _resolve_approval(approval_id: str, target: ApprovalStatus, reviewer: str, comment: str) -> ApprovalRequest:
        approval = deps.approvals.get(approval_id)
        if approval is None:
            raise HTTPException(status_code=404, detail=f"approval not found: {approval_id}")
        if approval.status != ApprovalStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"approval already resolved: {approval.status.value}")
        approval.status = target
        approval.reviewer = reviewer
        approval.resolved_at = utc_now_iso()
        if comment:
            approval.details = dict(approval.details or {})
            approval.details["review_comment"] = comment
        deps.approvals.put(approval)
        outcome = "approved" if target == ApprovalStatus.APPROVED else "rejected"
        deps.coordinator.update_run(
            approval.run_id,
            stage=f"approval_{outcome}",
            status_message=f"Approval {outcome}: {approval.summary}",
            metadata={"pending_approval_id": None, "last_approval_id": approval.approval_id},
        )
        deps.coordinator.append_event(
            approval.run_id,
            f"approval_{outcome}",
            {
                "approval_id": approval.approval_id,
                "reviewer": reviewer,
                "comment": comment,
            },
        )
        return approval

    @router.post("/api/v2/approvals/{approval_id}/approve")
    async def approve_request(approval_id: str, body: ApprovalResolveRequest) -> dict:
        approval = _resolve_approval(approval_id, ApprovalStatus.APPROVED, body.reviewer, body.comment)
        return {"approval": approval.model_dump()}

    @router.post("/api/v2/approvals/{approval_id}/reject")
    async def reject_request(approval_id: str, body: ApprovalResolveRequest) -> dict:
        approval = _resolve_approval(approval_id, ApprovalStatus.REJECTED, body.reviewer, body.comment)
        return {"approval": approval.model_dump()}

    @router.get("/api/v2/pipelines/templates")
    async def list_pipeline_templates() -> dict:
        return {
            "items": [
                {
                    "template": template,
                    "name": payload["name"],
                    "description": payload["description"],
                    "shortcuts": payload["shortcuts"],
                }
                for template, payload in deps.pipeline_templates.items()
            ]
        }

    def _execute_pipeline_run(*, pipeline_run_id: str, template: str, origin: str, force: bool) -> dict:
        spec = deps.pipeline_templates.get(template)
        if spec is None:
            raise ValueError(f"pipeline template not found: {template}")
        shortcuts_list = list(spec["shortcuts"])
        for name in shortcuts_list:
            if deps.shortcuts.get(name) is None:
                raise ValueError(f"shortcut not found for template `{template}`: {name}")
        deps.coordinator.update_run(
            pipeline_run_id,
            stage="pipeline_running",
            status_message=f"Pipeline `{template}` running with {len(shortcuts_list)} shortcuts.",
            metadata={"pipeline_template": template, "pipeline_shortcuts": shortcuts_list},
        )
        deps.coordinator.append_event(
            pipeline_run_id,
            "pipeline_started",
            {"template": template, "shortcuts": shortcuts_list},
        )
        child_runs = []
        failed_runs = []
        for name in shortcuts_list:
            child = _execute_shortcut(
                name,
                force,
                f"{origin}:pipeline:{template}",
                parent_run_id=pipeline_run_id,
                raise_on_failure=False,
            )
            child_runs.append(child)
            if child.state == RunState.FAILED:
                failed_runs.append(child)
        summary = (
            f"Pipeline `{template}` finished. "
            f"total={len(child_runs)}, failed={len(failed_runs)}, succeeded={len(child_runs) - len(failed_runs)}"
        )
        report = {
            "template": template,
            "shortcuts": shortcuts_list,
            "total": len(child_runs),
            "failed": len(failed_runs),
            "succeeded": len(child_runs) - len(failed_runs),
            "child_runs": [run.model_dump() for run in child_runs],
        }
        artifact = ArtifactRecord(
            artifact_id=f"artifact-{uuid4().hex[:12]}",
            run_id=pipeline_run_id,
            artifact_type=ArtifactType.PIPELINE_REPORT,
            title=f"pipeline report: {template}",
            summary=summary,
            payload=report,
        )
        deps.artifacts.put(artifact)
        deps.coordinator.attach_artifact(pipeline_run_id, artifact.artifact_id)
        deps.coordinator.update_run(
            pipeline_run_id,
            stage="pipeline_executed",
            status_message=summary,
            metadata={
                "pipeline_template": template,
                "pipeline_child_run_ids": [run.run_id for run in child_runs],
                "pipeline_failed_count": len(failed_runs),
                "pipeline_artifact_id": artifact.artifact_id,
            },
        )
        deps.coordinator.append_event(
            pipeline_run_id,
            "pipeline_finished",
            {"template": template, "total": len(child_runs), "failed": len(failed_runs)},
        )
        if failed_runs:
            raise RuntimeError(summary)
        return {"summary": summary, "artifact_id": artifact.artifact_id, "child_run_ids": [run.run_id for run in child_runs]}

    @router.post("/api/v2/pipelines/execute")
    async def execute_pipeline(body: PipelineExecuteRequest) -> dict:
        spec = deps.pipeline_templates.get(body.template)
        if spec is None:
            raise HTTPException(status_code=404, detail=f"pipeline template not found: {body.template}")
        run = deps.coordinator.create_run(
            RunType.PIPELINE,
            origin=body.origin,
            owner_agent="project_manager",
            status_message=f"Pipeline `{body.template}` queued.",
        )
        run = deps.coordinator.transition(
            run.run_id,
            RunState.RUNNING,
            stage="pipeline_queued",
            status_message=f"Pipeline `{body.template}` queued.",
        )
        if body.background:
            task = deps.tasks.submit(
                task_name=f"pipeline:{body.template}",
                handler=_execute_pipeline_run,
                run_id=run.run_id,
                pipeline_run_id=run.run_id,
                template=body.template,
                origin=body.origin,
                force=body.force,
            )
            return {"run": run.model_dump(), "task": task.model_dump(), "template": body.template}
        try:
            result = await asyncio.to_thread(
                _execute_pipeline_run,
                pipeline_run_id=run.run_id,
                template=body.template,
                origin=body.origin,
                force=body.force,
            )
            run = deps.coordinator.transition(
                run.run_id,
                RunState.COMPLETED,
                stage="pipeline_completed",
                status_message=result["summary"],
            )
            return {"run": run.model_dump(), "result": result, "template": body.template}
        except Exception as exc:  # noqa: BLE001
            run = deps.coordinator.transition(
                run.run_id,
                RunState.FAILED,
                stage="pipeline_failed",
                status_message=str(exc),
            )
            return {"run": run.model_dump(), "error": str(exc), "template": body.template}

    @router.post("/api/v2/coordination/execute")
    async def execute_coordination(body: CoordinationRunRequest) -> dict:
        conflict_strategy, strategy_source = _resolve_conflict_strategy(
            profile_id=body.profile_id,
            raw_value=body.conflict_strategy,
        )
        active_conflict = detect_active_coordination_conflict(
            profile_id=body.profile_id,
            runs=deps.coordinator.list_runs(),
        )
        conflict_decision = decide_coordination_conflict(
            strategy=conflict_strategy,
            conflict_run=active_conflict,
        )
        if conflict_decision.should_reject:
            _append_coordination_audit(
                event_type="coordination_conflict_decided",
                profile_id=body.profile_id,
                strategy=conflict_strategy.value,
                outcome="rejected",
                reason=conflict_decision.reason,
                conflict_run_id=conflict_decision.conflict_run_id,
                payload={"detected": active_conflict is not None, "decision": conflict_decision.to_dict()},
            )
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "coordination conflict detected",
                    "profile_id": body.profile_id,
                    "conflict_run_id": conflict_decision.conflict_run_id,
                    "strategy": conflict_strategy.value,
                },
            )
        run = deps.coordinator.create_run(
            RunType.CHAT,
            origin=body.origin,
            owner_agent="coordinator",
            status_message="Coordination run queued.",
        )
        run = deps.coordinator.update_run(
            run.run_id,
            metadata={
                "profile_id": body.profile_id,
                "coordination_role": "root",
                "conflict_strategy": conflict_strategy.value,
                "conflict_strategy_source": strategy_source,
                "conflict_decision": conflict_decision.to_dict(),
            },
        )
        if conflict_decision.should_queue:
            run = deps.coordinator.update_run(
                run.run_id,
                stage="coordination_queued_conflict",
                status_message=f"Queued by active conflict run: {conflict_decision.conflict_run_id}",
                metadata={
                    "queued_for_run_id": conflict_decision.conflict_run_id,
                    "queue_reason": conflict_decision.reason,
                },
            )
            deps.coordinator.append_event(
                run.run_id,
                "coordination_conflict_queued",
                {
                    "profile_id": body.profile_id,
                    "conflict_run_id": conflict_decision.conflict_run_id,
                    "strategy": conflict_strategy.value,
                },
            )
            _append_coordination_audit(
                event_type="coordination_conflict_decided",
                profile_id=body.profile_id,
                strategy=conflict_strategy.value,
                outcome="queued",
                reason=conflict_decision.reason,
                run_id=run.run_id,
                conflict_run_id=conflict_decision.conflict_run_id,
                route_mode="queued",
                payload={"detected": active_conflict is not None, "decision": conflict_decision.to_dict()},
            )
            return {
                "run": run.model_dump(),
                "queued": True,
                "conflict": conflict_decision.to_dict(),
                "conflict_strategy_source": strategy_source,
                "route_result": None,
                "plan": None,
                "merged": None,
                "delegated": {"child_runs": [], "topology": None},
            }
        run = deps.coordinator.transition(run.run_id, RunState.RUNNING, stage="routing", status_message="Routing coordination request...")
        try:
            forced_mode = CoordinationMode.SINGLE_AGENT if conflict_decision.should_degrade_single_agent else None
            result = deps.coordination_supervisor.execute(
                run.run_id,
                body.message,
                forced_mode=forced_mode,
                priority=body.priority,
                budget_seconds=body.budget_seconds,
            )
            final_run = result["run"]
            merged = result.get("merged")
            if merged:
                merged_artifact_id = f"artifact-{uuid4().hex[:12]}"
                merged_artifact = ArtifactRecord(
                    artifact_id=merged_artifact_id,
                    run_id=final_run.run_id,
                    artifact_type=ArtifactType.COORDINATION_REPORT,
                    title="coordination merged result",
                    summary=merged.get("summary", ""),
                    payload={
                        "route_result": {
                            "mode": getattr(
                                result.get("route_result", {}).get("mode", ""),
                                "value",
                                result.get("route_result", {}).get("mode", ""),
                            ),
                            "reason": result.get("route_result", {}).get("reason", ""),
                        },
                        "plan": result.get("plan"),
                        "merged": merged,
                    },
                )
                deps.artifacts.put(merged_artifact)
                deps.coordinator.attach_artifact(final_run.run_id, merged_artifact_id)
                final_run = deps.coordinator.update_run(final_run.run_id, metadata={"merged_artifact_id": merged_artifact_id})
            route_mode = getattr(result.get("route_result", {}).get("mode", ""), "value", result.get("route_result", {}).get("mode", ""))
            outcome = "degraded_single_agent" if conflict_decision.should_degrade_single_agent else "executed"
            _append_coordination_audit(
                event_type="coordination_conflict_decided",
                profile_id=body.profile_id,
                strategy=conflict_strategy.value,
                outcome=outcome,
                reason=conflict_decision.reason,
                run_id=final_run.run_id,
                conflict_run_id=conflict_decision.conflict_run_id,
                route_mode=route_mode,
                payload={
                    "detected": active_conflict is not None,
                    "decision": conflict_decision.to_dict(),
                    "priority": body.priority,
                    "budget_seconds": body.budget_seconds,
                },
            )
            return {
                "run": final_run.model_dump(),
                "queued": False,
                "conflict": conflict_decision.to_dict(),
                "conflict_strategy_source": strategy_source,
                "plan": result.get("plan"),
                "route_result": {
                    "mode": getattr(result.get("route_result", {}).get("mode", ""), "value", result.get("route_result", {}).get("mode", "")),
                    "reason": result.get("route_result", {}).get("reason", ""),
                },
                "merged": result.get("merged"),
                "delegated": {
                    "child_runs": [child.model_dump() for child in result.get("delegated", {}).get("child_runs", [])],
                    "topology": result.get("delegated", {}).get("topology").model_dump()
                    if result.get("delegated", {}).get("topology")
                    else None,
                },
            }
        except Exception as exc:  # noqa: BLE001
            run = deps.coordinator.update_run(
                run.run_id,
                stage="failed",
                status_message=f"Coordination failed: {exc}",
                metadata={"error": str(exc)},
            )
            run = deps.coordinator.transition(
                run.run_id,
                RunState.FAILED,
                stage=run.stage,
                status_message=run.status_message,
            )
            _append_coordination_audit(
                event_type="coordination_conflict_decided",
                profile_id=body.profile_id,
                strategy=conflict_strategy.value,
                outcome="failed",
                reason=str(exc),
                run_id=run.run_id,
                conflict_run_id=conflict_decision.conflict_run_id,
                payload={"detected": active_conflict is not None, "decision": conflict_decision.to_dict()},
            )
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @router.get("/api/v2/coordination/policies/conflict-strategy")
    async def get_coordination_conflict_policy(profile_id: str = Query(default="default")) -> dict:
        override = deps.coordination_policy.get_strategy(profile_id)
        if override:
            return {"profile_id": profile_id, "strategy": override, "source": "policy_override"}
        return {
            "profile_id": profile_id,
            "strategy": deps.settings.coordination.default_conflict_strategy,
            "source": "settings_default",
        }

    @router.post("/api/v2/coordination/policies/conflict-strategy")
    async def set_coordination_conflict_policy(body: CoordinationConflictPolicyUpdateRequest) -> dict:
        try:
            normalized = CoordinationConflictStrategy(body.strategy.strip().lower()).value
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"invalid conflict_strategy: {body.strategy}") from exc
        record = deps.coordination_policy.set_strategy(
            profile_id=body.profile_id,
            strategy=normalized,
            source=body.source,
        )
        return {"policy": record}

    @router.get("/api/v2/coordination/persistence/health")
    async def get_coordination_persistence_health() -> dict:
        return {
            "audit": deps.coordination_audit.get_health_report(),
            "policy": deps.coordination_policy.get_health_report(),
        }

    @router.get("/api/v2/coordination/persistence/cutover/controls")
    async def get_coordination_persistence_cutover_controls() -> dict:
        if not hasattr(deps.coordination_audit, "get_read_routing_controls") or not hasattr(
            deps.coordination_policy, "get_read_routing_controls"
        ):
            raise HTTPException(status_code=400, detail="cutover controls are unavailable in current mode")
        return {
            "audit": deps.coordination_audit.get_read_routing_controls(),
            "policy": deps.coordination_policy.get_read_routing_controls(),
        }

    @router.post("/api/v2/coordination/persistence/cutover/controls")
    async def update_coordination_persistence_cutover_controls(body: CoordinationCutoverControlUpdateRequest) -> dict:
        if not hasattr(deps.coordination_audit, "update_read_routing_controls") or not hasattr(
            deps.coordination_policy, "update_read_routing_controls"
        ):
            raise HTTPException(status_code=400, detail="cutover controls are unavailable in current mode")
        audit = deps.coordination_audit.update_read_routing_controls(
            profile_allowlist=body.profile_allowlist,
            rollout_percentage=body.rollout_percentage,
            source=body.source,
        )
        policy = deps.coordination_policy.update_read_routing_controls(
            profile_allowlist=body.profile_allowlist,
            rollout_percentage=body.rollout_percentage,
            source=body.source,
        )
        return {"audit": audit, "policy": policy}

    @router.get("/api/v2/coordination/persistence/archives")
    async def list_coordination_persistence_archives(limit: int = Query(default=50)) -> dict:
        return {"items": deps.coordination_audit.list_archives(limit=limit)}

    @router.get("/api/v2/coordination/persistence/migration-plan")
    async def get_coordination_persistence_migration_plan() -> dict:
        dual_write = bool(deps.settings.coordination.dual_write_enabled)
        return {
            "status": "draft",
            "target": "database-backed coordination persistence",
            "current_state": {
                "audit_store": "jsonl_file+sqlite_dual_write" if dual_write else "jsonl_file",
                "policy_store": "json_file+sqlite_dual_write" if dual_write else "json_file",
                "state_dir": deps.settings.coordination.state_dir,
                "database_path": deps.settings.coordination.database_path,
                "dual_write_enabled": dual_write,
                "database_read_preferred": bool(deps.settings.coordination.database_read_preferred),
                "database_read_fallback_to_file": bool(deps.settings.coordination.database_read_fallback_to_file),
                "database_read_profile_allowlist": list(deps.settings.coordination.database_read_profile_allowlist or []),
                "database_read_rollout_percentage": int(deps.settings.coordination.database_read_rollout_percentage),
            },
            "phases": [
                {
                    "phase": "schema",
                    "summary": "Define audit and policy tables with profile/time indexes.",
                },
                {
                    "phase": "dual_write",
                    "summary": "Write both file and database, compare counts and checksums.",
                },
                {
                    "phase": "cutover",
                    "summary": "Read path switches to database with file fallback.",
                },
                {
                    "phase": "decommission",
                    "summary": "Retain file archives as read-only backups and stop file writes.",
                },
            ],
            "api_draft": {
                "health": "/api/v2/coordination/persistence/health",
                "cutover_controls": "/api/v2/coordination/persistence/cutover/controls",
                "archives": "/api/v2/coordination/persistence/archives",
                "migration_plan": "/api/v2/coordination/persistence/migration-plan",
                "consistency": "/api/v2/coordination/persistence/consistency",
                "cutover_drill": "/api/v2/coordination/persistence/cutover/drill",
            },
        }

    @router.get("/api/v2/coordination/persistence/dashboard")
    async def get_coordination_persistence_dashboard() -> dict:
        audit = deps.coordination_audit.get_health_report()
        policy = deps.coordination_policy.get_health_report()
        audit_observability = dict(audit.get("read_observability") or {})
        policy_observability = dict(policy.get("read_observability") or {})
        archives = deps.coordination_audit.list_archives(limit=500)
        latest_archive = archives[0] if archives else None
        rotate_max_bytes = max(int(deps.settings.coordination.audit_rotate_max_bytes), 1)
        current_size_bytes = int(audit.get("current_size_bytes", 0))
        usage_ratio = min(max(current_size_bytes / rotate_max_bytes, 0.0), 10.0)
        alerts: list[dict] = []
        if str(audit.get("status", "ok")) in {"warn", "recovered"}:
            alerts.append(
                {
                    "level": "warn",
                    "type": "audit_health",
                    "message": f"audit store status is `{audit.get('status')}`",
                    "recommended_action": "inspect backup and recovery logs",
                }
            )
        if usage_ratio >= 0.85:
            alerts.append(
                {
                    "level": "warn",
                    "type": "rotation_pressure",
                    "message": f"audit file usage is high ({usage_ratio:.2f})",
                    "recommended_action": "reduce rotate interval or lower size threshold",
                }
            )
        if int(audit.get("invalid_lines_detected", 0)) > 0:
            alerts.append(
                {
                    "level": "warn",
                    "type": "data_quality",
                    "message": f"invalid audit lines detected: {audit.get('invalid_lines_detected')}",
                    "recommended_action": "review writer stability and archive backups",
                }
            )
        fallback_anomaly_count = int(audit_observability.get("fallback_anomaly_count", 0)) + int(
            policy_observability.get("fallback_anomaly_count", 0)
        )
        if fallback_anomaly_count > 0:
            alerts.append(
                {
                    "level": "warn",
                    "type": "cutover_fallback",
                    "message": f"database read fallback anomalies detected: {fallback_anomaly_count}",
                    "recommended_action": "inspect sqlite read path and gray-release cohort settings",
                }
            )
        thresholds = {
            "audit_rotate_max_bytes": rotate_max_bytes,
            "audit_rotate_interval_seconds": int(deps.settings.coordination.audit_rotate_interval_seconds),
            "audit_retention_max_events": int(deps.settings.coordination.audit_retention_max_events),
            "audit_export_limit_max": int(deps.settings.coordination.audit_export_limit_max),
            "database_read_rollout_percentage": int(deps.settings.coordination.database_read_rollout_percentage),
            "recommended_warn_usage_ratio": 0.85,
            "recommended_critical_usage_ratio": 0.95,
        }
        consistency = None
        if hasattr(deps.coordination_audit, "compare_consistency") and hasattr(deps.coordination_policy, "compare_consistency"):
            consistency = {
                "audit": deps.coordination_audit.compare_consistency(window_limit=200),
                "policy": deps.coordination_policy.compare_consistency(limit=200),
            }
        total_cutover_reads = int(audit_observability.get("total_reads", 0)) + int(policy_observability.get("total_reads", 0))
        total_cutover_sqlite_reads = int(audit_observability.get("sqlite_reads", 0)) + int(
            policy_observability.get("sqlite_reads", 0)
        )
        total_gray_reads = int(audit_observability.get("gray_selected_reads", 0)) + int(
            policy_observability.get("gray_selected_reads", 0)
        )
        cutover_controls = None
        if hasattr(deps.coordination_audit, "get_read_routing_controls") and hasattr(
            deps.coordination_policy, "get_read_routing_controls"
        ):
            cutover_controls = {
                "audit": deps.coordination_audit.get_read_routing_controls(),
                "policy": deps.coordination_policy.get_read_routing_controls(),
            }
        return {
            "summary": {
                "status": "warn" if alerts else "ok",
                "alerts_total": len(alerts),
                "archives_total": len(archives),
                "profiles_total": int(policy.get("profiles_count", 0)),
            },
            "metrics": {
                "audit": {
                    "current_size_bytes": current_size_bytes,
                    "max_size_bytes": rotate_max_bytes,
                    "usage_ratio": usage_ratio,
                    "retained_events": int(audit.get("retained_events", 0)),
                    "invalid_lines_detected": int(audit.get("invalid_lines_detected", 0)),
                    "last_rotated_at": audit.get("last_rotated_at"),
                    "last_rotation_reason": audit.get("last_rotation_reason"),
                },
                "policy": {
                    "profiles_count": int(policy.get("profiles_count", 0)),
                    "status": policy.get("status", "unknown"),
                },
                "archive": {
                    "latest": latest_archive,
                    "total": len(archives),
                },
                "cutover": {
                    "total_reads": total_cutover_reads,
                    "sqlite_reads": total_cutover_sqlite_reads,
                    "database_coverage_ratio": round((total_cutover_sqlite_reads / total_cutover_reads), 4)
                    if total_cutover_reads
                    else 0.0,
                    "gray_selected_reads": total_gray_reads,
                    "gray_coverage_ratio": round((total_gray_reads / total_cutover_reads), 4) if total_cutover_reads else 0.0,
                    "fallback_anomaly_count": fallback_anomaly_count,
                    "audit": audit_observability,
                    "policy": policy_observability,
                    "controls": cutover_controls,
                },
            },
            "alerts": alerts,
            "thresholds": thresholds,
            "consistency": consistency,
        }

    @router.get("/api/v2/coordination/persistence/consistency")
    async def get_coordination_persistence_consistency(
        profile_id: str | None = Query(default=None),
        window_limit: int = Query(default=200),
        policy_limit: int = Query(default=500),
    ) -> dict:
        if not hasattr(deps.coordination_audit, "compare_consistency") or not hasattr(deps.coordination_policy, "compare_consistency"):
            raise HTTPException(status_code=400, detail="dual-write consistency checks are unavailable in current mode")
        audit_report = deps.coordination_audit.compare_consistency(
            profile_id=profile_id,
            window_limit=window_limit,
        )
        policy_report = deps.coordination_policy.compare_consistency(limit=policy_limit)
        status = "consistent"
        if audit_report.get("status") == "disabled" or policy_report.get("status") == "disabled":
            status = "disabled"
        elif audit_report.get("status") == "mismatch" or policy_report.get("status") == "mismatch":
            status = "mismatch"
        return {
            "status": status,
            "window": {
                "profile_id": profile_id,
                "audit_window_limit": max(int(window_limit), 1),
                "policy_limit": max(int(policy_limit), 1),
            },
            "reports": {
                "audit": audit_report,
                "policy": policy_report,
            },
        }

    @router.get("/api/v2/coordination/persistence/cutover/drill")
    async def run_coordination_persistence_cutover_drill(
        profile_id: str = Query(default="default"),
        window_limit: int = Query(default=100),
        simulate_secondary_failure: bool = Query(default=False),
    ) -> dict:
        if not hasattr(deps.coordination_audit, "drill_read") or not hasattr(deps.coordination_policy, "drill_read"):
            raise HTTPException(status_code=400, detail="cutover drill is unavailable in current mode")
        audit_report = deps.coordination_audit.drill_read(
            profile_id=profile_id,
            window_limit=window_limit,
            simulate_secondary_failure=simulate_secondary_failure,
        )
        policy_report = deps.coordination_policy.drill_read(
            profile_id=profile_id,
            simulate_secondary_failure=simulate_secondary_failure,
        )
        status = "ok"
        if str(audit_report.get("status")) == "degraded" or str(policy_report.get("status")) == "degraded":
            status = "degraded"
        return {
            "status": status,
            "profile_id": profile_id,
            "simulate_secondary_failure": bool(simulate_secondary_failure),
            "reports": {
                "audit": audit_report,
                "policy": policy_report,
            },
        }

    @router.get("/api/v2/coordination/audit/events")
    async def list_coordination_audit_events(
        profile_id: str | None = Query(default=None),
        strategy: str | None = Query(default=None),
        outcome: str | None = Query(default=None),
        event_type: str | None = Query(default=None),
        limit: int = Query(default=200),
    ) -> dict:
        items = deps.coordination_audit.list_events(
            profile_id=profile_id,
            strategy=strategy,
            outcome=outcome,
            event_type=event_type,
            limit=limit,
        )
        return {"items": [item.to_dict() for item in items]}

    @router.get("/api/v2/coordination/audit/export")
    async def export_coordination_audit(
        profile_id: str | None = Query(default=None),
        strategy: str | None = Query(default=None),
        outcome: str | None = Query(default=None),
        event_type: str | None = Query(default=None),
        limit: int = Query(default=1000),
    ) -> dict:
        capped_limit = min(max(int(limit), 1), deps.settings.coordination.audit_export_limit_max)
        items = deps.coordination_audit.list_events(
            profile_id=profile_id,
            strategy=strategy,
            outcome=outcome,
            event_type=event_type,
            limit=capped_limit,
        )
        return {
            "summary": {
                "total": len(items),
                "profile_id": profile_id,
                "strategy": strategy,
                "outcome": outcome,
                "event_type": event_type,
                "requested_limit": int(limit),
                "effective_limit": capped_limit,
                "configured_export_limit_max": deps.settings.coordination.audit_export_limit_max,
            },
            "items": [item.to_dict() for item in items],
        }

    return router
