# Phase 7 演练与发布材料归档规范（目录与命名）

更新日期：2026-04-10

## 1. 目标

统一演练与发布材料的归档目录、命名规范和索引方式，确保可追溯、可审计、可复用。

## 2. 目录规范

归档根目录：`docs/archive/phase7/<archive_id>/`

- `drills/`：演练和观测守护输出
- `reviews/`：双周复评、季度审计、版本审计
- `postmortem/`：复盘材料包
- 根目录附带：
  - `manifest.json`（结构化清单）
  - `ARCHIVE_INDEX.md`（人工可读索引）

## 3. 命名规范

- `archive_id`：推荐 `YYYYMMDD`（例：`20260410`）
- 文件保持“来源文件名”不变，避免二次命名导致追溯困难
- 归档索引模板：`docs/templates/Phase7_归档索引模板.md`

## 4. 自动归档脚本

- 脚本：`scripts/phase7_archive_materials.py`
- 默认模式：`copy`（非破坏式）
- 可选模式：`move`（迁移源文件）

若希望“一键先补齐 drill 报告再归档”，可使用串联脚本：

- `scripts/phase7_backfill_and_archive.py`

示例：

```bash
# 预览归档计划
python scripts/phase7_archive_materials.py --archive-id 20260410 --version v2-cutover-r1 --dry-run

# 执行归档（默认 copy）
python scripts/phase7_archive_materials.py --archive-id 20260410 --version v2-cutover-r1 --owner release-manager

# 一键补齐 4 个 drill 报告后再归档
python scripts/phase7_backfill_and_archive.py --archive-id 20260410 --version v2-cutover-r1 --owner release-manager
```

## 5. 闭环要求

1. 每次版本窗口结束后执行一次归档；
2. 季度审计签核前必须确认归档索引与清单完整；
3. 若存在缺失项（`missing_count > 0`），需在 2 个工作日内补齐。
