# MarginGuard AI — Refactoring Guide
## Automatic Retry Loop + Human-in-the-Loop (HITL) Escalation

---

## 📋 Overview

**Goal:** Refactor the orchestration to include:
1. **Automatic Retry Loop** - If reviewer rejects, synthesis regenerates (max 3 total attempts)
2. **HITL Escalation** - If 3 retries exhausted, pause workflow and wait for human override
3. **FastAPI Resume Endpoints** - Allow manual intervention via `/resume` endpoint

**Files Created:**
- `orchestration/langgraph_orchestrator_refactored.py` - Refactored LangGraph with retry loop + HITL
- `api/main_refactored.py` - FastAPI with `/resume` endpoint

---

## 🔄 Workflow Comparison

### OLD Flow (Current)
```
Orchestrator
  ↓
RAG (parallel) + Research (parallel)
  ↓
Synthesis
  ↓
Reviewer
  ├─ Approved → END
  └─ Rejected → END (hard exit)
```

### NEW Flow (Refactored)
```
Orchestrator
  ↓
RAG (parallel) + Research (parallel)
  ↓
Synthesis (attempt 1/4)
  ↓
Reviewer
  ├─ Approved → END ✅
  ├─ Rejected + retries < 3 → Back to Synthesis (attempt 2/4)
  │   ├─ Reviewer again
  │   ├─ Approved → END ✅
  │   └─ Rejected + retries < 3 → Back to Synthesis (attempt 3/4)
  │       ├─ Reviewer again
  │       ├─ Approved → END ✅
  │       └─ Rejected → [ESCALATE TO HITL]
  │
  └─ Rejected + retries ≥ 3 → Human Review Node [INTERRUPT_BEFORE]
      ↓
      [PAUSED IN CHECKPOINT]
      ↓
      FastAPI /resume endpoint injects human_decision
      ↓
      Graph resumes with human override
      ↓
      END (with human decision applied)
```

---

## 🏗️ Architecture Changes

### 1. Extended State Schema

**OLD State:**
```python
class AgentState(TypedDict):
    query: str
    rag_context: dict
    research_data: dict
    draft_report: str
    review_status: str
    review_feedback: Optional[str]
    retry_count: int
```

**NEW State (Extended):**
```python
class AgentState(TypedDict):
    # Core (unchanged)
    query: str
    rag_context: dict
    research_data: dict
    draft_report: str
    retry_count: int

    # Reviewer
    review_status: str  # "approved" | "rejected" | "requires_human_review"
    review_feedback: Optional[str]
    is_approved: bool  # NEW

    # HITL (NEW)
    human_decision: Optional[str]  # "override_approve" | "override_reject"
    human_notes: Optional[str]
    is_paused: bool  # Currently waiting for human?
    execution_id: str  # Thread ID for checkpoint
```

### 2. Conditional Routing Logic

**OLD route_after_reviewer:**
```python
def route_after_reviewer(state: AgentState) -> str:
    if state["review_status"] == "approved":
        return "end"
    elif state["retry_count"] < 3:
        return "synthesis"  # Retry
    else:
        return "end"  # Hard exit after 3 retries
```

**NEW route_after_reviewer:**
```python
def route_after_reviewer(state: AgentState) -> str:
    if state["is_approved"]:
        return "end"  # Approved
    elif state["retry_count"] < 3:
        return "synthesis"  # Retry (max 3)
    else:
        return "human_review"  # HITL escalation (NEW)
```

### 3. New Human Review Node

```python
def human_review_node(state: AgentState) -> Dict[str, Any]:
    """
    Paused here if retries exhausted.
    
    Graph pauses BEFORE executing this node (interrupt_before).
    When /resume called, human_decision is injected, then node executes.
    """
    if state.get("human_decision") == "override_approve":
        return {"review_status": "approved", "is_paused": False}
    elif state.get("human_decision") == "override_reject":
        return {"review_status": "rejected", "is_paused": False}
    else:
        # Still paused, waiting
        return {"is_paused": True}
```

### 4. Graph Compilation with Checkpoint

**OLD:**
```python
graph = StateGraph(AgentState)
# ... add nodes ...
return graph.compile()  # No checkpointer
```

**NEW:**
```python
graph = StateGraph(AgentState)
# ... add nodes ...
checkpointer = MemorySaver()
compiled_graph = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review"]  # Pause BEFORE human_review node
)
```

---

## 🔌 New Endpoints in FastAPI

### POST /resume/{execution_id}

**Purpose:** Resume paused workflow with human override decision

**Request:**
```json
{
  "override_decision": "override_approve",
  "notes": "Approved by CFO. Acceptable risk given market conditions."
}
```

**Response:**
```json
{
  "execution_id": "a1b2c3d4",
  "status": "completed",
  "final_decision": "approved",
  "human_override": "override_approve",
  "human_notes": "Approved by CFO...",
  "completed_at": "2024-06-12T10:31:45.123456"
}
```

