# Human-in-the-Loop (HITL) Implementation Guide
## MarginGuard AI — Production-Grade Compliance Review Pattern

---

## 1. Overview

This guide covers the complete implementation of a **Human-in-the-Loop (HITL)** pattern integrated into MarginGuard's multi-agent pricing analysis pipeline using **LangGraph** and **FastAPI**.

### What is HITL?

Human-in-the-Loop is an operational pattern where AI systems automatically pause execution when they encounter high-risk decisions that require human judgment. Instead of making a final decision autonomously, the system:

1. **Detects** high-risk conditions (gray-area pricing, high-value products)
2. **Pauses** execution and checkpoints state
3. **Waits** for human review
4. **Accepts** human override decision
5. **Resumes** execution with human input applied

### Why HITL for Pricing?

Pricing decisions carry business risk:
- **Gray-area pricing** (within 2% of margin floor) is compliant but risky
- **High-value products** (Enterprise, Cloud) warrant management review
- **Automated decisions alone** can't capture context and stakeholder consensus

HITL bridges this gap: **Automation + Human Judgment = Optimal Risk Management**

---

## 2. Architecture Overview

### 2.1 System Flow

```
User Query
    ↓
┌─────────────────────────────────┐
│ FastAPI: POST /analyze          │
│ ├─ Validate request             │
│ └─ Return execution_id          │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│ Background Task (LangGraph)     │
│ ├─ Orchestrator Node            │
│ ├─ RAG Agent (parallel)         │
│ ├─ Research Agent (parallel)    │
│ ├─ Synthesis Agent              │
│ └─ Reviewer Agent               │
└────────────┬────────────────────┘
             ↓
        Review Status?
             │
    ┌────────┼────────┐
    ↓        ↓        ↓
APPROVED REJECTED REQUIRES_HUMAN_REVIEW
    ↓        ↓        ↓
   FINAL    FINAL  [INTERRUPT_BEFORE]
  (END)     (END)    (PAUSED)
                        ↓
            ┌───────────────────┐
            │ Client polls:      │
            │ GET /status/{id}   │
            │ response:          │
            │ paused_for_review  │
            └─────────┬──────────┘
                      ↓
            ┌───────────────────┐
            │ Human Reviews     │
            │ & Decides:        │
            │ POST /resume/{id} │
            │ + decision        │
            └─────────┬──────────┘
                      ↓
        ┌─────────────────────────┐
        │ Graph Resumes:          │
        │ Human Review Node       │
        │ ↓                       │
        │ Final Decision Node     │
        │ (apply override)        │
        │ ↓                       │
        │ END with human decision │
        └─────────────────────────┘
```

### 2.2 State Machine

```
State Transitions:

START
  ↓
RUNNING (Orchestrator, RAG, Research, Synthesis, Reviewer executing)
  ├─→ review_status: "approved" → FINAL_DECISION → COMPLETED
  ├─→ review_status: "rejected" → FINAL_DECISION → COMPLETED
  └─→ review_status: "requires_human_review" → [INTERRUPT_BEFORE] → PAUSED
       ├─ is_paused: true
       ├─ Checkpoint saved to MemorySaver
       └─ Awaiting human_decision via API
            ↓
       HUMAN_REVIEW (after /resume endpoint)
       ├─ human_decision injected
       ├─ is_paused: false
       └─ FINAL_DECISION (apply override)
           ├─ review_status = human_decision (if override_approve/reject)
           └─ COMPLETED
```

---

## 3. Code Architecture

### 3.1 Files Created

```
orchestration/
├── hitl_orchestrator.py      # LangGraph definition + HITL logic
└── README.md

api/
├── hitl_api.py               # FastAPI endpoints for HITL
└── README.md
```

### 3.2 Key Components

#### **orchestration/hitl_orchestrator.py**

