/**
 * EmailAgent.jsx
 * Production-grade Email Agent UI — 38 modes across 11 categories.
 * React + Tailwind CSS. Communicates with /api/email.
 */

import React, { useState, useRef, useEffect, useCallback } from "react";

const API_BASE = "/api/email";

// ── Categories & Features ─────────────────────────────────────────────────────
const CATEGORIES = [
  {
    id: "core", label: "📧 Core Ops", color: "blue",
    features: [
      { id: "compose",   label: "Compose",       icon: "✍️",  desc: "Write a new email from a prompt",              needsContext: false },
      { id: "reply",     label: "Reply",         icon: "↩️",  desc: "Reply to an email (paste original below)",    needsOriginal: true },
      { id: "forward",   label: "Forward",       icon: "↗️",  desc: "Forward an email with an intro note",         needsOriginal: true },
    ]
  },
  {
    id: "ai", label: "🤖 AI Writing", color: "purple",
    features: [
      { id: "rewrite_tone",    label: "Rewrite Tone",     icon: "🎭", desc: "Rewrite for formal/casual/assertive/friendly", needsOriginal: true },
      { id: "resize",          label: "Shorten / Expand", icon: "↕️", desc: "Make the email shorter or longer",             needsOriginal: true },
      { id: "fix_grammar",     label: "Fix Grammar",      icon: "✅", desc: "Correct grammar, spelling, punctuation",       needsOriginal: true },
      { id: "improve_clarity", label: "Improve Clarity",  icon: "💡", desc: "Improve clarity, structure, and flow",         needsOriginal: true },
      { id: "translate",       label: "Translate",        icon: "🌍", desc: "Translate email to any language",               needsOriginal: true },
      { id: "suggest_subject", label: "Subject Lines",    icon: "📌", desc: "Get 5 subject line suggestions",               needsOriginal: true },
      { id: "from_bullets",    label: "From Bullets",     icon: "📝", desc: "Turn bullet points into a full email",          needsContext: false },
      { id: "match_style",     label: "Match Style",      icon: "🪞", desc: "Rewrite to match recipient's writing style",   needsOriginal: true },
    ]
  },
  {
    id: "inbox", label: "📥 Inbox", color: "green",
    features: [
      { id: "read",   label: "Read Inbox", icon: "📬", desc: "Fetch emails from your inbox",                needsContext: false },
      { id: "search", label: "Search",     icon: "🔍", desc: "Search by sender, subject, keyword, date",   needsContext: false },
      { id: "digest", label: "Digest",     icon: "📰", desc: "Get a summarized digest of your recent mail", needsContext: false },
    ]
  },
  {
    id: "analysis", label: "🔬 Analysis", color: "indigo",
    features: [
      { id: "summarize",        label: "Summarize",        icon: "📋", desc: "Summarize email + action items + priority",    needsOriginal: true },
      { id: "summarize_thread", label: "Thread Summary",   icon: "🧵", desc: "Summarize a full email thread",                needsOriginal: true },
      { id: "extract_actions",  label: "Action Items",     icon: "✅", desc: "Extract tasks, deadlines, commitments",        needsOriginal: true },
      { id: "extract_entities", label: "Extract Entities", icon: "🏷️", desc: "Names, emails, phones, dates, amounts",        needsOriginal: true },
      { id: "analyze",          label: "Analyze",          icon: "📊", desc: "Sentiment, intent, urgency, tone",             needsOriginal: true },
      { id: "classify",         label: "Classify",         icon: "🗂️", desc: "Category, type, priority, labels",             needsOriginal: true },
    ]
  },
  {
    id: "smart", label: "⚡ Smart", color: "orange",
    features: [
      { id: "smart_reply", label: "Smart Reply",   icon: "💬", desc: "3 one-click reply suggestions",               needsOriginal: true },
      { id: "auto_reply",  label: "Auto-Reply",    icon: "🤖", desc: "Generate out-of-office / auto-reply",         needsContext: false },
      { id: "follow_up",   label: "Follow-Up",     icon: "🔔", desc: "Write a follow-up if no reply in N days",     needsOriginal: true },
    ]
  },
  {
    id: "templates", label: "📄 Templates", color: "teal",
    features: [
      { id: "template",   label: "Create Template", icon: "📄", desc: "Create a reusable template with {{placeholders}}", needsContext: false },
      { id: "mail_merge", label: "Mail Merge",      icon: "📤", desc: "Personalized bulk email with CSV recipients",       needsContext: false },
      { id: "drip",       label: "Drip Campaign",   icon: "💧", desc: "Design a multi-step email sequence",                needsContext: false },
      { id: "ab_test",    label: "A/B Test",        icon: "🧪", desc: "Generate 3 subject line variants for testing",      needsOriginal: true },
    ]
  },
  {
    id: "scheduling", label: "⏰ Scheduling", color: "yellow",
    features: [
      { id: "schedule",  label: "Schedule Send", icon: "⏰", desc: "Schedule email for a specific time + get code", needsContext: false },
      { id: "best_time", label: "Best Time",     icon: "📅", desc: "Predict the best time to send",                needsContext: false },
    ]
  },
  {
    id: "security", label: "🔒 Security", color: "red",
    features: [
      { id: "security_check", label: "Security Check",  icon: "🛡️", desc: "Detect phishing, spam, suspicious links", needsOriginal: true },
      { id: "sensitive_data", label: "Sensitive Data",  icon: "🔍", desc: "Find SSNs, credit cards, PII in email",   needsOriginal: true },
      { id: "gdpr",           label: "GDPR Check",      icon: "🇪🇺", desc: "GDPR compliance analysis + score",        needsOriginal: true },
    ]
  },
  {
    id: "integrations", label: "🔌 Integrations", color: "violet",
    features: [
      { id: "crm_log",     label: "CRM Log",     icon: "💼", desc: "Extract Salesforce/HubSpot CRM data",          needsOriginal: true },
      { id: "meeting",     label: "Meeting",     icon: "📅", desc: "Detect meeting request + generate .ics",       needsOriginal: true },
      { id: "unsubscribe", label: "Unsubscribe", icon: "🚫", desc: "Find unsubscribe links + generate instructions", needsOriginal: true },
    ]
  },
  {
    id: "bulk", label: "📦 Bulk", color: "stone",
    features: [
      { id: "bulk", label: "Bulk Actions", icon: "📦", desc: "Generate code for bulk delete/archive/mark read", needsContext: false },
    ]
  },
  {
    id: "output", label: "📤 Output", color: "cyan",
    features: [
      { id: "export",    label: "Export Email", icon: "💾", desc: "Export as .eml, .txt, .html, .csv",          needsOriginal: true },
      { id: "signature", label: "Signature",    icon: "✍️", desc: "Generate professional email signature HTML", needsContext: false },
    ]
  },
];

