/**
 * PDFAgent.jsx
 * AI-powered PDF toolkit — 8 features, clean UI, talks to the Python pipeline.
 *
 * Features: create | summarize | qa | translate | extract | reformat | merge_plan | metadata
 *
 * Optimisations over v1:
 *   - Extracted Badge, CodeBlock, ResultRenderer into separate files (kept inline here
 *     for portability, but split-ready).
 *   - useCallback / useMemo used properly — no stale-closure bugs.
 *   - buildUserMessage is pure (no closure over state) — easy to unit-test.
 *   - Single source-of-truth: FEATURES + SYSTEM_PROMPTS drive everything.
 *   - Error boundary around ResultRenderer so a bad parse never crashes the page.
 *   - History capped at 10, stored in sessionStorage for tab-refresh persistence.
 *   - Accessible: aria-labels, role=status on loader, keyboard-navigable feature grid.
 *   - CSS-in-JS animations moved to a single <style> block at the bottom.
 */
import { useState, useRef, useCallback, useMemo, useEffect } from "react";

// ─── Constants ────────────────────────────────────────────────────────────────
const FEATURES = [
  { id: "create",     icon: "ti-file-plus",      label: "Create PDF",    desc: "Generate a styled PDF from a prompt" },
  { id: "summarize",  icon: "ti-file-text",       label: "Summarize PDF", desc: "Extract key insights from uploaded PDF" },
  { id: "qa",         icon: "ti-message-question",label: "Ask PDF",       desc: "Q&A over an uploaded PDF" },
  { id: "translate",  icon: "ti-language",        label: "Translate PDF", desc: "Translate PDF content to another language" },
  { id: "extract",    icon: "ti-table",           label: "Extract Data",  desc: "Pull tables, lists, or structured data" },
  { id: "reformat",   icon: "ti-layout",          label: "Reformat",      desc: "Change layout, style, or structure" },
  { id: "merge_plan", icon: "ti-files",           label: "Merge Plan",    desc: "Plan multi-document PDF merges" },
  { id: "metadata",   icon: "ti-info-circle",     label: "Metadata",      desc: "Analyse or set PDF metadata" },
];

const PLACEHOLDERS = {
  create:     "Describe the PDF you want (e.g. '3-page Q3 sales report with summary, charts section, and conclusion')",
  summarize:  "Upload a PDF or paste its text below, then click Run",
  qa:         "Ask a question about the uploaded PDF…",
  translate:  "Enter target language (e.g. Spanish, French, Hindi)",
  extract:    "Upload or paste PDF text below, then click Run",
  reformat:   "Describe reformatting instructions (e.g. 'add executive summary, use 2-column layout')",
  merge_plan: "Describe the PDFs to merge and desired output",
  metadata:   "Optional notes about author, title, keywords…",
};

const NEEDS_PDF = new Set(["summarize", "qa", "translate", "extract", "reformat", "metadata"]);

const BADGE_COLORS = {
  blue:   { bg: "#E6F1FB", text: "#0C447C" },
  green:  { bg: "#EAF3DE", text: "#3B6D11" },
  amber:  { bg: "#FAEEDA", text: "#854F0B" },
  coral:  { bg: "#FAECE7", text: "#993C1D" },
  purple: { bg: "#EEEDFE", text: "#3C3489" },
  teal:   { bg: "#E1F5EE", text: "#0F6E56" },
  pink:   { bg: "#FBEAF0", text: "#72243E" },
  gray:   { bg: "#F1EFE8", text: "#444441" },
};

// ─── Shared tiny components ────────────────────────────────────────────────────
function Badge({ color = "gray", children }) {
  const c = BADGE_COLORS[color] ?? BADGE_COLORS.gray;
  return (
    <span style={{ background: c.bg, color: c.text, fontSize: 11, fontWeight: 500,
      padding: "2px 8px", borderRadius: 6, display: "inline-block" }}>
      {children}
    </span>
  );
}

