# AI Agent System — Deployment Guide

Complete guide for deploying on local machine, VPS (Oracle/Render/Railway), or Docker.

---

## OPTION 1 — Local Machine (Fastest, 5 minutes)

### Step 1: Clone the repo
git clone https://github.com/prasadmanas8b-debug/ai-agent-project
cd ai-agent-project

### Step 2: One-command setup
bash setup.sh

### Step 3: Add your API keys
Open .env and fill in:
GROQ_API_KEY=your_key_here       ← Required (get free at console.groq.com)
TAVILY_API_KEY=your_key_here     ← Optional (tavily.com)
GITHUB_TOKEN=your_token_here     ← Optional (github.com/settings/tokens)
EMAIL_ADDRESS=your@gmail.com     ← Optional
EMAIL_PASSWORD=your_app_password ← Optional

### Step 4: Run CLI
python main.py

### Step 5: Or run API server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
Visit: http://localhost:8000/docs

---

## OPTION 2 — Docker (Recommended for teams)

### Prerequisites
- Docker + Docker Compose installed

### Step 1: Clone and configure
git clone https://github.com/prasadmanas8b-debug/ai-agent-project
cd ai-agent-project
cp .env.example .env
# Edit .env with your API keys

### Step 2: Run CLI agent
docker-compose up agent

### Step 3: Run API server
docker-compose up api
# API available at: http://localhost:8000

### Step 4: Run both together
docker-compose up

### Step 5: Stop everything
docker-compose down

---

## OPTION 3 — Oracle Cloud Free Tier (Free forever, 24/7)

Oracle gives 4 OCPU + 24GB RAM free forever. Best for self-hosting.

### Step 1: Create Oracle Cloud account
https://cloud.oracle.com — choose Always Free tier

### Step 2: Create VM
- Shape: VM.Standard.A2.Flex (4 OCPU, 24GB RAM)
- OS: Ubuntu 22.04
- Enable public IP

### Step 3: Open firewall port 8000
In Oracle Cloud console:
Security List → Add Ingress Rule → TCP Port 8000

### Step 4: SSH into your VM
ssh ubuntu@YOUR_VM_IP

### Step 5: Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
newgrp docker

### Step 6: Clone and deploy
git clone https://github.com/prasadmanas8b-debug/ai-agent-project
cd ai-agent-project
cp .env.example .env
nano .env   ← add your API keys

# Run API server (background)
docker-compose up api -d

### Step 7: Access your API
http://YOUR_VM_IP:8000/docs

---

## OPTION 4 — Railway.app (Easiest cloud deploy, free tier)

### Step 1: Go to railway.app
### Step 2: New Project → Deploy from GitHub repo
### Step 3: Select your repo: prasadmanas8b-debug/ai-agent-project
### Step 4: Add environment variables in Railway dashboard
- GROQ_API_KEY
- TAVILY_API_KEY
- (all from .env.example)
### Step 5: Set start command:
uvicorn api.main:app --host 0.0.0.0 --port $PORT
### Step 6: Deploy — Railway gives you a public URL automatically

---

## OPTION 5 — Render.com (Free tier, auto-deploys from GitHub)

### Step 1: render.com → New Web Service
### Step 2: Connect GitHub → select ai-agent-project repo
### Step 3: Settings:
- Build Command: pip install -r requirements.txt
- Start Command: uvicorn api.main:app --host 0.0.0.0 --port $PORT
### Step 4: Add environment variables from .env.example
### Step 5: Deploy

---

## API Endpoints (after any deployment)

GET  /              → health check
GET  /api/modes     → list all agent capabilities
POST /api/agent     → run any task

Example request:
curl -X POST https://YOUR_URL/api/agent \
  -H "Content-Type: application/json" \
  -d '{"task": "Research latest AI trends"}'

Interactive API docs:
https://YOUR_URL/docs

---

## Running Tests

bash run_tests.sh

Or manually:
pytest tests/ -v

---

## Minimum Requirements

- Python 3.11+
- 1GB RAM (2GB+ recommended)
- 1GB disk space
- Internet access (for Groq API calls)
- GROQ_API_KEY (only required key)

---

## Troubleshooting

Problem: "GROQ_API_KEY not set"
Fix: cp .env.example .env and add your key

Problem: "ModuleNotFoundError"
Fix: pip install -r requirements.txt

Problem: "Permission denied" on setup.sh
Fix: chmod +x setup.sh && bash setup.sh

Problem: Port 8000 already in use
Fix: uvicorn api.main:app --port 8001

Problem: Docker permission denied
Fix: sudo usermod -aG docker $USER && newgrp docker

