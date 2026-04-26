# Phase 7：切换评估与回退演练清单

更新日期：2026-04-09

## 1. 切换评估（Go/No-Go）清单

### 1.1 必须满足

- [ ] `tests/v2` 全量通过
- [ ] Phase 6 对比报告齐全：
  - [ ] `docs/Phase6_资料库导入_V1_V2_链路对比报告.md`
  - [ ] `docs/Phase6_标准流水线_V1_V2_稳定性对比报告.md`
  - [ ] `docs/Phase6_V1_V2_对比基线与回归脚本.md`
- [ ] 基线脚本通过：
  - [ ] `scripts/v1_v2_baseline_regression.py`
  - [ ] 输出 `docs/reports/phase6_v1_v2_baseline_latest.json` 且 `failed=0`

### 1.2 推荐满足

- [ ] 关键页面（Run Console / Approval / Task Center / Artifact Viewer）可访问
- [ ] 资料库导入链路可跑通（upload -> run/task -> artifact）
- [ ] 标准流水线可跑通（pipeline run -> child runs -> pipeline_report）

## 2. 回退演练（Dry-run）清单

### 2.1 演练脚本

- `scripts/phase7_rollback_drill.py`
- 输出：`docs/reports/phase7_rollback_drill_latest.json`

### 2.2 演练步骤

1. 冻结 V2 灰度开关（停止新增切流）
2. 将客户端网关基地址指回 V1
3. 执行 V1 冒烟：
   - `/api/v1/status`
   - `/api/v1/library/stats`
   - `/api/v1/pipelines`
4. 通知用户并记录恢复时间
5. 保留 V2 故障上下文用于复盘

## 3. 自动化辅助脚本

### 3.1 切换就绪检查

- `scripts/phase7_cutover_readiness.py`
- 默认读取：
  - `docs/reports/phase6_v1_v2_baseline_latest.json`
- 默认输出：
  - `docs/reports/phase7_cutover_readiness_latest.json`

示例：

```bash
python scripts/phase7_cutover_readiness.py --run-tests
```

### 3.2 切换前联动演练（审批/任务/回退）

- `scripts/phase7_pre_cutover_drill.py`
- 串联动作：
  1. 触发 `system_status` run
  2. 创建并通过一条 approval
  3. 提交并观察一条后台 task（`intel_today`）
  4. 调用 rollback drill 预检
- 默认输出：
  - `docs/reports/phase7_pre_cutover_drill_latest.json`

示例：

```bash
python scripts/phase7_pre_cutover_drill.py --v1-base http://127.0.0.1:18789 --v2-base http://127.0.0.1:18790
```

### 3.3 按场景灰度切换演练（先资料库 / 后流水线）

- `scripts/phase7_canary_rollout_drill.py`
- 策略：
  1. **资料库灰度阶段**（library-first）
     - 调用 `v1_v2_baseline_regression.py`
     - 检查 V2 资料库导入链路是否稳定
  2. **流水线灰度阶段**（pipeline-second）
     - 调用 `phase7_pre_cutover_drill.py`
     - 检查审批/任务/回退联动下的流水线链路
  3. 任一阶段失败则停止推进，进入回退预案
- 默认输出：
  - `docs/reports/phase7_canary_rollout_latest.json`
  - 以及阶段子报告：
    - `docs/reports/phase7_canary_library_baseline.json`
    - `docs/reports/phase7_canary_pipeline_pre_cutover.json`
    - `docs/reports/phase7_canary_pipeline_rollback.json`

示例：

```bash
# 全流程（资料库 -> 流水线）
python scripts/phase7_canary_rollout_drill.py --v1-base http://127.0.0.1:18789 --v2-base http://127.0.0.1:18790

# 仅资料库阶段
python scripts/phase7_canary_rollout_drill.py --stage library

# 仅流水线阶段
python scripts/phase7_canary_rollout_drill.py --stage pipeline
```

### 3.4 回退演练检查

示例：

```bash
python scripts/phase7_rollback_drill.py --v1-base http://127.0.0.1:18789 --v2-base http://127.0.0.1:18790
```

### 3.5 切换后观测守护（阈值 + 回退触发）

- `scripts/phase7_observability_guard.py`
- 策略文件：`docs/phase7_observability_policy.json`
- 输出：`docs/reports/phase7_observability_guard_latest.json`
- 详细规则：`docs/Phase7_观测指标与回退触发条件.md`

示例：

```bash
python scripts/phase7_observability_guard.py --v2-base http://127.0.0.1:18790
```

### 3.6 切换评审材料模板（发布/回退决策记录）

- 模板总览：`docs/Phase7_切换评审材料模板.md`
- 模板文件：
  - `docs/templates/Phase7_发布决策记录模板.md`
  - `docs/templates/Phase7_回退决策记录模板.md`
  - `docs/templates/Phase7_切换评审会议纪要模板.md`
- 生成脚本：
  - `scripts/phase7_generate_decision_pack.py`

示例：

```bash
python scripts/phase7_generate_decision_pack.py --version v2-canary-20260409 --owner release-manager
```

