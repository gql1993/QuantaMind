# 知识库 — 从设计文档中构建可检索的文本知识
# 当前实现：优先使用 PostgreSQL + pgvector，本地轻量向量化；失败时回退关键词匹配

import json
import logging
import os
import re
import hashlib
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

_log = logging.getLogger("quantamind.knowledge_base")

# 知识条目：{id, source, title, content, keywords}
_entries: List[Dict[str, Any]] = []
_loaded = False
_pgvector_synced = False
_EMBED_DIM = 64


def _load_docs():
    """从 docs/ 目录加载所有文档文本到知识库"""
    global _loaded, _pgvector_synced
    if _loaded:
        return
    docs_dir = Path(__file__).resolve().parent.parent.parent / "docs"
    count = 0

    # 加载 Word 文档
    try:
        from docx import Document
        for docx_path in list(docs_dir.glob("*.docx")) + list(docs_dir.glob("QEDA/*.docx")):
            if docx_path.name.startswith("~$"):
                continue
            try:
                doc = Document(str(docx_path))
                paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                # 按段落分块（每 5 段一个条目）
                for i in range(0, len(paragraphs), 5):
                    chunk = "\n".join(paragraphs[i:i+5])
                    if len(chunk) > 30:
                        keywords = _extract_keywords(chunk)
                        _entries.append({
                            "id": f"doc_{count}",
                            "source": docx_path.name,
                            "title": paragraphs[i][:60] if paragraphs[i:] else "",
                            "content": chunk[:1000],
                            "keywords": keywords,
                        })
                        count += 1
            except Exception as e:
                _log.warning("加载文档失败 %s: %s", docx_path.name, e)
    except ImportError:
        _log.warning("python-docx 未安装，跳过 Word 文档")

    # 加载已提取的 JSON 表格数据
    for json_path in docs_dir.glob("*_tables.json"):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                tables = json.load(f)
            for t in tables:
                if t.get("rows"):
                    content = json.dumps(t, ensure_ascii=False)[:800]
                    _entries.append({
                        "id": f"tbl_{count}",
                        "source": json_path.name,
                        "title": " | ".join(t.get("headers", [])[:5]),
                        "content": content,
                        "keywords": _extract_keywords(content),
                    })
                    count += 1
        except Exception:
            pass

    # 加载 Markdown 文档
    for md_path in docs_dir.glob("*.md"):
        try:
            text = md_path.read_text(encoding="utf-8", errors="replace")
            sections = re.split(r'\n#{1,3}\s+', text)
            for sec in sections:
                if len(sec.strip()) > 50:
                    title = sec.split("\n")[0][:60]
                    _entries.append({
                        "id": f"md_{count}",
                        "source": md_path.name,
                        "title": title,
                        "content": sec[:1000],
                        "keywords": _extract_keywords(sec),
                    })
                    count += 1
        except Exception:
            pass

    _loaded = True
    _pgvector_synced = False
    _log.info("知识库加载完成：%d 条知识条目", count)


def _extract_keywords(text: str) -> List[str]:
    """提取关键词（量子芯片相关术语）"""
    keywords = set()
    terms = ["transmon", "xmon", "量子比特", "约瑟夫森", "耦合器", "谐振腔", "频率",
             "电容", "电感", "T1", "T2", "GHz", "MHz", "nH", "fF",
             "版图", "GDS", "DRC", "仿真", "HFSS", "Q3D", "良率", "SPC",
             "校准", "Rabi", "光谱", "读出", "保真度", "CPW", "共面波导",
             "SQUID", "曼哈顿", "Dolan", "蓝宝石", "钽膜", "铝膜",
             "布线", "掩膜", "EBL", "封装", "SMP", "空气桥"]
    text_lower = text.lower()
    for term in terms:
        if term.lower() in text_lower:
            keywords.add(term)
    return list(keywords)[:10]


def _tokenize(text: str) -> List[str]:
    return re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9_]+', text.lower())


def _embed_text(text: str, dim: int = _EMBED_DIM) -> List[float]:
    vec = [0.0] * dim
    for token in _tokenize(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:2], "big") % dim
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        weight = 1.0 + (digest[3] / 255.0)
        vec[idx] += sign * weight
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [round(v / norm, 6) for v in vec]


def _vector_literal(values: List[float]) -> str:
    return "[" + ",".join(f"{v:.6f}" for v in values) + "]"


def _pgvector_cfg() -> Dict[str, Any]:
    from quantamind import config as app_config
    return app_config.get_database_config("ai_pgvector")


def _pg_conn():
    import psycopg

    cfg = _pgvector_cfg()
    return psycopg.connect(
        host=cfg.get("host", "127.0.0.1"),
        port=cfg.get("port", 5432),
        dbname=cfg.get("database", "quantamind_design"),
        user=cfg.get("user", "postgres"),
        password=cfg.get("password", ""),
        connect_timeout=3,
    )


