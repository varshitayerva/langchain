# How to Run MarginGuard Backend & Frontend

## Prerequisites Check

```bash
# Check Python version (need 3.9+)
python --version

# Check Node version (need 14+)
node --version

# Check npm version (need 6+)
npm --version
```

---

## Option 1: Run Backend ONLY (HITL API)

### Terminal 1: Backend
```bash
# Navigate to project root
cd c:\Users\samriddhi.mishra\langchain\reviewer\langchain

# Install dependencies
pip install -r api/requirements.txt

# Run the HITL FastAPI server
python -m uvicorn api.hitl_api:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Access API:**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Test Endpoint: http://localhost:8000/info

---

## Option 2: Run Frontend ONLY (React)

### Terminal 2: Frontend
```bash
# Navigate to frontend folder
cd c:\Users\samriddhi.mishra\langchain\reviewer\langchain\frontend

# Install dependencies (first time only)
npm install

# Start development server
npm start
```

**Expected Output:**
```
Compiled successfully!

You can now view marginguard in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

**Access Frontend:**
- Open browser: http://localhost:3000

---

## Option 3: Run BOTH Backend & Frontend (COMPLETE SETUP)

### Setup Step 1: Open Terminal 1 for Backend

```bash
# Terminal 1: Backend
cd c:\Users\samriddhi.mishra\langchain\reviewer\langchain
pip install -r api/requirements.txt
python -m uvicorn api.hitl_api:app --reload --host 0.0.0.0 --port 8000
```

**Wait for:**
```
✓ Uvicorn running on http://0.0.0.0:8000
✓ Application startup complete
```

### Setup Step 2: Open Terminal 2 for Frontend

```bash
# Terminal 2: Frontend
cd c:\Users\samriddhi.mishra\langchain\reviewer\langchain\frontend
npm install
npm start
```

**Wait for:**
```
✓ Compiled successfully!
✓ Ready to open http://localhost:3000
```

### Step 3: Access Application

Open in browser:
```
http://localhost:3000
```

---

## Quick Copy-Paste Commands

### Windows PowerShell

```powershell
# Terminal 1 - Backend
cd 'c:\Users\samriddhi.mishra\langchain\reviewer\langchain'
pip install -r api/requirements.txt
python -m uvicorn api.hitl_api:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend (in separate PowerShell window)
cd 'c:\Users\samriddhi.mishra\langchain\reviewer\langchain\frontend'
npm install
npm start
```

### Windows CMD

```cmd
REM Terminal 1 - Backend
cd c:\Users\samriddhi.mishra\langchain\reviewer\langchain
pip install -r api/requirements.txt
python -m uvicorn api.hitl_api:app --reload --host 0.0.0.0 --port 8000

REM Terminal 2 - Frontend (in separate CMD window)
cd c:\Users\samriddhi.mishra\langchain\reviewer\langchain\frontend
npm install
npm start
```

### macOS/Linux Bash

```bash
# Terminal 1 - Backend
cd ~/path/to/langchain/reviewer/langchain
pip install -r api/requirements.txt
python -m uvicorn api.hitl_api:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend (in separate terminal)
cd ~/path/to/langchain/reviewer/langchain/frontend
npm install
npm start
```

---

## Testing the Integration

### Test 1: Check Backend is Running
```bash
# From any terminal
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "orchestrator": "ready",
#   "timestamp": "2024-06-12T10:30:45.123456"
# }
```

### Test 2: Start Analysis via API
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "iPhone 15 Pro pricing", "save_result": true}'

# Expected response:
# {
#   "execution_id": "a1b2c3d4-...",
#   "status": "started",
#   "message": "Analysis started for: iPhone 15 Pro pricing",
#   "created_at": "2024-06-12T10:30:45.123456"
# }
```

### Test 3: Access Frontend
Open browser: `http://localhost:3000`

---

## Alternative: Run with Old API (Original main.py)

If you want to use the original backend instead of HITL:

```bash
# Terminal 1 - Backend (Original)
cd c:\Users\samriddhi.mishra\langchain\reviewer\langchain
pip install -r api/requirements.txt
python api/main.py

# Terminal 2 - Frontend
cd c:\Users\samriddhi.mishra\langchain\reviewer\langchain\frontend
npm install
npm start
```

---

## Port Configuration

