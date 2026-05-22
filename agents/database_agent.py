"""
agents/database_agent.py
Production-grade Database Agent — 42 features across 7 categories.
AI layer  : Groq (llama-4-scout) for NL→SQL, analysis, insights, summaries.
DB layer  : SQLite (built-in) · PostgreSQL (psycopg2) · MySQL (pymysql)
            — mock/demo mode when no DB is configured.

Categories:
  Connection & Setup, Read & Query, Write Operations, AI-Powered Analysis,
  Data Export, Cross-Agent Integration, Safety & Validation

Stack: langchain_groq · ChatGroq · meta-llama/llama-4-scout-17b-16e-instruct
       sqlite3 (stdlib) · psycopg2 (optional) · pymysql (optional)
       pandas · csv · json · openpyxl
"""

from __future__ import annotations
import os, re, json, csv, sqlite3, io, traceback
from datetime import datetime
from typing import Any
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import AgentState

load_dotenv()

# ── LLM ───────────────────────────────────────────────────────────────────────

_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.2,
            max_tokens=4096,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm

def _llm_call(system: str, user: str) -> str:
    resp = _get_llm().invoke([SystemMessage(content=system), HumanMessage(content=user)])
    return resp.content.strip()

def _parse_json(raw: str) -> Any:
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)

# ── DB Connection helpers ──────────────────────────────────────────────────────

def _get_db_type() -> str:
    return os.getenv("DB_TYPE", "sqlite").lower()

def _get_connection():
    db_type = _get_db_type()
    if db_type == "sqlite":
        db_path = os.getenv("DB_SQLITE_PATH", "database.db")
        return sqlite3.connect(db_path), "sqlite"
    elif db_type == "postgresql":
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database=os.getenv("DB_NAME", ""),
                user=os.getenv("DB_USER", ""),
                password=os.getenv("DB_PASSWORD", ""),
            )
            return conn, "postgresql"
        except ImportError:
            raise RuntimeError("psycopg2 not installed. Run: pip install psycopg2-binary")
    elif db_type == "mysql":
        try:
            import pymysql
            conn = pymysql.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "3306")),
                database=os.getenv("DB_NAME", ""),
                user=os.getenv("DB_USER", ""),
                password=os.getenv("DB_PASSWORD", ""),
                cursorclass=pymysql.cursors.DictCursor,
            )
            return conn, "mysql"
        except ImportError:
            raise RuntimeError("pymysql not installed. Run: pip install pymysql")
    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}. Use sqlite | postgresql | mysql")

def _execute_query(query: str, params=None, fetch: bool = True) -> list[dict]:
    conn, db_type = _get_connection()
    try:
        if db_type == "sqlite":
            conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params or [])
        if fetch:
            rows = cur.fetchall()
            if db_type == "sqlite":
                return [dict(r) for r in rows]
            elif db_type == "mysql":
                return list(rows)
            else:
                cols = [d[0] for d in cur.description] if cur.description else []
                return [dict(zip(cols, r)) for r in rows]
        else:
            conn.commit()
            return [{"affected_rows": cur.rowcount}]
    finally:
        conn.close()

