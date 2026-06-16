# MarginGuard AI — FastAPI Backend

Production-ready FastAPI server for multi-agent pricing strategy analysis with LangGraph orchestration.

## Overview

MarginGuard automates pricing intelligence by detecting when competitors undercut prices or ship comparable features, then automatically checking if reacting is feasible within margin constraints.

**Problem:** Product managers spend hours manually checking competitors, often missing opportunities or violating margin guardrails.

**Solution:** Five agents work in parallel and sequence to generate compliance-audited pricing strategies with automatic retries.

## Architecture

### API Server Stack

```
FastAPI
  ↓
Background Tasks (Threading)
  ↓
LangGraph Orchestrator
  ↓
5 Agents (RAG, Research, Synthesis, Reviewer)
  ↓
PostgreSQL + pgvector (RAG)
Tavily API (Research)
XAI Grok (Reviewer)
```

### Request Flow

```
Client
  ↓
POST /analyze
  ↓
Create Execution (UUID)
  ↓
Background Task
  ├→ Step 1: Initialize
  ├→ Step 2: RAG Agent
  ├→ Step 3: Research Agent (parallel)
  ├→ Step 4: Synthesis Agent
  ├→ Step 5: Reviewer Agent
  │     └→ If rejected: Loop back to Synthesis (max 3 times)
  └→ Save Result
  ↓
GET /status/{id}
  ↓ (polling)
GET /result/{id} when done
```

## Installation

### 1. Prerequisites

- Python 3.9+
- PostgreSQL 12+ with pgvector extension
- Tavily API key (for research)
- XAI API key (optional, for reviewer)

### 2. Install Dependencies

```bash
cd api
pip install -r requirements.txt
```

### 3. Setup Environment

Create `.env` file in project root:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=fde_langchain

# APIs
TAVILY_API_KEY=your_tavily_api_key
XAI_API_KEY=your_xai_api_key  # Optional
```

### 4. Start Services

PostgreSQL:
```bash
docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 ankane/pgvector
```

Or if installed locally:
```bash
brew services start postgresql  # macOS
sudo service postgresql start   # Linux
```

### 5. Run API

```bash
cd api
python main.py

# Or with uvicorn:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Quick Start

### 1. Open Interactive Docs

Navigate to: **http://localhost:8000/docs**

This opens Swagger UI where you can test all endpoints.

### 2. Start Analysis

**POST /analyze**

Request:
```json
{
  "query": "CloudScale Enterprise Tier-2 pricing",
  "save_result": true
}
```

Response:
```json
{
  "execution_id": "a1b2c3d4",
  "status": "started",
  "created_at": "2024-01-12T10:30:45.123456",
  "check_status_url": "/status/a1b2c3d4",
  "get_result_url": "/result/a1b2c3d4"
}
```

### 3. Check Progress

**GET /status/a1b2c3d4**

Response:
```json
{
  "execution_id": "a1b2c3d4",
  "status": "running",
  "step": 3,
  "message": "Executing research and synthesis agents...",
  "progress": 50.0,
  "created_at": "2024-01-12T10:30:45.123456",
  "updated_at": "2024-01-12T10:31:02.654321"
}
```

### 4. Get Result

**GET /result/a1b2c3d4**

Response:
```json
{
  "execution_id": "a1b2c3d4",
  "status": "success",
  "query": "CloudScale Enterprise Tier-2 pricing",
  "review_status": "approved",
  "retry_count": 1,
  "draft_report": "# Market Position & Pricing Strategy Report\n\n...",
  "completed_at": "2024-01-12T10:31:15.987654"
}
```

## API Reference

### Analysis Endpoints

#### POST /analyze

Start a new pricing analysis pipeline.

**Request:**
```json
{
  "query": "Product name and what you want to analyze",
  "save_result": true
}
```

**Parameters:**
- `query` (str, required) - Product query or analysis request
- `save_result` (bool, optional, default=true) - Save result to JSON file

**Response:** 200 OK
```json
{
  "execution_id": "string",
  "status": "started",
  "created_at": "ISO-8601 timestamp",
  "check_status_url": "/status/{execution_id}",
  "get_result_url": "/result/{execution_id}"
}
```