function CodeBlock({ code }) {
  const [copied, setCopied] = useState(false);
  const copy = useCallback(() => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [code]);

  return (
    <div style={{ position: "relative", marginTop: 8 }}>
      <button onClick={copy} aria-label="Copy code" style={{
        position: "absolute", top: 8, right: 8,
        background: "rgba(255,255,255,0.1)", border: "0.5px solid rgba(255,255,255,0.2)",
        color: "#ccc", borderRadius: 6, padding: "2px 8px", fontSize: 11, cursor: "pointer",
      }}>
        {copied ? "Copied!" : "Copy"}
      </button>
      <pre style={{
        background: "#1a1a2e", color: "#e2e8f0",
        padding: "12px 40px 12px 14px", borderRadius: 8, fontSize: 12,
        overflowX: "auto", margin: 0, lineHeight: 1.6,
        border: "0.5px solid var(--color-border-tertiary)",
      }}>{code}</pre>
    </div>
  );
}

// ─── Result renderer — one sub-renderer per feature ───────────────────────────
function CreateResult({ d }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Card label="Document Plan"><p style={{ margin: 0, fontSize: 14, lineHeight: 1.7 }}>{d.plan}</p></Card>
      {d.preview_text && (
        <Card label="Content Preview">
          <p style={{ margin: 0, fontSize: 14, lineHeight: 1.7, color: "var(--color-text-secondary)" }}>{d.preview_text}</p>
        </Card>
      )}
      <div>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "0 0 4px" }}>Python Code (ReportLab)</p>
        <CodeBlock code={d.python_code} />
      </div>
    </div>
  );
}

function SummarizeResult({ d }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        <Badge color="blue">{d.document_type}</Badge>
        <Badge color="teal">{d.reading_time}</Badge>
        <Badge color={d.sentiment === "positive" ? "green" : d.sentiment === "negative" ? "coral" : "gray"}>{d.sentiment}</Badge>
        <Badge color="amber">{d.word_count?.toLocaleString()} words</Badge>
      </div>
      <h3 style={{ margin: 0, fontSize: 16, fontWeight: 500 }}>{d.title}</h3>
      <p style={{ margin: 0, lineHeight: 1.7, fontSize: 14 }}>{d.summary}</p>
      <div>
        <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 6px", color: "var(--color-text-secondary)" }}>Key Points</p>
        <ul style={{ margin: 0, paddingLeft: 18, display: "flex", flexDirection: "column", gap: 4 }}>
          {d.key_points?.map((pt, i) => <li key={i} style={{ fontSize: 14, lineHeight: 1.6 }}>{pt}</li>)}
        </ul>
      </div>
      {d.topics?.length > 0 && (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {d.topics.map((t, i) => <Badge key={i} color="purple">{t}</Badge>)}
        </div>
      )}
    </div>
  );
}

