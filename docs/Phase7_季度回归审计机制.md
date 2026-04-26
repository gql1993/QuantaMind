# Phase 7 季度回归审计机制（报告签核闭环）

更新日期：2026-04-10

## 1. 目标

建立“季度回归审计 + 签核记录 + 整改闭环”的固定机制，确保持续观测结果进入治理闭环：

- 每季度产出回归审计结论（`PASS / CONDITIONAL_PASS / FAIL`）
- 形成跨角色签核记录（发布/技术/测试/运维）
- 将审计发现转化为可追踪整改动作

## 2. 资产清单

- 机制文档：`docs/Phase7_季度回归审计机制.md`
- 审计报告模板：`docs/templates/Phase7_季度回归审计报告模板.md`
- 签核记录模板：`docs/templates/Phase7_季度回归审计签核记录模板.md`
- 生成脚本：`scripts/phase7_quarterly_regression_audit.py`
- 默认输出：
  - `docs/reports/phase7_quarterly_regression_audit_latest.json`
  - `docs/reports/phase7_quarterly_regression_audit_latest.md`
  - `docs/reports/phase7_quarterly_regression_signoff_latest.md`

## 3. 输入来源（默认）

- 观测策略：`docs/phase7_observability_policy.json`
- 观测守护：`docs/reports/phase7_observability_guard_latest.json`
- 关键演练报告：
  - `docs/reports/phase6_v1_v2_baseline_latest.json`
  - `docs/reports/phase7_canary_rollout_latest.json`
  - `docs/reports/phase7_pre_cutover_drill_latest.json`
  - `docs/reports/phase7_rollback_drill_latest.json`
- 双周复评报告：`docs/reports/phase7_biweekly_stability_review*.json`

## 4. 执行方式

```bash
python scripts/phase7_quarterly_regression_audit.py --version-scope v2-cutover-r1 --owner release-manager
```

可选参数：

- `--window-days`：季度观测窗口（默认 90 天）
- `--expected-biweekly-min`：季度内最小双周复评次数（默认 4）

## 5. 结论规则（默认）

- `PASS`：无 critical、无关键失败项，且审计节奏完整
- `CONDITIONAL_PASS`：存在告警/节奏缺失/时效风险，需限期整改并签核
- `FAIL`：存在 critical 或回退级风险，需冻结推进并重新审计

## 6. 签核闭环要求

1. 审计报告生成后 2 个工作日内完成签核；
2. 对 `CONDITIONAL_PASS` / `FAIL` 结论，必须登记整改行动项；
3. 下季度审计需验证上一季度整改项关闭情况。
