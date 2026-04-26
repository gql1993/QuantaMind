# Phase 6：V1/V2 对比基线与回归脚本

更新日期：2026-04-09

## 1. 目标

建立可重复执行的 V1/V2 基线检查与回归入口，用于阶段性验证迁移质量。

## 2. 新增脚本

### 2.1 基线对比脚本

- 路径：`scripts/v1_v2_baseline_regression.py`
- 默认地址：
  - V1: `http://127.0.0.1:18789`
  - V2: `http://127.0.0.1:18790`
- 产出：
  - JSON 报告：`docs/reports/phase6_v1_v2_baseline_latest.json`
- 核心检查项：
  1. `v1_status`
  2. `v2_health`
  3. `v1_library_stats`
  4. `v2_library_stats`
  5. `v2_pipeline_templates`
  6. `v2_library_upload_and_ingest`（上传 + task 完成）
  7. `v2_pipeline_execute`（触发 + task 收敛）

示例：

```bash
python scripts/v1_v2_baseline_regression.py --v1-base http://127.0.0.1:18789 --v2-base http://127.0.0.1:18790
```

### 2.2 Phase 6 回归总入口

- 路径：`scripts/run_phase6_regression.py`
- 默认执行：
  1. `pytest tests/v2 -q`
  2. `v1_v2_baseline_regression.py`

示例：

```bash
python scripts/run_phase6_regression.py --v1-base http://127.0.0.1:18789 --v2-base http://127.0.0.1:18790
```

可选：

- `--skip-tests`
- `--skip-baseline`

## 3. 基线使用建议

- 每次 Phase 6/7 关键迁移后执行一次总入口脚本
- 将 `docs/reports/phase6_v1_v2_baseline_latest.json` 纳入评审附件
- 若 baseline 失败，先定位具体 check，再决定回退或修复策略

## 4. 与路线图关系

- 本文对应路线图中“Phase 6：沉淀 V1/V2 对比基线与回归脚本”项
- 后续可扩展：
  - 增加延迟/成功率统计字段
  - 增加审批链路与 artifact viewer UI 冒烟脚本