const ALL_FEATURES = CATEGORIES.flatMap(c => c.features.map(f => ({ ...f, category: c.id })));

const COLOR_BTN = {
  blue:   "bg-blue-600 hover:bg-blue-700",
  purple: "bg-purple-600 hover:bg-purple-700",
  green:  "bg-green-600 hover:bg-green-700",
  indigo: "bg-indigo-600 hover:bg-indigo-700",
  orange: "bg-orange-500 hover:bg-orange-600",
  teal:   "bg-teal-600 hover:bg-teal-700",
  yellow: "bg-yellow-500 hover:bg-yellow-600",
  red:    "bg-red-600 hover:bg-red-700",
  violet: "bg-violet-600 hover:bg-violet-700",
  stone:  "bg-stone-600 hover:bg-stone-700",
  cyan:   "bg-cyan-600 hover:bg-cyan-700",
};

const COLOR_BADGE = {
  blue:   "bg-blue-50 text-blue-700 border-blue-200",
  purple: "bg-purple-50 text-purple-700 border-purple-200",
  green:  "bg-green-50 text-green-700 border-green-200",
  indigo: "bg-indigo-50 text-indigo-700 border-indigo-200",
  orange: "bg-orange-50 text-orange-700 border-orange-200",
  teal:   "bg-teal-50 text-teal-700 border-teal-200",
  yellow: "bg-yellow-50 text-yellow-700 border-yellow-200",
  red:    "bg-red-50 text-red-700 border-red-200",
  violet: "bg-violet-50 text-violet-700 border-violet-200",
  stone:  "bg-stone-50 text-stone-700 border-stone-200",
  cyan:   "bg-cyan-50 text-cyan-700 border-cyan-200",
};

