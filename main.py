"""
main.py  --  Entry point for the AI Agent System.
Agents: Research · Writer · Coder · GitHub · PDF · Email · Convo
        (orchestrated by Supervisor)
"""
import json, os, base64
from graph.pipeline_graph import build_graph

def main():
    graph = build_graph()

    print("\n" + "="*60)
    print("  AI Agent System  --  Research · Write · Code · PDF · Email · Chat")
    print("="*60)
    print("General:")
    print("  Research quantum computing")
    print("  Implement a binary search in Python")
    print("  Research AI trends and save to GitHub")
    print()
    print("PDF Agent (43 features):")
    print("  Summarize PDF at uploads/report.pdf")
    print("  OCR scanned PDF at uploads/scan.pdf")
    print("  Compress uploads/large.pdf")
    print("  Compare uploads/v1.pdf with uploads/v2.pdf")
    print("  Create a professional project proposal PDF")
    print("  Redact 'John Smith' from uploads/doc.pdf")
    print()
    print("Email Agent (38 features):")
    print("  Compose a follow-up email to the investor")
    print("  Read my inbox (last 10 emails)")
    print("  Summarize the email [paste email below task]")
    print("  Write a follow-up if no reply in 3 days")
    print("  Check this email for phishing")
    print("  Generate a drip campaign for SaaS onboarding")
    print("  Translate this email to French")
    print("  Extract action items from this email")
    print("  Create an email template for cold outreach")
    print("  A/B test subject lines for this campaign")
    print("="*60 + "\n")

    user_input = input("What do you want to do? ").strip()
    if not user_input:
        print("No input. Exiting.")
        return

    # Allow multi-line paste for email context
    email_body = ""
    if any(kw in user_input.lower() for kw in ["summarize email", "analyze email", "reply to", "rewrite", "check email", "classify email"]):
        print("\n[Optional] Paste the email content (press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        email_body = "\n".join(lines[:-1] if lines else [])

    initial_state = {
        "task":                 user_input,
        "research_notes":       "",
        "final_report":         "",
        "code_result":          "",
        "github_result":        "",
        "pdf_result":           "",
        "email_result":         "",
        "convo_result":         "",
        "conversation_history": [],
        "next":                 "",
        # PDF Agent fields
        "pdf_mode":             "auto",
        "pdf_text":             "",
        "pdf_bytes":            b"",
        "pdf2_bytes":           b"",
        # Email Agent fields
        "email_mode":           "auto",
        "email_context":        {"original_email": email_body} if email_body else {},
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

    # ── PDF result ────────────────────────────────────────────────────────────
    if result.get("pdf_result"):
        print("\n--- PDF Agent ---")
        try:
            parsed = json.loads(result["pdf_result"])
            skip = {"pdf_b64","pdf2_b64","python_code","full_text","translated_content",
                    "rewritten_text","ocr_text","markdown","html","images","parts","csvs"}
            summary = {k: v for k, v in parsed.items() if k not in skip}
            print(json.dumps(summary, indent=2, ensure_ascii=False))

            os.makedirs("outputs", exist_ok=True)
            if parsed.get("pdf_b64"):
                path = "outputs/pdf_agent_output.pdf"
                with open(path, "wb") as f:
                    f.write(base64.b64decode(parsed["pdf_b64"]))
                print(f"✅ PDF saved → {path}")
            if parsed.get("images"):
                os.makedirs("outputs/images", exist_ok=True)
                for img in parsed["images"]:
                    fname = f"outputs/images/page_{img.get('page',0)}.{img.get('ext',img.get('format','png'))}"
                    with open(fname,"wb") as f:
                        f.write(base64.b64decode(img["image_b64"]))
                print(f"✅ {len(parsed['images'])} image(s) saved → outputs/images/")
            if parsed.get("parts"):
                for i, part in enumerate(parsed["parts"],1):
                    fname = f"outputs/split_part_{i}_pages_{part['range']}.pdf"
                    with open(fname,"wb") as f:
                        f.write(base64.b64decode(part["pdf_b64"]))
                print(f"✅ {len(parsed['parts'])} split PDF(s) saved → outputs/")
            if parsed.get("csvs"):
                for i, csv in enumerate(parsed["csvs"],1):
                    fname = f"outputs/table_{i}_{csv.get('title','data')}.csv"
                    with open(fname,"w") as f:
                        f.write(csv["csv"])
                print(f"✅ {len(parsed['csvs'])} CSV(s) saved → outputs/")
            if parsed.get("markdown"):
                with open("outputs/output.md","w") as f:
                    f.write(parsed["markdown"])
                print("✅ Markdown saved → outputs/output.md")
            if parsed.get("html"):
                with open("outputs/output.html","w") as f:
                    f.write(parsed["html"])
                print("✅ HTML saved → outputs/output.html")
        except (json.JSONDecodeError, KeyError):
            print(result["pdf_result"][:800])

    # ── Email result ──────────────────────────────────────────────────────────
    if result.get("email_result"):
        print("\n--- Email Agent ---")
        try:
            parsed = json.loads(result["email_result"])
            skip = {"body_html","python_code","signature_html","translated_body","error","traceback"}
            summary = {k: v for k, v in parsed.items() if k not in skip}
            print(json.dumps(summary, indent=2, ensure_ascii=False))

            os.makedirs("outputs", exist_ok=True)
            # Save HTML body
            if parsed.get("body_html"):
                with open("outputs/email_output.html","w") as f:
                    f.write(parsed["body_html"])
                print("✅ HTML email saved → outputs/email_output.html")
            # Save export content
            if parsed.get("content") and parsed.get("filename"):
                fpath = f"outputs/{parsed['filename']}"
                with open(fpath,"w") as f:
                    f.write(parsed["content"])
                print(f"✅ Export saved → {fpath}")
            # Save code
            if parsed.get("python_code"):
                with open("outputs/email_code.py","w") as f:
                    f.write(parsed["python_code"])
                print("✅ Python code saved → outputs/email_code.py")
            # Send result
            if parsed.get("send_result"):
                sr = parsed["send_result"]
                if sr.get("sent"):
                    print(f"✅ Email sent to {sr.get('to')}")
                elif sr.get("mock"):
                    print(f"📝 Mock mode: {sr.get('note')}")
                else:
                    print(f"❌ Send failed: {sr.get('error')}")
        except (json.JSONDecodeError, KeyError):
            print(result["email_result"][:800])

if __name__ == "__main__":
    main()