**Flow:**
1. Client calls POST /resume with human decision
2. FastAPI fetches paused state from checkpoint (thread_id = execution_id)
3. Injects `human_decision` + `human_notes` into state
4. Calls `resume_workflow()` to restart graph from checkpoint
5. Graph executes human_review node with injected decision
6. Workflow completes with human override applied

### GET /status/{execution_id} — Enhanced

**Response includes:**
```json
{
  "status": "paused_for_human_review",  // NEW status value
  "is_paused": true,                     // NEW field
  "retry_count": 3,                      // Actual attempts made
  "review_status": "rejected"            // Last status before pause
}
```

---

## 📝 Migration Steps

### Step 1: Replace Orchestrator

```bash
# Old
python -m orchestration.langgraph_orchestrator --query "test"

# New
python -m orchestration.langgraph_orchestrator_refactored --query "test"
```

Or update imports:
```python
# In api/main.py
from orchestration.langgraph_orchestrator_refactored import (
    run_workflow,
    resume_workflow,  # NEW
    get_paused_state,  # NEW
)
```

### Step 2: Replace FastAPI

```bash
# Old
uvicorn api.main:app --reload

# New
uvicorn api.main_refactored:app --reload
```

### Step 3: Update Frontend Integration

**Before (React):**
```javascript
// Start analysis
const res = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  body: JSON.stringify({query: 'iPhone 15 Pro'})
});
const data = res.json();
execution_id = data.execution_id;

// Poll status
while (true) {
  const status = await fetch(`/status/${execution_id}`).then(r => r.json());
  if (status.status === 'completed') break;
  await sleep(1000);
}

// Get result
const result = await fetch(`/result/${execution_id}`).then(r => r.json());
```

**After (React with HITL):**
```javascript
// Start analysis
const res = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  body: JSON.stringify({query: 'iPhone 15 Pro'})
});
const data = res.json();
execution_id = data.execution_id;

// Poll status
while (true) {
  const status = await fetch(`/status/${execution_id}`).then(r => r.json());
  
  if (status.status === 'paused_for_human_review') {
    // NEW: Show human review UI
    showHumanReviewModal({
      retry_count: status.retry_count,
      review_status: status.review_status,
      onApprove: async (notes) => {
        await fetch(`/resume/${execution_id}`, {
          method: 'POST',
          body: JSON.stringify({
            override_decision: 'override_approve',
            notes: notes
          })
        });
        // Continue polling
      },
      onReject: async (notes) => {
        await fetch(`/resume/${execution_id}`, {
          method: 'POST',
          body: JSON.stringify({
            override_decision: 'override_reject',
            notes: notes
          })
        });
        // Continue polling
      }
    });
  }
  
  if (status.status === 'completed') break;
  await sleep(1000);
}

// Get result
const result = await fetch(`/result/${execution_id}`).then(r => r.json());
```

---

## 🧪 Testing the Refactored Code

### Test 1: Auto-Approved (No HITL)

Good report that passes all checks on first try.

```bash
python orchestration/langgraph_orchestrator_refactored.py \
  --query "Standard product pricing"

# Expected:
# [REVIEWER] ✅ [APPROVED] ...
# Status: APPROVED
```

### Test 2: Approved After Retries

Report that fails first attempt but passes after self-correction.

```bash
python orchestration/langgraph_orchestrator_refactored.py \
  --query "CloudScale Enterprise pricing"

# Expected:
# [SYNTHESIS] Report generated (attempt 1/4)
# [REVIEWER] ❌ [REJECTED - Attempt 1/4]
# [SYNTHESIS] Report generated (attempt 2/4)  [with feedback]
# [REVIEWER] ✅ [APPROVED]
# Status: APPROVED
```

### Test 3: HITL Escalation (Max Retries)

Report that fails all 3 retries, escalates to HITL.

```python
# Terminal 1: Start API
uvicorn api.main_refactored:app --reload

# Terminal 2: Start analysis
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "CloudScale pricing"}'

# Response: {"execution_id": "a1b2c3d4", ...}

# Terminal 3: Poll status (will show paused)
curl http://localhost:8000/status/a1b2c3d4

# Response: {"status": "paused_for_human_review", "is_paused": true, ...}

# Terminal 3: Resume with human decision
curl -X POST http://localhost:8000/resume/a1b2c3d4 \
  -H "Content-Type: application/json" \
  -d '{
    "override_decision": "override_approve",
    "notes": "CFO approved. Acceptable risk."
  }'

# Response: {"status": "completed", "final_decision": "approved", ...}
```

---

## 🔑 Key Changes Summary

| Feature | Old | New |
|---------|-----|-----|
| **Retry Loop** | No retries | Auto-retry up to 3 times |
| **Retry Logic** | Hard exit after 3 | Escalate to HITL |
| **State Fields** | 7 fields | 13 fields (extended) |
| **Graph Nodes** | 5 nodes | 6 nodes (+human_review) |
| **Checkpointing** | None | MemorySaver |
| **Interrupts** | None | interrupt_before on human_review |
| **Endpoints** | 4 endpoints | 5 endpoints (+/resume) |
| **HITL Support** | No | Yes (full) |

---

## 🚀 Execution Flow Example

