# MarginGuard AI — LangGraph Orchestration

Production-ready LangGraph workflow integrating real agents for multi-agent pricing strategy generation.

## Overview

The orchestrator coordinates 5 specialized agents working in parallel and sequence:

1. **RAG Agent** - Retrieves products and policies from PostgreSQL + pgvector
2. **Research Agent** - Gathers competitive intelligence via Tavily API
3. **Synthesis Agent** - Generates pricing strategy reports
4. **Reviewer Agent** - Audits reports for compliance and financial guardrails
5. **Orchestrator** - Coordinates all agents with intelligent routing

**Key Feature:** Automatic retry loop — if a report fails compliance, the system regenerates and re-audits up to 3 times.

## Architecture

### Workflow Graph

```
┌──────────────────┐
│  ORCHESTRATOR    │ ← Initialize
└────────┬─────────┘
         │
    ┌────┴─────────────────────────┐
    ↓                              ↓
┌─────────────┐          ┌──────────────────┐
│ RAG AGENT   │          │ RESEARCH AGENT   │
│ (Parallel)  │          │ (Parallel)       │
│ Products    │          │ Competitors      │
└──────┬──────┘          └────────┬─────────┘
       │                          │
       └──────────┬───────────────┘
                  ↓
        ┌────────────────────┐
        │ SYNTHESIS AGENT    │ ← Converge
        │ Generate Report    │
        └────────┬───────────┘
                 ↓
        ┌────────────────────┐
        │ REVIEWER AGENT     │ ← Audit
        │ Compliance Check   │
        └────────┬───────────┘
                 │
    ┌────────────┼────────────┐
    ↓            ↓            ↓
 APPROVED    REJECTED      MAX RETRIES
   (END)     (RETRY)        (END/FAIL)
```

### State Flow

**TypedDict: AgentState**

```python
query: str                    # User query: "CloudScale Enterprise Tier-2"
rag_context: dict            # {product_data: [...], policy_snippet: "..."}
research_data: dict          # {competitor_name: "...", competitors: [...]}
draft_report: str            # Markdown report with DATA SUMMARY MATRIX
review_status: str           # "approved" or "rejected"
review_feedback: Optional[str]  # Why report was rejected
retry_count: int             # 0-3 attempts
```

## Installation

### 1. Install LangGraph

```bash
pip install langgraph langchain-core
```

### 2. Install Agent Dependencies

```bash
# RAG Agent dependencies
cd ../rag_agent
pip install -r requirements.txt

# Research Agent dependencies
cd ../researcher_agent
pip install -r requirements.txt

# Reviewer Agent dependencies
cd ../reviewer
pip install -r requirements.txt
```

### 3. Setup .env File

Create `.env` in the project root:

```bash
# RAG Agent (PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=fde_langchain

# Research Agent (Tavily)
TAVILY_API_KEY=your_tavily_api_key

# Reviewer Agent (XAI)
XAI_API_KEY=your_xai_api_key
```

## Quick Start

### Basic Execution

```bash
python langgraph_orchestrator.py
```

### Custom Query

```bash
python langgraph_orchestrator.py --query "Affordable smartwatch under $300"
```

### Save Results

```bash
python langgraph_orchestrator.py --output-json results.json
```

## Code Structure

### Main Components

**langgraph_orchestrator.py** contains:

| Component | Purpose |
|-----------|---------|
| `AgentState` | TypedDict schema for state |
| `RealRAGAgent` | Wrapper for RAG agent from `../rag_agent/` |
| `RealResearchAgent` | Wrapper for Research agent from `../researcher_agent/` |
| `SynthesisAgent` | Report generation |
| `RealReviewerAgent` | Wrapper for Reviewer agent from `../reviewer/` |
| `*_node()` functions | Node implementations |
| `route_after_*()` functions | Conditional routing logic |
| `build_langgraph()` | Graph compilation |
| `run_workflow()` | Execution entry point |

### Node Flow

#### 1. Orchestrator Node

```python
def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    """Initialize and route to agents."""
    print("Starting pipeline")
    return {
        "query": state["query"],
        "rag_context": {},
        "research_data": {},
        ...
    }
```

#### 2. RAG Agent Node (Parallel)