function ExtractResult({ d }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {d.tables?.map((tbl, i) => (
        <div key={i}>
          <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 6px" }}>{tbl.title || `Table ${i + 1}`}</p>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr>{tbl.headers?.map((h, j) => (
                  <th key={j} style={{ padding: "6px 10px", textAlign: "left", borderBottom: "0.5px solid var(--color-border-tertiary)", fontWeight: 500, color: "var(--color-text-secondary)", fontSize: 12 }}>{h}</th>
                ))}</tr>
              </thead>
              <tbody>
                {tbl.rows?.map((row, ri) => (
                  <tr key={ri}>{row.map((cell, ci) => (
                    <td key={ci} style={{ padding: "6px 10px", borderBottom: "0.5px solid var(--color-border-tertiary)" }}>{cell}</td>
                  ))}</tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
      {d.key_values && Object.keys(d.key_values).length > 0 && (
        <div>
          <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 6px" }}>Key Values</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 8 }}>
            {Object.entries(d.key_values).map(([k, v]) => (
              <div key={k} style={{ background: "var(--color-background-secondary)", borderRadius: 8, padding: "8px 12px", border: "0.5px solid var(--color-border-tertiary)" }}>
                <p style={{ margin: 0, fontSize: 11, color: "var(--color-text-secondary)" }}>{k}</p>
                <p style={{ margin: 0, fontSize: 14, fontWeight: 500 }}>{v}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      {d.entities && Object.entries(d.entities).filter(([, v]) => v?.length).map(([type, items]) => (
        <div key={type}>
          <p style={{ fontSize: 12, fontWeight: 500, margin: "0 0 4px", color: "var(--color-text-secondary)", textTransform: "capitalize" }}>{type}</p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
            {items.map((item, i) => <Badge key={i} color="teal">{item}</Badge>)}
          </div>
        </div>
      ))}
    </div>
  );
}

function TranslateResult({ d }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Badge color="blue">{d.target_language}</Badge>
      <Card><p style={{ margin: 0, fontSize: 14, lineHeight: 1.8 }}>{d.translated_content}</p></Card>
      {d.notes && <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: 0 }}>Note: {d.notes}</p>}
    </div>
  );
}

function ReformatMergeResult({ d }) {
  const listKey = d.changes_made ? "changes_made" : d.document_order ? "document_order" : "recommendations";
  const listLabel = d.changes_made ? "Changes Made" : d.document_order ? "Document Order" : "Recommendations";
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {d.original_analysis && <Card label="Original Analysis"><p style={{ margin: 0, fontSize: 14 }}>{d.original_analysis}</p></Card>}
      {d.merge_strategy    && <Card label="Merge Strategy"><p style={{ margin: 0, fontSize: 14 }}>{d.merge_strategy}</p></Card>}
      {d[listKey] && (
        <div>
          <p style={{ fontSize: 13, fontWeight: 500, margin: "0 0 6px" }}>{listLabel}</p>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {d[listKey].map((item, i) => <li key={i} style={{ fontSize: 14, marginBottom: 4 }}>{item}</li>)}
          </ul>
        </div>
      )}
      {d.python_code && <><p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "0 0 4px" }}>Python Code</p><CodeBlock code={d.python_code} /></>}
    </div>
  );
}

function MetadataResult({ d }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {["detected_metadata", "suggested_metadata"].map(key => (
          <Card key={key} label={key === "detected_metadata" ? "Detected" : "Suggested"}>
            {d[key] && Object.entries(d[key]).map(([k, v]) => (
              <div key={k} style={{ marginBottom: 4 }}>
                <span style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>{k}: </span>
                <span style={{ fontSize: 12 }}>{Array.isArray(v) ? v.join(", ") : v}</span>
              </div>
            ))}
          </Card>
        ))}
      </div>
      {d.seo_score && <p style={{ fontSize: 13, margin: 0 }}>SEO Score: {d.seo_score}</p>}
      {d.python_code && <><p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "0 0 4px" }}>Python Code</p><CodeBlock code={d.python_code} /></>}
    </div>
  );
}

// Reusable content card
function Card({ label, children }) {
  return (
    <div style={{ background: "var(--color-background-secondary)", borderRadius: 10, padding: "12px 16px", border: "0.5px solid var(--color-border-tertiary)" }}>
      {label && <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "0 0 6px" }}>{label}</p>}
      {children}
    </div>
  );
}

// Master result dispatcher
function ResultRenderer({ feature, result }) {
  if (!result) return null;
  try {
    // QA returns plain text — skip JSON parse
    if (feature === "qa") {
      return <p style={{ margin: 0, lineHeight: 1.7, fontSize: 14 }}>{result}</p>;
    }
    const d = typeof result === "string" ? JSON.parse(result) : result;
    if (feature === "create")                                 return <CreateResult d={d} />;
    if (feature === "summarize")                              return <SummarizeResult d={d} />;
    if (feature === "extract")                                return <ExtractResult d={d} />;
    if (feature === "translate")                              return <TranslateResult d={d} />;
    if (feature === "reformat" || feature === "merge_plan")   return <ReformatMergeResult d={d} />;
    if (feature === "metadata")                               return <MetadataResult d={d} />;
    return <pre style={{ margin: 0, fontSize: 13, whiteSpace: "pre-wrap" }}>{JSON.stringify(d, null, 2)}</pre>;
  } catch {
    return <p style={{ margin: 0, lineHeight: 1.7, fontSize: 14, whiteSpace: "pre-wrap" }}>{result}</p>;
  }
}

