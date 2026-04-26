# Phase 8-6 跨团队发布节奏协同与冲突仲裁机制固化

更新日期：2026-04-10

## 1. 目标

固化跨团队发布申请、排期冲突仲裁、结果留痕机制，降低发布窗口冲突风险。

## 2. 资产清单

- 机制文档：`docs/Phase8_跨团队发布节奏协同与冲突仲裁机制.md`
- 策略文件：`docs/phase8_team_release_policy.json`
- 模板：
  - `docs/templates/Phase8_跨团队发布申请模板.json`
  - `docs/templates/Phase8_跨团队发布协调纪要模板.md`
- 执行脚本：`scripts/phase8_release_cadence_arbitration.py`
- 默认输出：
  - `docs/reports/phase8_release_cadence_arbitration_latest.json`
  - `docs/reports/phase8_release_cadence_arbitration_latest.md`

## 3. 输入来源（默认）

- 发布申请：`docs/templates/Phase8_跨团队发布申请模板.json`
- on-call 态势：`docs/reports/phase8_oncall_handbook_latest.json`

## 4. 执行方式

```bash
python scripts/phase8_release_cadence_arbitration.py --owner release-manager
```

## 5. 仲裁规则（默认）

- 高风险发布并行上限为 1；
- on-call 为 `P1/P2` 时，中高风险发布延后；
- 同时间窗冲突按优先级保留其一，其余顺延。

## 6. 决策类型

- `APPROVED`：全部通过
- `PARTIAL_APPROVED`：部分通过，部分延期
- `REPLAN_REQUIRED`：需要重排期
- `HOLD_ALL`：窗口冻结
