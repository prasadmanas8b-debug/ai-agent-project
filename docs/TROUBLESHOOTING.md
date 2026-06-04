# Troubleshooting Guide
**AI Agent Orchestration Framework — v2.0**

---

## Common Errors

### `GROQ_API_KEY not set` / `Config FATAL`

**Cause:** Required environment variable missing.

**Fix:**
```bash
cp .env.example .env
# Add your Groq API key to .env:
GROQ_API_KEY=gsk_your_key_here
```
Get a key at: https://console.groq.com

---

### `Research Agent: Search error: TAVILY_API_KEY not found`

**Cause:** Tavily API key not configured.

**Fix:**
- Add `TAVILY_API_KEY=tvly-your_key_here` to `.env`
- Or ignore — the Research Agent falls back to LLM-only knowledge

---

### `GitHub Agent: GITHUB_TOKEN not set` / `GITHUB_REPO not set`

**Cause:** GitHub credentials missing.

**Fix:**
```
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=your-username/your-repo
```
Create a token at: https://github.com/settings/tokens (needs `repo` scope)

---

### `Circuit breaker 'groq' is OPEN`

**Cause:** Groq API had 5+ consecutive failures. The circuit breaker tripped to protect the system.

**Fix:**
1. Wait 60 seconds — the circuit auto-recovers in `HALF_OPEN` state
2. Check Groq status: https://status.groq.com
3. Verify your API key is valid and has quota remaining
4. Check your internet connection

---

### `❌ GitHub Agent: could not parse LLM response as JSON`

**Cause:** LLM returned a malformed JSON response for the GitHub action.

**Fix:**
- Retry the task — usually a transient LLM issue
- Rephrase the task more clearly: "List files in the agents folder" instead of "show me agents"
- Check if Groq has a service incident

---

### `❌ Path traversal attempt blocked`

**Cause:** The GitHub Agent tried to write outside the `git_agent_output/` folder.

**This is a security feature, not a bug.** All file writes are intentionally locked to `git_agent_output/`.

If you need to write to a different location, update `GITHUB_OUTPUT_FOLDER` in `.env`.

---

### `TesseractNotFoundError` / `pytesseract` errors

**Cause:** Tesseract OCR binary not installed at system level.

**Fix:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download: https://github.com/UB-Mannheim/tesseract/wiki
```
Then restart the application.

---

### `weasyprint` import errors or missing fonts

**Cause:** weasyprint system library dependencies not installed.

**Fix:**
```bash
# Ubuntu/Debian
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0

# macOS
brew install pango gdk-pixbuf
```

---

### `Email Agent: SMTP Authentication failed`

**Cause:** Wrong email/password or need an App Password.

**Fix for Gmail:**
1. Enable 2-Step Verification on your Google account
2. Go to: Google Account → Security → App Passwords
3. Create an app password for "Mail"
4. Use that 16-character app password as `EMAIL_PASSWORD` in `.env`

---

### `Database Agent: DB_URL not set / cannot connect`

**Cause:** Database connection not configured.

**Fix for SQLite (default):**
```
DB_TYPE=sqlite
DB_SQLITE_PATH=database.db
```

**Fix for PostgreSQL:**
```
DB_TYPE=postgresql
DB_URL=postgresql://user:password@localhost:5432/mydb
```

---

### `[Supervisor] Max iterations reached`

**Cause:** The pipeline ran the supervisor→agent loop 10 times without completing. Possible causes:
- Complex multi-step task where the supervisor keeps re-routing
- A bug where an agent isn't setting its output field correctly

**Debug:**
1. Check the trace file: `outputs/traces/run_{run_id}.json`
2. Look at `agent_history` to see which agents ran
3. Check `error_log` for silent failures

**Fix:**
- Increase `MAX_GRAPH_ITERATIONS` in `.env` (default: 10)
- Rephrase the task to be more specific about what you want

---

### `PromptInjectionError: Input contains potentially malicious content`

**Cause:** Your input matched a prompt injection detection pattern.

**Fix:** Rephrase without the flagged language. Common false positives:
- "ignore this part" → use "skip this section" instead
- "you are now writing a report" → use "write a report about"
- "forget the previous example" → use "use a different example"

If a legitimate task is incorrectly blocked, set `ENABLE_PROMPT_GUARD=false` in `.env` (not recommended for production).

---

### `outputs/` directory errors

**Cause:** Missing or incorrect permissions on output directories.

**Fix:**
```bash
mkdir -p outputs/logs outputs/traces memory
chmod 755 outputs outputs/logs outputs/traces memory
```

---

### Tests failing with `ModuleNotFoundError`

**Cause:** Missing Python dependencies.

**Fix:**
```bash
pip install -r requirements.txt
pip install pytest pytest-cov sqlparse  # test dependencies
```

---

### Research Agent returns only LLM knowledge (no web search)

**Cause:** `TAVILY_API_KEY` not set — agent falls back to LLM.

**Indicators:** No `🔎 Searching:` lines in output.

**Fix:** Add Tavily API key to `.env`. Free tier: 1000 searches/month at https://tavily.com.

---

## Performance Issues

### LLM calls are very slow

1. Check Groq API status: https://status.groq.com
2. Verify you're not on a heavily rate-limited free tier
3. The `llama-3.3-70b-versatile` model is large — consider `llama-3.1-8b-instant` for testing

### Research takes too long

The Research Agent makes 2-4 sequential Tavily calls. This is by design for quality.
To reduce: set `TAVILY_MAX_RESULTS=3` in `.env`.

---

## Debug Mode

Enable verbose logging:
```
LOG_LEVEL=DEBUG
LOG_FORMAT=human
```

This shows every LLM call, tool invocation, and routing decision in human-readable format.

---

## Getting Help

1. Check `outputs/logs/agent_framework.log` for structured error logs
2. Check `outputs/traces/` for the most recent run trace
3. Run `python -c "from config.settings import settings; print(settings)"` to verify configuration
