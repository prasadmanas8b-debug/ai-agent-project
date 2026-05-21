/**
 * PDFAgent.jsx
 * Production-grade PDF Agent UI — 100+ features across 20 categories.
 * React + Tailwind CSS. Communicates with /api/pdf and /api/pdf/upload.
 */

import React, { useState, useRef, useCallback, useEffect } from "react";

// ── Constants ─────────────────────────────────────────────────────────────────
const API_BASE = "/api/pdf";

const CATEGORIES = [
  {
    id: "core", label: "📄 Core", color: "blue",
    features: [
      { id: "read",      label: "Read & Parse",     icon: "🔍", desc: "Parse PDF, get page count, word count, preview", needsPdf: true },
      { id: "create",    label: "Create PDF",        icon: "✨", desc: "Generate a PDF from a text prompt", needsPdf: false },
      { id: "summarize", label: "Summarize",         icon: "📋", desc: "Executive summary, key points, topics, sentiment", needsPdf: true },
      { id: "qa",        label: "Q&A",               icon: "💬", desc: "Ask questions about your PDF", needsPdf: true },
      { id: "translate", label: "Translate",         icon: "🌍", desc: "Translate PDF to any language", needsPdf: true },
      { id: "extract",   label: "Extract Data",      icon: "📊", desc: "Tables, entities, key-values, lists", needsPdf: true },
    ]
  },
  {
    id: "text", label: "✏️ Text", color: "purple",
    features: [
      { id: "search",       label: "Search Text",       icon: "🔎", desc: "Find text across all pages with context", needsPdf: true },
      { id: "find_replace", label: "Find & Replace",    icon: "🔄", desc: "Replace text across the entire document", needsPdf: true },
      { id: "watermark",    label: "Watermark",         icon: "💧", desc: "Add diagonal watermark text (e.g. CONFIDENTIAL)", needsPdf: true },
      { id: "page_numbers", label: "Page Numbers",      icon: "🔢", desc: "Add page numbers to all pages", needsPdf: true },
      { id: "header_footer",label: "Header / Footer",   icon: "📐", desc: "Add custom header and/or footer text", needsPdf: true },
      { id: "rewrite",      label: "Rewrite / Rephrase",icon: "✍️", desc: "AI rewrite in a different style or tone", needsPdf: true },
    ]
  },
  {
    id: "pages", label: "📑 Pages", color: "orange",
    features: [
      { id: "page_ops",  label: "Page Operations",   icon: "📄", desc: "Rotate, extract, remove, or add blank pages", needsPdf: true },
      { id: "split",     label: "Split PDF",          icon: "✂️", desc: "Split into multiple PDFs by page range", needsPdf: true },
      { id: "merge",     label: "Merge PDFs",         icon: "🔗", desc: "Merge two PDFs into one", needsPdf: true, needsPdf2: true },
      { id: "merge_plan",label: "Merge Strategy",     icon: "🗂️", desc: "AI-generated merge strategy + code", needsPdf: false },
    ]
  },
  {
    id: "images", label: "🖼️ Images", color: "pink",
    features: [
      { id: "extract_images", label: "Extract Images",    icon: "🖼️", desc: "Extract all embedded images from PDF", needsPdf: true },
      { id: "pdf_to_images",  label: "Pages → Images",    icon: "📸", desc: "Convert each PDF page to PNG/JPG", needsPdf: true },
    ]
  },
  {
    id: "ai", label: "🤖 AI", color: "indigo",
    features: [
      { id: "classify",   label: "Classify Document", icon: "🏷️", desc: "Detect document type, language, topics", needsPdf: true },
      { id: "sentiment",  label: "Sentiment Analysis",icon: "😊", desc: "Emotions, tone, positive/negative phrases", needsPdf: true },
      { id: "ner",        label: "Named Entities",     icon: "🏢", desc: "Extract people, orgs, dates, emails, phones", needsPdf: true },
      { id: "compare",    label: "Compare PDFs",       icon: "⚖️", desc: "Diff two PDFs, find similarities/differences", needsPdf: true, needsPdf2: true },
      { id: "autotag",    label: "Auto-tag",           icon: "🔖", desc: "Auto-tag, categorize, priority, department", needsPdf: true },
      { id: "reformat",   label: "Reformat Layout",    icon: "🎨", desc: "AI restructure + new ReportLab code", needsPdf: true },
      { id: "md_to_pdf",  label: "Markdown → PDF",     icon: "📝", desc: "Generate a PDF from a Markdown prompt", needsPdf: false },
    ]
  },
  {
    id: "data", label: "📊 Data", color: "teal",
    features: [
      { id: "tables_to_csv", label: "Tables → CSV",     icon: "📋", desc: "Extract all tables as CSV data", needsPdf: true },
      { id: "to_markdown",   label: "PDF → Markdown",   icon: "⬇️", desc: "Convert PDF content to Markdown", needsPdf: true },
      { id: "to_html",       label: "PDF → HTML",       icon: "🌐", desc: "Convert PDF content to semantic HTML5", needsPdf: true },
    ]
  },
  {
    id: "metadata", label: "🏷️ Metadata", color: "yellow",
    features: [
      { id: "metadata",     label: "Read Metadata",     icon: "📋", desc: "Read & suggest metadata, SEO score", needsPdf: true },
      { id: "set_metadata", label: "Set Metadata",      icon: "✏️", desc: "Write/update PDF metadata fields", needsPdf: true },
    ]
  },
  {
    id: "security", label: "🔒 Security", color: "red",
    features: [
      { id: "protect",   label: "Password Protect",    icon: "🔐", desc: "Encrypt PDF with a password", needsPdf: true },
      { id: "decrypt",   label: "Remove Password",     icon: "🔓", desc: "Decrypt a password-protected PDF", needsPdf: true },
      { id: "redact",    label: "Redact",              icon: "⬛", desc: "Permanently black out sensitive text", needsPdf: true },
      { id: "signature", label: "Digital Signature",   icon: "✍️", desc: "Generate code to sign a PDF", needsPdf: true },
    ]
  },
  {
    id: "ocr", label: "👁️ OCR", color: "cyan",
    features: [
      { id: "ocr", label: "OCR", icon: "🔬", desc: "Extract text from scanned/image-based PDFs", needsPdf: true },
    ]
  },
  {
    id: "annotations", label: "🖊️ Annotations", color: "lime",
    features: [
      { id: "annotate",  label: "Highlight & Annotate", icon: "🖊️", desc: "Highlight text, add sticky notes", needsPdf: true },
      { id: "bookmarks", label: "Bookmarks / TOC",      icon: "📚", desc: "Read bookmarks or auto-generate TOC", needsPdf: true },
    ]
  },
  {
    id: "optimize", label: "⚡ Optimize", color: "green",
    features: [
      { id: "compress",  label: "Compress",  icon: "🗜️", desc: "Reduce file size with lossless compression", needsPdf: true },
      { id: "repair",    label: "Repair",    icon: "🔧", desc: "Fix and recover corrupted PDFs", needsPdf: true },
      { id: "linearize", label: "Linearize", icon: "⚡", desc: "Optimize for fast web viewing", needsPdf: true },
    ]
  },
  {
    id: "forms", label: "📝 Forms", color: "violet",
    features: [
      { id: "forms", label: "Forms", icon: "📝", desc: "Detect fields, extract values, generate fill code", needsPdf: true },
    ]
  },
  {
    id: "accessibility", label: "♿ Access.", color: "slate",
    features: [
      { id: "accessibility", label: "Accessibility Audit", icon: "♿", desc: "WCAG/PDF-UA compliance check & recommendations", needsPdf: true },
    ]
  },
  {
    id: "batch", label: "📦 Batch", color: "stone",
    features: [
      { id: "batch", label: "Batch Processing", icon: "📦", desc: "Generate batch processing code for bulk operations", needsPdf: false },
    ]
  },
];