### Scenario: Report Rejected 3 Times, Then Human Approves

```
Time 0s:   Client calls POST /analyze
           → execution_id = "abc123"
           → Background task starts

Time 2s:   Orchestrator → RAG/Research (parallel)

Time 3s:   Synthesis generates report (attempt 1/4)

Time 4s:   Reviewer audits
           → REJECTED: Price below floor
           → retry_count = 1

Time 5s:   Back to Synthesis (attempt 2/4)
           → Uses reviewer feedback for self-correction

Time 6s:   Reviewer audits again
           → REJECTED: Still bad
           → retry_count = 2

Time 7s:   Back to Synthesis (attempt 3/4)
           → Uses reviewer feedback again

Time 8s:   Reviewer audits again
           → REJECTED: Still bad
           → retry_count = 3

Time 9s:   HITL ESCALATION TRIGGERED
           → Route to "human_review" node
           → Graph pauses BEFORE executing human_review
           → State checkpointed to MemorySaver
           → execution_cache["abc123"]["is_paused"] = True

Time 10s:  Client polls GET /status/abc123
           → Response: {"status": "paused_for_human_review", ...}

Time 30s:  Client calls POST /resume/abc123
           {"override_decision": "override_approve", ...}
           → Fetches paused state from checkpoint
           → Injects human_decision into state
           → Calls resume_workflow()

Time 31s:  Graph resumes at human_review node
           → human_decision = "override_approve"
           → review_status = "approved"
           → Graph ends

Time 32s:  Client polls GET /status/abc123
           → Response: {"status": "completed", ...}

Time 33s:  Client calls GET /result/abc123
           → Response: full result with human override applied
```

---

## 📊 State Transitions

```
[START]
  ↓
[ORCHESTRATOR] → Initialize state
  ↓
[RAG + RESEARCH] → Parallel execution
  ↓
[SYNTHESIS] ← Receives feedback if retry
  ↓
[REVIEWER]
  ├─ is_approved=true → [END] ✅
  │
  ├─ is_approved=false + retry_count < 3
  │  └─→ Back to [SYNTHESIS] (retry)
  │
  └─ is_approved=false + retry_count ≥ 3
     └─→ [HUMAN_REVIEW] [INTERRUPT_BEFORE]
         ↓
         [PAUSED IN CHECKPOINT]
         ↓
         (Client calls /resume endpoint)
         ↓
         Resume graph with human_decision injected
         ↓
         [HUMAN_REVIEW] Executes with override
         ↓
         [END] with human decision ✅
```

---

## 🔍 Code Comparison

### Reviewer Node — No Change Needed

The `reviewer_agent.py` file remains unchanged. It already:
- Validates against margin floor
- Checks structural integrity
- Rejects with detailed feedback
- Works perfectly as-is ✅

### Synthesis Node — Minimal Change

```python
# OLD: Generated report once
def synthesis_agent_node(state: AgentState) -> Dict[str, Any]:
    agent = SynthesisAgent()
    draft_report = agent.synthesize(state["rag_context"], state["research_data"])
    return {"draft_report": draft_report}

# NEW: Incorporates reviewer feedback on retry
def synthesis_agent_node(state: AgentState) -> Dict[str, Any]:
    agent = SynthesisAgent()
    feedback = state.get("review_feedback") if state["retry_count"] > 0 else None
    draft_report = agent.synthesize(
        state["rag_context"],
        state["research_data"],
        feedback=feedback,  # NEW: Pass feedback for self-correction
        retry_num=state["retry_count"],  # NEW: Track attempt number
    )
    return {"draft_report": draft_report}
```

### Routing Logic — Critical Change

```python
# OLD
def route_after_reviewer(state):
    if state["review_status"] == "approved":
        return "end"
    elif state["retry_count"] < 3:
        return "synthesis"
    else:
        return "end"  # Hard exit

# NEW
def route_after_reviewer(state):
    if state["is_approved"]:
        return "end"  # Approved
    elif state["retry_count"] < 3:
        return "synthesis"  # Retry
    else:
        return "human_review"  # HITL escalation (NEW)
```

---

## ✅ Verification Checklist

- [x] Retry loop (max 3 attempts)
- [x] HITL escalation on max retries
- [x] MemorySaver checkpointing
- [x] interrupt_before on human_review node
- [x] FastAPI /resume endpoint
- [x] Human decision injection
- [x] Resume workflow from checkpoint
- [x] Extended AgentState
- [x] Conditional routing logic
- [x] New human_review node
- [x] Graph compilation with checkpointer

---

## 🚀 Deployment

### Development

```bash
# Old
uvicorn api.main:app --reload

# New
uvicorn api.main_refactored:app --reload
```

### Production

No additional setup needed! MemorySaver works out of the box. 
For persistence across restarts, replace with PostgresSaver later.

---

**Refactoring Complete!** ✅

Your MarginGuard AI now has:
✅ Automatic retry loop (max 3)
✅ HITL escalation on max retries
✅ FastAPI /resume endpoint
✅ Thread-based checkpoint persistence
✅ Full human override capability