const TASK_HINTS = {
  compose:          "Write a follow-up email to the investor about Series A progress...",
  reply:            "Politely decline the meeting request but propose next week...",
  forward:          "Forward to the team with context about what needs attention...",
  rewrite_tone:     "Rewrite in formal tone / make it more assertive / casual...",
  resize:           "Shorten this to 3 sentences / expand with more detail...",
  fix_grammar:      "Fix grammar and spelling in the email above...",
  improve_clarity:  "Improve the clarity and structure of this email...",
  translate:        "Translate to French / Spanish / German...",
  suggest_subject:  "Suggest 5 subject lines for this sales email...",
  from_bullets:     "- Follow up on last week's call\n- Share the updated proposal\n- Ask about timeline",
  match_style:      "Rewrite: 'Please send the report.' in the same style as the original...",
  read:             "Show last 10 emails / fetch from Sent / get 5 emails from Drafts",
  search:           "Search emails from john@company.com / subject 'invoice' / keyword 'urgent' since 2026-01-01",
  digest:           "Give me a daily digest of my inbox / weekly email summary",
  summarize:        "Summarize this email and list action items...",
  summarize_thread: "Summarize the full thread — who needs to do what...",
  extract_actions:  "Extract all tasks, deadlines, and follow-ups from this email...",
  extract_entities: "Extract all names, emails, and phone numbers...",
  analyze:          "Analyze the sentiment, tone, and intent of this email...",
  classify:         "Classify this email and assign priority labels...",
  smart_reply:      "Generate 3 quick reply options for this email...",
  auto_reply:       "Out of office from May 25 to June 1, contact sarah@company.com in urgent cases",
  follow_up:        "Write a follow-up email if no reply in 3 days...",
  template:         "Create a cold outreach template for SaaS sales...",
  mail_merge:       "Mail merge a welcome email for new customers with {{name}} and {{company}}",
  drip:             "Design a 4-email onboarding drip campaign for a SaaS product...",
  ab_test:          "Generate 3 A/B test subject lines for this product launch email...",
  schedule:         "Schedule this email for tomorrow at 9 AM IST...",
  best_time:        "When is the best time to send a B2B sales email?",
  security_check:   "Check if this email is phishing or spam...",
  sensitive_data:   "Scan this email for SSNs or credit card numbers...",
  gdpr:             "Check this marketing email for GDPR compliance...",
  crm_log:          "Extract CRM data for Salesforce from this email...",
  meeting:          "Detect meeting request and generate a .ics calendar invite...",
  unsubscribe:      "Find the unsubscribe link in this newsletter...",
  bulk:             "Generate code to bulk-archive all emails older than 30 days from newsletters@...",
  export:           "Export this email as .eml / .html / .csv",
  signature:        "Create a signature for Kunal Roy, Senior Engineer at Acme Corp, kunal@acme.com",
};

