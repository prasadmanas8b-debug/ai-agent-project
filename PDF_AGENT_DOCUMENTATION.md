# PDF Agent — Production-Grade Documentation

Multi-agent AI system powered by Groq (llama-4-scout) + PyMuPDF + pypdf + ReportLab.

## 🚀 Features — 43 handlers across 14 categories

### Core Operations
| Mode | Description |
|------|-------------|
| `read` | Parse PDF — page count, word count, text preview, scanned detection |
| `create` | Generate PDF from a text prompt (ReportLab code + content plan) |
| `summarize` | Executive summary, key points, topics, sentiment, language |
| `qa` | Q&A over PDF content with source section citations |
| `translate` | Translate PDF to any language |
| `extract` | Tables, key-values, lists, named entities |

### Text Operations
| Mode | Description |
|------|-------------|
| `search` | Full-text search across all pages with bounding box coords |
| `find_replace` | Find & replace text — returns occurrence count + code |
| `watermark` | Add diagonal watermark text (e.g. CONFIDENTIAL) |
| `page_numbers` | Add page numbers to all pages |
| `header_footer` | Add custom header and/or footer |
| `rewrite` | AI rewrite in a different style/tone |

### Page Management
| Mode | Description |
|------|-------------|
| `page_ops` | Rotate, extract, remove, add blank pages — returns modified PDF |
| `split` | Split by page range — returns array of PDF parts |
| `merge` | Merge two PDFs (pass `pdf_bytes` + `pdf2_bytes`) |
| `merge_plan` | AI merge strategy + pypdf code (no file needed) |

### Image Operations
| Mode | Description |
|------|-------------|
| `extract_images` | Extract all embedded images as base64 |
| `pdf_to_images` | Convert each page to PNG/JPG (2x resolution) |

### AI-Powered
| Mode | Description |
|------|-------------|
| `classify` | Document type, language, topics, reasoning |
| `sentiment` | Emotion breakdown, tone, key phrases |
| `ner` | People, orgs, locations, dates, emails, phones, URLs |
| `compare` | Diff two PDFs — similarity %, unique content, differences |
| `autotag` | Auto-tags, categories, department, priority, action required |
| `reformat` | AI restructure + new ReportLab code |
| `md_to_pdf` | Generate Markdown + PDF code from a prompt |

### Data Extraction
| Mode | Description |
|------|-------------|
| `tables_to_csv` | Extract all tables as downloadable CSV |
| `to_markdown` | Convert PDF content to Markdown |
| `to_html` | Convert PDF content to semantic HTML5 |

### Metadata
| Mode | Description |
|------|-------------|
| `metadata` | Read metadata, suggest improvements, SEO score |
| `set_metadata` | Write/update title, author, subject, keywords |

### Security
| Mode | Description |
|------|-------------|
| `protect` | Password-encrypt PDF |
| `decrypt` | Remove password from PDF |
| `redact` | Permanently black out sensitive text |
| `signature` | Generate digital signature code (pyhanko) |

### OCR
| Mode | Description |
|------|-------------|
| `ocr` | Extract text from scanned PDFs via pytesseract |

### Annotations
| Mode | Description |
|------|-------------|
| `annotate` | Highlight text, add sticky notes |
| `bookmarks` | Read bookmarks or auto-generate TOC |

### Optimization
| Mode | Description |
|------|-------------|
| `compress` | Lossless compression — reports size reduction % |
| `repair` | Fix corrupted PDFs via PyMuPDF rebuild |
| `linearize` | Optimize for fast web view |

### Forms
| Mode | Description |
|------|-------------|
| `forms` | Detect fillable fields, extract values, generate fill code |

### Accessibility
| Mode | Description |
|------|-------------|
| `accessibility` | WCAG/PDF-UA audit — issues, severity, fixes |

### Batch
| Mode | Description |
|------|-------------|
| `batch` | Generate Python batch processing scripts |

---

## 📡 API Reference

### `POST /api/pdf` — JSON body
```json
{
  "task":     "Summarize this PDF",
  "pdf_mode": "summarize",
  "pdf_b64":  "<base64-encoded PDF bytes>",
  "pdf2_b64": "<base64 of second PDF for compare/merge>"
}
```

### `POST /api/pdf/upload` — Multipart form
```
task=<string>
pdf_mode=<mode>
file=<PDF file>
file2=<second PDF file>   (for compare/merge)
```

### `GET /api/pdf/modes` — List all available modes

---

## 🏗️ Architecture

```
state["task"]        → _infer_mode()  → handler(pdf_bytes, task)
state["pdf_mode"]    ↗                                ↓
state["pdf_bytes"]                          state["pdf_result"]  (JSON string)
state["pdf2_bytes"]
```

All handlers return a dict. The main entry serializes it to `state["pdf_result"]` as a JSON string.

Handlers that produce a modified PDF include `pdf_b64` in the response (base64-encoded bytes).

---

## ⚙️ Setup

```bash
pip install pymupdf pypdf reportlab pillow pytesseract
# For OCR: sudo apt-get install tesseract-ocr
# For linearize: pymupdf already handles this
```

## 🔌 Integration

```python
from agents.pdf_agent import run_pdf_agent

state = run_pdf_agent({
    "task": "Summarize this document",
    "pdf_mode": "summarize",
    "pdf_bytes": open("report.pdf", "rb").read(),
})
print(state["pdf_result"])  # JSON string
```

---

*Stack: LangChain · ChatGroq · meta-llama/llama-4-scout-17b-16e-instruct · PyMuPDF · pypdf · ReportLab · pytesseract*
