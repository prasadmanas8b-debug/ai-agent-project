"""
main.py — Entry point for the AI Agent System.

Agents: Research · Writer · Coder · GitHub · PDF · Email · Convo · Database
Orchestrated by a LangGraph Supervisor.

Usage:
    python main.py
"""

import json
import os
import base64

from graph.pipeline_graph import build_graph


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ensure_outputs_dir() -> None:
    """Create outputs/ directory, removing any git artifact file if needed."""
    if os.path.isfile("outputs"):
        os.remove("outputs")
    os.makedirs("outputs", exist_ok=True)


def _print_banner() -> None:
    line = "=" * 65
    print(f"\n{line}")
    print("  AI Agent System  —  Research · Write · Code · PDF · Email · Chat · DB")
    print(line)
    print()
    print("Example tasks:")
    print("  Research quantum computing")
    print("  Implement a binary search in Python")
    print("  Research AI trends and save to GitHub")
    print("  Summarize PDF at uploads/report.pdf")
    print("  Compose a follow-up email to the investor")
    print("  List all tables in the database")
    print("  What can you do?")
    print(f"{line}\n")


def _read_email_body() -> str:
    """Prompt for an optional multi-line email body (press Enter twice to finish)."""
    print("\n[Optional] Paste the email content (press Enter twice to finish):")
    lines: list[str] = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    return "\n".join(lines[:-1] if lines else [])


def _needs_email_body(task: str) -> bool:
    keywords = ("summarize email", "analyze email", "reply to", "rewrite",
                 "check email", "classify email")
    return any(kw in task.lower() for kw in keywords)


def _save_pdf_outputs(parsed: dict) -> None:
    """Persist PDF agent artefacts (PDFs, images, CSVs, markdown, HTML)."""
    os.makedirs("outputs", exist_ok=True)

    if parsed.get("pdf_b64"):
        path = "outputs/pdf_agent_output.pdf"
        with open(path, "wb") as f:
            f.write(base64.b64decode(parsed["pdf_b64"]))
        print(f"  PDF saved → {path}")

    if parsed.get("images"):
        os.makedirs("outputs/images", exist_ok=True)
        for img in parsed["images"]:
            ext   = img.get("ext") or img.get("format", "png")
            fname = f"outputs/images/page_{img.get('page', 0)}.{ext}"
            with open(fname, "wb") as f:
                f.write(base64.b64decode(img["image_b64"]))
        print(f"  {len(parsed['images'])} image(s) saved → outputs/images/")

    if parsed.get("parts"):
        for i, part in enumerate(parsed["parts"], 1):
            fname = f"outputs/split_part_{i}_pages_{part['range']}.pdf"
            with open(fname, "wb") as f:
                f.write(base64.b64decode(part["pdf_b64"]))
        print(f"  {len(parsed['parts'])} split PDF(s) saved → outputs/")

    if parsed.get("csvs"):
        for i, csv_item in enumerate(parsed["csvs"], 1):
            fname = f"outputs/table_{i}_{csv_item.get('title', 'data')}.csv"
            with open(fname, "w", encoding="utf-8") as f:
                f.write(csv_item["csv"])
        print(f"  {len(parsed['csvs'])} CSV(s) saved → outputs/")

    if parsed.get("markdown"):
        with open("outputs/output.md", "w", encoding="utf-8") as f:
            f.write(parsed["markdown"])
        print("  Markdown saved → outputs/output.md")

    if parsed.get("html"):
        with open("outputs/output.html", "w", encoding="utf-8") as f:
            f.write(parsed["html"])
        print("  HTML saved → outputs/output.html")