### 3.7 正式切换窗口与值班预案

- 方案文档：`docs/Phase7_正式切换窗口与值班预案.md`
- 模板文件：`docs/templates/Phase7_正式切换窗口与值班预案模板.md`
- 生成脚本：`scripts/phase7_generate_cutover_plan.py`
- 生成目录：`docs/reports/cutover-plan/`

示例：

```bash
python scripts/phase7_generate_cutover_plan.py --date 2026-04-10 --version v2-cutover-r1 --window-start 20:00 --window-end 23:00 --commander release-manager --dev-oncall dev-oncall --qa-oncall qa-oncall --ops-oncall ops-oncall
```

### 3.8 正式切换前一周演练节奏（每日检查项）

- 节奏文档：`docs/Phase7_切换前一周演练节奏.md`
- 每日模板：`docs/templates/Phase7_每日演练检查项模板.md`
- 生成脚本：`scripts/phase7_generate_weekly_drill_plan.py`
- 输出目录：`docs/reports/weekly-drill/`

示例：

```bash
# 生成 7 天检查项
python scripts/phase7_generate_weekly_drill_plan.py --start-date 2026-04-12 --version v2-cutover-r1 --owner release-manager

# 仅预览，不写文件
python scripts/phase7_generate_weekly_drill_plan.py --start-date 2026-04-12 --dry-run
```

### 3.9 切换完成后复盘模板（问题分级与改进跟踪）

- 机制文档：`docs/Phase7_切换后复盘与改进跟踪.md`
- 复盘模板：`docs/templates/Phase7_切换后复盘报告模板.md`
- 分级与跟踪模板：`docs/templates/Phase7_问题分级与改进跟踪模板.md`
- 行动项台账模板：`docs/templates/Phase7_复盘行动项台账模板.md`
- 生成脚本：`scripts/phase7_generate_postmortem_pack.py`
- 输出目录：`docs/reports/postmortem-pack/`

示例：

```bash
python scripts/phase7_generate_postmortem_pack.py --date 2026-04-09 --version v2-cutover-r1 --owner release-manager
```

### 3.10 双周稳定性复评机制（持续观测）

- 机制文档：`docs/Phase7_双周稳定性复评机制.md`
- 复评模板：`docs/templates/Phase7_双周稳定性复评模板.md`
- 生成脚本：`scripts/phase7_biweekly_stability_review.py`
- 默认输出：
  - `docs/reports/phase7_biweekly_stability_review_latest.json`
  - `docs/reports/phase7_biweekly_stability_review_latest.md`

示例：

```bash
# 标准执行（含实时探针）
python scripts/phase7_biweekly_stability_review.py --version v2-cutover-r1 --owner release-manager

# 离线执行（仅使用报告）
python scripts/phase7_biweekly_stability_review.py --skip-live-probes
```

### 3.11 季度回归审计机制（报告签核闭环）

- 机制文档：`docs/Phase7_季度回归审计机制.md`
- 审计报告模板：`docs/templates/Phase7_季度回归审计报告模板.md`
- 签核记录模板：`docs/templates/Phase7_季度回归审计签核记录模板.md`
- 生成脚本：`scripts/phase7_quarterly_regression_audit.py`
- 默认输出：
  - `docs/reports/phase7_quarterly_regression_audit_latest.json`
  - `docs/reports/phase7_quarterly_regression_audit_latest.md`
  - `docs/reports/phase7_quarterly_regression_signoff_latest.md`

示例：

```bash
python scripts/phase7_quarterly_regression_audit.py --version-scope v2-cutover-r1 --owner release-manager
```

### 3.12 版本级变更审计与责任追踪机制

- 机制文档：`docs/Phase7_版本级变更审计与责任追踪机制.md`
- 审计模板：`docs/templates/Phase7_版本级变更审计模板.md`
- 责任追踪模板：`docs/templates/Phase7_版本责任追踪模板.md`
- 生成脚本：`scripts/phase7_version_change_audit.py`
- 默认输出：
  - `docs/reports/phase7_version_change_audit_latest.json`
  - `docs/reports/phase7_version_change_audit_latest.md`
  - `docs/reports/phase7_version_accountability_trace_latest.md`

示例：

```bash
python scripts/phase7_version_change_audit.py --version-id v2-cutover-r1 --owner release-manager
```

### 3.13 演练与发布材料归档规范（目录与命名）

- 规范文档：`docs/Phase7_演练与发布材料归档规范.md`
- 归档索引模板：`docs/templates/Phase7_归档索引模板.md`
- 自动归档脚本：`scripts/phase7_archive_materials.py`
- 默认归档目录：`docs/archive/phase7/<archive_id>/`

示例：

```bash
# 预览
python scripts/phase7_archive_materials.py --archive-id 20260410 --version v2-cutover-r1 --dry-run

# 执行归档
python scripts/phase7_archive_materials.py --archive-id 20260410 --version v2-cutover-r1 --owner release-manager

# 一键补齐 drill 报告并归档
python scripts/phase7_backfill_and_archive.py --archive-id 20260410 --version v2-cutover-r1 --owner release-manager
```
