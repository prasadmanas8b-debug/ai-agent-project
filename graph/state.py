"""
graph/state.py  --  Shared whiteboard passed between all agents.
"""
from typing import TypedDict, List, Dict, Optional

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

    convo_result: str
    # Written by Convo Agent -- latest conversational reply.

    conversation_history: List[Dict[str, str]]
    # Maintained by Convo Agent -- list of {role: str, content: str} dicts.
    # role is "user" or "assistant".

    next: str
    # Written by Supervisor each loop.
    # Values: "research" | "writer" | "coder" | "github" | "pdf" | "convo" | "FINISH"

    # ── PDF Agent fields ──────────────────────────────────────────────────────

    pdf_mode: str
    # Controls which PDF feature to invoke. Options:
    #   Core:        read | create | summarize | qa | translate | extract
    #   Text:        search | find_replace | watermark | page_numbers | header_footer | rewrite
    #   Pages:       page_ops | split | merge | merge_plan
    #   Images:      extract_images | pdf_to_images
    #   AI:          classify | sentiment | ner | compare | autotag | reformat | md_to_pdf
    #   Data:        tables_to_csv | to_markdown | to_html
    #   Metadata:    metadata | set_metadata
    #   Security:    protect | decrypt | redact | signature
    #   OCR:         ocr
    #   Annotations: annotate | bookmarks
    #   Optimize:    compress | repair | linearize
    #   Forms:       forms
    #   Accesibility:accessibility
    #   Batch:       batch
    # Defaults to "auto" (inferred from task string).

    pdf_text: str
    # Optional: pre-extracted text to pass directly to the PDF agent.
    # Skips file loading if provided.

    pdf_bytes: bytes
    # Optional: raw bytes of the primary PDF file.
    # Pass this when you have the PDF in memory (e.g. from an upload).
    # If not provided, the agent will try to detect a file path or URL in `task`.

    pdf2_bytes: bytes
    # Optional: raw bytes of a second PDF file.
    # Required for: compare, merge
    # Not used by any other mode.