```python
def rag_agent_node(state: AgentState) -> Dict[str, Any]:
    """Call real RAG agent."""
    agent = RealRAGAgent()
    rag_context = agent.retrieve(state["query"])
    return {"rag_context": rag_context}
```

#### 3. Research Agent Node (Parallel)

```python
def research_agent_node(state: AgentState) -> Dict[str, Any]:
    """Call real Research agent."""
    agent = RealResearchAgent()
    research_data = agent.research_market(query, product_data)
    return {"research_data": research_data}
```

#### 4. Synthesis Agent Node

```python
def synthesis_agent_node(state: AgentState) -> Dict[str, Any]:
    """Generate pricing report (runs after RAG & Research converge)."""
    agent = SynthesisAgent()
    report = agent.synthesize(state["rag_context"], state["research_data"])
    return {"draft_report": report}
```

#### 5. Reviewer Agent Node

```python
def reviewer_agent_node(state: AgentState) -> Dict[str, Any]:
    """Audit report for compliance."""
    agent = RealReviewerAgent()
    result = agent.audit(state["draft_report"], state["rag_context"], ...)
    return {
        "review_status": result["status"],
        "review_feedback": result["feedback"],
        "retry_count": state["retry_count"] + 1
    }
```

### Routing Logic

#### After Orchestrator

```python
def route_after_orchestrator(state: AgentState) -> list:
    """Dispatch to RAG and Research in parallel."""
    return [
        Send("rag_agent", state),
        Send("research_agent", state),
    ]
```

Returns: List of `Send` objects for concurrent execution

#### After Reviewer

```python
def route_after_reviewer(state: AgentState) -> str:
    """Conditional routing based on compliance audit."""
    if state["review_status"] == "approved":
        return "end"  # Success
    elif state["retry_count"] < 3:
        return "synthesis"  # Retry
    else:
        return "end"  # Max retries exceeded
```

Returns: Node name to route to next

## Usage Examples

### Run Workflow Programmatically

```python
from orchestration.langgraph_orchestrator import run_workflow, print_workflow_summary

# Execute workflow
final_state = run_workflow("CloudScale Enterprise Tier-2 pricing")

# Print results
print_workflow_summary(final_state)

# Access output
report = final_state["draft_report"]
status = final_state["review_status"]
retries = final_state["retry_count"]
```

### Direct Graph Invocation

```python
from orchestration.langgraph_orchestrator import build_langgraph, AgentState

# Build the graph
graph = build_langgraph()

# Create initial state
initial_state = AgentState(
    query="Your query",
    rag_context={},
    research_data={},
    draft_report="",
    review_status="",
    review_feedback=None,
    retry_count=0,
)

# Execute
result = graph.invoke(initial_state)
print(f"Status: {result['review_status']}")
```

### Stream Execution

```python
from orchestration.langgraph_orchestrator import build_langgraph, AgentState

graph = build_langgraph()

state = AgentState(
    query="test",
    rag_context={},
    research_data={},
    draft_report="",
    review_status="",
    review_feedback=None,
    retry_count=0,
)

# Stream updates
for chunk in graph.stream(state):
    print(f"Step: {chunk}")
```

## Execution Scenarios

### Success Path

```
Query → RAG & Research (parallel) → Synthesis → Reviewer
        (all complete in ~2-3 seconds)
        Result: APPROVED → END
```

### Rejection Path (with Retries)

```
Query → RAG & Research → Synthesis → Reviewer → REJECTED
                             ↑         ↓
                             ←────── Retry 1 (retry_count = 1)
                                      ↓
                                   REJECTED
                             ←────── Retry 2 (retry_count = 2)
                                      ↓
                                   APPROVED → END

Total execution: ~4-6 seconds
```

### Max Retries Exceeded

```
Query → RAG & Research → Synthesis → Reviewer → REJECTED
                             ↑         ↓
                             ←────── Retry 1
                                      ↓
                                   REJECTED
                             ←────── Retry 2
                                      ↓
                                   REJECTED
                             ←────── Retry 3
                                      ↓
                                   REJECTED
                                      ↓
                                   MAX RETRIES → END (FAIL)

Total execution: ~8-10 seconds
```

## Real Agent Integration

### RAG Agent

The orchestrator imports and uses the real RAG agent:

```python
from rag_agent.rag_agent import RAGAgent

class RealRAGAgent:
    def retrieve(self, query: str) -> Dict[str, Any]:
        agent = RAGAgent()
        return agent.retrieve(query, top_k=3)
```

