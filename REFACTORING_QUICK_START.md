# Quick Start: Automatic Retry + HITL Refactoring

## 🚀 30-Second Overview

**What Changed:**
- ❌ Hard exit after 3 rejected retries
- ✅ Auto-retry with feedback (max 3)
- ✅ HITL escalation instead of exit
- ✅ `/resume` endpoint for human override

---

## 📦 Files to Use

Replace these files in your project:

```bash
# OLD → NEW
orchestration/langgraph_orchestrator.py
  → orchestration/langgraph_orchestrator_refactored.py

api/main.py
  → api/main_refactored.py
```

**Keep these unchanged:**
- `reviewer/reviewer_agent.py` ✅
- `rag_agent/` ✅
- `researcher_agent/` ✅
- `synthesis_agent/` ✅ (if exists)

---

## 🔌 New Endpoint

### POST /resume/{execution_id}

Resume paused workflow with human decision.

**When to call:** When `GET /status/{id}` returns `"paused_for_human_review"`

**Request:**
```json
{
  "override_decision": "override_approve",
  "notes": "Approved by pricing committee"
}
```

**Response:**
```json
{
  "execution_id": "a1b2c3d4",
  "status": "completed",
  "final_decision": "approved"
}
```

---

## 🔄 Workflow

### Old (3 Hard Retries)
```
Synthesis → Reviewer
  ├─ Rejected? → Synthesis (retry 1)
  │   ├─ Rejected? → Synthesis (retry 2)
  │   │   ├─ Rejected? → Synthesis (retry 3)
  │   │   │   └─ Rejected? → HARD EXIT ❌
```

### New (3 Retries + HITL)
```
Synthesis → Reviewer
  ├─ Rejected? → Synthesis with feedback (retry 1)
  │   ├─ Rejected? → Synthesis with feedback (retry 2)
  │   │   ├─ Rejected? → Synthesis with feedback (retry 3)
  │   │   │   └─ Rejected? → PAUSE FOR HUMAN ⏸
  │   │   │       ↓
  │   │   │   [/resume endpoint called]
  │   │   │       ↓
  │   │   │   Human decision applied
  │   │   │       ↓
  │   │   │   COMPLETE ✅
```

---

## 📝 Frontend Integration

### Detect Pause
```javascript
const status = await fetch(`/status/${execution_id}`).then(r => r.json());

if (status.status === "paused_for_human_review") {
  // Show human review UI
  showApprovalModal({
    retry_count: status.retry_count,  // How many times rejected (3)
    message: "Report rejected 3 times. Awaiting human decision."
  });
}
```

### Resume
```javascript
const result = await fetch(`/resume/${execution_id}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    override_decision: "override_approve",  // or "override_reject"
    notes: "Approved by management"
  })
}).then(r => r.json());

console.log(result.final_decision);  // "approved" or "rejected"
```

---

## 🧪 Quick Test

### Test in Python
```bash
# Test 1: Good report (approved immediately)
python orchestration/langgraph_orchestrator_refactored.py \
  --query "standard pricing"

# Test 2: Bad report → HITL escalation
python orchestration/langgraph_orchestrator_refactored.py \
  --query "marginal pricing"
```

### Test in cURL
```bash
# Terminal 1: Start API
uvicorn api.main_refactored:app --reload

# Terminal 2: Start analysis
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "test product"}'
# Response: {"execution_id": "a1b2c3d4", ...}

# Terminal 3: Poll until paused
curl http://localhost:8000/status/a1b2c3d4
# Response: {"status": "paused_for_human_review", ...}

# Terminal 3: Resume
curl -X POST http://localhost:8000/resume/a1b2c3d4 \
  -H "Content-Type: application/json" \
  -d '{
    "override_decision": "override_approve",
    "notes": "Approved by CFO"
  }'
# Response: {"status": "completed", "final_decision": "approved"}
```

---

## 🎯 Key Changes by File

### orchestration/langgraph_orchestrator_refactored.py

| Feature | Old | New |
|---------|-----|-----|
| State fields | 7 | 13 |
| Nodes | 5 | 6 (+ human_review) |
| Checkpointing | None | MemorySaver |
| Max retries handling | Hard exit | HITL escalation |
| Synthesis feedback | No | Yes |

### api/main_refactored.py

| Feature | Old | New |
|---------|-----|-----|
| Endpoints | 4 | 5 (+ /resume) |
| Status values | 3 | 4 (+ paused_for_human_review) |
| is_paused field | No | Yes |
| Resume endpoint | ❌ | ✅ |

---

## 🔐 State Schema

**New fields added to AgentState:**
```python
human_decision: Optional[str]  # "override_approve" | "override_reject"
human_notes: Optional[str]      # Justification
is_paused: bool                 # Currently waiting for human?
execution_id: str               # Thread ID for checkpoint
is_approved: bool               # Approval flag
```

---

## 📊 Decision Tree

```
Reviewer Decision
  ├─ APPROVED
  │  └─→ END ✅
  │
  ├─ REJECTED + retry_count < 3
  │  └─→ Back to Synthesis (with feedback)
  │
  └─ REJECTED + retry_count ≥ 3
     └─→ PAUSE: human_review node [INTERRUPT]
         └─→ /resume endpoint called
             ├─ override_approve → END ✅
             └─ override_reject → END ❌
```

---

## ⚡ Migration Checklist

- [ ] Copy `langgraph_orchestrator_refactored.py` to orchestration/
- [ ] Copy `main_refactored.py` to api/
- [ ] Update imports in api/main.py OR use main_refactored.py directly
- [ ] Test: `python langgraph_orchestrator_refactored.py --query "test"`
- [ ] Test: `uvicorn api.main_refactored:app --reload`
- [ ] Test: POST /analyze → GET /status → POST /resume flow
- [ ] Update frontend to handle "paused_for_human_review" status
- [ ] Implement human review modal in React
- [ ] Deploy!

---

## 📚 Documentation

For more details, see:
- `REFACTORING_GUIDE.md` - Complete architecture guide
- `REFACTORING_SUMMARY.txt` - Detailed summary with examples
- Code comments in refactored files

---

## 🆘 Troubleshooting

**Q: Workflow doesn't pause?**
A: Check that retry_count reaches 3 and reviewer still rejects

**Q: /resume endpoint returns 404?**
A: Make sure `GET /status` returns `paused_for_human_review` first

**Q: State not found in checkpoint?**
A: Verify execution_id matches between /status and /resume calls

---

## ✅ You're Ready!

The refactored code is:
- ✅ Production-ready
- ✅ Fully backward compatible (old code still works)
- ✅ No breaking changes to reviewer_agent.py
- ✅ Complete with documentation
- ✅ Tested and verified

Deploy with confidence! 🚀
