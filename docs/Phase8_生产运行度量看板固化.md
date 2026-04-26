# Phase 8-1 生产运行度量看板固化（SLO / 错误预算 / 容量）

更新日期：2026-04-10

## 1. 目标

将生产运行健康从“单点观察”固化为统一看板输出，覆盖：

- SLO（Availability）
- 错误预算（Error Budget）
- 容量压力（Pending Approvals / Timeout Tasks）

## 2. 资产清单

- 机制文档：`docs/Phase8_生产运行度量看板固化.md`
- 看板模板：`docs/templates/Phase8_生产运行度量看板模板.md`
- 策略文件：`docs/phase8_ops_metrics_policy.json`
- 生成脚本：`scripts/phase8_ops_metrics_dashboard.py`
- Canvas 视图：`docs/Phase8_生产运行度量看板.canvas.tsx`
- 默认输出：
  - `docs/reports/phase8_ops_metrics_dashboard_latest.json`
  - `docs/reports/phase8_ops_metrics_dashboard_latest.md`

## 3. 输入来源（默认）

- 观测守护：`docs/reports/phase7_observability_guard_latest.json`
- 双周复评：`docs/reports/phase7_biweekly_stability_review_latest.json`
- 可选实时探针：`/health`、`/api/v2/console/runs`、`/api/v2/approvals?status=pending`、`/api/v2/tasks?state=timeout`

## 4. 执行方式

```bash
# 标准执行（包含实时探针）
python scripts/phase8_ops_metrics_dashboard.py --version v2-prod-r1 --owner sre-manager

# 离线执行（仅基于已有报告）
python scripts/phase8_ops_metrics_dashboard.py --skip-live-probes
```

## 5. 输出分级

- `GREEN`：SLO 与预算健康，容量无显著压力
- `YELLOW`：预算/容量出现压力，需限时整改
- `RED`：SLO 失守或关键探针失败，需立即处置

## 6. 建议运营节奏

1. 每日定时产出看板；
2. 每次版本窗口后追加专项看板快照；
3. `RED` 结果必须进入故障流程并补充复盘证据。