**Requires:**
- PostgreSQL with pgvector extension
- `DB_*` environment variables set

### Research Agent

```python
from researcher_agent.research_agent import ResearchAgent

class RealResearchAgent:
    def research_market(self, query: str, product_data: Dict) -> Dict:
        agent = ResearchAgent()
        return agent.research_product(product_data)
```

**Requires:**
- Tavily API key (`TAVILY_API_KEY`)

### Reviewer Agent

```python
from reviewer.reviewer_agent import review

class RealReviewerAgent:
    def audit(self, report: str, rag_context: Dict, research_data: Dict) -> Dict:
        return review(report, rag_context, research_data)
```

**Requires:**
- XAI API key (`XAI_API_KEY`) - falls back to mock if unavailable

## Performance

| Scenario | Time | Notes |
|----------|------|-------|
| Success (1 execution) | ~2-3s | Parallel RAG/Research |
| 1 Rejection + Retry | ~4-5s | Synthesis re-runs once |
| 3 Rejections + Max Retries | ~8-10s | Full retry loop |
| Parallel Speedup | ~1.8-2x | vs sequential execution |

## Error Handling

The orchestrator gracefully handles:

- **Missing RAG Agent:** Falls back to empty product data
- **Missing Research Agent:** Uses empty competitor data
- **Missing Reviewer Agent:** Auto-approves reports
- **API Failures:** Catches and logs errors, continues with fallback data
- **Invalid State:** Handles missing fields with defaults

Example:

```python
try:
    agent = RAGAgent()
    return agent.retrieve(query)
except Exception as e:
    print(f"[ERROR] RAG failed: {e}")
    return {
        "error": str(e),
        "product_data": [],
        "policy_snippet": ""
    }
```

## Testing

Run the workflow with various queries:

```bash
# Test 1: Basic pricing query
python langgraph_orchestrator.py --query "CloudScale Enterprise Tier-2"

# Test 2: Budget-conscious query
python langgraph_orchestrator.py --query "Affordable smartwatch under $300"

# Test 3: Premium product
python langgraph_orchestrator.py --query "Enterprise cloud platform comparison"
```

## Debugging

### Enable Logging

```bash
export PYTHONUNBUFFERED=1
python langgraph_orchestrator.py 2>&1 | tee execution.log
```

### Check Agent Availability

```python
from langgraph_orchestrator import RAGAgent, ResearchAgent, review

print(f"RAG Agent: {RAGAgent is not None}")
print(f"Research Agent: {ResearchAgent is not None}")
print(f"Reviewer: {review is not None}")
```

### Inspect State

```python
def debug_node(state: AgentState) -> Dict:
    print(f"State keys: {state.keys()}")
    print(f"Query: {state['query']}")
    print(f"RAG Context: {state['rag_context']}")
    return state
```

## Troubleshooting

### "LangGraph not installed"

```bash
pip install langgraph langchain-core
```

### "RAG Agent not found"

Ensure RAG agent dependencies are installed:
```bash
cd ../rag_agent && pip install -r requirements.txt
```

### "PostgreSQL connection refused"

Check PostgreSQL is running:
```bash
# macOS/Linux
brew services start postgresql

# Windows
# Start PostgreSQL service from Services
```

### "Tavily API key not found"

Set in `.env`:
```
TAVILY_API_KEY=your_key_here
```

### Workflow hangs

Check if agents are blocking on API calls. Add timeouts:
```python
# In agent wrappers
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Agent call timed out")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30 second timeout
```

## Next Steps

1. **Set up agents** - Install dependencies for RAG, Research, Reviewer
2. **Configure .env** - Add API keys and database credentials
3. **Run tests** - Verify each agent works independently
4. **Execute workflow** - Run the orchestrator
5. **Monitor** - Log and track execution metrics
6. **Deploy** - Wrap in FastAPI for production use

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [StateGraph API](https://langchain-ai.github.io/langgraph/reference/graphs/)
- [Conditional Edges](https://langchain-ai.github.io/langgraph/how-tos/conditional-edge-routing/)
- [Parallel Execution](https://langchain-ai.github.io/langgraph/how-tos/parallelize-steps/)

## License

MIT License

---

**Built with LangGraph, LangChain, and real AI agents** 🚀