**Errors:**
- 400 Bad Request - Empty query

**Example:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Affordable smartwatch under $300",
    "save_result": true
  }'
```

#### GET /status/{execution_id}

Check execution progress.

**Response:** 200 OK
```json
{
  "execution_id": "string",
  "status": "pending|running|completed|error",
  "step": 0-5,
  "message": "Human-readable status",
  "progress": 0-100,
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp",
  "error": null  // or error message if failed
}
```

**Errors:**
- 404 Not Found - Execution ID doesn't exist

**Status Values:**
- `pending` - Queued, waiting to start
- `running` - Currently processing
- `completed` - Done (check /result for details)
- `error` - Failed (check error field)

**Example:**
```bash
curl "http://localhost:8000/status/a1b2c3d4"
```

#### GET /result/{execution_id}

Get final analysis result.

**Response:** 200 OK (when completed)
```json
{
  "execution_id": "string",
  "status": "success",
  "query": "original query",
  "review_status": "approved|rejected",
  "retry_count": 0-3,
  "draft_report": "Markdown report",
  "rag_context": {
    "product_data": [...],
    "policy_snippet": "..."
  },
  "research_data": {
    "competitor_name": "...",
    "competitors": [...]
  },
  "review_feedback": null,  // or rejection reason
  "completed_at": "ISO-8601 timestamp"
}
```

**Status Codes:**
- 200 OK - Result ready
- 202 Accepted - Still processing
- 404 Not Found - Execution not found
- 500 Server Error - Analysis failed

**Example:**
```bash
curl "http://localhost:8000/result/a1b2c3d4"
```

#### GET /result/{execution_id}/download

Download result as JSON file.

**Response:** 200 OK with file

**Example:**
```bash
curl "http://localhost:8000/result/a1b2c3d4/download" \
  -o analysis_result.json
```

### System Endpoints

#### GET /health

Health check and system status.

**Response:** 200 OK
```json
{
  "status": "healthy",
  "timestamp": "ISO-8601 timestamp",
  "langgraph_available": true,
  "version": "2.0.0"
}
```

#### GET /info

API information and capabilities.

**Response:** 200 OK
```json
{
  "title": "MarginGuard AI",
  "version": "2.0.0",
  "features": [...],
  "endpoints": {...},
  "langgraph_available": true
}
```

#### GET /executions

List recent executions (for debugging).

**Query Parameters:**
- `limit` (int, 1-100, default=10) - Number of recent executions to return

**Response:** 200 OK
```json
{
  "total": 42,
  "recent": [
    {
      "id": "a1b2c3d4",
      "status": "completed",
      "created_at": "ISO-8601 timestamp",
      "progress": 100.0
    }
  ]
}
```

#### GET /

Welcome and quick start guide.

**Response:** 200 OK
```json
{
  "message": "Welcome to MarginGuard AI",
  "version": "2.0.0",
  "docs": "/docs",
  "quick_start": {
    "1_start": "POST /analyze",
    "2_monitor": "GET /status/{execution_id}",
    "3_retrieve": "GET /result/{execution_id}"
  }
}
```

## Workflow Steps

### Success Path (2-3 seconds)

```
Step 1 (10%):   Initialize Orchestrator
Step 2 (25%):   RAG Agent - Product Retrieval
Step 3 (50%):   Research & Synthesis Agents
Step 4 (75%):   Reviewer - Compliance Audit APPROVED
Step 5 (100%):  Complete - Report Ready
```

### Rejection Path with Retries (8-10 seconds)

```
Step 1 (10%):   Initialize
Step 2 (25%):   RAG Agent
Step 3 (50%):   Research & Synthesis
Step 4 (75%):   Reviewer - REJECTED (price below margin)
Step 3 (50%):   Synthesis Retry 1 (with feedback)
Step 4 (75%):   Reviewer RETRY 1 - REJECTED
Step 3 (50%):   Synthesis Retry 2
Step 4 (75%):   Reviewer RETRY 2 - APPROVED
Step 5 (100%):  Complete - Report Ready (retry_count=2)
```

## Data Models

### AnalysisRequest

```python
{
    "query": str,           # Required, min 1 char
    "save_result": bool     # Optional, default True
}
```

### ExecutionState

```python
{
    "execution_id": str,        # UUID
    "status": str,              # pending, running, completed, error
    "created_at": str,          # ISO-8601
    "updated_at": str,          # ISO-8601
    "step": int,                # 0-5
    "message": str,             # Current step description
    "progress": float,          # 0.0-100.0
    "result": dict,             # Final result (when completed)
    "error": str                # Error message (when failed)
}
```

### ResultData

```python
{
    "query": str,               # Original query
    "review_status": str,       # "approved" or "rejected"
    "retry_count": int,         # 0-3
    "draft_report": str,        # Markdown report
    "rag_context": dict,        # Product & policy data
    "research_data": dict,      # Competitor data
    "review_feedback": str,     # Why rejected (if applicable)
    "completed_at": str         # ISO-8601
}
```

## File Structure

```
api/
├── main.py                 ← FastAPI application
├── requirements.txt        ← Dependencies
├── QUICKSTART.md          ← Quick start guide
├── README.md              ← This file
└── results/               ← Saved analysis results
    ├── a1b2c3d4.json
    ├── x1y2z3w9.json
    └── ...