| Component | Purpose |
|-----------|---------|
| `AgentState` | Extended TypedDict with HITL fields |
| `PricingValidator` | Detects HITL triggers (gray area, high-value) |
| `*_node()` functions | LangGraph node implementations |
| `build_hitl_graph()` | Compiles StateGraph with interrupts |
| `run_workflow()` | Executes workflow, returns immediately if paused |
| `resume_workflow()` | Resumes paused workflow with human decision |
| `get_workflow_status()` | Fetches current execution state |

#### **api/hitl_api.py**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/analyze` | POST | Start analysis, return execution_id |
| `/analyze/status/{id}` | GET | Check status, detect if paused |
| `/analyze/resume/{id}` | POST | Resume with human decision |
| `/health` | GET | System health check |
| `/info` | GET | API capabilities |

---

## 4. Implementation Details

### 4.1 Extended AgentState

```python
class AgentState(TypedDict):
    # Core pipeline
    query: str
    execution_id: str
    rag_context: Dict[str, Any]
    research_data: Dict[str, Any]
    draft_report: str

    # Compliance
    review_status: str  # "approved" | "rejected" | "requires_human_review"
    review_feedback: Optional[str]
    retry_count: int

    # HITL-specific
    human_decision: Optional[str]  # "override_approve" | "override_reject"
    human_notes: Optional[str]

    # Risk assessment
    risk_factors: List[str]
    gray_area_trigger: bool  # Price within 2% of floor?
    high_value_category: bool  # Enterprise/Cloud product?

    # Execution metadata
    is_paused: bool
    created_at: str
    updated_at: str
```

### 4.2 HITL Trigger Logic

**File:** `orchestration/hitl_orchestrator.py` → `PricingValidator.validate_pricing()`

```python
def validate_pricing(report: str, rag_context: Dict, research_data: Dict) -> Dict:
    """
    Validation Logic:
    
    1. Extract Pricing Data
       ├─ recommended_price (from markdown)
       └─ margin_floor (from RAG)
    
    2. Hard Floor Check
       ├─ If price < floor → REJECTED
       └─ Continue if price >= floor
    
    3. Gray Area Detection
       ├─ gray_area_upper = floor * 1.02 (2% threshold)
       └─ If price in [floor, gray_area_upper] → risk_factor
    
    4. High-Value Category Check
       ├─ Is category "Enterprise", "Cloud", "Premium"?
       └─ If yes → risk_factor
    
    5. HITL Trigger Decision
       └─ If (gray_area OR high_value) → "requires_human_review"
          Otherwise → "approved"
    """
    # Pseudocode
    if price < floor:
        return {"status": "rejected"}
    
    gray_area = (floor <= price < floor * 1.02)
    high_value = product_category in ["Enterprise", "Cloud", "Premium"]
    
    if gray_area or high_value:
        return {"status": "requires_human_review"}
    
    return {"status": "approved"}
```

### 4.3 LangGraph Compilation with Interrupts

**File:** `orchestration/hitl_orchestrator.py` → `build_hitl_graph()`

```python
def build_hitl_graph():
    graph_builder = StateGraph(AgentState)
    
    # Add nodes
    graph_builder.add_node("orchestrator", orchestrator_node)
    graph_builder.add_node("rag_agent", rag_agent_node)
    graph_builder.add_node("research_agent", research_agent_node)
    graph_builder.add_node("synthesis", synthesis_agent_node)
    graph_builder.add_node("reviewer", reviewer_agent_node)
    graph_builder.add_node("human_review", human_review_node)
    graph_builder.add_node("final_decision", final_decision_node)
    
    # Add conditional routing
    graph_builder.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        {
            "human_review": "human_review",      # HITL trigger
            "final_decision": "final_decision"   # Auto-approved/rejected
        }
    )
    
    # CRITICAL: Compile with interrupt_before
    # When state['review_status'] == 'requires_human_review':
    # Graph PAUSES BEFORE executing "human_review" node
    # State is checkpointed to MemorySaver
    graph = graph_builder.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["human_review"]  # ← HITL pause point
    )
    
    return graph
```

**How `interrupt_before` Works:**

1. When workflow reaches `reviewer_agent_node`:
   - If `review_status == "requires_human_review"`
   - Conditional routing returns `"human_review"`