### Current Ports
```
Frontend: http://localhost:3000
Backend:  http://localhost:8000
```

### Change Backend Port (if 8000 is in use)
```bash
python -m uvicorn api.hitl_api:app --reload --host 0.0.0.0 --port 8001
```

### Change Frontend Port (if 3000 is in use)

Edit `frontend/package.json`:
```json
"scripts": {
  "start": "PORT=3001 react-scripts start"
}
```

Then run: `npm start`

---

## Troubleshooting

### Backend Issues

**"Port 8000 already in use"**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process (Windows)
taskkill /PID <PID> /F

# Use different port
python -m uvicorn api.hitl_api:app --port 8001
```

**"ModuleNotFoundError: No module named 'fastapi'"**
```bash
# Reinstall dependencies
pip install --upgrade -r api/requirements.txt
```

**"LangGraph not available"**
```bash
pip install langgraph langchain-core
```

### Frontend Issues

**"npm: command not found"**
```bash
# Install Node.js from https://nodejs.org/
# Then run: npm install
```

**"Port 3000 already in use"**
```bash
# Kill process using port 3000
# macOS/Linux: lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9
# Windows: netstat -ano | findstr :3000

# Or use different port
PORT=3001 npm start
```

**"Dependencies not installed"**
```bash
# Clear cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
npm start
```

---

## Full Workflow Example

### Step 1: Start Backend
```bash
# Terminal 1
cd c:\Users\samriddhi.mishra\langchain\reviewer\langchain
pip install -r api/requirements.txt
python -m uvicorn api.hitl_api:app --reload
```

Output:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Start Frontend
```bash
# Terminal 2
cd c:\Users\samriddhi.mishra\langchain\reviewer\langchain\frontend
npm install
npm start
```

Output:
```
Compiled successfully!
You can now view marginguard in the browser.
Local: http://localhost:3000
```

### Step 3: Open Application
```
Browser: http://localhost:3000
```

### Step 4: Use Application
1. Upload a PDF policy (any PDF)
2. Enter product name (e.g., "iPhone 15 Pro")
3. Click "Analyze Product"
4. Watch the pipeline console execute
5. View results in tabs

### Step 5: Test HITL (if using HITL API)
If analysis pauses for review:
- Frontend will show "Awaiting Human Review"
- Risk factors will be displayed
- You can approve/reject
- Then workflow resumes

---

## Docker Alternative (Optional)

### Build & Run with Docker

```bash
# Build image
docker build -t marginguard .

# Run container
docker run -p 8000:8000 -p 3000:3000 marginguard
```

Requires `Dockerfile` in project root.

---

## Environment Variables (Optional)

Create `.env` file in project root:

```bash
# .env file
ANTHROPIC_API_KEY=your_key_here
TAVILY_API_KEY=your_tavily_key
XAI_API_KEY=your_xai_key
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
```

Load in Python:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Production Deployment

### Using Gunicorn (Backend)

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn api.hitl_api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Using PM2 (Node/Frontend)

```bash
# Install PM2
npm install -g pm2

# Start frontend
pm2 start "npm start" --name "frontend"

# Start backend
pm2 start "python -m uvicorn api.hitl_api:app" --name "backend"

# Monitor
pm2 monit
```

---

## Summary

| Task | Command |
|------|---------|
| **Start Backend** | `python -m uvicorn api.hitl_api:app --reload` |
| **Start Frontend** | `npm install && npm start` (in frontend folder) |
| **Check Backend Health** | `curl http://localhost:8000/health` |
| **Access Frontend** | `http://localhost:3000` |
| **API Docs** | `http://localhost:8000/docs` |

---

## Quick Reference Card

```
═══════════════════════════════════════════════════════════════

  MARGINGUARD STARTUP GUIDE

═══════════════════════════════════════════════════════════════

TERMINAL 1 (Backend):
  cd path/to/langchain
  pip install -r api/requirements.txt
  python -m uvicorn api.hitl_api:app --reload

TERMINAL 2 (Frontend):
  cd path/to/langchain/frontend
  npm install
  npm start

BROWSER:
  http://localhost:3000

BACKEND DOCS:
  http://localhost:8000/docs

═══════════════════════════════════════════════════════════════
```

---

**You're ready to run MarginGuard!** 🚀
