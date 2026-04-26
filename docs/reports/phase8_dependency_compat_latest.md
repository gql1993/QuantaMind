# Phase 8 跨版本依赖升级兼容性回归报告（模板）

生成日期：2026-04-10 16:45:15  
版本范围：v2-prod-r1  
负责人：release-manager

---

## 1. 结论

- 兼容性结论：`BLOCK`
- 摘要：checks passed=1/3, high_risk=1, result=BLOCK.

## 2. 依赖变更清单

| 变更ID | 依赖 | 版本变更 | 风险 | 升级原因 | 兼容性关注点 |
|---|---|---|---|---|---|
| DEP-001 | fastapi | 0.110.x -> 0.111.x | medium | 安全修复与性能优化 | gateway 路由与请求模型兼容 |
| DEP-002 | pydantic | 2.6.x -> 2.7.x | high | 模型校验一致性升级 | BaseModel 序列化与默认值行为 |

## 3. 回归执行结果

| 检查项 | 命令 | 退出码 | 结论 |
|---|---|---|---|
| pytest_v2_regression | `C:\Users\Huawei\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/v2 -q` | 0 | pass |
| baseline_v1_v2 | `C:\Users\Huawei\AppData\Local\Programs\Python\Python311\python.exe scripts/v1_v2_baseline_regression.py --v1-base http://127.0.0.1:18789 --v2-base http://127.0.0.1:18790` | 1 | fail |
| ops_metrics_dashboard_offline | `C:\Users\Huawei\AppData\Local\Programs\Python\Python311\python.exe scripts/phase8_ops_metrics_dashboard.py --version v2-prod-r1 --owner release-manager --skip-live-probes` | 1 | fail |

## 4. 风险与处置动作

- 存在失败检查项（2/3）。
- 依赖变更中包含高风险项（1）。

## 5. 证据

- 依赖变更清单：`docs/templates/Phase8_依赖变更清单模板.json`
- 回归证据：检查项 stdout/stderr tail 已写入 json 报告