2. Before executing `human_review` node:
   - Graph pauses execution
   - Current state checkpointed to MemorySaver
   - Execution thread remains suspended

3. State remains paused until:
   - FastAPI endpoint `/analyze/resume/{id}` is called
   - Human decision is injected into state
   - Graph resumes from suspension point

### 4.4 FastAPI Integration

#### **Endpoint: POST /analyze**

```python
@app.post("/analyze", response_model=AnalysisResponse)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """
    Initiates analysis in background task.
    Returns immediately (non-blocking).
    """
    # Background task runs workflow
    background_tasks.add_task(execute_workflow, request.query)
    
    return AnalysisResponse(
        execution_id="pending",
        status="started",
        message=f"Analysis started for: {request.query}",
        created_at=datetime.utcnow().isoformat()
    )
```

**Client Flow:**
```javascript
// 1. Start analysis
const response = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "iPhone 15 Pro pricing",
    save_result: true
  })
});
const data = await response.json();
execution_id = data.execution_id; // Save for later

// 2. Poll status every 1-2 seconds
```

#### **Endpoint: GET /analyze/status/{execution_id}**

```python
@app.get("/analyze/status/{execution_id}")
async def check_status(execution_id: str) -> StatusResponse:
    """
    Returns:
    - If running: step=2, progress=50%
    - If paused: step=4, progress=80%, is_paused=true
    - If completed: step=5, progress=100%
    """
    status = get_workflow_status(graph, execution_id)
    
    return StatusResponse(
        execution_id=execution_id,
        status=status["status"],  # "paused_for_human_review" ← HITL trigger
        is_paused=status["is_paused"],
        review_feedback=status["review_feedback"],
        risk_factors=status["risk_factors"]
    )
```

**Client Polling Logic:**
```javascript
async function pollStatus(execution_id) {
  while (true) {
    const response = await fetch(
      `http://localhost:8000/analyze/status/${execution_id}`
    );
    const status = await response.json();
    
    if (status.status === "paused_for_human_review") {
      // Display review UI, wait for human decision
      console.log("Paused for review");
      console.log("Risk factors:", status.risk_factors);
      break;
    }
    
    if (status.status === "completed") {
      // Workflow done
      console.log("Completed");
      break;
    }
    
    // Still running, wait 1 second and poll again
    await new Promise(r => setTimeout(r, 1000));
  }
}
```

#### **Endpoint: POST /analyze/resume/{execution_id}**

```python
@app.post("/analyze/resume/{execution_id}")
async def resume_with_decision(
    execution_id: str,
    request: HumanDecisionRequest
) -> ResumeResponse:
    """
    Resumes paused workflow with human decision.
    
    Request body:
    {
      "override_decision": "override_approve",  // or "override_reject"
      "notes": "Approved per management consensus"
    }
    
    Process:
    1. Fetch paused state from MemorySaver
    2. Inject human_decision + human_notes
    3. Resume graph execution
    4. Return final decision
    """
    # Verify paused
    if not is_paused(execution_id):
        raise HTTPException(400, "Workflow not paused")
    
    # Resume with human input
    result = resume_workflow(
        graph,
        execution_id,
        request.override_decision,
        request.notes
    )
    
    return ResumeResponse(
        execution_id=execution_id,
        status="completed",
        final_decision=result["review_status"],
        human_decision=request.override_decision,
        human_notes=request.notes
    )
```

**Client Usage:**
```javascript
// When human reviews and makes decision
const response = await fetch(
  `http://localhost:8000/analyze/resume/${execution_id}`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      override_decision: "override_approve",
      notes: "Approved by CFO - acceptable margin risk given market conditions"
    })
  }
);
const result = await response.json();
console.log("Final decision:", result.final_decision);
```

---

## 5. Testing & Validation

### 5.1 Test Case 1: Auto-Approved (No HITL)

**Scenario:** Recommended price is $800, margin floor is $600 (33% margin)

```python
# Run
result = run_workflow(graph, "Standard product pricing")

