# Phase 7 演练与发布材料归档索引

归档批次：{{ARCHIVE_ID}}  
归档日期：{{DATE}}  
版本标识：{{VERSION}}  
归档负责人：{{OWNER}}  
归档模式：{{MODE}}

---

## 1. 目录结构

根目录：`{{ARCHIVE_ROOT}}`

- `drills/`：演练与守护类报告
- `reviews/`：双周复评、季度审计、版本审计
- `postmortem/`：复盘材料包

## 2. 文件清单

| 分组 | 文件 | 源路径 |
|---|---|---|
{{FILE_ROWS}}

## 3. 说明

- 归档清单以 `manifest.json` 为准；
- 若为 `copy` 模式，源文件保持不变；
- 若为 `move` 模式，源文件迁移到归档目录。