def _get_schema_text() -> str:
    db_type = _get_db_type()
    try:
        if db_type == "sqlite":
            rows = _execute_query(
                "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            return "\n\n".join(f"Table: {r['name']}\n{r['sql']}" for r in rows)
        elif db_type == "postgresql":
            rows = _execute_query("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)
            schema = {}
            for r in rows:
                t = r["table_name"]
                schema.setdefault(t, []).append(f"  {r['column_name']} {r['data_type']}")
            return "\n\n".join(f"Table: {t}\n" + "\n".join(cols) for t, cols in schema.items())
        elif db_type == "mysql":
            tables = _execute_query("SHOW TABLES")
            lines = []
            for t in tables:
                tname = list(t.values())[0]
                cols = _execute_query(f"DESCRIBE `{tname}`")
                col_str = "\n".join(f"  {c['Field']} {c['Type']}" for c in cols)
                lines.append(f"Table: {tname}\n{col_str}")
            return "\n\n".join(lines)
    except Exception as e:
        return f"[schema unavailable: {e}]"

def _mock_mode() -> bool:
    db_type = _get_db_type()
    if db_type == "sqlite":
        return False  # SQLite always works
    return not all([os.getenv("DB_HOST"), os.getenv("DB_NAME"), os.getenv("DB_USER")])

def _write_audit_log(query: str, mode: str):
    log_path = os.getenv("DB_AUDIT_LOG", "outputs/db_audit.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] mode={mode} | {query[:300]}\n")


# ════════════════════════════════════════════════════════════════════════════════
# CATEGORY 1 — Connection & Setup
# ════════════════════════════════════════════════════════════════════════════════

def feat_connect(task: str, db_context: dict) -> dict:
    """Feature 1 — Test/verify DB connection."""
    try:
        conn, db_type = _get_connection()
        conn.close()
        return {
            "status": "connected",
            "db_type": db_type,
            "host": os.getenv("DB_HOST", "local"),
            "database": os.getenv("DB_SQLITE_PATH", os.getenv("DB_NAME", "database.db")),
            "message": f"Successfully connected to {db_type} database.",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def feat_list_databases(task: str, db_context: dict) -> dict:
    """Feature 2 — List all databases / schemas on the server."""
    db_type = _get_db_type()
    try:
        if db_type == "sqlite":
            db_path = os.getenv("DB_SQLITE_PATH", "database.db")
            return {"databases": [db_path], "note": "SQLite uses a single file per database."}
        elif db_type == "postgresql":
            rows = _execute_query("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname")
            return {"databases": [r["datname"] for r in rows]}
        elif db_type == "mysql":
            rows = _execute_query("SHOW DATABASES")
            return {"databases": [list(r.values())[0] for r in rows]}
    except Exception as e:
        return {"error": str(e)}

def feat_list_tables(task: str, db_context: dict) -> dict:
    """Feature 3 — List all tables in the current database."""
    db_type = _get_db_type()
    try:
        if db_type == "sqlite":
            rows = _execute_query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [r["name"] for r in rows]
        elif db_type == "postgresql":
            rows = _execute_query(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
            )
            tables = [r["table_name"] for r in rows]
        elif db_type == "mysql":
            rows = _execute_query("SHOW TABLES")
            tables = [list(r.values())[0] for r in rows]
        else:
            tables = []
        return {"tables": tables, "count": len(tables)}
    except Exception as e:
        return {"error": str(e)}

def feat_table_schema(task: str, db_context: dict) -> dict:
    """Feature 4 — Show schema (columns + types) for a specific table."""
    table = db_context.get("table", "")
    if not table:
        table = _llm_call(
            "Extract the table name from the user task. Return only the table name, nothing else.",
            task
        ).strip().strip('"\'')
    db_type = _get_db_type()
    try:
        if db_type == "sqlite":
            rows = _execute_query(f"PRAGMA table_info('{table}')")
            columns = [{"name": r["name"], "type": r["type"], "not_null": bool(r["notnull"]),
                        "default": r["dflt_value"], "primary_key": bool(r["pk"])} for r in rows]
        elif db_type == "postgresql":
            rows = _execute_query(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = '{table}' ORDER BY ordinal_position
            """)
            columns = rows
        elif db_type == "mysql":
            rows = _execute_query(f"DESCRIBE `{table}`")
            columns = rows
        else:
            columns = []
        return {"table": table, "columns": columns, "column_count": len(columns)}
    except Exception as e:
        return {"error": str(e)}

def feat_health_check(task: str, db_context: dict) -> dict:
    """Feature 5 — Full health check: connection, table count, row counts."""
    try:
        conn_result = feat_connect(task, db_context)
        if conn_result.get("status") != "connected":
            return conn_result
        tables_result = feat_list_tables(task, db_context)
        tables = tables_result.get("tables", [])
        table_stats = []
        for t in tables[:10]:
            try:
                count = _execute_query(f"SELECT COUNT(*) as c FROM {t}")
                table_stats.append({"table": t, "row_count": count[0]["c"]})
            except:
                table_stats.append({"table": t, "row_count": "error"})
        return {
            "status": "healthy",
            "db_type": conn_result["db_type"],
            "table_count": len(tables),
            "table_stats": table_stats,
            "checked_at": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def feat_disconnect(task: str, db_context: dict) -> dict:
    """Feature 6 — Confirm clean disconnect (connections are per-query, this confirms state)."""
    return {
        "status": "disconnected",
        "message": "Database connections are managed per-query. All connections are cleanly closed after each operation.",
        "db_type": _get_db_type(),
    }


# ════════════════════════════════════════════════════════════════════════════════
# CATEGORY 2 — Read & Query
# ════════════════════════════════════════════════════════════════════════════════

def feat_query(task: str, db_context: dict) -> dict:
    """Feature 7 — Run a raw SELECT query provided by the user."""
    query = db_context.get("query", "").strip()
    if not query:
        return {"error": "No query provided. Set db_context['query'] with your SELECT statement."}
    if not re.match(r"^\s*SELECT", query, re.IGNORECASE):
        return {"error": "Only SELECT queries allowed in feat_query. Use feat_write for mutations."}
    _write_audit_log(query, "query")
    try:
        rows = _execute_query(query)
        return {"rows": rows, "count": len(rows), "query": query}
    except Exception as e:
        return {"error": str(e), "query": query}

def feat_filter(task: str, db_context: dict) -> dict:
    """Feature 8 — Filter rows from a table by a condition."""
    table = db_context.get("table", "")
    condition = db_context.get("condition", "1=1")
    limit = db_context.get("limit", 100)
    if not table:
        return {"error": "Set db_context['table'] to the table name."}
    query = f"SELECT * FROM {table} WHERE {condition} LIMIT {limit}"
    _write_audit_log(query, "filter")
    try:
        rows = _execute_query(query)
        return {"table": table, "condition": condition, "rows": rows, "count": len(rows)}
    except Exception as e:
        return {"error": str(e)}

def feat_search(task: str, db_context: dict) -> dict:
    """Feature 9 — Full-text search across all text columns of a table."""
    table = db_context.get("table", "")
    keyword = db_context.get("keyword", "")
    if not table or not keyword:
        return {"error": "Set db_context['table'] and db_context['keyword']."}
    schema = feat_table_schema(task, db_context)
    text_cols = [c["name"] for c in schema.get("columns", [])
                 if any(t in str(c.get("type","")).upper() for t in ["TEXT","CHAR","VARCHAR","STRING"])]
    if not text_cols:
        return {"error": f"No text columns found in table '{table}'."}
    where = " OR ".join(f"CAST({col} AS TEXT) LIKE '%{keyword}%'" for col in text_cols)
    query = f"SELECT * FROM {table} WHERE {where} LIMIT 100"
    _write_audit_log(query, "search")
    try:
        rows = _execute_query(query)
        return {"table": table, "keyword": keyword, "columns_searched": text_cols,
                "rows": rows, "count": len(rows)}
    except Exception as e:
        return {"error": str(e)}

def feat_paginate(task: str, db_context: dict) -> dict:
    """Feature 10 — Paginate results with limit and offset."""
    table = db_context.get("table", "")
    page = int(db_context.get("page", 1))
    page_size = int(db_context.get("page_size", 20))
    offset = (page - 1) * page_size
    order_by = db_context.get("order_by", "rowid")
    if not table:
        return {"error": "Set db_context['table']."}
    query = f"SELECT * FROM {table} ORDER BY {order_by} LIMIT {page_size} OFFSET {offset}"
    _write_audit_log(query, "paginate")
    try:
        rows = _execute_query(query)
        total_rows = _execute_query(f"SELECT COUNT(*) as c FROM {table}")[0]["c"]
        return {
            "table": table, "page": page, "page_size": page_size,
            "total_rows": total_rows, "total_pages": -(-total_rows // page_size),
            "rows": rows, "count": len(rows),
        }
    except Exception as e:
        return {"error": str(e)}

def feat_sort(task: str, db_context: dict) -> dict:
    """Feature 11 — Sort table results by a column."""
    table = db_context.get("table", "")
    column = db_context.get("column", "")
    order = db_context.get("order", "ASC").upper()
    limit = int(db_context.get("limit", 50))
    if not table or not column:
        return {"error": "Set db_context['table'] and db_context['column']."}
    query = f"SELECT * FROM {table} ORDER BY {column} {order} LIMIT {limit}"
    _write_audit_log(query, "sort")
    try:
        rows = _execute_query(query)
        return {"table": table, "sorted_by": column, "order": order, "rows": rows, "count": len(rows)}
    except Exception as e:
        return {"error": str(e)}

def feat_join(task: str, db_context: dict) -> dict:
    """Feature 12 — Join two tables on a common key."""
    table1 = db_context.get("table1", "")
    table2 = db_context.get("table2", "")
    on = db_context.get("on", "")
    join_type = db_context.get("join_type", "INNER").upper()
    limit = int(db_context.get("limit", 100))
    if not all([table1, table2, on]):
        return {"error": "Set db_context['table1'], ['table2'], and ['on'] (e.g. 'orders.user_id = users.id')."}
    query = f"SELECT * FROM {table1} {join_type} JOIN {table2} ON {on} LIMIT {limit}"
    _write_audit_log(query, "join")
    try:
        rows = _execute_query(query)
        return {"table1": table1, "table2": table2, "join_type": join_type, "on": on,
                "rows": rows, "count": len(rows)}
    except Exception as e:
        return {"error": str(e)}

def feat_aggregate(task: str, db_context: dict) -> dict:
    """Feature 13 — Aggregate: COUNT, SUM, AVG, MAX, MIN with optional GROUP BY."""
    table = db_context.get("table", "")
    agg_func = db_context.get("agg_func", "COUNT").upper()
    column = db_context.get("column", "*")
    group_by = db_context.get("group_by", "")
    condition = db_context.get("condition", "")
    if not table:
        return {"error": "Set db_context['table']."}
    select = f"{agg_func}({column}) as result"
    if group_by:
        select = f"{group_by}, {select}"
    query = f"SELECT {select} FROM {table}"
    if condition:
        query += f" WHERE {condition}"
    if group_by:
        query += f" GROUP BY {group_by} ORDER BY result DESC LIMIT 50"
    _write_audit_log(query, "aggregate")
    try:
        rows = _execute_query(query)
        return {"table": table, "aggregation": f"{agg_func}({column})", "group_by": group_by,
                "rows": rows, "count": len(rows)}
    except Exception as e:
        return {"error": str(e)}

def feat_distinct(task: str, db_context: dict) -> dict:
    """Feature 14 — Get distinct values in a column."""
    table = db_context.get("table", "")
    column = db_context.get("column", "")
    if not table or not column:
        return {"error": "Set db_context['table'] and db_context['column']."}
    query = f"SELECT DISTINCT {column} FROM {table} ORDER BY {column} LIMIT 200"
    _write_audit_log(query, "distinct")
    try:
        rows = _execute_query(query)
        return {"table": table, "column": column, "distinct_values": [r[column] for r in rows],
                "count": len(rows)}
    except Exception as e:
        return {"error": str(e)}


# ════════════════════════════════════════════════════════════════════════════════
# CATEGORY 3 — Write Operations
# ════════════════════════════════════════════════════════════════════════════════

def _check_readonly(mode: str) -> dict | None:
    if os.getenv("DB_READ_ONLY", "false").lower() == "true":
        return {"error": f"Database is in READ-ONLY mode. Cannot run '{mode}'. Set DB_READ_ONLY=false to enable writes."}
    return None

def feat_insert(task: str, db_context: dict) -> dict:
    """Feature 15 — Insert a new row into a table."""
    guard = _check_readonly("insert")
    if guard: return guard
    table = db_context.get("table", "")
    data = db_context.get("data", {})
    if not table or not data:
        return {"error": "Set db_context['table'] and db_context['data'] (dict of column:value)."}
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?" if _get_db_type() == "sqlite" else "%s"] * len(data))
    query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    _write_audit_log(query, "insert")
    try:
        result = _execute_query(query, list(data.values()), fetch=False)
        return {"status": "inserted", "table": table, "data": data, "result": result}
    except Exception as e:
        return {"error": str(e)}

def feat_update(task: str, db_context: dict) -> dict:
    """Feature 16 — Update rows matching a condition."""
    guard = _check_readonly("update")
    if guard: return guard
    table = db_context.get("table", "")
    updates = db_context.get("updates", {})
    condition = db_context.get("condition", "")
    if not table or not updates or not condition:
        return {"error": "Set db_context['table'], ['updates'] (dict), and ['condition'] (WHERE clause)."}
    ph = "?" if _get_db_type() == "sqlite" else "%s"
    set_clause = ", ".join(f"{k} = {ph}" for k in updates)
    query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
    _write_audit_log(query, "update")
    try:
        result = _execute_query(query, list(updates.values()), fetch=False)
        return {"status": "updated", "table": table, "updates": updates,
                "condition": condition, "result": result}
    except Exception as e:
        return {"error": str(e)}

def feat_delete(task: str, db_context: dict) -> dict:
    """Feature 17 — Delete rows matching a condition (requires explicit condition)."""
    guard = _check_readonly("delete")
    if guard: return guard
    table = db_context.get("table", "")
    condition = db_context.get("condition", "")
    if not table or not condition:
        return {"error": "Set db_context['table'] and db_context['condition']. A WHERE condition is REQUIRED for safety."}
    if condition.strip().lower() in ("1=1", "true", "1"):
        return {"error": "Refusing to delete all rows. Provide a specific condition."}
    query = f"DELETE FROM {table} WHERE {condition}"
    _write_audit_log(query, "delete")
    try:
        result = _execute_query(query, fetch=False)
        return {"status": "deleted", "table": table, "condition": condition, "result": result}
    except Exception as e:
        return {"error": str(e)}

def feat_bulk_insert(task: str, db_context: dict) -> dict:
    """Feature 18 — Bulk insert rows from a list of dicts or a CSV file path."""
    guard = _check_readonly("bulk_insert")
    if guard: return guard
    table = db_context.get("table", "")
    rows_data = db_context.get("rows", [])
    csv_path = db_context.get("csv_path", "")
    if csv_path and os.path.exists(csv_path):
        with open(csv_path, newline="", encoding="utf-8") as f:
            rows_data = list(csv.DictReader(f))
    if not table or not rows_data:
        return {"error": "Set db_context['table'] and db_context['rows'] (list of dicts) or ['csv_path']."}
    cols = list(rows_data[0].keys())
    ph = "?" if _get_db_type() == "sqlite" else "%s"
    placeholders = ", ".join([ph] * len(cols))
    query = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
    conn, db_type = _get_connection()
    try:
        cur = conn.cursor()
        values = [list(r.values()) for r in rows_data]
        cur.executemany(query, values)
        conn.commit()
        return {"status": "bulk_inserted", "table": table, "rows_inserted": len(rows_data)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def feat_upsert(task: str, db_context: dict) -> dict:
    """Feature 19 — Upsert (INSERT OR REPLACE) a row."""
    guard = _check_readonly("upsert")
    if guard: return guard
    table = db_context.get("table", "")
    data = db_context.get("data", {})
    if not table or not data:
        return {"error": "Set db_context['table'] and db_context['data']."}
    db_type = _get_db_type()
    cols = ", ".join(data.keys())
    ph = "?" if db_type == "sqlite" else "%s"
    placeholders = ", ".join([ph] * len(data))
    if db_type == "sqlite":
        query = f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})"
    elif db_type == "postgresql":
        query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
    else:
        query = f"REPLACE INTO {table} ({cols}) VALUES ({placeholders})"
    _write_audit_log(query, "upsert")
    try:
        result = _execute_query(query, list(data.values()), fetch=False)
        return {"status": "upserted", "table": table, "data": data, "result": result}
    except Exception as e:
        return {"error": str(e)}

def feat_truncate(task: str, db_context: dict) -> dict:
    """Feature 20 — Truncate a table (delete all rows, keep structure). Requires confirm=True."""
    guard = _check_readonly("truncate")
    if guard: return guard
    table = db_context.get("table", "")
    confirm = db_context.get("confirm", False)
    if not table:
        return {"error": "Set db_context['table']."}
    if not confirm:
        return {"error": "Set db_context['confirm'] = True to confirm truncation. This deletes ALL rows."}
    db_type = _get_db_type()
    query = f"DELETE FROM {table}" if db_type == "sqlite" else f"TRUNCATE TABLE {table}"
    _write_audit_log(query, "truncate")
    try:
        result = _execute_query(query, fetch=False)
        return {"status": "truncated", "table": table, "result": result}
    except Exception as e:
        return {"error": str(e)}


# ════════════════════════════════════════════════════════════════════════════════
# CATEGORY 4 — AI-Powered Analysis
# ════════════════════════════════════════════════════════════════════════════════

def feat_nl_to_sql(task: str, db_context: dict) -> dict:
    """Feature 21 — Natural language → SQL query (execute it too)."""
    schema = _get_schema_text()
    nl_query = db_context.get("nl_query", task)
    system = f"""You are an expert SQL query generator.
Database type: {_get_db_type()}
Schema:
{schema}

Rules:
- Generate a single valid SQL SELECT query only.
- Return ONLY the SQL, no explanation, no markdown.
- Never generate DROP, DELETE, UPDATE, INSERT.
- Use table/column names exactly as in schema."""
    sql = _llm_call(system, f"Convert this to SQL: {nl_query}")
    sql = re.sub(r"^```sql\s*|```$", "", sql.strip())
    _write_audit_log(sql, "nl_to_sql")
    try:
        rows = _execute_query(sql)
        return {"nl_query": nl_query, "generated_sql": sql, "rows": rows, "count": len(rows)}
    except Exception as e:
        return {"nl_query": nl_query, "generated_sql": sql, "error": str(e)}

def feat_summarize_table(task: str, db_context: dict) -> dict:
    """Feature 22 — Summarize an entire table in plain English using AI."""
    table = db_context.get("table", "")
    if not table:
        return {"error": "Set db_context['table']."}
    try:
        rows = _execute_query(f"SELECT * FROM {table} LIMIT 50")
        count = _execute_query(f"SELECT COUNT(*) as c FROM {table}")[0]["c"]
        schema = feat_table_schema(task, {"table": table})
        summary = _llm_call(
            "You are a data analyst. Summarize the following database table in plain English. "
            "Include: what the table is about, key patterns, notable values, and row count.",
            f"Table: {table}\nTotal rows: {count}\nSchema: {json.dumps(schema)}\nSample rows:\n{json.dumps(rows[:20], default=str)}"
        )
        return {"table": table, "total_rows": count, "summary": summary}
    except Exception as e:
        return {"error": str(e)}

def feat_find_anomalies(task: str, db_context: dict) -> dict:
    """Feature 23 — Detect anomalies and outliers in a table using AI."""
    table = db_context.get("table", "")
    if not table:
        return {"error": "Set db_context['table']."}
    try:
        rows = _execute_query(f"SELECT * FROM {table} LIMIT 200")
        analysis = _llm_call(
            "You are a data quality expert. Analyze the following data and identify anomalies, outliers, "
            "unusual patterns, missing values, or suspicious entries. Be specific.",
            f"Table: {table}\nData:\n{json.dumps(rows, default=str)}"
        )
        return {"table": table, "rows_analyzed": len(rows), "anomaly_report": analysis}
    except Exception as e:
        return {"error": str(e)}

def feat_find_duplicates(task: str, db_context: dict) -> dict:
    """Feature 24 — Detect duplicate rows in a table."""
    table = db_context.get("table", "")
    columns = db_context.get("columns", [])
    if not table:
        return {"error": "Set db_context['table']."}
    try:
        schema = feat_table_schema(task, {"table": table})
        all_cols = [c["name"] for c in schema.get("columns", [])]
        check_cols = columns if columns else all_cols
        col_str = ", ".join(check_cols)
        query = f"""
            SELECT {col_str}, COUNT(*) as duplicate_count
            FROM {table}
            GROUP BY {col_str}
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 50
        """
        rows = _execute_query(query)
        return {"table": table, "columns_checked": check_cols,
                "duplicate_groups": rows, "count": len(rows)}
    except Exception as e:
        return {"error": str(e)}

def feat_data_quality(task: str, db_context: dict) -> dict:
    """Feature 25 — Column-level data quality report: nulls, empties, type mismatches."""
    table = db_context.get("table", "")
    if not table:
        return {"error": "Set db_context['table']."}
    try:
        schema = feat_table_schema(task, {"table": table})
        columns = [c["name"] for c in schema.get("columns", [])]
        total = _execute_query(f"SELECT COUNT(*) as c FROM {table}")[0]["c"]
        report = []
        for col in columns:
            null_count = _execute_query(f"SELECT COUNT(*) as c FROM {table} WHERE {col} IS NULL")[0]["c"]
            report.append({
                "column": col,
                "total_rows": total,
                "null_count": null_count,
                "null_pct": round(null_count / total * 100, 2) if total else 0,
                "fill_rate_pct": round((total - null_count) / total * 100, 2) if total else 0,
            })
        return {"table": table, "total_rows": total, "column_report": report}
    except Exception as e:
        return {"error": str(e)}

def feat_trend_analysis(task: str, db_context: dict) -> dict:
    """Feature 26 — Trend analysis over a datetime column."""
    table = db_context.get("table", "")
    date_col = db_context.get("date_column", "")
    value_col = db_context.get("value_column", "")
    if not table or not date_col:
        return {"error": "Set db_context['table'] and db_context['date_column']."}
    try:
        agg = f"SUM({value_col})" if value_col else "COUNT(*)"
        query = f"""
            SELECT strftime('%Y-%m', {date_col}) as period, {agg} as value
            FROM {table}
            WHERE {date_col} IS NOT NULL
            GROUP BY period ORDER BY period
        """
        rows = _execute_query(query)
        ai_summary = _llm_call(
            "You are a data analyst. Summarize this time-series trend in 3-4 sentences.",
            f"Table: {table}, Date column: {date_col}\nData: {json.dumps(rows, default=str)}"
        )
        return {"table": table, "date_column": date_col, "value_column": value_col or "COUNT",
                "trend_data": rows, "ai_summary": ai_summary}
    except Exception as e:
        return {"error": str(e)}

def feat_correlation(task: str, db_context: dict) -> dict:
    """Feature 27 — Correlation analysis between two numeric columns using AI."""
    table = db_context.get("table", "")
    col1 = db_context.get("column1", "")
    col2 = db_context.get("column2", "")
    if not all([table, col1, col2]):
        return {"error": "Set db_context['table'], ['column1'], ['column2']."}
    try:
        rows = _execute_query(f"SELECT {col1}, {col2} FROM {table} WHERE {col1} IS NOT NULL AND {col2} IS NOT NULL LIMIT 500")
        analysis = _llm_call(
            "You are a statistician. Analyze the correlation between these two columns. "
            "Describe the relationship, strength, direction, and any notable patterns.",
            f"Table: {table}\nColumn 1: {col1}\nColumn 2: {col2}\nData sample: {json.dumps(rows[:50], default=str)}"
        )
        return {"table": table, "column1": col1, "column2": col2,
                "sample_size": len(rows), "correlation_analysis": analysis}
    except Exception as e:
        return {"error": str(e)}

def feat_auto_insights(task: str, db_context: dict) -> dict:
    """Feature 28 — Auto-generate top 5 business insights from a query result or table."""
    table = db_context.get("table", "")
    query = db_context.get("query", "")
    if not table and not query:
        return {"error": "Set db_context['table'] or db_context['query']."}
    try:
        if query:
            rows = _execute_query(query)
        else:
            rows = _execute_query(f"SELECT * FROM {table} LIMIT 100")
        insights = _llm_call(
            "You are a senior business analyst. Generate exactly 5 actionable business insights "
            "from this data. Number them 1-5. Be specific and data-driven.",
            f"Data:\n{json.dumps(rows, default=str)}"
        )
        return {"source": table or "custom_query", "rows_analyzed": len(rows), "insights": insights}
    except Exception as e:
        return {"error": str(e)}


# ════════════════════════════════════════════════════════════════════════════════
# CATEGORY 5 — Data Export
# ════════════════════════════════════════════════════════════════════════════════

def feat_export_csv(task: str, db_context: dict) -> dict:
    """Feature 29 — Export a table or query result to CSV."""
    table = db_context.get("table", "")
    query = db_context.get("query", "")
    output_path = db_context.get("output_path", f"outputs/db_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sql = query or f"SELECT * FROM {table}"
    try:
        rows = _execute_query(sql)
        if not rows:
            return {"error": "No rows returned to export."}
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return {"status": "exported", "format": "csv", "rows": len(rows), "output_path": output_path}
    except Exception as e:
        return {"error": str(e)}

def feat_export_json(task: str, db_context: dict) -> dict:
    """Feature 30 — Export a table or query result to JSON."""
    table = db_context.get("table", "")
    query = db_context.get("query", "")
    output_path = db_context.get("output_path", f"outputs/db_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sql = query or f"SELECT * FROM {table}"
    try:
        rows = _execute_query(sql)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, default=str)
        return {"status": "exported", "format": "json", "rows": len(rows), "output_path": output_path}
    except Exception as e:
        return {"error": str(e)}

def feat_export_excel(task: str, db_context: dict) -> dict:
    """Feature 31 — Export a table or query result to Excel (.xlsx)."""
    try:
        import openpyxl
    except ImportError:
        return {"error": "openpyxl not installed. Run: pip install openpyxl"}
    table = db_context.get("table", "")
    query = db_context.get("query", "")
    output_path = db_context.get("output_path", f"outputs/db_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sql = query or f"SELECT * FROM {table}"
    try:
        rows = _execute_query(sql)
        if not rows:
            return {"error": "No rows returned."}
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = table or "Query Result"
        headers = list(rows[0].keys())
        ws.append(headers)
        for r in rows:
            ws.append([str(v) if v is not None else "" for v in r.values()])
        wb.save(output_path)
        return {"status": "exported", "format": "xlsx", "rows": len(rows), "output_path": output_path}
    except Exception as e:
        return {"error": str(e)}

def feat_export_schema_md(task: str, db_context: dict) -> dict:
    """Feature 32 — Export full database schema as a Markdown document."""
    output_path = db_context.get("output_path", f"outputs/db_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        tables_result = feat_list_tables(task, db_context)
        tables = tables_result.get("tables", [])
        lines = [f"# Database Schema\n\nDB Type: `{_get_db_type()}`  \nGenerated: `{datetime.now().isoformat()}`\n"]
        for t in tables:
            schema = feat_table_schema(task, {"table": t})
            lines.append(f"\n## Table: `{t}`\n")
            lines.append("| Column | Type | Not Null | Primary Key |")
            lines.append("|--------|------|----------|-------------|")
            for c in schema.get("columns", []):
                lines.append(f"| {c.get('name','')} | {c.get('type','')} | {c.get('not_null','')} | {c.get('primary_key','')} |")
        content = "\n".join(lines)
        with open(output_path, "w") as f:
            f.write(content)
        return {"status": "exported", "format": "markdown", "tables": len(tables), "output_path": output_path}
    except Exception as e:
        return {"error": str(e)}

def feat_sql_dump(task: str, db_context: dict) -> dict:
    """Feature 33 — Export full DB as SQL dump (SQLite only)."""
    db_type = _get_db_type()
    if db_type != "sqlite":
        return {"error": "SQL dump is currently supported for SQLite only. Use pg_dump or mysqldump for other DBs."}
    output_path = db_context.get("output_path", f"outputs/db_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        db_path = os.getenv("DB_SQLITE_PATH", "database.db")
        conn = sqlite3.connect(db_path)
        with open(output_path, "w") as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")
        conn.close()
        return {"status": "exported", "format": "sql", "output_path": output_path}
    except Exception as e:
        return {"error": str(e)}


# ════════════════════════════════════════════════════════════════════════════════
# CATEGORY 6 — Cross-Agent Integration
# ════════════════════════════════════════════════════════════════════════════════

def feat_to_writer(task: str, db_context: dict) -> dict:
    """Feature 34 — Run a query and pass results to Writer Agent for a report."""
    query = db_context.get("query", "")
    table = db_context.get("table", "")
    if not query and not table:
        return {"error": "Set db_context['query'] or db_context['table']."}
    sql = query or f"SELECT * FROM {table} LIMIT 100"
    try:
        rows = _execute_query(sql)
        summary = _llm_call(
            "You are a data analyst preparing a professional report. "
            "Write a clear, structured report based on this database query result. "
            "Include key findings, patterns, and recommendations.",
            f"Query: {sql}\nResults ({len(rows)} rows):\n{json.dumps(rows, default=str)}"
        )
        return {
            "status": "ready_for_writer",
            "query": sql,
            "row_count": len(rows),
            "report_draft": summary,
            "note": "Set state['final_report'] to this report_draft to continue the pipeline."
        }
    except Exception as e:
        return {"error": str(e)}

def feat_to_coder(task: str, db_context: dict) -> dict:
    """Feature 35 — Pass query result + task to Coder Agent for analysis script."""
    query = db_context.get("query", "")
    table = db_context.get("table", "")
    sql = query or f"SELECT * FROM {table} LIMIT 100"
    try:
        rows = _execute_query(sql)
        code_task = (
            f"Write a Python script to analyze this database query result.\n"
            f"Query: {sql}\n"
            f"Sample data (first 5 rows): {json.dumps(rows[:5], default=str)}\n"
            f"User requirement: {task}"
        )
        return {
            "status": "ready_for_coder",
            "query": sql,
            "row_count": len(rows),
            "code_task": code_task,
            "note": "Set state['task'] to code_task and route to coder agent."
        }
    except Exception as e:
        return {"error": str(e)}

def feat_to_github(task: str, db_context: dict) -> dict:
    """Feature 36 — Export query result as JSON and prepare for GitHub Agent to commit."""
    result = feat_export_json(task, db_context)
    if "error" in result:
        return result
    return {
        "status": "ready_for_github",
        "file_path": result["output_path"],
        "rows": result["rows"],
        "github_task": f"Commit the file at {result['output_path']} to the repository.",
        "note": "Route to github agent with this github_task."
    }

def feat_to_pdf(task: str, db_context: dict) -> dict:
    """Feature 37 — Export query result as a PDF-ready markdown report via PDF Agent."""
    query = db_context.get("query", "")
    table = db_context.get("table", "")
    sql = query or f"SELECT * FROM {table} LIMIT 100"
    try:
        rows = _execute_query(sql)
        md_report = _llm_call(
            "Generate a professional Markdown report from this database query result. "
            "Include a title, summary section, a data table, and key insights.",
            f"Query: {sql}\nData ({len(rows)} rows):\n{json.dumps(rows, default=str)}"
        )
        return {
            "status": "ready_for_pdf",
            "markdown_report": md_report,
            "row_count": len(rows),
            "note": "Pass markdown_report to pdf_agent with mode='md_to_pdf'."
        }
    except Exception as e:
        return {"error": str(e)}

def feat_to_email(task: str, db_context: dict) -> dict:
    """Feature 38 — Summarize query result and prepare an email-ready summary."""
    query = db_context.get("query", "")
    table = db_context.get("table", "")
    sql = query or f"SELECT * FROM {table} LIMIT 100"
    try:
        rows = _execute_query(sql)
        email_body = _llm_call(
            "Write a professional email body summarizing this database query result. "
            "Include key numbers, trends, and a brief conclusion. Keep it under 300 words.",
            f"Query: {sql}\nData ({len(rows)} rows):\n{json.dumps(rows, default=str)}"
        )
        return {
            "status": "ready_for_email",
            "email_body": email_body,
            "row_count": len(rows),
            "suggested_subject": f"Database Report: {table or 'Query Results'} — {datetime.now().strftime('%b %d, %Y')}",
            "note": "Pass email_body to email_agent with mode='compose' and auto_send=True."
        }
    except Exception as e:
        return {"error": str(e)}


# ════════════════════════════════════════════════════════════════════════════════
# CATEGORY 7 — Safety & Validation
# ════════════════════════════════════════════════════════════════════════════════

_DANGEROUS_PATTERNS = [
    r"\bDROP\b", r"\bTRUNCATE\b", r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)",
    r"\bALTER\b", r"\bCREATE\b", r"\bGRANT\b", r"\bREVOKE\b",
]

def feat_validate_query(task: str, db_context: dict) -> dict:
    """Feature 39 — Detect dangerous SQL patterns before execution."""
    query = db_context.get("query", task)
    findings = []
    for pattern in _DANGEROUS_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            findings.append(pattern.replace(r"\b","").replace("\\",""))
    if findings:
        return {
            "safe": False,
            "query": query,
            "dangerous_patterns_found": findings,
            "recommendation": "This query contains potentially destructive operations. Review before executing.",
        }
    return {"safe": True, "query": query, "message": "No dangerous patterns detected."}

def feat_explain(task: str, db_context: dict) -> dict:
    """Feature 40 — EXPLAIN a query (dry-run / query plan)."""
    query = db_context.get("query", "")
    if not query:
        return {"error": "Set db_context['query']."}
    db_type = _get_db_type()
    explain_prefix = "EXPLAIN QUERY PLAN" if db_type == "sqlite" else "EXPLAIN"
    try:
        plan = _execute_query(f"{explain_prefix} {query}")
        return {"query": query, "execution_plan": plan}
    except Exception as e:
        return {"error": str(e)}

def feat_readonly_toggle(task: str, db_context: dict) -> dict:
    """Feature 41 — Report current read-only status (toggle via DB_READ_ONLY env var)."""
    current = os.getenv("DB_READ_ONLY", "false").lower()
    return {
        "read_only_mode": current == "true",
        "current_value": current,
        "instruction": "Set DB_READ_ONLY=true in your .env to enable read-only mode. Set to false to allow writes.",
        "note": "This is an environment variable — change it in .env and restart the server."
    }

def feat_audit_log(task: str, db_context: dict) -> dict:
    """Feature 42 — View the query audit log."""
    log_path = os.getenv("DB_AUDIT_LOG", "outputs/db_audit.log")
    limit = int(db_context.get("limit", 50))
    if not os.path.exists(log_path):
        return {"message": "No audit log found yet.", "log_path": log_path}
    with open(log_path, "r") as f:
        lines = f.readlines()
    recent = lines[-limit:]
    return {
        "log_path": log_path,
        "total_entries": len(lines),
        "showing_last": len(recent),
        "entries": [l.strip() for l in recent],
    }


# ════════════════════════════════════════════════════════════════════════════════
# Feature Map + Mode Keywords
# ════════════════════════════════════════════════════════════════════════════════

FEATURE_MAP = {
    # Category 1 — Connection & Setup
    "connect":           feat_connect,
    "list_databases":    feat_list_databases,
    "list_tables":       feat_list_tables,
    "table_schema":      feat_table_schema,
    "health_check":      feat_health_check,
    "disconnect":        feat_disconnect,
    # Category 2 — Read & Query
    "query":             feat_query,
    "filter":            feat_filter,
    "search":            feat_search,
    "paginate":          feat_paginate,
    "sort":              feat_sort,
    "join":              feat_join,
    "aggregate":         feat_aggregate,
    "distinct":          feat_distinct,
    # Category 3 — Write Operations
    "insert":            feat_insert,
    "update":            feat_update,
    "delete":            feat_delete,
    "bulk_insert":       feat_bulk_insert,
    "upsert":            feat_upsert,
    "truncate":          feat_truncate,
    # Category 4 — AI-Powered Analysis
    "nl_to_sql":         feat_nl_to_sql,
    "summarize_table":   feat_summarize_table,
    "find_anomalies":    feat_find_anomalies,
    "find_duplicates":   feat_find_duplicates,
    "data_quality":      feat_data_quality,
    "trend_analysis":    feat_trend_analysis,
    "correlation":       feat_correlation,
    "auto_insights":     feat_auto_insights,
    # Category 5 — Data Export
    "export_csv":        feat_export_csv,
    "export_json":       feat_export_json,
    "export_excel":      feat_export_excel,
    "export_schema_md":  feat_export_schema_md,
    "sql_dump":          feat_sql_dump,
    # Category 6 — Cross-Agent Integration
    "to_writer":         feat_to_writer,
    "to_coder":          feat_to_coder,
    "to_github":         feat_to_github,
    "to_pdf":            feat_to_pdf,
    "to_email":          feat_to_email,
    # Category 7 — Safety & Validation
    "validate_query":    feat_validate_query,
    "explain":           feat_explain,
    "readonly_toggle":   feat_readonly_toggle,
    "audit_log":         feat_audit_log,
}

_MODE_KEYWORDS = {
    "connect":          ["connect to db", "connect database", "test connection", "db connection"],
    "list_databases":   ["list databases", "show databases", "all databases"],
    "list_tables":      ["list tables", "show tables", "all tables", "what tables"],
    "table_schema":     ["schema", "columns of", "structure of", "table info", "describe table"],
    "health_check":     ["health check", "db health", "database status", "check db"],
    "query":            ["run query", "execute query", "select query", "raw sql"],
    "filter":           ["filter", "where clause", "rows where", "find rows"],
    "search":           ["search", "find in table", "look for", "search database"],
    "paginate":         ["paginate", "page 2", "next page", "offset"],
    "sort":             ["sort by", "order by", "ascending", "descending"],
    "join":             ["join", "combine tables", "merge tables"],
    "aggregate":        ["count", "sum", "average", "max", "min", "group by", "total"],
    "distinct":         ["distinct", "unique values", "unique entries"],
    "insert":           ["insert", "add row", "add record", "new row", "create record"],
    "update":           ["update", "change value", "modify row", "set column"],
    "delete":           ["delete row", "remove row", "delete record"],
    "bulk_insert":      ["bulk insert", "import csv", "bulk upload", "load data"],
    "upsert":           ["upsert", "insert or replace", "insert or update"],
    "truncate":         ["truncate", "clear table", "empty table"],
    "nl_to_sql":        ["natural language", "in plain english", "convert to sql", "write a query for",
                         "how many", "show me", "get me", "find all", "what is the total"],
    "summarize_table":  ["summarize table", "describe the data", "what is in this table", "table overview"],
    "find_anomalies":   ["anomaly", "outlier", "unusual", "suspicious data", "strange values"],
    "find_duplicates":  ["duplicate", "repeated rows", "find duplicates"],
    "data_quality":     ["data quality", "null values", "missing data", "data report"],
    "trend_analysis":   ["trend", "over time", "monthly", "weekly", "time series"],
    "correlation":      ["correlation", "relationship between", "compare columns"],
    "auto_insights":    ["insights", "what can you tell", "analyze this data", "business insights"],
    "export_csv":       ["export csv", "download csv", "save as csv", "to csv"],
    "export_json":      ["export json", "save json", "to json"],
    "export_excel":     ["export excel", "excel file", "xlsx", "spreadsheet"],
    "export_schema_md": ["export schema", "schema document", "schema markdown"],
    "sql_dump":         ["sql dump", "backup database", "dump db"],
    "to_writer":        ["write a report", "generate report", "report from database"],
    "to_coder":         ["write code", "python script", "analyze with code"],
    "to_github":        ["save to github", "commit to repo", "push to github"],
    "to_pdf":           ["export to pdf", "database pdf", "report as pdf"],
    "to_email":         ["email the results", "send report", "email summary", "mail this"],
    "validate_query":   ["validate query", "check query", "is this query safe", "dangerous sql"],
    "explain":          ["explain query", "query plan", "dry run", "explain plan"],
    "readonly_toggle":  ["read only", "readonly mode", "disable writes"],
    "audit_log":        ["audit log", "query history", "what queries", "log"],
}

def _infer_mode(task: str) -> str:
    tl = task.lower()
    for mode, keywords in _MODE_KEYWORDS.items():
        if any(kw in tl for kw in keywords):
            return mode
    return "nl_to_sql"  # Default: treat as natural language query


# ════════════════════════════════════════════════════════════════════════════════
# Main entry point
# ════════════════════════════════════════════════════════════════════════════════

def run_database_agent(state: AgentState) -> AgentState:
    task       = state.get("task", "")
    mode       = state.get("db_mode", "auto").strip().lower()
    db_context = state.get("db_context", {})

    print(f"\n🗄️  Database Agent — task: {task[:80]}  mode: {mode}")

    if mode in ("auto", "", None):
        mode = _infer_mode(task)
    print(f"🗄️  Database Agent — resolved mode: {mode}")

    handler = FEATURE_MAP.get(mode)
    if not handler:
        result = {
            "error": f"Unknown mode: '{mode}'.",
            "available_modes": sorted(FEATURE_MAP.keys()),
        }
    else:
        try:
            result = handler(task, db_context)
        except Exception as e:
            result = {"error": str(e), "traceback": traceback.format_exc()[-1000:]}

    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(f"🗄️  Database Agent — done, {len(output):,} chars")
    return {**state, "db_result": output}