# Expected: status = "completed", review_status = "approved"
assert result["status"] == "completed"
assert result["result"]["review_status"] == "approved"
```

**Why:** Price far above floor, no risk factors → skips HITL

### 5.2 Test Case 2: Gray Area (HITL Triggered)

**Scenario:** Recommended price is $612, margin floor is $600 (2% buffer)

```python
# Run
result = run_workflow(graph, "CloudScale Enterprise pricing")

# Expected: status = "paused_for_human_review", is_paused = true
assert result["status"] == "paused_for_human_review"
assert result["result"]["is_paused"] == True
assert "gray area" in result["result"]["review_feedback"].lower()

# Resume with human approval
resume_result = resume_workflow(
    graph,
    result["execution_id"],
    "override_approve",
    "CFO approved - acceptable risk"
)

# Expected: final decision = "approved"
assert resume_result["result"]["review_status"] == "approved"
```

**Why:** Price in gray area (within 2% of floor) → triggers HITL

### 5.3 Test Case 3: Hard Floor Violation (Auto-Rejected)

**Scenario:** Recommended price is $550, margin floor is $600

```python
# Run
result = run_workflow(graph, "Discounted pricing query")

# Expected: status = "completed", review_status = "rejected"
assert result["status"] == "completed"
assert result["result"]["review_status"] == "rejected"
```

**Why:** Hard floor breach → immediate rejection, no HITL

### 5.4 Test Case 4: High-Value Category (HITL Triggered)

**Scenario:** Enterprise product, even if price well above floor

```python
# Run (product category is "Enterprise")
result = run_workflow(graph, "Enterprise SaaS platform pricing")

# Expected: status = "paused_for_human_review"
assert result["status"] == "paused_for_human_review"
assert result["result"]["high_value_category"] == True
```

**Why:** Enterprise products warrant human review regardless of margin buffer

---

## 6. Production Deployment

### 6.1 Persistence Layer

**Current:** MemorySaver (in-memory) → **Only for development**

**Production:** Use persistent checkpointer:

```python
from langgraph.checkpoint.postgres import PostgresSaver

# Replace MemorySaver
checkpointer = PostgresSaver(
    connection="postgresql://user:password@localhost/langgraph"
)

graph = graph_builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review"]
)
```

### 6.2 Execution Store

**Current:** In-memory dict → **Only for development**

**Production:** Use Redis:

```python
import redis

redis_client = redis.Redis(host="localhost", port=6379, db=0)

# Store execution
def store_execution(execution_id: str, result: Dict):
    redis_client.setex(
        f"exec:{execution_id}",
        ttl=86400,  # 24 hours
        value=json.dumps(result)
    )

# Retrieve execution
def get_execution(execution_id: str):
    data = redis_client.get(f"exec:{execution_id}")
    return json.loads(data) if data else None
```

### 6.3 Deployment Stack

```
┌──────────────────────────────────────────┐
│            Load Balancer (Nginx)         │
└────────────────┬─────────────────────────┘
                 │
     ┌───────────┼───────────┐
     ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ FastAPI │ │ FastAPI │ │ FastAPI │ (multiple instances)
│ Worker1 │ │ Worker2 │ │ Worker3 │
└────┬────┘ └────┬────┘ └────┬────┘
     │           │           │
     └───────────┼───────────┘
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
 ┌─────────────┐     ┌──────────────┐
 │  PostgreSQL │     │    Redis     │
 │ + pgvector  │     │    Cache     │
 │ + LangGraph │     │  + Checkpts  │
 └─────────────┘     └──────────────┘
```

### 6.4 Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "api.hitl_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: langgraph
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/langgraph
      REDIS_URL: redis://redis:6379

volumes:
  postgres_data:
```

---

## 7. Monitoring & Observability

### 7.1 Key Metrics to Track