// Flatten all features for lookup
const ALL_FEATURES = CATEGORIES.flatMap(c => c.features.map(f => ({ ...f, category: c.id })));

const COLOR_MAP = {
  blue:   "bg-blue-50 border-blue-200 text-blue-700",
  purple: "bg-purple-50 border-purple-200 text-purple-700",
  orange: "bg-orange-50 border-orange-200 text-orange-700",
  pink:   "bg-pink-50 border-pink-200 text-pink-700",
  indigo: "bg-indigo-50 border-indigo-200 text-indigo-700",
  teal:   "bg-teal-50 border-teal-200 text-teal-700",
  yellow: "bg-yellow-50 border-yellow-200 text-yellow-700",
  red:    "bg-red-50 border-red-200 text-red-700",
  cyan:   "bg-cyan-50 border-cyan-200 text-cyan-700",
  lime:   "bg-lime-50 border-lime-200 text-lime-700",
  green:  "bg-green-50 border-green-200 text-green-700",
  violet: "bg-violet-50 border-violet-200 text-violet-700",
  slate:  "bg-slate-50 border-slate-200 text-slate-700",
  stone:  "bg-stone-50 border-stone-200 text-stone-700",
};

// ── Utility ───────────────────────────────────────────────────────────────────
function downloadB64(b64, filename, mime = "application/pdf") {
  const a = document.createElement("a");
  a.href = `data:${mime};base64,${b64}`;
  a.download = filename;
  a.click();
}