def _print_results(result: dict) -> None:
    """Print a human-friendly summary of all agent results."""
    sep = "=" * 65
    print(f"\n{sep}\n  DONE\n{sep}")

    if result.get("convo_result"):
        print(f"\n--- Conversation ---\n{result['convo_result']}")

    if result.get("final_report"):
        print("\n--- Report Preview (first 800 chars) ---")
        print(result["final_report"][:800])
        slug = result.get("task", "report")[:30].replace(" ", "_")
        path = f"outputs/report_{slug}.md"
        os.makedirs("outputs", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(result["final_report"])
        print(f"\n  Full report saved → {path}")

    if result.get("code_result"):
        print(f"\n--- Coder Agent ---\n{result['code_result']}")

    if result.get("github_result"):
        print(f"\n--- GitHub Agent ---\n{result['github_result']}")

    # PDF result
    if result.get("pdf_result"):
        print("\n--- PDF Agent ---")
        try:
            parsed = json.loads(result["pdf_result"])
            _SKIP  = {"pdf_b64", "pdf2_b64", "python_code", "full_text",
                      "translated_content", "rewritten_text", "ocr_text",
                      "markdown", "html", "images", "parts", "csvs"}
            summary = {k: v for k, v in parsed.items() if k not in _SKIP}
            print(json.dumps(summary, indent=2, ensure_ascii=False))
            _save_pdf_outputs(parsed)
        except (json.JSONDecodeError, KeyError):
            print(result["pdf_result"][:800])

    # Email result
    if result.get("email_result"):
        print("\n--- Email Agent ---")
        try:
            parsed = json.loads(result["email_result"])
            _SKIP  = {"body_html", "python_code", "signature_html",
                      "translated_body", "error", "traceback"}
            summary = {k: v for k, v in parsed.items() if k not in _SKIP}
            print(json.dumps(summary, indent=2, ensure_ascii=False))

            if parsed.get("body_html"):
                with open("outputs/email_output.html", "w", encoding="utf-8") as f:
                    f.write(parsed["body_html"])
                print("  HTML email saved → outputs/email_output.html")

            if parsed.get("content") and parsed.get("filename"):
                fpath = f"outputs/{parsed['filename']}"
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(parsed["content"])
                print(f"  Export saved → {fpath}")

            send = parsed.get("send_result", {})
            if send.get("sent"):
                print(f"  Email sent to {send.get('to')}")
            elif send.get("mock"):
                print(f"  Mock mode: {send.get('note')}")
            elif send.get("error"):
                print(f"  Send failed: {send.get('error')}")
        except (json.JSONDecodeError, KeyError):
            print(result["email_result"][:800])

    # Database result
    if result.get("db_result"):
        print("\n--- Database Agent ---")
        try:
            parsed = json.loads(result["db_result"])
            _SKIP  = {"rows", "entries", "trend_data", "duplicate_groups", "column_report"}
            summary = {k: v for k, v in parsed.items() if k not in _SKIP}
            print(json.dumps(summary, indent=2, ensure_ascii=False))
            if parsed.get("rows") is not None:
                print(f"  rows returned: {len(parsed['rows'])}")
        except (json.JSONDecodeError, KeyError):
            print(result["db_result"][:800])

    if result.get("research_notes") and not result.get("final_report"):
        print("\n--- Research Notes (first 500 chars) ---")
        print(result["research_notes"][:500])


def _build_initial_state(task: str, email_context: dict | None = None) -> dict:
    """Build a clean initial AgentState dict."""
    return {
        "task":                 task,
        "next":                 "",
        "research_notes":       "",
        "final_report":         "",
        "code_result":          "",
        "github_result":        "",
        "pdf_result":           "",
        "email_result":         "",
        "convo_result":         "",
        "db_result":            "",
        "conversation_history": [],
        "pdf_mode":             "auto",
        "pdf_text":             "",
        "pdf_bytes":            b"",
        "pdf2_bytes":           b"",
        "email_mode":           "auto",
        "email_context":        email_context or {},
        "db_mode":              "auto",
        "db_context":           {},
    }


# ── Main loop ─────────────────────────────────────────────────────────────────

def main() -> None:
    _ensure_outputs_dir()
    _print_banner()

    try:
        graph = build_graph()
    except Exception as exc:
        print(f"\n[FATAL] Could not build agent graph: {exc}")
        raise

    print("Type your task and press Enter. Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            task = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not task:
            continue

        if task.lower() in ("exit", "quit", "q", "bye"):
            print("Goodbye!")
            break

        # Optional email body for email-analysis tasks
        email_context: dict = {}
        if _needs_email_body(task):
            body = _read_email_body()
            if body.strip():
                email_context["original_email"] = body

        state = _build_initial_state(task, email_context)

        print("\nProcessing...\n")
        try:
            result = graph.invoke(state)
            _print_results(result)
        except Exception as exc:
            print(f"\n[ERROR] Agent pipeline failed: {exc}")
            import traceback
            traceback.print_exc()

        print()


if __name__ == "__main__":
    main()
