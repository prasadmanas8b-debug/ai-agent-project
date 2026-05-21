# PDF Agent — Technical Documentation

**Project:** AI Agent System  
**File:** `agents/pdf_agent.py`  
**Author:** AI Agent Project Team  
**Last Updated:** May 2026  
**Version:** 1.0

---

## 1. Overview

The **PDF Agent** is a specialized AI-powered module in the multi-agent pipeline. Its job is to **automatically read, extract text from, and intelligently summarize any PDF document** — whether it lives on the local filesystem or at a public URL on the internet.

It eliminates the need to manually open, read, or copy-paste content from PDF files. The user simply mentions a PDF path or URL in their task, and the agent handles everything: downloading, parsing, and producing a clean, structured summary using an LLM.

---

## 2. Role in the System

```
User Input
    ↓
Supervisor Agent
    ↓ (detects: "pdf", "summarize pdf", "extract from", "read pdf")
PDF Agent
    ├── Download PDF (if URL) or Read from disk (if local path)
    ├── Extract raw text page-by-page using PyMuPDF
    ├── Summarize with Groq LLM
    └── Return structured summary → state["pdf_result"]
    ↓
Supervisor Agent → FINISH
```

The Supervisor routes to the PDF Agent when the task contains keywords like:
`pdf`, `PDF`, `summarize pdf`, `extract pdf`, `read pdf`, or a `.pdf` file path / URL.

---

## 3. Supported Input Sources

| Source Type | Example Task |
|---|---|
| **Local file (relative path)** | `"Summarize PDF at report.pdf"` |
| **Local file (uploads/ folder)** | `"Extract text from uploads/budget.pdf"` |
| **Absolute path** | `"Read /home/user/docs/contract.pdf"` |
| **Public URL** | `"Summarize https://arxiv.org/pdf/2301.00001.pdf"` |

> **Default lookup order for relative paths:**
> 1. Current working directory
> 2. `uploads/` folder
> 3. `git_agent_output/` folder

---

## 4. How It Works — Step by Step

### Step 1 — Receive Task from Supervisor
The agent receives the shared pipeline `state` dict containing the user's task string.

```python
state = {
    "task": "summarize PDF at uploads/annual_report.pdf",
    ...
}
```

---

### Step 2 — Detect PDF Source (`_detect_pdf_source`)
The task string is parsed using regex to find either:
- A **URL** matching `https://...*.pdf`
- A **file path** matching `*.pdf` (absolute or relative)

**Returns:** `(source_type, source_value)`
- `source_type` → `"url"`, `"path"`, or `"none"`
- `source_value` → the actual URL or file path string

If no PDF is found in the task, the agent returns a helpful error message with usage examples and stops gracefully — it does **not** crash the pipeline.

---

### Step 3 — Load PDF Bytes

**If URL** → `_load_pdf_from_url(url)`
- Makes an HTTP GET request with a standard browser `User-Agent` header to avoid bot-blocking
- Timeout: **30 seconds**
- Returns raw PDF bytes

**If local path** → `_load_pdf_from_path(path)`
- Checks if the file exists — raises `FileNotFoundError` with a clear message if not
- Reads and returns raw PDF bytes

---

### Step 4 — Extract Text (`_extract_text_from_bytes`)
Uses **PyMuPDF (fitz)** to parse the PDF bytes in memory (no temp files created):
- Iterates through every page of the document
- Extracts plain text from each page
- Labels each page: `[Page 1]`, `[Page 2]`, etc.
- Skips blank pages automatically
- Returns a single string of all extracted text

**Example output:**
```
[Page 1]
Annual Financial Report 2025
Total Revenue: ₹4.2 Crore
...

[Page 2]
Key Highlights
- 23% growth in Q3
...
```

---

### Step 5 — Summarize with LLM (`_summarize_text`)
The extracted text is passed to **Groq's LLM** (`llama-3.3-70b-versatile`) with a structured analyst prompt.

**Context window management:**
- Only the first **12,000 characters** of extracted text are sent to the LLM
- If the document is longer, a note is appended: `[Document was truncated to fit context window]`

**LLM Output Structure (always follows this format):**

```markdown
## Document Overview
2-3 sentence description of what the document is.

## Key Points
- Most important facts, arguments, or data points

## Details
Important sections, findings, tables, quotes

## Bottom Line
One paragraph — the single most critical takeaway
```

---

### Step 6 — Return Result
The final result is written to `state["pdf_result"]` in this format:

```
📄 PDF Processed: `uploads/annual_report.pdf`
📏 Extracted: 18,432 characters

## Document Overview
...

## Key Points
...

## Bottom Line
...
```

The Supervisor then reads this filled state and routes to `FINISH`.

---

## 5. Key Technical Details

| Property | Value |
|---|---|
| **LLM Model** | `llama-3.3-70b-versatile` (via Groq API) |
| **LLM Temperature** | `0.3` (analytical, mostly deterministic) |
| **PDF Parser** | PyMuPDF (`fitz`) — in-memory, no temp files |
| **Max Text Sent to LLM** | 12,000 characters |
| **HTTP Timeout (URL download)** | 30 seconds |
| **LLM Initialization** | Lazy (only created on first call — safe to import) |
| **Output State Field** | `state["pdf_result"]` |

---

## 6. Internal Functions Reference

| Function | Visibility | Purpose |
|---|---|---|
| `run_pdf_agent(state)` | **Public** | Main entry point called by the pipeline |
| `_detect_pdf_source(task)` | Private | Regex-parse task to find PDF URL or path |
| `_load_pdf_from_url(url)` | Private | Download PDF bytes from a public URL |
| `_load_pdf_from_path(path)` | Private | Read PDF bytes from local filesystem |
| `_extract_text_from_bytes(pdf_bytes)` | Private | Extract page-by-page text using PyMuPDF |
| `_summarize_text(raw_text, task)` | Private | Send text to LLM, receive structured summary |
| `_get_llm()` | Private | Lazy LLM singleton initializer |

