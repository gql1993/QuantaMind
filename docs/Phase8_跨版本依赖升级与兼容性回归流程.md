# Phase 8-2 跨版本依赖升级与兼容性回归流程固化

更新日期：2026-04-10

## 1. 目标

将依赖升级从“手工试错”固化为标准流程，形成：

- 依赖变更清单
- 自动兼容性回归报告
- 签核记录与闭环动作

## 2. 资产清单

- 流程文档：`docs/Phase8_跨版本依赖升级与兼容性回归流程.md`
- 变更清单模板：`docs/templates/Phase8_依赖变更清单模板.json`
- 回归报告模板：`docs/templates/Phase8_兼容性回归报告模板.md`
- 签核记录模板：`docs/templates/Phase8_兼容性签核记录模板.md`
- 执行脚本：`scripts/phase8_dependency_compat_regression.py`
- 默认输出：
  - `docs/reports/phase8_dependency_compat_latest.json`
  - `docs/reports/phase8_dependency_compat_latest.md`
  - `docs/reports/phase8_dependency_compat_signoff_latest.md`

## 3. 默认回归链路

1. `pytest tests/v2 -q`
2. `scripts/v1_v2_baseline_regression.py`
3. `scripts/phase8_ops_metrics_dashboard.py --skip-live-probes`

## 4. 执行方式

```bash
python scripts/phase8_dependency_compat_regression.py --version v2-prod-r1 --owner release-manager
```

可选参数：

- `--change-set`：指定依赖变更清单 JSON
- `--v1-base` / `--v2-base`：指定网关地址

## 5. 结果分级

- `PASS`：检查项全部通过
- `CONDITIONAL_PASS`：有失败项但无高风险阻断，需限时整改
- `BLOCK`：失败项 + 高风险依赖变更，冻结发布

## 6. 闭环要求

1. 每次依赖升级必须产出本报告；
2. `CONDITIONAL_PASS/BLOCK` 必须登记动作并复跑；
3. 签核通过后方可进入版本归档流程。