def _ensure_pgvector_schema() -> bool:
    try:
        cfg = _pgvector_cfg()
        table = cfg.get("table", "knowledge_chunks")
        dim = int(cfg.get("dimensions", _EMBED_DIM))
        with _pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        id text PRIMARY KEY,
                        source text,
                        title text,
                        content text,
                        keywords jsonb,
                        embedding vector({dim}),
                        updated_at timestamptz DEFAULT now()
                    )
                    """
                )
                try:
                    cur.execute(
                        f"CREATE INDEX IF NOT EXISTS {table}_embedding_idx ON {table} USING hnsw (embedding vector_cosine_ops)"
                    )
                except Exception:
                    pass
            conn.commit()
        return True
    except Exception as e:
        _log.warning("pgvector schema init failed: %s", e)
        return False


def _sync_entries_to_pgvector() -> bool:
    global _pgvector_synced
    if _pgvector_synced:
        return True
    if not _ensure_pgvector_schema():
        return False
    try:
        cfg = _pgvector_cfg()
        table = cfg.get("table", "knowledge_chunks")
        with _pg_conn() as conn:
            with conn.cursor() as cur:
                for entry in _entries:
                    embedding = _vector_literal(_embed_text(entry["title"] + "\n" + entry["content"]))
                    cur.execute(
                        f"""
                        INSERT INTO {table} (id, source, title, content, keywords, embedding, updated_at)
                        VALUES (%s, %s, %s, %s, %s::jsonb, %s::vector, now())
                        ON CONFLICT (id) DO UPDATE SET
                            source = EXCLUDED.source,
                            title = EXCLUDED.title,
                            content = EXCLUDED.content,
                            keywords = EXCLUDED.keywords,
                            embedding = EXCLUDED.embedding,
                            updated_at = now()
                        """,
                        (
                            entry["id"],
                            entry["source"],
                            entry["title"],
                            entry["content"],
                            json.dumps(entry["keywords"], ensure_ascii=False),
                            embedding,
                        ),
                    )
            conn.commit()
        _pgvector_synced = True
        return True
    except Exception as e:
        _log.warning("pgvector sync failed: %s", e)
        return False


def _search_pgvector(query: str, max_results: int) -> List[Dict[str, Any]]:
    cfg = _pgvector_cfg()
    table = cfg.get("table", "knowledge_chunks")
    qv = _vector_literal(_embed_text(query))
    with _pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, source, title, content, keywords, 1 - (embedding <=> %s::vector) AS score
                FROM {table}
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (qv, qv, max_results),
            )
            rows = cur.fetchall()
    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "source": row[1],
            "title": row[2],
            "content": row[3],
            "keywords": row[4],
            "score": float(row[5]) if row[5] is not None else 0.0,
            "backend": "pgvector",
        })
    return results


def _upsert_entry_to_pgvector(entry: Dict[str, Any]) -> bool:
    if not _ensure_pgvector_schema():
        return False
    try:
        cfg = _pgvector_cfg()
        table = cfg.get("table", "knowledge_chunks")
        with _pg_conn() as conn:
            with conn.cursor() as cur:
                embedding = _vector_literal(_embed_text(entry["title"] + "\n" + entry["content"]))
                cur.execute(
                    f"""
                    INSERT INTO {table} (id, source, title, content, keywords, embedding, updated_at)
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s::vector, now())
                    ON CONFLICT (id) DO UPDATE SET
                        source = EXCLUDED.source,
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        keywords = EXCLUDED.keywords,
                        embedding = EXCLUDED.embedding,
                        updated_at = now()
                    """,
                    (
                        entry["id"],
                        entry["source"],
                        entry["title"],
                        entry["content"],
                        json.dumps(entry.get("keywords", []), ensure_ascii=False),
                        embedding,
                    ),
                )
            conn.commit()
        return True
    except Exception as e:
        _log.warning("pgvector upsert failed for %s: %s", entry.get("id"), e)
        return False


def _chunk_text(text: str, size: int = 800, overlap: int = 120) -> List[str]:
    cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not cleaned:
        return []
    if len(cleaned) <= size:
        return [cleaned]
    chunks = []
    step = max(size - overlap, 1)
    for i in range(0, len(cleaned), step):
        chunk = cleaned[i:i + size].strip()
        if chunk:
            chunks.append(chunk)
        if i + size >= len(cleaned):
            break
    return chunks


def _record_text(record: Dict[str, Any]) -> str:
    pr = record.get("parse_result") or {}
    pieces = [
        record.get("filename", ""),
        record.get("file_type", ""),
        pr.get("text_preview", ""),
        pr.get("code_preview", ""),
        pr.get("preview", ""),
        pr.get("docstring", ""),
    ]
    if pr.get("titles"):
        pieces.append("\n".join(pr["titles"][:20]))
    if pr.get("imports"):
        pieces.append("\n".join(pr["imports"][:20]))
    if pr.get("headers"):
        pieces.append(" | ".join(pr["headers"][:20]))
    if pr.get("rows"):
        pieces.append("\n".join(" | ".join(map(str, row[:10])) for row in pr["rows"][:30]))
    if pr.get("tables_data"):
        for table in pr["tables_data"][:10]:
            pieces.append(" | ".join(table.get("headers", [])[:10]))
            pieces.append("\n".join(" | ".join(map(str, row[:10])) for row in table.get("rows", [])[:20]))
    if pr.get("extracted_params"):
        pieces.append(json.dumps(pr["extracted_params"], ensure_ascii=False))
    if not any(pieces):
        pieces.append(json.dumps(pr, ensure_ascii=False))
    return "\n\n".join(str(p) for p in pieces if p)


def index_library_record(record: Dict[str, Any]) -> Dict[str, Any]:
    file_id = record.get("file_id")
    if not file_id:
        return {"indexed": 0, "backend": "none", "error": "missing file_id"}

    base_text = _record_text(record)
    chunks = _chunk_text(base_text)
    if not chunks:
        return {"indexed": 0, "backend": "none", "error": "no text extracted"}

    indexed = 0
    for idx, chunk in enumerate(chunks):
        entry = {
            "id": f"lib_{file_id}_{idx}",
            "source": f"library:{record.get('filename', '')}",
            "title": f"{record.get('filename', '')} / 分块 {idx + 1}",
            "content": chunk,
            "keywords": _extract_keywords(chunk),
        }
        # 更新内存关键词索引，便于回退搜索也能命中新上传文件
        _entries[:] = [e for e in _entries if e.get("id") != entry["id"]]
        _entries.append(entry)
        if _upsert_entry_to_pgvector(entry):
            indexed += 1

    return {"indexed": indexed, "chunks": len(chunks), "backend": "pgvector" if indexed else "keyword"}


def index_external_record(record_id: str, source: str, title: str, content: str,
                          keywords: Optional[List[str]] = None) -> Dict[str, Any]:
    if not record_id:
        return {"indexed": 0, "backend": "none", "error": "missing record_id"}

    chunks = _chunk_text(content)
    if not chunks:
        return {"indexed": 0, "backend": "none", "error": "empty content"}

    indexed = 0
    for idx, chunk in enumerate(chunks):
        entry = {
            "id": f"ext_{record_id}_{idx}",
            "source": source,
            "title": title if idx == 0 else f"{title} / 分块 {idx + 1}",
            "content": chunk,
            "keywords": list(dict.fromkeys((keywords or []) + _extract_keywords(chunk)))[:16],
        }
        _entries[:] = [e for e in _entries if e.get("id") != entry["id"]]
        _entries.append(entry)
        if _upsert_entry_to_pgvector(entry):
            indexed += 1

    return {"indexed": indexed, "chunks": len(chunks), "backend": "pgvector" if indexed else "keyword"}


def delete_library_record(file_id: str) -> Dict[str, Any]:
    prefix = f"lib_{file_id}_"
    removed_mem = 0
    before = len(_entries)
    _entries[:] = [e for e in _entries if not str(e.get("id", "")).startswith(prefix)]
    removed_mem = before - len(_entries)
    removed_db = 0
    try:
        if _ensure_pgvector_schema():
            cfg = _pgvector_cfg()
            table = cfg.get("table", "knowledge_chunks")
            with _pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"DELETE FROM {table} WHERE id LIKE %s", (prefix + "%",))
                    removed_db = cur.rowcount or 0
                conn.commit()
    except Exception as e:
        _log.warning("pgvector delete failed for %s: %s", file_id, e)
    return {"removed_memory": removed_mem, "removed_pgvector": removed_db}


def search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """搜索知识库（关键词匹配 + 相关性排序）"""
    _load_docs()
    if not query:
        return []

    if _sync_entries_to_pgvector():
        try:
            return _search_pgvector(query, max_results)
        except Exception as e:
            _log.warning("pgvector search failed, fallback to keyword match: %s", e)

    query_lower = query.lower()
    query_words = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', query_lower))

    scored = []
    for entry in _entries:
        score = 0
        content_lower = entry["content"].lower()
        title_lower = entry["title"].lower()
        # 标题匹配加权
        for w in query_words:
            if w in title_lower:
                score += 3
            if w in content_lower:
                score += 1
        # 关键词匹配
        for kw in entry["keywords"]:
            if kw.lower() in query_lower:
                score += 2
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score": s, **e, "backend": "keyword"} for s, e in scored[:max_results]]


def get_stats() -> Dict[str, Any]:
    _load_docs()
    sources = {}
    for e in _entries:
        src = e["source"]
        sources[src] = sources.get(src, 0) + 1
    return {"total_entries": len(_entries), "sources": sources, "loaded": _loaded, "pgvector_synced": _pgvector_synced}
