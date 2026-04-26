# Phase 8-3 生产告警分层与 On-Call 响应手册固化

更新日期：2026-04-10

## 1. 目标

建立标准化告警分层与 on-call 响应机制，确保：

- 告警等级清晰（P1 / P2 / P3）
- 升级路径明确（通知角色 + 通道）
- 值班交接和复盘闭环可执行

## 2. 资产清单

- 机制文档：`docs/Phase8_生产告警分层与OnCall响应手册.md`
- 策略文件：`docs/phase8_alert_policy.json`
- 模板：
  - `docs/templates/Phase8_OnCall响应手册模板.md`
  - `docs/templates/Phase8_OnCall交接模板.md`
- 生成脚本：`scripts/phase8_generate_oncall_handbook.py`
- 默认输出：
  - `docs/reports/phase8_oncall_handbook_latest.json`
  - `docs/reports/phase8_oncall_handbook_latest.md`
  - `docs/reports/phase8_oncall_handoff_latest.md`

## 3. 输入来源（默认）

- `docs/reports/phase7_observability_guard_latest.json`
- `docs/reports/phase8_ops_metrics_dashboard_latest.json`
- `docs/reports/phase8_dependency_compat_latest.json`

## 4. 执行方式

```bash
python scripts/phase8_generate_oncall_handbook.py --version v2-prod-r1 --owner oncall-manager
```

## 5. 告警级别定义

- `P1`：核心可用性风险，立即响应并进入 war-room
- `P2`：重要能力退化，限时恢复
- `P3`：低风险提示，纳入常规跟踪

## 6. 闭环要求

1. 每次值班交接前生成最新 handoff 文档；
2. `P1/P2` 必须补齐复盘与归档证据；
3. 每周回顾告警分层命中情况并调整策略阈值。
