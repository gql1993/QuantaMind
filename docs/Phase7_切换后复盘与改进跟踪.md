# Phase 7 切换后复盘与改进跟踪

本文档用于固化切换完成后的复盘机制，确保问题分级、改进动作、验收闭环可持续执行。

## 1. 使用目标

- 统一记录切换后故障与异常，不遗漏关键证据；
- 对问题按 `P0~P3` 分级，明确处置优先级；
- 将改进动作转化为可追踪台账，并形成验收结论。

## 2. 模板与脚本

- 复盘报告模板：`docs/templates/Phase7_切换后复盘报告模板.md`
- 问题分级与改进跟踪模板：`docs/templates/Phase7_问题分级与改进跟踪模板.md`
- 复盘行动项台账模板：`docs/templates/Phase7_复盘行动项台账模板.md`
- 自动生成脚本：`scripts/phase7_generate_postmortem_pack.py`
- 默认输出目录：`docs/reports/postmortem-pack/`

## 3. 推荐执行节奏

1. 切换后 24 小时内：完成初版复盘报告与时间线；
2. 切换后 48 小时内：完成问题分级与责任归属；
3. 切换后 7 天内：完成行动项计划并确认验收人；
4. 后续每周：更新台账进展，直至高优先级项全部关闭。

## 4. 命令示例

```bash
# 生成复盘材料包
python scripts/phase7_generate_postmortem_pack.py --date 2026-04-09 --version v2-cutover-r1 --owner release-manager

# 自定义输出目录
python scripts/phase7_generate_postmortem_pack.py --output-dir docs/reports/postmortem-pack/r1
```

## 5. 产出清单（示例）

- `docs/reports/postmortem-pack/20260409_切换后复盘报告.md`
- `docs/reports/postmortem-pack/20260409_问题分级与改进跟踪.md`
- `docs/reports/postmortem-pack/20260409_复盘行动项台账.md`
