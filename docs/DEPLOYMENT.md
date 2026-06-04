# Deployment Guide
**AI Agent Orchestration Framework — v2.0**

---

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| Python | 3.10 | 3.11+ |
| RAM | 512 MB | 2 GB |
| Disk | 1 GB | 5 GB |
| CPU | 1 core | 2+ cores |

### System-Level Dependencies

These must be installed at the OS level before running:

**For PDF OCR (pytesseract):**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# macOS
brew install tesseract

# Windows
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
```

**For PDF HTML rendering (weasyprint):**
```bash
# Ubuntu/Debian
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
                     libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# macOS
brew install pango gdk-pixbuf libffi

# Note: weasyprint is optional — PDF generation will fall back gracefully if unavailable
```

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/prasadmanas8b-debug/ai-agent-project
cd ai-agent-project
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys (see Environment Variables section below)
```

### 3. Run

```bash
python main.py
```

---

## Environment Variables

### Required

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key — get at https://console.groq.com |

### Recommended

| Variable | Description | Default |
|---|---|---|
| `TAVILY_API_KEY` | Tavily search API key — https://tavily.com | (LLM fallback) |
| `GITHUB_TOKEN` | GitHub Personal Access Token (repo scope) | (GitHub agent disabled) |
| `GITHUB_REPO` | Target repo in format `owner/repo` | (GitHub agent disabled) |

### Email Agent

| Variable | Description | Default |
|---|---|---|
| `EMAIL_ADDRESS` | Your email address | (mock mode) |
| `EMAIL_PASSWORD` | App password (not your login password!) | (mock mode) |
| `EMAIL_SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `EMAIL_SMTP_PORT` | SMTP port | `587` |
| `EMAIL_IMAP_HOST` | IMAP server hostname | `imap.gmail.com` |

**Gmail setup:** Go to Google Account → Security → 2-Step Verification → App Passwords → Create app password for "Mail".

### Database Agent

| Variable | Description | Default |
|---|---|---|
| `DB_TYPE` | `sqlite`, `postgresql`, `mysql` | `sqlite` |
| `DB_SQLITE_PATH` | Path to SQLite file | `database.db` |
| `DB_URL` | Full connection URL for Postgres/MySQL | — |
| `DB_READ_ONLY` | Restrict to SELECT only | `false` |

### Security & Limits

| Variable | Description | Default |
|---|---|---|
| `MAX_TASK_LENGTH` | Max input characters | `2000` |
| `ENABLE_PROMPT_GUARD` | Enable injection defense | `true` |
| `LLM_TIMEOUT_SECONDS` | LLM call timeout | `30` |
| `LLM_MAX_RETRIES` | Retry attempts for LLM calls | `3` |

### Observability

| Variable | Description | Default |
|---|---|---|
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |
| `LOG_FORMAT` | `json` or `human` | `json` |
| `ENABLE_TRACING` | Write trace files | `true` |
| `ENABLE_METRICS` | Collect metrics | `true` |
| `TRACES_DIR` | Trace output directory | `outputs/traces` |
| `LOGS_DIR` | Log file directory | `outputs/logs` |

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr tesseract-ocr-eng \
    libpango-1.0-0 libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create output directories
RUN mkdir -p outputs/logs outputs/traces memory

# Non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "main.py"]
```

### docker-compose.yml

```yaml
version: "3.9"

services:
  agent:
    build: .
    env_file: .env
    volumes:
      - ./outputs:/app/outputs
      - ./memory:/app/memory
      - ./uploads:/app/uploads
    stdin_open: true
    tty: true

  # Optional: add PostgreSQL for database agent
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: agentdb
      POSTGRES_USER: agent
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### Build and run

```bash
docker-compose up --build
```

---

## API Deployment

The framework includes FastAPI endpoints for PDF and Email agents:

```bash
# Install additional deps
pip install uvicorn fastapi python-multipart

# Run API server
uvicorn api.pdf_endpoint:app --host 0.0.0.0 --port 8000 --reload
uvicorn api.email_endpoint:app --host 0.0.0.0 --port 8001 --reload
```

**API Security (required for production):**

Set an API key in `.env`:
```
API_KEY=your-secret-key-here
```

Then pass it as a header:
```
Authorization: Bearer your-secret-key-here
```

---

## Running Tests

```bash
# Full test suite
pytest tests/ -v

# With coverage report
pip install pytest-cov
pytest tests/ -v --cov=. --cov-report=html

# Specific test files
pytest tests/test_tools.py -v
pytest tests/test_security.py -v
pytest tests/test_observability.py -v

# Run database agent tests (requires DB setup)
python tests/test_database_agent.py
```

---

## Production Checklist

Before deploying to production:

- [ ] All required env vars set in `.env` (not committed to git)
- [ ] `.env` is in `.gitignore`
- [ ] `DB_READ_ONLY=true` if database agent should be read-only
- [ ] `ENABLE_PROMPT_GUARD=true` (default)
- [ ] API endpoints have authentication configured
- [ ] `outputs/` directory is writable by the application user
- [ ] System dependencies installed (tesseract, pango) if using PDF agent
- [ ] `LOG_LEVEL=INFO` (not DEBUG) in production
- [ ] Circuit breaker thresholds tuned for your Groq API tier
- [ ] Monitoring set up for `outputs/logs/agent_framework.log`

---

## Monitoring in Production

### Log file location
```
outputs/logs/agent_framework.log
```
Rotating: 10MB per file, 5 files kept = max 50MB total.

### Metrics snapshot
```python
from observability.metrics import metrics
import json
print(json.dumps(metrics.report(), indent=2))
```

### Recent traces
```python
from observability.tracer import tracer
traces = tracer.list_traces(limit=10)
for t in traces:
    print(f"{t['start_time']} | {t['status']} | {t['task'][:60]}")
```
