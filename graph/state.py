"""
graph/state.py  --  Shared whiteboard passed between all agents.
"""
from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    task: str
    # Original user input. Set once, never changed.

    research_notes: str
    # Written by Research Agent -- raw web research text.

    final_report: str
    # Written by Writer Agent -- polished markdown report.

    code_result: str
    # Written by Coder Agent -- save confirmation + line count.

    github_result: str
    # Written by GitHub Agent -- result of file/branch operations.

    pdf_result: str
    # Written by PDF Agent -- JSON string with result data.

    email_result: str
    # Written by Email Agent -- JSON string with result data.

    convo_result: str
    # Written by Convo Agent -- latest conversational reply.

    db_result: str
    # Written by Database Agent -- JSON string with query/operation result.

    conversation_history: List[Dict[str, str]]
    # Maintained by Convo Agent -- list of {role: str, content: str} dicts.
    # role is "user" or "assistant".

    next: str
    # Written by Supervisor each loop.
    # Values: "research"|"writer"|"coder"|"github"|"pdf"|"email"|"convo"|"database"|"FINISH"

    # ── PDF Agent fields ──────────────────────────────────────────────────────

    pdf_mode: str
    # Controls which PDF feature to invoke. Defaults to "auto".

    pdf_text: str
    # Optional pre-extracted text for the PDF agent. Skips file loading if provided.

    pdf_bytes: bytes
    # Optional: raw bytes of the primary PDF file.

    pdf2_bytes: bytes
    # Optional: raw bytes of a second PDF file (for compare / merge).

    # ── Email Agent fields ────────────────────────────────────────────────────

    email_mode: str
    # Controls which Email feature to invoke. Defaults to "auto".

    email_context: Dict[str, Any]
    # Optional context dict for the email agent.

    # ── Database Agent fields ─────────────────────────────────────────────────

    db_mode: str
    # Controls which Database feature to invoke. Defaults to "auto".
    # Options: connect|list_databases|list_tables|table_schema|health_check|disconnect|
    #   query|filter|search|paginate|sort|join|aggregate|distinct|
    #   insert|update|delete|bulk_insert|upsert|truncate|
    #   nl_to_sql|summarize_table|find_anomalies|find_duplicates|data_quality|
    #   trend_analysis|correlation|auto_insights|
    #   export_csv|export_json|export_excel|export_schema_md|sql_dump|
    #   to_writer|to_coder|to_github|to_pdf|to_email|
    #   validate_query|explain|readonly_toggle|audit_log

    db_context: Dict[str, Any]
    # Optional context dict for the database agent. Supported keys:
    #   table:        str  -- target table name
    #   query:        str  -- raw SQL SELECT query
    #   nl_query:     str  -- natural language query for nl_to_sql
    #   condition:    str  -- WHERE clause string
    #   data:         dict -- column:value pairs for insert/update/upsert
    #   updates:      dict -- column:value pairs for update
    #   rows:         list -- list of dicts for bulk_insert
    #   csv_path:     str  -- path to CSV file for bulk_insert
    #   column:       str  -- target column name
    #   columns:      list -- list of column names
    #   limit:        int  -- max rows to return
    #   page:         int  -- page number for pagination
    #   page_size:    int  -- rows per page
    #   order_by:     str  -- ORDER BY column
    #   keyword:      str  -- search term
    #   agg_func:     str  -- COUNT|SUM|AVG|MAX|MIN
    #   group_by:     str  -- GROUP BY column
    #   table1:       str  -- first table for JOIN
    #   table2:       str  -- second table for JOIN
    #   on:           str  -- JOIN condition
    #   join_type:    str  -- INNER|LEFT|RIGHT|FULL
    #   date_column:  str  -- datetime column for trend analysis
    #   value_column: str  -- numeric column for trend analysis
    #   column1:      str  -- first column for correlation
    #   column2:      str  -- second column for correlation
    #   output_path:  str  -- file path for exports
    #   confirm:      bool -- required True for truncate