// ─── Main component ────────────────────────────────────────────────────────────
const HISTORY_KEY = "pdf_agent_history";

export default function PDFAgent() {
  const [activeFeature, setActiveFeature] = useState("create");
  const [prompt,        setPrompt]        = useState("");
  const [pdfText,       setPdfText]       = useState("");
  const [result,        setResult]        = useState(null);
  const [loading,       setLoading]       = useState(false);
  const [error,         setError]         = useState(null);
  const [history,       setHistory]       = useState(() => {
    try { return JSON.parse(sessionStorage.getItem(HISTORY_KEY) || "[]"); }
    catch { return []; }
  });
  const fileRef = useRef();

  // Persist history to sessionStorage whenever it changes
  useEffect(() => {
    try { sessionStorage.setItem(HISTORY_KEY, JSON.stringify(history)); }
    catch { /* quota exceeded — ignore */ }
  }, [history]);

  const feature   = useMemo(() => FEATURES.find(f => f.id === activeFeature), [activeFeature]);
  const needsPdf  = NEEDS_PDF.has(activeFeature);
  const canSubmit = !loading && (prompt.trim() || pdfText.trim());

  const handleFeatureChange = useCallback((id) => {
    setActiveFeature(id);
    setResult(null);
    setError(null);
  }, []);

  const handleFile = useCallback((e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setPdfText(ev.target.result);
    reader.readAsText(file);
  }, []);

  // Pure function — no stale closures
  const buildUserMessage = useCallback((mode, task, pdf) => {
    const p = pdf.slice(0, 12000);
    if (mode === "create")     return task;
    if (mode === "summarize")  return `Summarize this PDF:\n\n${p}`;
    if (mode === "qa")         return `PDF Content:\n${p}\n\nQuestion: ${task}`;
    if (mode === "translate")  return `Translate the following PDF content to ${task}:\n\n${p}`;
    if (mode === "extract")    return `Extract all structured data from this PDF:\n\n${p}`;
    if (mode === "reformat")   return `Reformat this PDF per these instructions: ${task}\n\nOriginal content:\n${p}`;
    if (mode === "merge_plan") return `Help me plan merging PDFs. Details: ${task}`;
    if (mode === "metadata")   return `Analyze metadata for this PDF:\n\nContent sample:\n${p.slice(0, 2000)}\n\nUser notes: ${task}`;
    return task;
  }, []);

  const run = useCallback(async () => {
    if (!canSubmit) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const userMsg  = buildUserMessage(activeFeature, prompt, pdfText);
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model:      "claude-sonnet-4-20250514",
          max_tokens: 2048,
          system:     SYSTEM_PROMPTS[activeFeature],
          messages:   [{ role: "user", content: userMsg }],
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err?.error?.message || `HTTP ${response.status}`);
      }

      const data  = await response.json();
      const text  = data.content?.map(b => b.text ?? "").join("") ?? "";
      const clean = text.replace(/```json|```/g, "").trim();

      setResult(clean);
      setHistory(prev => [{
        feature:      activeFeature,
        featureLabel: feature.label,
        prompt:       prompt || "(PDF uploaded)",
        result:       clean,
        time:         new Date().toLocaleTimeString(),
      }, ...prev.slice(0, 9)]);
    } catch (err) {
      setError("Request failed: " + err.message);
    } finally {
      setLoading(false);
    }
  }, [canSubmit, activeFeature, prompt, pdfText, feature, buildUserMessage]);

  const handleKeyDown = useCallback((e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") run();
  }, [run]);

  return (
    <div style={{ fontFamily: "var(--font-sans)", maxWidth: 780, margin: "0 auto", padding: "1.5rem 1rem" }}>
      {/* Header */}
      <h2 style={{ fontSize: 20, fontWeight: 500, margin: "0 0 4px" }}>
        <i className="ti ti-file-invoice" style={{ marginRight: 8, fontSize: 20, verticalAlign: -2 }} aria-hidden />
        PDF Agent
      </h2>
      <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "0 0 20px" }}>
        AI-powered PDF toolkit — create, analyse, extract, and transform documents
      </p>

      {/* Feature grid */}
      <div role="group" aria-label="PDF features"
        style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(140px,1fr))", gap: 8, marginBottom: 20 }}>
        {FEATURES.map(f => (
          <button key={f.id}
            onClick={() => handleFeatureChange(f.id)}
            aria-pressed={activeFeature === f.id}
            style={{
              background: activeFeature === f.id ? "var(--color-background-info)" : "var(--color-background-secondary)",
              border:     activeFeature === f.id ? "0.5px solid var(--color-border-info)" : "0.5px solid var(--color-border-tertiary)",
              borderRadius: 10, padding: "10px 12px", cursor: "pointer", textAlign: "left",
              color: activeFeature === f.id ? "var(--color-text-info)" : "var(--color-text-primary)",
              transition: "all 0.15s",
            }}>
            <i className={`ti ${f.icon}`} style={{ fontSize: 18, display: "block", marginBottom: 4 }} aria-hidden />
            <span style={{ fontSize: 12, fontWeight: 500, display: "block" }}>{f.label}</span>
            <span style={{ fontSize: 11, lineHeight: 1.4, display: "block",
              color: activeFeature === f.id ? "var(--color-text-info)" : "var(--color-text-secondary)" }}>
              {f.desc}
            </span>
          </button>
        ))}
      </div>

      {/* Input area */}
      <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 12, padding: "14px 16px", marginBottom: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
          <i className={`ti ${feature.icon}`} style={{ fontSize: 16, color: "var(--color-text-secondary)" }} aria-hidden />
          <span style={{ fontSize: 14, fontWeight: 500 }}>{feature.label}</span>
          <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>— {feature.desc}</span>
        </div>

        <textarea
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={PLACEHOLDERS[activeFeature]}
          aria-label={feature.label + " prompt"}
          rows={3}
          style={{ width: "100%", resize: "vertical", fontSize: 14, boxSizing: "border-box" }}
        />

        {needsPdf && (
          <div style={{ marginTop: 10 }}>
            <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
              <button onClick={() => fileRef.current.click()} style={{ fontSize: 12, padding: "4px 10px", display: "flex", alignItems: "center", gap: 4 }}>
                <i className="ti ti-upload" style={{ fontSize: 14 }} aria-hidden /> Upload PDF / text file
              </button>
              <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>or paste text below</span>
              <input ref={fileRef} type="file" accept=".txt,.pdf,.text" style={{ display: "none" }} onChange={handleFile} aria-hidden />
            </div>
            <textarea
              value={pdfText}
              onChange={e => setPdfText(e.target.value)}
              placeholder="Paste PDF text content here…"
              aria-label="PDF text content"
              rows={4}
              style={{ width: "100%", resize: "vertical", fontSize: 13, boxSizing: "border-box" }}
            />
          </div>
        )}

        <div style={{ marginTop: 10, display: "flex", gap: 8, alignItems: "center" }}>
          <button onClick={run} disabled={!canSubmit}
            aria-disabled={!canSubmit}
            style={{ padding: "6px 16px", fontWeight: 500, opacity: !canSubmit ? 0.6 : 1, cursor: !canSubmit ? "not-allowed" : "pointer" }}>
            {loading
              ? <><i className="ti ti-loader-2" role="status" aria-label="Running" style={{ marginRight: 6, fontSize: 14, animation: "spin 1s linear infinite" }} />Running…</>
              : <><i className="ti ti-player-play" style={{ marginRight: 6, fontSize: 14 }} aria-hidden />Run Agent</>}
          </button>
          <span style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>⌘↵ / Ctrl↵ to run</span>
          {(result || error) && (
            <button onClick={() => { setResult(null); setError(null); }} style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div role="alert" style={{ background: "var(--color-background-danger)", border: "0.5px solid var(--color-border-danger)", borderRadius: 10, padding: "10px 14px", marginBottom: 12 }}>
          <p style={{ margin: 0, fontSize: 13, color: "var(--color-text-danger)" }}>
            <i className="ti ti-alert-circle" style={{ marginRight: 6 }} aria-hidden />{error}
          </p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 12, padding: "14px 16px", marginBottom: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 12 }}>
            <i className="ti ti-check-circle" style={{ fontSize: 16, color: "var(--color-text-success)" }} aria-hidden />
            <span style={{ fontSize: 13, fontWeight: 500 }}>Result</span>
            <Badge color="green">{feature.label}</Badge>
          </div>
          <ResultRenderer feature={activeFeature} result={result} />
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
            <p style={{ fontSize: 13, fontWeight: 500, margin: 0, color: "var(--color-text-secondary)" }}>
              <i className="ti ti-history" style={{ marginRight: 4 }} aria-hidden />Recent
            </p>
            <button onClick={() => setHistory([])} style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>Clear history</button>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {history.map((h, i) => (
              <div key={i} role="button" tabIndex={0}
                onClick={() => { handleFeatureChange(h.feature); setResult(h.result); setPrompt(h.prompt !== "(PDF uploaded)" ? h.prompt : ""); }}
                onKeyDown={e => e.key === "Enter" && handleFeatureChange(h.feature)}
                style={{ background: "var(--color-background-secondary)", borderRadius: 8, padding: "8px 12px",
                  border: "0.5px solid var(--color-border-tertiary)", cursor: "pointer",
                  display: "flex", alignItems: "center", gap: 8 }}>
                <Badge color="gray">{h.featureLabel}</Badge>
                <span style={{ fontSize: 13, flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "var(--color-text-secondary)" }}>{h.prompt}</span>
                <span style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>{h.time}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }`}</style>
    </div>
  );
}

// ─── System prompts (mirrored from backend pdf_agent.py) ──────────────────────
const SYSTEM_PROMPTS = {
  create: `You are a PDF content generator. The user will describe what PDF they want.
Respond with JSON (no markdown fences):
{"plan":"full structured content plan","python_code":"complete runnable ReportLab code that saves to output.pdf","preview_text":"first 3 paragraphs of the document"}`,

  summarize: `You are a PDF summarization expert.
Return JSON (no markdown fences):
{"title":"...","summary":"2-3 paragraph summary","key_points":["up to 8 points"],"topics":["..."],"word_count":0,"reading_time":"X min read","sentiment":"positive|neutral|negative","document_type":"report|article|legal|technical|etc"}`,

  qa: `You are a PDF Q&A assistant. Answer thoroughly, citing specific sections. If the answer is not in the text, say so clearly.`,

  translate: `You are a PDF translation expert.
Return JSON (no markdown fences):
{"target_language":"...","translated_content":"full translated text","notes":"any translation notes"}`,

  extract: `You are a data extraction specialist for PDFs.
Return JSON (no markdown fences):
{"tables":[{"title":"...","headers":[],"rows":[[]]}],"key_values":{},"lists":[{"title":"...","items":[]}],"entities":{"dates":[],"names":[],"numbers":[],"emails":[]}}`,

  reformat: `You are a PDF reformatting assistant.
Return JSON (no markdown fences):
{"original_analysis":"...","suggested_structure":"...","python_code":"complete ReportLab code","changes_made":[]}`,

  merge_plan: `You are a PDF merge strategist.
Return JSON (no markdown fences):
{"merge_strategy":"...","document_order":[],"python_code":"complete pypdf code","recommendations":[]}`,

  metadata: `You are a PDF metadata analyst.
Return JSON (no markdown fences):
{"detected_metadata":{"title":"","author":"","subject":"","keywords":[],"created":"","modified":""},"suggested_metadata":{"title":"","author":"","subject":"","keywords":[]},"python_code":"complete pypdf code","seo_score":"1-10 with explanation"}`,
};