```

## Integration with LangGraph

The API integrates the complete LangGraph orchestrator:

```python
from orchestration.langgraph_orchestrator import run_workflow

# In background task:
final_state = run_workflow(query)
# Returns: {query, rag_context, research_data, draft_report, review_status, ...}
```

The orchestrator handles:
- RAG agent integration
- Research agent integration  
- Synthesis report generation
- Reviewer compliance audit
- Automatic retry logic
- State management

## Performance

| Metric | Value |
|--------|-------|
| Success path latency | 2-3 seconds |
| 1 rejection + retry | 4-5 seconds |
| Max retries (3) | 8-10 seconds |
| Concurrent requests | Unlimited (thread-per-request) |
| Memory per execution | ~100KB |
| Results storage | ~50-100KB per analysis |

## Deployment

### Development

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
# Using Gunicorn + Uvicorn
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t marginguard-api .
docker run -p 8000:8000 --env-file .env marginguard-api
```

## Monitoring

### Enable Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Track Metrics

```python
import time

start = time.time()
response = requests.post(f"{BASE_URL}/analyze", json={...})
execution_time = time.time() - start
```

### Debug Executions

```bash
curl "http://localhost:8000/executions?limit=20"
```

## Troubleshooting

### "LangGraph not available"

```
[WARN] LangGraph orchestrator not available
```

**Solution:**
```bash
pip install langgraph langchain-core
```

### "PostgreSQL connection refused"

**Solution:**
```bash
docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 ankane/pgvector
```

### "Tavily API error"

**Solution:** Add to `.env`:
```env
TAVILY_API_KEY=your_actual_key
```

### "Port 8000 already in use"

**Solution:**
```bash
uvicorn main:app --port 8001
```

### Slow Analysis

Check execution details:
```bash
curl "http://localhost:8000/status/{execution_id}"
```

If step 2 (RAG) is slow: PostgreSQL may need indexing
If step 3 (Research) is slow: Tavily API latency

## Next Steps

1. ✅ Install and run API
2. ✅ Test endpoints via /docs
3. **→ Build frontend** to consume endpoints
4. **→ Add monitoring** (Prometheus, DataDog, etc.)
5. **→ Deploy to production** (Kubernetes, AWS, etc.)
6. **→ Add authentication** (API keys, OAuth)
7. **→ Cache results** (Redis)

## Documentation Links

- **Quick Start:** `QUICKSTART.md`
- **Orchestration:** `../orchestration/README.md`
- **LangGraph:** `../orchestration/ARCHITECTURE.md`
- **Full API Docs:** `http://localhost:8000/docs` (when running)

## Support

For issues or questions:
1. Check logs in console
2. Review `/health` endpoint
3. Check `/executions` for recent runs
4. See troubleshooting section above
5. Review code comments in `main.py`

---

**MarginGuard AI FastAPI Backend** - Ready for Production 🚀
