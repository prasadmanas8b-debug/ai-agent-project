"""
main.py  --  Entry point for the AI Agent System.
Agents: Research -> Writer -> Coder -> GitHub -> PDF -> Convo (orchestrated by Supervisor)
"""
import json
from graph.pipeline_graph import build_graph

def main():
    graph = build_graph()

    print("\n" + "="*60)
    print("  AI Agent System  --  Research . Write . Code . Act . PDF . Chat")
    print("="*60)
    print("General examples:")
    print("  Research quantum computing")
    print("  Implement a binary search in Python")
    print("  Research neural networks and write code for it")
    print("  Research AI trends and save to GitHub")
    print("  Hi, what can you do?")
    print()
    print("PDF Agent examples (43 features):")
    print("  Summarize PDF at uploads/report.pdf")
    print("  Extract all tables from uploads/data.pdf as CSV")
    print("  Translate PDF at uploads/doc.pdf to French")
    print("  Compress uploads/large.pdf")
    print("  Watermark 'CONFIDENTIAL' on uploads/report.pdf")
    print("  OCR scanned PDF at uploads/scan.pdf")
    print("  Classify the document at uploads/unknown.pdf")
    print("  Search for 'revenue' in uploads/annual_report.pdf")
    print("  Compare uploads/v1.pdf with uploads/v2.pdf")
    print("  Create a professional project proposal PDF")
    print("  Sentiment analysis on uploads/feedback.pdf")
    print("  Password protect uploads/private.pdf password 'secret123'")
    print("  Redact 'John Smith' 'john@company.com' from uploads/doc.pdf")
    print("  Convert uploads/report.pdf to Markdown")
    print("  Add page numbers to uploads/presentation.pdf")
    print("="*60 + "\n")

    user_input = input("What do you want to do? ").strip()
    if not user_input:
        print("No input. Exiting.")
        return

    initial_state = {
        "task":                 user_input,
        "research_notes":       "",
        "final_report":         "",
        "code_result":          "",
        "github_result":        "",
        "pdf_result":           "",
        "convo_result":         "",
        "conversation_history": [],
        "next":                 "",
        # PDF Agent fields (populated by agent or caller)
        "pdf_mode":             "auto",
        "pdf_text":             "",
        "pdf_bytes":            b"",
        "pdf2_bytes":           b"",
    }

    print("\n[System] Starting graph...\n")
    result = graph.invoke(initial_state)

    print("\n" + "="*60)
    print("  DONE")
    print("="*60)

    if result.get("convo_result"):
        print(f"\n--- Conversation ---\n{result['convo_result']}")

    if result.get("final_report"):
        print("\n--- Report Preview ---")
        print(result["final_report"][:800])

    if result.get("code_result"):
        print(f"\n--- Code Agent ---\n{result['code_result']}")

    if result.get("github_result"):
        print(f"\n--- GitHub ---\n{result['github_result']}")

    if result.get("pdf_result"):
        print(f"\n--- PDF Agent ---")
        try:
            parsed = json.loads(result["pdf_result"])
            # Pretty-print key fields, skip bulky base64 blobs
            summary = {k: v for k, v in parsed.items()
                       if k not in ("pdf_b64", "pdf2_b64", "python_code", "full_text",
                                    "translated_content", "rewritten_text", "ocr_text",
                                    "markdown", "html", "images", "parts", "csvs")}
            print(json.dumps(summary, indent=2, ensure_ascii=False))

            # Notify about downloadable outputs
            if parsed.get("pdf_b64"):
                out_path = "outputs/pdf_agent_output.pdf"
                import base64, os
                os.makedirs("outputs", exist_ok=True)
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(parsed["pdf_b64"]))
                print(f"\n✅ PDF saved to: {out_path}")

            if parsed.get("images"):
                import base64, os
                os.makedirs("outputs/images", exist_ok=True)
                for img in parsed["images"]:
                    fname = f"outputs/images/page_{img.get('page',0)}.{img.get('ext', img.get('format','png'))}"
                    with open(fname, "wb") as f:
                        f.write(base64.b64decode(img["image_b64"]))
                print(f"✅ {len(parsed['images'])} image(s) saved to outputs/images/")

            if parsed.get("parts"):
                import base64, os
                os.makedirs("outputs", exist_ok=True)
                for i, part in enumerate(parsed["parts"], 1):
                    fname = f"outputs/split_part_{i}_pages_{part['range']}.pdf"
                    with open(fname, "wb") as f:
                        f.write(base64.b64decode(part["pdf_b64"]))
                print(f"✅ {len(parsed['parts'])} split PDF(s) saved to outputs/")

            if parsed.get("csvs"):
                import os
                os.makedirs("outputs", exist_ok=True)
                for i, csv in enumerate(parsed["csvs"], 1):
                    fname = f"outputs/table_{i}_{csv.get('title','data')}.csv"
                    with open(fname, "w") as f:
                        f.write(csv["csv"])
                print(f"✅ {len(parsed['csvs'])} CSV(s) saved to outputs/")

            if parsed.get("markdown"):
                import os
                os.makedirs("outputs", exist_ok=True)
                with open("outputs/output.md", "w") as f:
                    f.write(parsed["markdown"])
                print("✅ Markdown saved to outputs/output.md")

            if parsed.get("html"):
                import os
                os.makedirs("outputs", exist_ok=True)
                with open("outputs/output.html", "w") as f:
                    f.write(parsed["html"])
                print("✅ HTML saved to outputs/output.html")

        except (json.JSONDecodeError, KeyError):
            print(result["pdf_result"][:800])

if __name__ == "__main__":
    main()
