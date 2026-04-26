# Phase 7 版本级变更审计与责任追踪机制

更新日期：2026-04-10

## 1. 目标

把“版本发布决策”从一次性判断固化为可追踪机制：

- 形成版本级审计结论（`APPROVE_CANDIDATE / REVIEW_REQUIRED / BLOCK`）
- 固化责任矩阵（发布/技术/测试/运维）
- 将风险和整改动作纳入可跟踪台账

## 2. 资产清单

- 机制文档：`docs/Phase7_版本级变更审计与责任追踪机制.md`
- 审计模板：`docs/templates/Phase7_版本级变更审计模板.md`
- 责任追踪模板：`docs/templates/Phase7_版本责任追踪模板.md`
- 生成脚本：`scripts/phase7_version_change_audit.py`
- 默认输出：
  - `docs/reports/phase7_version_change_audit_latest.json`
  - `docs/reports/phase7_version_change_audit_latest.md`
  - `docs/reports/phase7_version_accountability_trace_latest.md`

## 3. 输入来源（默认）

- 季度审计：`docs/reports/phase7_quarterly_regression_audit_latest.json`
- 双周复评：`docs/reports/phase7_biweekly_stability_review_latest.json`
- 观测守护：`docs/reports/phase7_observability_guard_latest.json`
- 复盘目录：`docs/reports/postmortem-pack/`

## 4. 执行方式

```bash
python scripts/phase7_version_change_audit.py --version-id v2-cutover-r1 --owner release-manager
```

可选负责人参数：

- `--release-owner`
- `--tech-owner`
- `--qa-owner`
- `--ops-owner`

## 5. 决策规则（默认）

- `APPROVE_CANDIDATE`：关键输入稳定，可进入发布签核
- `REVIEW_REQUIRED`：存在条件项，需责任人限期闭环
- `BLOCK`：存在回退级风险，必须冻结推进并复审

## 6. 责任追踪闭环

1. 审计报告输出后，生成责任追踪记录；
2. 对 `REVIEW_REQUIRED` / `BLOCK` 必须建立 trace 动作；
3. 下次版本审计需复核上次 trace 动作完成情况。