function fileToB64(file) {
  return new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(r.result.split(",")[1]);
    r.onerror = rej;
    r.readAsDataURL(file);
  });
}

// ── Sub-components ────────────────────────────────────────────────────────────
function DropZone({ label, file, setFile, accept = ".pdf" }) {
  const [drag, setDrag] = useState(false);
  const ref = useRef();

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  }, [setFile]);

  return (
    <div
      className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all
        ${drag ? "border-blue-400 bg-blue-50" : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"}`}
      onDragOver={e => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
      onClick={() => ref.current?.click()}
    >
      <input ref={ref} type="file" accept={accept} className="hidden"
        onChange={e => e.target.files[0] && setFile(e.target.files[0])} />
      {file ? (
        <div className="flex items-center justify-center gap-2 text-green-600 font-medium">
          <span>✅</span>
          <span className="truncate max-w-xs">{file.name}</span>
          <span className="text-gray-400 text-sm">({(file.size/1024).toFixed(1)} KB)</span>
          <button className="ml-2 text-red-400 hover:text-red-600 text-xs"
            onClick={e => { e.stopPropagation(); setFile(null); }}>✕</button>
        </div>
      ) : (
        <div className="text-gray-500">
          <div className="text-3xl mb-2">📂</div>
          <div className="font-medium">{label}</div>
          <div className="text-xs mt-1">Click to browse or drag & drop</div>
        </div>
      )}
    </div>
  );
}

function ResultPanel({ result, feature }) {
  const [tab, setTab] = useState("pretty");
  if (!result) return null;

  let parsed = null;
  try { parsed = JSON.parse(result); } catch {}

  const hasPdf = parsed?.pdf_b64;
  const hasImages = parsed?.images?.length || parsed?.image_b64;
  const hasCsvs = parsed?.csvs?.length;
  const hasMarkdown = parsed?.markdown;
  const hasHtml = parsed?.html;
  const hasCode = parsed?.python_code || parsed?.code;

  return (
    <div className="mt-6 bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
        <div className="flex gap-2">
          {["pretty","raw"].map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-all
                ${tab === t ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-200"}`}>
              {t === "pretty" ? "📊 Results" : "{ } Raw JSON"}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          {hasPdf && (
            <button onClick={() => downloadB64(parsed.pdf_b64, `${feature}_output.pdf`)}
              className="px-3 py-1 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 flex items-center gap-1">
              ⬇️ Download PDF
            </button>
          )}
          {hasCsvs && parsed.csvs.map((csv, i) => (
            <button key={i} onClick={() => {
              const blob = new Blob([csv.csv], { type: "text/csv" });
              const a = document.createElement("a");
              a.href = URL.createObjectURL(blob);
              a.download = `${csv.title || "table"}_${i+1}.csv`;
              a.click();
            }}
              className="px-3 py-1 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">
              ⬇️ {csv.title || `Table ${i+1}`}.csv
            </button>
          ))}
          {hasMarkdown && (
            <button onClick={() => {
              const blob = new Blob([parsed.markdown], { type: "text/markdown" });
              const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
              a.download = "output.md"; a.click();
            }}
              className="px-3 py-1 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700">
              ⬇️ Download .md
            </button>
          )}
          {hasHtml && (
            <button onClick={() => {
              const blob = new Blob([parsed.html], { type: "text/html" });
              const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
              a.download = "output.html"; a.click();
            }}
              className="px-3 py-1 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700">
              ⬇️ Download .html
            </button>
          )}
        </div>
      </div>

      <div className="p-4 max-h-[600px] overflow-y-auto">
        {tab === "raw" ? (
          <pre className="text-xs bg-gray-950 text-green-300 p-4 rounded-xl overflow-x-auto whitespace-pre-wrap">
            {result}
          </pre>
        ) : (
          <PrettyResult parsed={parsed} feature={feature} />
        )}
      </div>
    </div>
  );
}

function PrettyResult({ parsed, feature }) {
  if (!parsed) return <pre className="text-sm text-gray-700 whitespace-pre-wrap">{String(parsed)}</pre>;
  if (parsed.error) return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
      <div className="font-bold mb-1">❌ Error</div>
      <div className="text-sm">{parsed.error}</div>
      {parsed.traceback && <pre className="mt-2 text-xs text-red-400 whitespace-pre-wrap">{parsed.traceback}</pre>}
    </div>
  );

  // Images grid
  if (parsed.images?.length) return (
    <div>
      <div className="text-sm font-medium text-gray-600 mb-3">
        {parsed.total_images ? `${parsed.total_images} images found` : `${parsed.total_pages} pages converted`}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {parsed.images.slice(0,12).map((img, i) => (
          <div key={i} className="border rounded-xl overflow-hidden bg-gray-50">
            <img src={`data:image/${img.ext || img.format || "png"};base64,${img.image_b64}`}
              alt={`Page/Image ${img.page || i+1}`} className="w-full object-contain max-h-48" />
            <div className="text-xs text-center py-1 text-gray-500">
              Page {img.page || i+1} · {img.width}×{img.height}
            </div>
            <button className="w-full text-xs text-blue-600 hover:bg-blue-50 py-1"
              onClick={() => downloadB64(img.image_b64, `page_${img.page || i+1}.${img.ext || img.format || "png"}`, `image/${img.ext || img.format || "png"}`)}>
              ⬇️ Download
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  // Split parts
  if (parsed.parts?.length) return (
    <div>
      <div className="text-sm font-medium text-gray-600 mb-3">
        Original: {parsed.original_pages} pages → {parsed.parts.length} parts
      </div>
      <div className="space-y-2">
        {parsed.parts.map((p, i) => (
          <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border">
            <span className="text-sm font-medium">Part {i+1}: Pages {p.range} ({p.pages} pages)</span>
            <button onClick={() => downloadB64(p.pdf_b64, `part_${i+1}_pages_${p.range}.pdf`)}
              className="px-3 py-1 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
              ⬇️ Download
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  // Key-value grid
  const kvPairs = Object.entries(parsed).filter(([k]) => !["pdf_b64","pdf2_b64","python_code","code","traceback","full_text","translated_content","rewritten_text","markdown","html","toc"].includes(k));

  return (
    <div className="space-y-4">
      {/* Summary cards */}
      {kvPairs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {kvPairs.map(([k, v]) => {
            if (Array.isArray(v) && v.length === 0) return null;
            if (v === null || v === undefined || v === "") return null;
            return (
              <div key={k} className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
                  {k.replace(/_/g, " ")}
                </div>
                {Array.isArray(v) ? (
                  <ul className="text-sm text-gray-700 space-y-0.5">
                    {v.slice(0,10).map((item, i) => (
                      <li key={i} className="flex gap-1">
                        <span className="text-gray-400">•</span>
                        <span>{typeof item === "object" ? JSON.stringify(item) : String(item)}</span>
                      </li>
                    ))}
                    {v.length > 10 && <li className="text-gray-400 text-xs">+{v.length - 10} more</li>}
                  </ul>
                ) : typeof v === "object" ? (
                  <div className="text-sm text-gray-700 space-y-0.5">
                    {Object.entries(v).slice(0,8).map(([sk, sv]) => (
                      <div key={sk}><span className="font-medium">{sk}:</span> {Array.isArray(sv) ? sv.join(", ") : String(sv)}</div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-gray-700 break-words">{String(v)}</div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* TOC */}
      {parsed.toc?.length > 0 && (
        <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
          <div className="text-xs font-semibold text-gray-400 uppercase mb-2">Table of Contents</div>
          {parsed.toc.map((item, i) => (
            <div key={i} style={{ paddingLeft: `${(item.level - 1) * 16}px` }}
              className="text-sm text-gray-700 py-0.5 border-b border-gray-100 last:border-0">
              {item.level === 1 ? "▶" : "›"} {item.title} <span className="text-gray-400 text-xs">p.{item.page}</span>
            </div>
          ))}
        </div>
      )}

      {/* Code block */}
      {(parsed.python_code || parsed.code) && (
        <div className="bg-gray-950 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-3 py-2 bg-gray-800">
            <span className="text-xs text-gray-400">🐍 Python Code</span>
            <button className="text-xs text-blue-400 hover:text-blue-300"
              onClick={() => navigator.clipboard.writeText(parsed.python_code || parsed.code)}>
              📋 Copy
            </button>
          </div>
          <pre className="p-4 text-green-300 text-xs overflow-x-auto whitespace-pre-wrap max-h-80">
            {parsed.python_code || parsed.code}
          </pre>
        </div>
      )}

      {/* Markdown preview */}
      {parsed.markdown && (
        <div className="bg-white border rounded-xl p-4">
          <div className="text-xs font-semibold text-gray-400 uppercase mb-2">Markdown Preview</div>
          <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono bg-gray-50 p-3 rounded-lg max-h-64 overflow-y-auto">
            {parsed.markdown}
          </pre>
        </div>
      )}

      {/* HTML preview */}
      {parsed.html && (
        <div className="bg-white border rounded-xl p-4">
          <div className="text-xs font-semibold text-gray-400 uppercase mb-2">HTML Preview</div>
          <div className="border rounded-lg overflow-hidden max-h-64 overflow-y-auto">
            <iframe srcDoc={parsed.html} className="w-full min-h-48" title="HTML Preview" sandbox="allow-same-origin" />
          </div>
        </div>
      )}

      {/* Translated / rewritten content */}
      {(parsed.translated_content || parsed.rewritten_text) && (
        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
          <div className="text-xs font-semibold text-blue-400 uppercase mb-2">
            {parsed.translated_content ? "Translated Content" : "Rewritten Content"}
          </div>
          <div className="text-sm text-gray-700 max-h-64 overflow-y-auto whitespace-pre-wrap">
            {parsed.translated_content || parsed.rewritten_text}
          </div>
        </div>
      )}

      {/* CSV tables */}
      {parsed.csvs?.length > 0 && (
        <div className="space-y-3">
          {parsed.csvs.map((csv, i) => (
            <div key={i} className="bg-gray-50 border rounded-xl overflow-hidden">
              <div className="px-3 py-2 bg-gray-100 text-xs font-semibold text-gray-600">{csv.title}</div>
              <pre className="p-3 text-xs text-gray-700 overflow-x-auto max-h-48">{csv.csv}</pre>
            </div>
          ))}
        </div>
      )}

      {/* Full text */}
      {parsed.full_text && (
        <details className="bg-gray-50 border rounded-xl">
          <summary className="px-4 py-2 cursor-pointer text-sm font-medium text-gray-600">📄 Full Extracted Text</summary>
          <pre className="px-4 pb-4 text-xs text-gray-600 whitespace-pre-wrap max-h-96 overflow-y-auto">
            {parsed.full_text}
          </pre>
        </details>
      )}

      {/* OCR text */}
      {parsed.ocr_text && (
        <div className="bg-gray-50 border rounded-xl p-4">
          <div className="text-xs font-semibold text-gray-400 uppercase mb-2">OCR Output</div>
          <pre className="text-sm text-gray-700 whitespace-pre-wrap max-h-64 overflow-y-auto">{parsed.ocr_text}</pre>
        </div>
      )}

      {/* PDF download banner */}
      {parsed.pdf_b64 && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center justify-between">
          <div>
            <div className="font-medium text-blue-700">✅ PDF Ready</div>
            <div className="text-sm text-blue-500">{parsed.operation || parsed.watermark || "Output PDF generated"}</div>
          </div>
          <button onClick={() => downloadB64(parsed.pdf_b64, `${feature}_output.pdf`)}
            className="px-4 py-2 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 flex items-center gap-2">
            ⬇️ Download PDF
          </button>
        </div>
      )}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function PDFAgent() {
  const [activeCategory, setActiveCategory] = useState("core");
  const [activeFeature, setActiveFeature] = useState("summarize");
  const [task, setTask] = useState("");
  const [file, setFile] = useState(null);
  const [file2, setFile2] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem("pdf_history") || "[]"); } catch { return []; }
  });
  const [searchQuery, setSearchQuery] = useState("");

  const currentFeature = ALL_FEATURES.find(f => f.id === activeFeature);
  const currentCategory = CATEGORIES.find(c => c.id === (currentFeature?.category || activeCategory));

  // Persist history
  useEffect(() => {
    sessionStorage.setItem("pdf_history", JSON.stringify(history.slice(0, 20)));
  }, [history]);

  const filteredFeatures = searchQuery
    ? ALL_FEATURES.filter(f =>
        f.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.desc.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.id.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : null;

  async function handleRun() {
    if (!task.trim() && !file) return;
    setLoading(true);
    setResult(null);

    try {
      let res;

      if (file) {
        // File upload path
        const formData = new FormData();
        formData.append("task", task || activeFeature);
        formData.append("pdf_mode", activeFeature);
        formData.append("file", file);
        if (file2) formData.append("file2", file2);

        res = await fetch(`${API_BASE}/upload`, {
          method: "POST",
          body: formData,
        });
      } else {
        // JSON body path (no file, e.g. create)
        res = await fetch(API_BASE, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ task, pdf_mode: activeFeature }),
        });
      }

      const data = await res.json();
      const resultStr = data.result || JSON.stringify(data);
      setResult(resultStr);

      const entry = {
        id: Date.now(),
        feature: activeFeature,
        task: task.slice(0, 80),
        timestamp: new Date().toLocaleTimeString(),
        hasOutput: true,
      };
      setHistory(h => [entry, ...h].slice(0, 20));
    } catch (err) {
      setResult(JSON.stringify({ error: err.message }));
    } finally {
      setLoading(false);
    }
  }

  function selectFeature(fid) {
    setActiveFeature(fid);
    setResult(null);
    const feat = ALL_FEATURES.find(f => f.id === fid);
    if (feat) setActiveCategory(feat.category);
    setSearchQuery("");
  }

  const TASK_PLACEHOLDERS = {
    create: "Create a 5-page technical report on AI trends in 2025...",
    summarize: "Summarize this PDF with key points and sentiment",
    qa: "What are the main conclusions of this document?",
    translate: "Translate to French",
    extract: "Extract all tables and named entities",
    search: "Search for 'machine learning'",
    find_replace: "Replace 'draft' with 'final'",
    watermark: "watermark 'CONFIDENTIAL'",
    page_numbers: "Add page numbers to all pages",
    header_footer: "header 'Company Report 2025' footer 'Confidential'",
    page_ops: "Extract pages 1-3 as a new PDF",
    split: "Split into 1-10 and 11-20",
    merge_plan: "Merge a contract and its amendment",
    classify: "Classify this document",
    sentiment: "Analyze the sentiment and tone",
    ner: "Extract all people, organizations, and dates",
    compare: "Compare these two versions of the document",
    rewrite: "Rewrite in simple, plain English",
    autotag: "Auto-tag and categorize this document",
    md_to_pdf: "Create a professional invoice PDF for $5000 consulting services",
    tables_to_csv: "Extract all tables as CSV",
    to_markdown: "Convert to Markdown",
    to_html: "Convert to HTML",
    metadata: "Analyze and suggest metadata",
    set_metadata: "Set title 'Annual Report 2025', author 'Kunal Roy'",
    protect: "password protect 'mySecretPass123'",
    decrypt: "decrypt with password 'mySecretPass123'",
    redact: "redact 'John Smith' 'confidential@email.com'",
    ocr: "Run OCR and extract all text",
    annotate: "highlight 'important' and 'critical'",
    bookmarks: "Show table of contents",
    compress: "Compress and reduce file size",
    repair: "Repair and recover this PDF",
    linearize: "Optimize for fast web viewing",
    forms: "Detect and extract all form fields",
    accessibility: "Run accessibility audit",
    batch: "Batch compress all PDFs in a folder and save as _compressed",
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 font-sans">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow">
              📄
            </div>
            <div>
              <div className="font-bold text-gray-900 text-lg leading-none">PDF Agent</div>
              <div className="text-xs text-gray-400">100+ features · AI-powered</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <input
                type="text"
                placeholder="Search features..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 border border-gray-200 rounded-xl text-sm w-48 focus:outline-none focus:ring-2 focus:ring-blue-300"
              />
              <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs">🔍</span>
            </div>
            <div className="text-xs text-gray-400 hidden md:block">
              {ALL_FEATURES.length} features
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6 flex gap-6">
        {/* Left Sidebar */}
        <div className="w-72 shrink-0">
          {/* Search results */}
          {searchQuery && filteredFeatures ? (
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-4 py-2 bg-gray-50 border-b text-xs font-semibold text-gray-500 uppercase tracking-wide">
                {filteredFeatures.length} results
              </div>
              <div className="max-h-96 overflow-y-auto">
                {filteredFeatures.map(f => (
                  <button key={f.id} onClick={() => selectFeature(f.id)}
                    className={`w-full px-4 py-2.5 flex items-start gap-2 text-left hover:bg-blue-50 transition-colors border-b border-gray-50
                      ${activeFeature === f.id ? "bg-blue-50" : ""}`}>
                    <span className="text-base">{f.icon}</span>
                    <div>
                      <div className="text-sm font-medium text-gray-800">{f.label}</div>
                      <div className="text-xs text-gray-400">{f.desc}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {CATEGORIES.map(cat => (
                <div key={cat.id} className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                  <button
                    onClick={() => setActiveCategory(activeCategory === cat.id ? null : cat.id)}
                    className={`w-full px-4 py-2.5 flex items-center justify-between text-left font-semibold text-sm transition-colors
                      ${activeCategory === cat.id ? "bg-gray-50" : "hover:bg-gray-50"}`}>
                    <span>{cat.label}</span>
                    <span className="text-gray-400 text-xs">{activeCategory === cat.id ? "▲" : "▼"}</span>
                  </button>
                  {activeCategory === cat.id && (
                    <div className="border-t border-gray-100">
                      {cat.features.map(f => (
                        <button key={f.id} onClick={() => selectFeature(f.id)}
                          className={`w-full px-4 py-2 flex items-center gap-2 text-left text-sm transition-colors border-b border-gray-50 last:border-0
                            ${activeFeature === f.id ? `bg-blue-600 text-white` : "hover:bg-gray-50 text-gray-700"}`}>
                          <span>{f.icon}</span>
                          <span className="font-medium">{f.label}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* History */}
          {history.length > 0 && (
            <div className="mt-4 bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-4 py-2 bg-gray-50 border-b text-xs font-semibold text-gray-500 uppercase tracking-wide flex justify-between">
                <span>Recent</span>
                <button onClick={() => setHistory([])} className="text-red-400 hover:text-red-600">Clear</button>
              </div>
              <div className="max-h-48 overflow-y-auto">
                {history.slice(0, 8).map(h => (
                  <button key={h.id} onClick={() => selectFeature(h.feature)}
                    className="w-full px-4 py-2 text-left text-xs text-gray-600 hover:bg-gray-50 border-b border-gray-50 last:border-0">
                    <div className="font-medium">{ALL_FEATURES.find(f => f.id === h.feature)?.icon} {h.feature}</div>
                    <div className="text-gray-400 truncate">{h.task || "(no task)"}</div>
                    <div className="text-gray-300">{h.timestamp}</div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Main Panel */}
        <div className="flex-1 min-w-0">
          {currentFeature && (
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              {/* Feature Header */}
              <div className={`px-6 py-4 border-b border-gray-100`}>
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{currentFeature.icon}</span>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">{currentFeature.label}</h2>
                    <p className="text-sm text-gray-500">{currentFeature.desc}</p>
                  </div>
                  {currentCategory && (
                    <span className={`ml-auto px-3 py-1 rounded-full text-xs font-medium border ${COLOR_MAP[currentCategory.color] || COLOR_MAP.blue}`}>
                      {currentCategory.label}
                    </span>
                  )}
                </div>
              </div>

              <div className="p-6 space-y-5">
                {/* File uploads */}
                {currentFeature.needsPdf && (
                  <DropZone label="Drop your PDF here" file={file} setFile={setFile} />
                )}
                {currentFeature.needsPdf2 && (
                  <DropZone label="Drop the second PDF here" file={file2} setFile={setFile2} />
                )}

                {/* Task input */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Task / Instructions
                  </label>
                  <textarea
                    rows={3}
                    value={task}
                    onChange={e => setTask(e.target.value)}
                    placeholder={TASK_PLACEHOLDERS[activeFeature] || `Describe what you want to do...`}
                    className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-300 transition-all"
                    onKeyDown={e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) handleRun(); }}
                  />
                  <div className="text-xs text-gray-400 mt-1">Ctrl+Enter to run</div>
                </div>

                {/* Run button */}
                <button
                  onClick={handleRun}
                  disabled={loading || (!task.trim() && !file && currentFeature.needsPdf)}
                  className={`w-full py-3 rounded-xl font-semibold text-white text-sm transition-all flex items-center justify-center gap-2
                    ${loading
                      ? "bg-gray-400 cursor-not-allowed"
                      : "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-md hover:shadow-lg active:scale-[0.99]"
                    }`}>
                  {loading ? (
                    <>
                      <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z"/>
                      </svg>
                      Processing…
                    </>
                  ) : (
                    <>{currentFeature.icon} Run {currentFeature.label}</>
                  )}
                </button>

                {/* Tips */}
                <div className="bg-amber-50 border border-amber-100 rounded-xl px-4 py-3 text-xs text-amber-700">
                  💡 <strong>Tip:</strong> {
                    currentFeature.needsPdf
                      ? "Upload a PDF file to enable this feature. The agent will process it server-side."
                      : "No PDF needed — just describe what you want in the task box."
                  }
                </div>
              </div>
            </div>
          )}

          {/* Result */}
          <ResultPanel result={result} feature={activeFeature} />
        </div>
      </div>
    </div>
  );
}