// ── Result Renderer ───────────────────────────────────────────────────────────
function ResultPanel({ result, feature }) {
  const [tab, setTab] = useState("pretty");
  const [copied, setCopied] = useState("");

  if (!result) return null;
  let parsed = null;
  try { parsed = JSON.parse(result); } catch {}

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(""), 2000);
  };

  const downloadText = (text, filename, type = "text/plain") => {
    const blob = new Blob([text], { type });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
  };

  const hasBody     = parsed?.body || parsed?.rewritten || parsed?.corrected || parsed?.improved || parsed?.result;
  const hasCode     = parsed?.python_code;
  const hasHtml     = parsed?.body_html || parsed?.signature_html;
  const hasEmails   = parsed?.emails?.length;
  const hasReplies  = parsed?.replies?.length;
  const hasSequence = parsed?.sequence?.length;

  return (
    <div className="mt-5 bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
        <div className="flex gap-2">
          {["pretty","raw"].map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-all
                ${tab===t ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-200"}`}>
              {t === "pretty" ? "📊 Results" : "{ } JSON"}
            </button>
          ))}
        </div>
        <div className="flex gap-2 flex-wrap">
          {hasBody && (
            <button onClick={() => copyToClipboard(hasBody, "body")}
              className="px-3 py-1 bg-gray-600 text-white rounded-lg text-xs hover:bg-gray-700">
              {copied === "body" ? "✅ Copied" : "📋 Copy Body"}
            </button>
          )}
          {hasCode && (
            <button onClick={() => downloadText(hasCode, "email_code.py", "text/x-python")}
              className="px-3 py-1 bg-purple-600 text-white rounded-lg text-xs hover:bg-purple-700">
              ⬇️ Download Code
            </button>
          )}
          {hasHtml && (
            <button onClick={() => downloadText(parsed.body_html || parsed.signature_html, "email.html", "text/html")}
              className="px-3 py-1 bg-teal-600 text-white rounded-lg text-xs hover:bg-teal-700">
              ⬇️ HTML
            </button>
          )}
          {parsed?.content && (
            <button onClick={() => downloadText(parsed.content, parsed.filename || "email_export.txt")}
              className="px-3 py-1 bg-orange-600 text-white rounded-lg text-xs hover:bg-orange-700">
              ⬇️ {parsed.filename || "Export"}
            </button>
          )}
        </div>
      </div>

      <div className="p-4 max-h-[700px] overflow-y-auto">
        {tab === "raw" ? (
          <pre className="text-xs bg-gray-950 text-green-300 p-4 rounded-xl overflow-x-auto whitespace-pre-wrap">
            {result}
          </pre>
        ) : !parsed ? (
          <pre className="text-sm whitespace-pre-wrap text-gray-700">{result}</pre>
        ) : parsed.error ? (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <div className="font-bold text-red-700 mb-1">❌ Error</div>
            <div className="text-sm text-red-600">{parsed.error}</div>
            {parsed.traceback && <pre className="mt-2 text-xs text-red-400 whitespace-pre-wrap">{parsed.traceback}</pre>}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Email body section */}
            {(parsed.body || parsed.rewritten || parsed.corrected || parsed.improved || parsed.result) && (
              <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-xs font-semibold text-blue-500 uppercase tracking-wider">
                    {parsed.subject ? `📌 ${parsed.subject}` : "📧 Email Body"}
                  </div>
                  <button onClick={() => copyToClipboard(parsed.body || parsed.rewritten || parsed.corrected || parsed.improved || parsed.result, "body")}
                    className="text-xs text-blue-400 hover:text-blue-600">
                    {copied === "body" ? "✅" : "📋 Copy"}
                  </button>
                </div>
                {parsed.subject && <div className="font-bold text-gray-800 mb-2">{parsed.subject}</div>}
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
                  {parsed.body || parsed.rewritten || parsed.corrected || parsed.improved || parsed.result}
                </pre>
              </div>
            )}

            {/* Email list (inbox/search) */}
            {hasEmails && (
              <div>
                <div className="text-sm font-semibold text-gray-600 mb-2">{parsed.count || parsed.emails.length} emails</div>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {parsed.emails.map((e, i) => (
                    e.error ? (
                      <div key={i} className="p-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">{e.error}</div>
                    ) : (
                      <div key={i} className="p-3 bg-gray-50 border border-gray-100 rounded-xl hover:bg-blue-50 transition-colors">
                        <div className="flex items-start justify-between gap-2">
                          <div className="font-medium text-gray-800 text-sm truncate flex-1">{e.subject || "(no subject)"}</div>
                          <div className="text-xs text-gray-400 shrink-0">{e.date?.slice(0,16) || ""}</div>
                        </div>
                        <div className="text-xs text-gray-500 mt-0.5">{e.from}</div>
                        <div className="text-xs text-gray-400 mt-1 line-clamp-2">{e.body?.slice(0,120)}</div>
                        {e.attachments?.length > 0 && (
                          <div className="text-xs text-orange-500 mt-1">📎 {e.attachments.length} attachment(s)</div>
                        )}
                      </div>
                    )
                  ))}
                </div>
              </div>
            )}

            {/* Smart replies */}
            {hasReplies && (
              <div>
                <div className="text-sm font-semibold text-gray-600 mb-2">💬 Quick Reply Options</div>
                <div className="space-y-2">
                  {parsed.replies.map((r, i) => (
                    <div key={i} className="p-3 bg-gray-50 border border-gray-100 rounded-xl">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-semibold text-blue-600">{r.label}</span>
                        <button onClick={() => copyToClipboard(r.body, `reply_${i}`)}
                          className="text-xs text-gray-400 hover:text-gray-600">
                          {copied === `reply_${i}` ? "✅" : "📋"}
                        </button>
                      </div>
                      <div className="text-sm text-gray-700">{r.body}</div>
                      <div className="text-xs text-gray-400 mt-1">Tone: {r.tone}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Subject suggestions */}
            {parsed.suggestions?.length && (
              <div>
                <div className="text-sm font-semibold text-gray-600 mb-2">📌 Subject Line Suggestions</div>
                <div className="space-y-2">
                  {parsed.suggestions.map((s, i) => (
                    <div key={i} className="p-3 bg-gray-50 border border-gray-100 rounded-xl flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium text-gray-800">{s.subject}</div>
                        <div className="text-xs text-gray-400">{s.style} · {s.open_rate_prediction} open rate</div>
                      </div>
                      <button onClick={() => copyToClipboard(s.subject, `subj_${i}`)}
                        className="text-xs text-blue-400 hover:text-blue-600 ml-2">
                        {copied === `subj_${i}` ? "✅" : "📋"}
                      </button>
                    </div>
                  ))}
                  {parsed.recommended && (
                    <div className="px-3 py-2 bg-green-50 border border-green-100 rounded-xl text-sm text-green-700">
                      ✅ Recommended: <strong>{parsed.recommended}</strong>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Drip sequence */}
            {hasSequence && (
              <div>
                <div className="text-sm font-semibold text-gray-600 mb-2">💧 Drip Sequence — {parsed.campaign_name}</div>
                <div className="space-y-2">
                  {parsed.sequence.map((s, i) => (
                    <div key={i} className="p-3 bg-blue-50 border border-blue-100 rounded-xl">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="bg-blue-600 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center font-bold">
                          {i+1}
                        </span>
                        <span className="text-xs font-semibold text-blue-700">Day {s.day}</span>
                        <span className="text-xs text-gray-500">{s.goal}</span>
                      </div>
                      <div className="text-sm font-medium text-gray-800">{s.subject}</div>
                      <div className="text-xs text-gray-500 mt-1 line-clamp-2">{s.body}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action items */}
            {parsed.action_items?.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-100 rounded-xl p-4">
                <div className="text-xs font-semibold text-yellow-600 uppercase mb-2">✅ Action Items</div>
                {parsed.action_items.map((a, i) => (
                  <div key={i} className="text-sm text-gray-700 py-1 border-b border-yellow-100 last:border-0">
                    {typeof a === "object"
                      ? `• [${a.priority || "—"}] ${a.task} ${a.owner ? `— ${a.owner}` : ""} ${a.due_date ? `(due: ${a.due_date})` : ""}`
                      : `• ${a}`}
                  </div>
                ))}
              </div>
            )}

            {/* Security verdict */}
            {parsed.verdict && (
              <div className={`rounded-xl p-4 border ${
                parsed.verdict === "safe" ? "bg-green-50 border-green-200" :
                parsed.verdict === "suspicious" ? "bg-yellow-50 border-yellow-200" :
                "bg-red-50 border-red-200"
              }`}>
                <div className="font-bold text-lg">
                  {parsed.verdict === "safe" ? "✅ Safe" : parsed.verdict === "suspicious" ? "⚠️ Suspicious" : "🚨 Dangerous"}
                </div>
                <div className="text-sm mt-1">{parsed.recommendation}</div>
                {parsed.red_flags?.length > 0 && (
                  <ul className="mt-2 text-sm space-y-0.5">
                    {parsed.red_flags.map((f, i) => <li key={i} className="text-red-600">• {f}</li>)}
                  </ul>
                )}
              </div>
            )}

            {/* Generic key-value grid */}
            {(() => {
              const skip = new Set(["body","body_html","subject","rewritten","corrected","improved","result","python_code",
                "emails","replies","suggestions","sequence","action_items","verdict","recommendation","red_flags","content",
                "signature_html","translated_body","translated_subject","error","traceback","follow_up_date"]);
              const kvPairs = Object.entries(parsed).filter(([k,v]) => !skip.has(k) && v !== null && v !== "" && v !== undefined);
              if (!kvPairs.length) return null;
              return (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {kvPairs.map(([k, v]) => (
                    <div key={k} className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">{k.replace(/_/g," ")}</div>
                      {Array.isArray(v) ? (
                        <ul className="text-sm text-gray-700 space-y-0.5">
                          {v.slice(0,8).map((item,i) => (
                            <li key={i}>• {typeof item === "object" ? JSON.stringify(item) : String(item)}</li>
                          ))}
                          {v.length > 8 && <li className="text-gray-400 text-xs">+{v.length-8} more</li>}
                        </ul>
                      ) : typeof v === "object" ? (
                        <div className="text-sm text-gray-700">
                          {Object.entries(v).slice(0,6).map(([sk,sv]) => (
                            <div key={sk}><span className="font-medium">{sk}:</span> {Array.isArray(sv) ? sv.join(", ") : String(sv)}</div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-sm text-gray-700 break-words">{String(v)}</div>
                      )}
                    </div>
                  ))}
                </div>
              );
            })()}

            {/* HTML signature preview */}
            {(parsed.signature_html || parsed.body_html) && (
              <details className="border rounded-xl overflow-hidden">
                <summary className="px-4 py-2 bg-gray-50 cursor-pointer text-sm font-medium text-gray-600">
                  🌐 HTML Preview
                </summary>
                <div className="p-3 border-t">
                  <iframe srcDoc={parsed.signature_html || parsed.body_html}
                    className="w-full min-h-32 max-h-64" title="HTML Preview" sandbox="allow-same-origin" />
                </div>
              </details>
            )}

            {/* Code block */}
            {hasCode && (
              <div className="bg-gray-950 rounded-xl overflow-hidden">
                <div className="flex items-center justify-between px-3 py-2 bg-gray-800">
                  <span className="text-xs text-gray-400">🐍 Python Code</span>
                  <button className="text-xs text-blue-400 hover:text-blue-300"
                    onClick={() => copyToClipboard(parsed.python_code, "code")}>
                    {copied === "code" ? "✅ Copied" : "📋 Copy"}
                  </button>
                </div>
                <pre className="p-4 text-green-300 text-xs overflow-x-auto whitespace-pre-wrap max-h-80">
                  {parsed.python_code}
                </pre>
              </div>
            )}

            {/* Send result */}
            {parsed.send_result && (
              <div className={`rounded-xl p-3 border text-sm font-medium ${
                parsed.send_result.sent ? "bg-green-50 border-green-200 text-green-700" :
                parsed.send_result.mock ? "bg-blue-50 border-blue-200 text-blue-700" :
                "bg-red-50 border-red-200 text-red-700"
              }`}>
                {parsed.send_result.sent ? "✅ Email sent!" :
                 parsed.send_result.mock ? `📝 Mock mode — ${parsed.send_result.note}` :
                 `❌ Send failed: ${parsed.send_result.error}`}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function EmailAgent() {
  const [activeCategory, setActiveCategory] = useState("core");
  const [activeFeature, setActiveFeature]   = useState("compose");
  const [task, setTask]                     = useState("");
  const [originalEmail, setOriginalEmail]   = useState("");
  const [toAddr, setToAddr]                 = useState("");
  const [ccAddr, setCcAddr]                 = useState("");
  const [tone, setTone]                     = useState("formal");
  const [autoSend, setAutoSend]             = useState(false);
  const [loading, setLoading]               = useState(false);
  const [result, setResult]                 = useState(null);
  const [searchQuery, setSearchQuery]       = useState("");
  const [history, setHistory]               = useState(() => {
    try { return JSON.parse(sessionStorage.getItem("email_history") || "[]"); } catch { return []; }
  });

  const currentFeature  = ALL_FEATURES.find(f => f.id === activeFeature);
  const currentCategory = CATEGORIES.find(c => c.id === (currentFeature?.category || activeCategory));

  useEffect(() => {
    sessionStorage.setItem("email_history", JSON.stringify(history.slice(0,20)));
  }, [history]);

  const filteredFeatures = searchQuery
    ? ALL_FEATURES.filter(f =>
        f.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.desc.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : null;

  function selectFeature(fid) {
    setActiveFeature(fid);
    setResult(null);
    const feat = ALL_FEATURES.find(f => f.id === fid);
    if (feat) setActiveCategory(feat.category);
    setSearchQuery("");
  }

  async function handleRun() {
    if (!task.trim() && !originalEmail.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const emailContext = {
        original_email: originalEmail,
        to:             toAddr,
        cc:             ccAddr,
        tone:           tone,
        auto_send:      autoSend,
      };
      const res = await fetch(API_BASE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task, email_mode: activeFeature, email_context: emailContext }),
      });
      const data = await res.json();
      const resultStr = data.result || JSON.stringify(data);
      setResult(resultStr);
      setHistory(h => [{
        id: Date.now(), feature: activeFeature,
        task: task.slice(0,60), timestamp: new Date().toLocaleTimeString(),
      }, ...h].slice(0,20));
    } catch (err) {
      setResult(JSON.stringify({ error: err.message }));
    } finally {
      setLoading(false);
    }
  }

  const catColor = currentCategory?.color || "blue";
  const runBtnColor = COLOR_BTN[catColor] || "bg-blue-600 hover:bg-blue-700";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50 font-sans">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center text-white text-lg shadow">
              📧
            </div>
            <div>
              <div className="font-bold text-gray-900 text-lg leading-none">Email Agent</div>
              <div className="text-xs text-gray-400">38 features · AI-powered · SMTP/IMAP ready</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <input type="text" placeholder="Search features..." value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 border border-gray-200 rounded-xl text-sm w-48 focus:outline-none focus:ring-2 focus:ring-blue-300" />
              <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs">🔍</span>
            </div>
            <span className="text-xs text-gray-400 hidden md:block">{ALL_FEATURES.length} features</span>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6 flex gap-6">
        {/* Sidebar */}
        <div className="w-64 shrink-0 space-y-2">
          {searchQuery && filteredFeatures ? (
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-4 py-2 bg-gray-50 border-b text-xs font-semibold text-gray-400 uppercase">{filteredFeatures.length} results</div>
              <div className="max-h-96 overflow-y-auto">
                {filteredFeatures.map(f => (
                  <button key={f.id} onClick={() => selectFeature(f.id)}
                    className={`w-full px-4 py-2.5 flex items-start gap-2 text-left hover:bg-blue-50 border-b border-gray-50 transition-colors ${activeFeature===f.id?"bg-blue-50":""}`}>
                    <span>{f.icon}</span>
                    <div>
                      <div className="text-sm font-medium text-gray-800">{f.label}</div>
                      <div className="text-xs text-gray-400">{f.desc}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            CATEGORIES.map(cat => (
              <div key={cat.id} className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                <button onClick={() => setActiveCategory(activeCategory===cat.id ? null : cat.id)}
                  className="w-full px-4 py-2.5 flex items-center justify-between text-sm font-semibold hover:bg-gray-50 transition-colors">
                  <span>{cat.label}</span>
                  <span className="text-gray-400 text-xs">{activeCategory===cat.id?"▲":"▼"}</span>
                </button>
                {activeCategory===cat.id && (
                  <div className="border-t border-gray-100">
                    {cat.features.map(f => (
                      <button key={f.id} onClick={() => selectFeature(f.id)}
                        className={`w-full px-4 py-2 flex items-center gap-2 text-sm text-left border-b border-gray-50 last:border-0 transition-colors
                          ${activeFeature===f.id ? "bg-blue-600 text-white" : "hover:bg-gray-50 text-gray-700"}`}>
                        <span>{f.icon}</span>
                        <span className="font-medium">{f.label}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}

          {history.length > 0 && (
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-4 py-2 bg-gray-50 border-b text-xs font-semibold text-gray-400 uppercase flex justify-between">
                <span>Recent</span>
                <button onClick={() => setHistory([])} className="text-red-400 hover:text-red-600">Clear</button>
              </div>
              <div className="max-h-48 overflow-y-auto">
                {history.slice(0,8).map(h => (
                  <button key={h.id} onClick={() => selectFeature(h.feature)}
                    className="w-full px-4 py-2 text-left text-xs text-gray-600 hover:bg-gray-50 border-b border-gray-50">
                    <div className="font-medium">{ALL_FEATURES.find(f=>f.id===h.feature)?.icon} {h.feature}</div>
                    <div className="text-gray-400 truncate">{h.task}</div>
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
              <div className="px-6 py-4 border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{currentFeature.icon}</span>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">{currentFeature.label}</h2>
                    <p className="text-sm text-gray-500">{currentFeature.desc}</p>
                  </div>
                  {currentCategory && (
                    <span className={`ml-auto px-3 py-1 rounded-full text-xs font-medium border ${COLOR_BADGE[catColor]||COLOR_BADGE.blue}`}>
                      {currentCategory.label}
                    </span>
                  )}
                </div>
              </div>

              <div className="p-6 space-y-4">
                {/* Recipient fields — shown for compose/reply/forward */}
                {["compose","reply","forward","send"].includes(activeFeature) && (
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">To</label>
                      <input type="email" value={toAddr} onChange={e=>setToAddr(e.target.value)}
                        placeholder="recipient@email.com"
                        className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300" />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">CC</label>
                      <input type="email" value={ccAddr} onChange={e=>setCcAddr(e.target.value)}
                        placeholder="cc@email.com"
                        className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300" />
                    </div>
                  </div>
                )}

                {/* Tone selector */}
                {["compose","reply","rewrite_tone","from_bullets"].includes(activeFeature) && (
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Tone</label>
                    <div className="flex gap-2 flex-wrap">
                      {["formal","casual","friendly","assertive","empathetic","concise"].map(t => (
                        <button key={t} onClick={()=>setTone(t)}
                          className={`px-3 py-1 rounded-full text-xs font-medium border transition-all
                            ${tone===t ? "bg-blue-600 text-white border-blue-600" : "bg-gray-50 text-gray-600 border-gray-200 hover:border-blue-300"}`}>
                          {t}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Task input */}
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">
                    {activeFeature === "from_bullets" ? "Bullet Points" : "Task / Instructions"}
                  </label>
                  <textarea rows={4} value={task} onChange={e=>setTask(e.target.value)}
                    placeholder={TASK_HINTS[activeFeature] || "Describe what you want to do..."}
                    className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-300"
                    onKeyDown={e=>{if(e.key==="Enter"&&(e.ctrlKey||e.metaKey))handleRun()}} />
                  <div className="text-xs text-gray-400 mt-1">Ctrl+Enter to run</div>
                </div>

                {/* Original email textarea */}
                {(currentFeature?.needsOriginal || originalEmail) && (
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">
                      Original Email (paste here)
                    </label>
                    <textarea rows={5} value={originalEmail} onChange={e=>setOriginalEmail(e.target.value)}
                      placeholder="Paste the original email content here..."
                      className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-gray-50"
                    />
                  </div>
                )}

                {/* Auto-send toggle */}
                {["compose","reply","forward"].includes(activeFeature) && toAddr && (
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={autoSend} onChange={e=>setAutoSend(e.target.checked)}
                      className="w-4 h-4 rounded accent-blue-600" />
                    <span className="text-sm text-gray-600">Auto-send after composing (requires SMTP config)</span>
                  </label>
                )}

                {/* Run button */}
                <button onClick={handleRun}
                  disabled={loading || (!task.trim() && !originalEmail.trim())}
                  className={`w-full py-3 rounded-xl font-semibold text-white text-sm transition-all flex items-center justify-center gap-2
                    ${loading ? "bg-gray-400 cursor-not-allowed" : `${runBtnColor} shadow-md hover:shadow-lg active:scale-[0.99]`}`}>
                  {loading ? (
                    <><svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z"/>
                    </svg>Processing…</>
                  ) : (
                    <>{currentFeature.icon} Run {currentFeature.label}</>
                  )}
                </button>

                {/* Setup tip */}
                <div className="bg-amber-50 border border-amber-100 rounded-xl px-4 py-3 text-xs text-amber-700">
                  💡 <strong>SMTP/IMAP config:</strong> Set <code className="bg-amber-100 px-1 rounded">EMAIL_ADDRESS</code>, <code className="bg-amber-100 px-1 rounded">EMAIL_PASSWORD</code>, <code className="bg-amber-100 px-1 rounded">EMAIL_SMTP_HOST</code>, <code className="bg-amber-100 px-1 rounded">EMAIL_IMAP_HOST</code> in your <code className="bg-amber-100 px-1 rounded">.env</code> file. Without these, read/send features run in mock mode — AI composition still works fully.
                </div>
              </div>
            </div>
          )}

          <ResultPanel result={result} feature={activeFeature} />
        </div>
      </div>
    </div>
  );
}