---

## 7. Dependencies

| Library | Purpose | Install |
|---|---|---|
| `pymupdf` | PDF text extraction engine | `pip install pymupdf` |
| `langchain-groq` | LLM interface to Groq API | Already in requirements.txt |
| `langchain-core` | Message formatting | Already in requirements.txt |
| `python-dotenv` | Load API keys from `.env` | Already in requirements.txt |

> `pymupdf` has been added to `requirements.txt` in this project automatically.

**Required environment variable (in `.env`):**
```
GROQ_API_KEY=your_groq_api_key_here
```

---

## 8. Input & Output

### Input — Pipeline State
```python
{
    "task":           "summarize PDF at uploads/q4_report.pdf",
    "research_notes": "",
    "final_report":   "",
    "code_result":    "",
    "github_result":  "",
    "pdf_result":     "",   # empty — agent will fill this
    "next":           ""
}
```

### Output — Updated State
```python
{
    ...
    "pdf_result": (
        "📄 PDF Processed: `uploads/q4_report.pdf`\n"
        "📏 Extracted: 9,214 characters\n\n"
        "## Document Overview\n..."
        "## Key Points\n..."
        "## Details\n..."
        "## Bottom Line\n..."
    )
}
```

---

## 9. Error Handling

| Scenario | Behaviour | Pipeline Impact |
|---|---|---|
| No PDF path/URL in task | Returns helpful usage message | Pipeline continues, routes to FINISH |
| URL download fails (timeout, 404) | Returns `❌ PDF Agent: Failed to download...` | Pipeline continues gracefully |
| Local file not found | Returns `❌ PDF Agent: PDF file not found at path: '...'` | Pipeline continues gracefully |
| PyMuPDF not installed | Returns `ERROR: PyMuPDF not installed. Run: pip install pymupdf` | Pipeline continues gracefully |
| LLM API fails | Exception propagates up (same as other agents) | Pipeline error — check GROQ_API_KEY |
| PDF has no extractable text (scanned image PDF) | Returns `"No extractable text found in PDF."` | Pipeline continues, result noted |

> **Important:** The PDF Agent never raises unhandled exceptions for file/URL errors. All I/O errors are caught and converted to human-readable messages in `pdf_result`.

---

## 10. Limitations

1. **Scanned / Image PDFs** — PDFs that are scanned images (not text-based) will return `"No extractable text found"`. OCR (Optical Character Recognition) is not currently supported.

2. **12,000 character context cap** — Very large documents (100+ pages) will be truncated. Only the first ~12,000 characters are analyzed by the LLM. This covers approximately 6–10 pages depending on content density.

3. **Password-protected PDFs** — Encrypted PDFs requiring a password cannot be opened and will raise an error during extraction.

4. **URL restrictions** — Some websites block automated HTTP requests. The agent uses a standard browser User-Agent header to mitigate this, but it is not guaranteed to work for all sites.

5. **No output saved to GitHub** — Unlike the Coder Agent, the PDF Agent does not commit its output to GitHub. The summary lives only in `state["pdf_result"]` and is printed to the terminal.

---

## 11. Standalone Usage (for testing)

The agent can be tested independently without running the full pipeline:

```bash
# Test with a local file
python agents/pdf_agent.py uploads/myfile.pdf

# Test with a URL
python agents/pdf_agent.py https://arxiv.org/pdf/2301.00001.pdf

# Interactive prompt (no arguments)
python agents/pdf_agent.py
```

---

## 12. Example Run

**User task:**
```
Extract text from https://arxiv.org/pdf/1706.03762.pdf
```

**Terminal output:**
```
📄 PDF Agent -- task: Extract text from https://arxiv.org/pdf/1706.03762.pdf
📄 PDF Agent -- downloading from URL: https://arxiv.org/pdf/1706.03762.pdf
📄 PDF Agent -- extracting text...
📄 PDF Agent -- extracted 43,218 characters from PDF
📄 PDF Agent -- summarizing with LLM...
📄 PDF Agent -- done. Summary length: 1,842 chars
```

**Final pdf_result:**
```
📄 PDF Processed: `https://arxiv.org/pdf/1706.03762.pdf`
📏 Extracted: 43,218 characters

## Document Overview
This paper introduces the Transformer architecture, a novel neural network
model based entirely on attention mechanisms, dispensing with recurrence
and convolutions entirely...

## Key Points
- Proposed in 2017 by Vaswani et al. at Google Brain
- Achieves 28.4 BLEU on WMT 2014 English-to-German translation
- Training time: 3.5 days on 8 NVIDIA P100 GPUs
...

## Bottom Line
The Transformer redefined NLP by proving that attention alone — without
any recurrent or convolutional layers — can achieve state-of-the-art results,
becoming the foundation for GPT, BERT, and virtually every modern LLM.
```

---

## 13. Suggested Improvements (Roadmap)

- [ ] Add OCR support for scanned/image PDFs (using `pytesseract` or `easyocr`)
- [ ] Chunked summarization — process large docs in overlapping segments for full coverage
- [ ] Save PDF summaries to GitHub (`git_agent_output/`) like the Coder Agent does
- [ ] Support password-protected PDFs (accept password via task string)
- [ ] Add page range selection (e.g. "summarize pages 5–20 of report.pdf")
- [ ] Support other document formats: `.docx`, `.txt`, `.pptx`

---

*Documentation prepared for internal review. Part of the AI Agent System project.*
