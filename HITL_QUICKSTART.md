# Human-in-the-Loop (HITL) Quick Start

## 🚀 Get Running in 5 Minutes

### 1. Install (1 minute)
```bash
pip install langgraph langchain fastapi pydantic uvicorn httpx
```

### 2. Copy Files (30 seconds)
```bash
# Files already created:
# - orchestration/hitl_orchestrator.py
# - api/hitl_api.py
# - HITL_CLIENT_EXAMPLE.py
```

### 3. Start API (1 minute)
```bash
# Terminal 1
uvicorn api.hitl_api:app --reload --port 8000
```

Expected output:
```
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 4. Run Example (1 minute)
```bash
# Terminal 2
python HITL_CLIENT_EXAMPLE.py

# Select: 2 (Gray Area HITL example)
```

Expected output:
```
EXAMPLE 2: GRAY AREA (HITL Triggered)
📊 Starting analysis: CloudScale Enterprise pricing
✅ Analysis started
   Execution ID: a1b2c3d4-...

⏳ Polling status (interval=1.0s, timeout=300.0s)
   [0.1s] Step 2/5 (50%) - Orchestrator running
   [1.2s] Step 3/5 (75%) - Research in progress
   [2.1s] Step 4/5 (80%) - Reviewing pricing...

⚠️  PAUSED FOR HUMAN REVIEW
   Review Status: requires_human_review
   Feedback: HUMAN REVIEW REQUIRED: Price in gray area (within 2% of floor)
   Risk Factors:
     - Price in gray area (within 2% of floor)

[AUTO-APPROVE] Simulating human approval...
🔄 Resuming workflow with human decision
   Decision: override_approve
   Notes: Auto-approved by test client

✅ WORKFLOW RESUMED
   Final Decision: approved
   Human Decision: override_approve

✅ ANALYSIS COMPLETED
   Review Status: approved
```

---

## 📡 Use via cURL

### 1. Start Analysis
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "CloudScale Enterprise pricing", "save_result": true}'

# Response:
# {
#   "execution_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
#   "status": "started",
#   "message": "Analysis started for: CloudScale Enterprise pricing",
#   "created_at": "2024-06-12T10:30:45.123456"
# }
```

### 2. Check Status (every 1 second)
```bash
EXEC_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"

curl http://localhost:8000/analyze/status/$EXEC_ID

# When paused:
# {
#   "execution_id": "a1b2c3d4-...",
#   "status": "paused_for_human_review",
#   "is_paused": true,
#   "review_status": "requires_human_review",
#   "risk_factors": ["Price in gray area (within 2% of floor)"],
#   ...
# }
```

### 3. Resume with Human Decision
```bash
curl -X POST http://localhost:8000/analyze/resume/$EXEC_ID \
  -H "Content-Type: application/json" \
  -d '{
    "override_decision": "override_approve",
    "notes": "Approved by CFO - acceptable risk given enterprise value"
  }'

# Response:
# {
#   "execution_id": "a1b2c3d4-...",
#   "status": "completed",
#   "final_decision": "approved",
#   "human_decision": "override_approve",
#   "human_notes": "Approved by CFO...",
#   "completed_at": "2024-06-12T10:31:15.987654"
# }
```

---

## 🧪 Test Scenarios

### Scenario 1: Auto-Approved (No HITL)
**Setup:** Price far above floor, standard category
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Standard laptop pricing"}'

# Poll /status → step=5, progress=100%, status=completed
# No pause needed, returns immediately approved
```

### Scenario 2: Gray Area (HITL Triggered)
**Setup:** Price within 2% of margin floor
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "CloudScale Enterprise Tier-2"}'

# Poll /status → status=paused_for_human_review, is_paused=true
# Must call /resume endpoint to continue
```

### Scenario 3: Hard Violation (Auto-Rejected)
**Setup:** Price below margin floor
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Aggressive discount pricing"}'