```python
# Execution metrics
metrics = {
    "total_analyses_started": 150,
    "auto_approved": 102,         # 68% (no human needed)
    "paused_for_review": 35,      # 23% (HITL triggered)
    "auto_rejected": 13,          # 9% (hard violations)
    
    "average_pause_time": 300,    # seconds (5 minutes)
    "human_override_approve": 28, # of 35 paused
    "human_override_reject": 7,   # of 35 paused
    
    "end_to_end_latency": 8.5,   # seconds (with HITL)
    "false_positive_rate": 0.02,  # 2% unnecessary pauses
}
```

### 7.2 Logging Strategy

```python
import logging

logger = logging.getLogger(__name__)

# Log levels in hitl_orchestrator.py
logger.info("[REVIEWER AGENT] Decision: requires_human_review")
logger.info(f"[REVIEWER AGENT] Risk factors: {risk_factors}")

# Log levels in hitl_api.py
logger.info(f"[API] Status check: {execution_id} → paused_for_human_review")
logger.info(f"[API] Resumed with decision: {override_decision}")
```

### 7.3 Dashboard Example (Prometheus + Grafana)

```
Queries:
- rate(analyses_started[5m])
- sum(review_status) by (status)
- histogram_quantile(0.95, end_to_end_latency)
- human_override_rate

Alerts:
- If auto_rejected > 15% (quality issue)
- If avg_pause_time > 600s (bottleneck)
```

---

## 8. Troubleshooting

### Issue: "Paused state not found"

**Cause:** MemorySaver lost state (process restart)

**Fix (Production):** Use PostgresSaver
```python
checkpointer = PostgresSaver(connection_string)
```

### Issue: "Workflow not paused" when calling /resume

**Cause:** Workflow already completed or status check failed

**Fix:**
```python
# Verify in paused state first
status = await check_status(execution_id)
if status.status != "paused_for_human_review":
    raise Exception(f"Cannot resume - status is {status.status}")
```

### Issue: Interrupt not triggering

**Cause:** `gray_area_trigger` or `high_value_category` not set

**Fix:**
```python
# Ensure PricingValidator methods are called
result = PricingValidator.validate_pricing(...)
# This sets: gray_area_trigger, high_value_category
```

### Issue: Human decision not persisting

**Cause:** State not properly checkpointed before resume

**Fix:**
```python
# In resume_workflow, fetch state correctly
paused_state = graph.get_state(
    config={"configurable": {"thread_id": execution_id}}
)
```

---

## 9. Quick Start Guide

### Step 1: Install Dependencies

```bash
pip install langgraph langchain fastapi pydantic
```

### Step 2: Run Orchestrator Test

```bash
python orchestration/hitl_orchestrator.py
```

Expected output:
```
[ORCHESTRATOR] Starting pipeline...
[RAG AGENT] Retrieving product data
[RESEARCH AGENT] Researching competitors
[SYNTHESIS AGENT] Generating report
[REVIEWER AGENT] Decision: requires_human_review
[PAUSED] Workflow awaiting human review...
Risk Factors: ['Price in gray area (within 2% of floor)']

[RESUMING] Applying human override decision...
[HUMAN REVIEW] Decision: override_approve
[FINAL DECISION] APPROVED

Workflow Status: completed
```

### Step 3: Run FastAPI Server

```bash
uvicorn api.hitl_api:app --reload
```

### Step 4: Test via Client

```bash
# 1. Start analysis
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Enterprise pricing", "save_result": true}'

# Save execution_id

# 2. Check status
curl http://localhost:8000/analyze/status/{execution_id}

# 3. If paused, resume
curl -X POST http://localhost:8000/analyze/resume/{execution_id} \
  -H "Content-Type: application/json" \
  -d '{"override_decision": "override_approve", "notes": "Approved by CFO"}'
```

---

## 10. References

- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **Interrupt Pattern:** https://langchain-ai.github.io/langgraph/how-tos/human-in-the-loop/
- **FastAPI:** https://fastapi.tiangolo.com/
- **Pydantic V2:** https://docs.pydantic.dev/

---

**MarginGuard AI — Human-in-the-Loop Implementation** ✅
