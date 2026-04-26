# Phase 7 双周稳定性复评机制（持续观测）

更新日期：2026-04-09

## 1. 目标

将“切换后持续观测”固化为双周复评流程，形成固定节奏输出：

- 双周复评结论（`GREEN` / `YELLOW` / `RED`）
- 风险清单与改进行动
- 证据链（策略、观测守护、演练报告、复盘材料）

## 2. 资产清单

- 机制文档：`docs/Phase7_双周稳定性复评机制.md`
- 复评模板：`docs/templates/Phase7_双周稳定性复评模板.md`
- 生成脚本：`scripts/phase7_biweekly_stability_review.py`
- 默认输出：
  - `docs/reports/phase7_biweekly_stability_review_latest.json`
  - `docs/reports/phase7_biweekly_stability_review_latest.md`

## 3. 输入来源（默认）

- 策略：`docs/phase7_observability_policy.json`
- 观测守护：`docs/reports/phase7_observability_guard_latest.json`
- 基线/灰度/演练：
  - `docs/reports/phase6_v1_v2_baseline_latest.json`
  - `docs/reports/phase7_canary_rollout_latest.json`
  - `docs/reports/phase7_pre_cutover_drill_latest.json`
  - `docs/reports/phase7_rollback_drill_latest.json`
- 复盘材料目录：`docs/reports/postmortem-pack/`

## 4. 执行方式

```bash
# 标准执行（包含实时探针）
python scripts/phase7_biweekly_stability_review.py --version v2-cutover-r1 --owner release-manager

# 离线执行（仅基于已有报告）
python scripts/phase7_biweekly_stability_review.py --skip-live-probes
```

## 5. 结论分级规则

- `GREEN`：无 critical/warn 告警，且关键指标稳定
- `YELLOW`：存在 warn 或局部指标超阈值，需限时整改
- `RED`：出现 critical 或健康探针失败，需冻结推进并评估回退

## 6. 建议节奏

1. 每 2 周固定产出一次复评报告；
2. 每次发布窗口结束后，追加一次专项复评；
3. `RED` 结论必须进入复盘与决策流程并保留签核记录。