# Poll /status → step=5, progress=100%, review_status=rejected
# Immediate rejection, no pause
```

---

## 🔍 API Endpoints

| Endpoint | Method | Purpose | Status Codes |
|----------|--------|---------|--------------|
| `/analyze` | POST | Start analysis | 200, 400 |
| `/analyze/status/{id}` | GET | Check status | 200, 404 |
| `/analyze/resume/{id}` | POST | Resume with decision | 200, 400, 404, 500 |
| `/health` | GET | Health check | 200 |
| `/info` | GET | API info | 200 |

---

## 📊 Status Flow

```
POST /analyze
  ↓ (returns immediately)
  Execution started
  ↓
  Client polls GET /status/{id}
  ├─ status: "running" (step 1-4)
  ├─ status: "paused_for_human_review" (step 4, is_paused: true)
  ├─ status: "completed" (step 5)
  └─ status: "error" (failed)

If paused:
  ↓
  POST /analyze/resume/{id}
  ├─ Inject human_decision
  ├─ Resume graph execution
  └─ Return final_decision
```

---

## 🛠️ Customize Triggers

Edit `orchestration/hitl_orchestrator.py` → `PricingValidator` class:

```python
class PricingValidator:
    GRAY_AREA_THRESHOLD = 0.02  # ← Change 2% to something else
    HIGH_VALUE_CATEGORIES = {"Enterprise", "Cloud Services", "Premium"}  # ← Add/remove
    
    @classmethod
    def validate_pricing(cls, report, rag_context, research_data):
        # Add custom validation logic here
        pass
```

---

## 📝 Production Checklist

### Database
- [ ] Replace MemorySaver with PostgresSaver
- [ ] Connection string in environment variable

### Security
- [ ] Add authentication (JWT/OAuth)
- [ ] Restrict CORS origins
- [ ] Add rate limiting
- [ ] Encrypt sensitive state fields

### Monitoring
- [ ] Add Prometheus metrics
- [ ] Log all human decisions
- [ ] Track HITL pause duration
- [ ] Monitor override rate

### Deployment
- [ ] Use Gunicorn + Uvicorn workers
- [ ] Add load balancer (Nginx)
- [ ] Setup health checks
- [ ] Enable auto-restart

---

## ❓ Common Questions

**Q: How long can a workflow stay paused?**
A: Unlimited (state is persisted). Adjust retry/timeout settings as needed.

**Q: What happens if human never responds?**
A: State remains paused. Can implement timeout to auto-reject if needed.

**Q: Can multiple humans review same workflow?**
A: Current design: one decision. Can extend to add approval chains.

**Q: How do I customize gray-area threshold?**
A: Edit `GRAY_AREA_THRESHOLD` in PricingValidator class.

**Q: How do I track human decisions?**
A: Check logs and `human_notes` field in final state.

---

## 🐛 Troubleshooting

### API won't start
```bash
# Check port 8000 is free
lsof -i :8000

# Use different port
uvicorn api.hitl_api:app --port 8001
```

### Graph build fails
```bash
# Check LangGraph installed
pip list | grep langgraph

# Reinstall
pip install --upgrade langgraph
```

### Execution ID not found
```bash
# Workflow may still be starting, wait 1 second
# Or execution_id was wrong in status request
```

### Resume says "not paused"
```bash
# Workflow already completed or auto-approved
# Check /status first to verify is_paused=true
```

---

## 📚 Full Documentation

For complete details, see:
- **HITL_IMPLEMENTATION_GUIDE.md** - Architecture & deployment
- **HITL_SUMMARY.md** - Overview & comparison
- **HITL_CLIENT_EXAMPLE.py** - 5 working examples

---

## ✅ You're All Set!

```
✓ API running on http://localhost:8000
✓ Endpoints ready: /analyze, /status, /resume
✓ HITL working: Gray area detected → paused → resumed with human decision
✓ Test client ready: HITL_CLIENT_EXAMPLE.py

Next: Integrate with your frontend or existing API!
```

---

**MarginGuard HITL — Production Ready in 5 Minutes** 🚀
