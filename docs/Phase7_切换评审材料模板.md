# Phase 7：切换评审材料模板

更新日期：2026-04-09

## 1. 模板清单

- `docs/templates/Phase7_发布决策记录模板.md`
- `docs/templates/Phase7_回退决策记录模板.md`
- `docs/templates/Phase7_切换评审会议纪要模板.md`

## 2. 自动生成脚本

- `scripts/phase7_generate_decision_pack.py`

用途：按当天日期生成一套可直接填写的评审材料文件，默认输出到：

- `docs/reports/decision-pack/`

示例：

```bash
python scripts/phase7_generate_decision_pack.py --version v2-canary-20260409 --owner release-manager
```

生成结果（示例）：

- `docs/reports/decision-pack/20260409_发布决策记录.md`
- `docs/reports/decision-pack/20260409_回退决策记录.md`
- `docs/reports/decision-pack/20260409_切换评审会议纪要.md`

## 3. 使用建议

1. 在每次灰度窗口前先生成一套材料。
2. 将最新报告路径回填到模板中的“证据清单”。
3. 评审后将签字版归档到同目录，保留变更历史。
