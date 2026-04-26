# Phase 7：切换后观测指标与回退触发条件

更新日期：2026-04-09

## 1. 目标

把“切换后观测”从经验判断固化为可执行规则，输出统一结论：

- `ok`：可继续灰度/观察
- `warn`：告警，需人工跟进
- `rollback_now`：立即触发回退预案

## 2. 策略文件

- 路径：`docs/phase7_observability_policy.json`
- 结构：
  - `critical`：触发 `rollback_now` 的阈值
  - `warn`：触发 `warn` 的阈值

默认关键阈值：

- `v2_health_required = true`
- `rollback_precheck_required = true`
- `canary_failed_phases_max = 0`
- `baseline_failed_checks_max = 0`
- `failed_run_ratio_max = 0.2`
- `failed_runs_min_for_ratio = 3`

默认告警阈值：

- `pending_approvals_max = 20`
- `timeout_tasks_max = 5`
- `report_stale_hours_max = 24`

## 3. 自动评估脚本

- 脚本：`scripts/phase7_observability_guard.py`
- 默认输入：
  - `docs/reports/phase6_v1_v2_baseline_latest.json`
  - `docs/reports/phase7_canary_rollout_latest.json`
  - `docs/reports/phase7_pre_cutover_drill_latest.json`
  - `docs/reports/phase7_rollback_drill_latest.json`
  - 实时探针：`/health`、`/api/v2/console/runs`、`/api/v2/approvals?status=pending`、`/api/v2/tasks?state=timeout`
- 输出：
  - `docs/reports/phase7_observability_guard_latest.json`

示例：

```bash
python scripts/phase7_observability_guard.py --v2-base http://127.0.0.1:18790
```

## 4. 回退触发条件（固化）

满足任一条即判定 `rollback_now`：

1. V2 健康探针失败（`/health` 非 200 或 `status != ok`）
2. 回退预检未就绪（`rollback_ready != true`）
3. 灰度演练失败阶段数 > 0（`canary_failed_phases_max`）
4. 基线失败检查数 > 0（`baseline_failed_checks_max`）
5. 失败 run 比例超过阈值且失败 run 数达到最小样本量

## 5. 联动建议

- 每次灰度窗口开始前执行：
  1. `phase7_canary_rollout_drill.py`
  2. `phase7_observability_guard.py`
- 若 guard 结果为 `rollback_now`：
  - 立即执行回退流程（参见 `Phase7_切换评估与回退演练清单.md`）
  - 记录触发项与证据，进入复盘
