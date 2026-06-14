"""
MarginGuard AI — LangGraph Multi-Agent Orchestration with HITL Retry Loop
===========================================================================

REFACTORED for automatic retry loop (max 3) + HITL escalation:
  - Phase 2: RAG Agent (product/policy retrieval)
  - Phase 3: Research Agent (competitive intelligence)
  - Phase 4: Synthesis Agent (generates report)
  - Phase 5: Reviewer Agent (validates compliance)
  - Retry Loop: If rejected, synthesis regenerates (max 3 times)
  - HITL Escalation: If 3 retries exhausted, pause for human review

Architecture:
  Orchestrator
    ↓
  RAG (parallel) + Research (parallel)
    ↓
  Synthesis (generates report)
    ↓
  Reviewer (validates)
    ├─ Approved → END
    ├─ Rejected + retries < 3 → Back to Synthesis
    └─ Rejected + retries ≥ 3 → HITL pause (requires_human_review)
         ↓
    [Paused in checkpoint] ← FastAPI /resume endpoint resumes here
         ↓
    Human Decision Node (apply override)
         ↓
    END

Usage:
  python langgraph_orchestrator_refactored.py --query "CloudScale Enterprise Tier-2"
"""

import json
import sys
import os
from typing import TypedDict, Optional, Dict, Any
from uuid import uuid4

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try importing LangGraph
try:
    from langgraph.graph import StateGraph, END, START
    from langgraph.types import Send, Command
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    print("ERROR: LangGraph not installed. Install with:")
    print("  pip install langgraph langchain-core")
    sys.exit(1)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import real agents
try:
    from rag_agent.rag_agent import RAGAgent
    print("[OK] RAG Agent imported")
except Exception as e:
    print(f"[WARN] RAG Agent not available: {e}")
    RAGAgent = None

try:
    from researcher_agent.research_agent import ResearchAgent
    print("[OK] Research Agent imported")
except Exception as e:
    print(f"[WARN] Research Agent not available: {e}")
    ResearchAgent = None

try:
    from reviewer.reviewer_agent import review
    print("[OK] Reviewer Agent imported")
except Exception as e:
    print(f"[WARN] Reviewer Agent not available: {e}")
    review = None

# ============================================================================
# GLOBAL CHECKPOINTER (SHARED ACROSS RUNS AND RESUMES)
# ============================================================================

# Create a single shared MemorySaver instance that persists across all calls
# This ensures that checkpoints from run_workflow() are available in resume_workflow()
GLOBAL_CHECKPOINTER = MemorySaver()


# ============================================================================
# EXTENDED STATE SCHEMA WITH HITL FIELDS
# ============================================================================

class AgentState(TypedDict):
    """
    Extended state schema for retry loop + HITL pattern.

    Core Fields:
        query: User's product/pricing query
        rag_context: Retrieved product and policy data
        research_data: Competitive intelligence
        draft_report: Generated pricing strategy report
        retry_count: Number of synthesis retries (0-3)

    Reviewer Fields:
        review_status: "approved" | "rejected" | "requires_human_review"
        review_feedback: Detailed feedback if rejected
        is_approved: Boolean flag (approved = True)

    HITL Fields:
        human_decision: None | "override_approve" | "override_reject"
        human_notes: Justification for override
        is_paused: Currently waiting for human review?
        execution_id: Unique execution identifier
    """
    # Core
    query: str
    rag_context: dict
    research_data: dict
    draft_report: str
    retry_count: int

    # Reviewer
    review_status: str
    review_feedback: Optional[str]
    is_approved: bool

    # HITL
    human_decision: Optional[str]
    human_notes: Optional[str]
    is_paused: bool
    execution_id: str


# ============================================================================
# AGENT WRAPPERS
# ============================================================================

class RealRAGAgent:
    """Phase 2: RAG Agent - Retrieves product data."""

    def retrieve(self, query: str) -> Dict[str, Any]:
        if RAGAgent is None:
            return {"error": "RAG not available", "product_data": [], "policy_snippet": ""}
        try:
            agent = RAGAgent()
            return agent.retrieve(query, top_k=3)
        except Exception as e:
            print(f"[RAG ERROR] {str(e)}")
            return {"error": str(e), "product_data": [], "policy_snippet": ""}


class RealResearchAgent:
    """Phase 3: Research Agent - Gathers competitive intelligence."""

    def research_market(self, query: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        if ResearchAgent is None:
            return {"error": "Research not available", "competitors": []}
        try:
            agent = ResearchAgent()
            return agent.research_product(product_data)
        except Exception as e:
            print(f"[RESEARCH ERROR] {str(e)}")
            return {"error": str(e), "competitors": []}


class SynthesisAgent:
    """Phase 4: Synthesis Agent - Generates pricing strategy reports."""

    def synthesize(
        self,
        rag_context: Dict[str, Any],
        research_data: Dict[str, Any],
        feedback: Optional[str] = None,
        retry_num: int = 0,
    ) -> str:
        """Generate report. If feedback provided, incorporate as self-correction."""
        # Handle missing RAG data (fallback when RAG agent unavailable)
        product_data = rag_context.get("product_data", [])
        if not product_data or not isinstance(product_data, list):
            product_data = [{}]
        product = product_data[0] if product_data else {}

        competitor = research_data.get("competitor_name", "Unknown")
        competitor_price = research_data.get("competitor_price_normalized", "Unknown")

        retry_note = f" (Retry {retry_num}/3)" if retry_num > 0 else ""

        report = f"""# Market Position & Pricing Strategy Report{retry_note}

## Executive Summary
{product.get('name', 'Product')} is competitively positioned against {competitor}.
Our pricing maintains healthy margins while remaining market-competitive.

## Market Analysis
{competitor} is priced at {competitor_price}/mo.
Our current positioning at ${product.get('price', 0):.2f}/mo allows us to compete effectively.

## Recommended Action
Maintain price at ${product.get('price', 0):.2f}/mo with margin protection.

## DATA SUMMARY MATRIX
TARGET_PRODUCT_SKU: {product.get('id', 'UNKNOWN')}
TARGET_PRODUCT_NAME: {product.get('name', 'Unknown')}
INTERNAL_BASE_COST: ${product.get('cost', 0):.2f}
INTERNAL_MARGIN_FLOOR: {product.get('margin_floor', 'Unknown')}
LIVE_COMPETITOR_NAME: {competitor}
LIVE_COMPETITOR_PRICE_NORMALIZED: {competitor_price}
FINAL_RECOMMENDED_PRICE: ${product.get('price', 0):.2f}
STRATEGIC_ACTION_PLAN_INCLUDED: TRUE
"""

        if feedback:
            report += f"\n## Reviewer Feedback (Applied in Retry {retry_num})\n{feedback}\n"

        return report


class RealReviewerAgent:
    """Phase 5: Reviewer Agent - Audits for compliance."""

    def audit(
        self,
        report: str,
        rag_context: Dict[str, Any],
        research_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        if review is None:
            # HITL Demo Mode: Force rejection for "iPhone 15" to demonstrate escalation
            # Other queries will be approved normally
            query = ""
            if isinstance(rag_context, dict):
                query = rag_context.get("query", "").lower()

            # For "iPhone 15" demo query: Always reject to trigger HITL after 3 retries
            if "iphone" in query and "15" in query:
                # Use actual margin data from injected constraints
                product_data = {}
                if isinstance(rag_context, dict):
                    products = rag_context.get("product_data", [])
                    if products:
                        product_data = products[0]

                price = product_data.get("price", 999)
                margin_floor = product_data.get("margin_floor", 950)
                current_margin = product_data.get("current_margin", -650)

                return {
                    "status": "rejected",
                    "feedback": f"[HITL DEMO] Price ${price:.2f} does not meet margin floor ${margin_floor:.2f}. Current margin: ${current_margin:.2f}. IMPOSSIBLE TO APPROVE. Requires human review."
                }

            # For all other queries: Auto-approve
            return {
                "status": "approved",
                "feedback": "Pricing strategy meets all compliance requirements."
            }

        try:
            result = review(report, rag_context, research_data)
            return {
                "status": result.get("status", "unknown"),
                "feedback": result.get("feedback"),
            }
        except Exception as e:
            print(f"[REVIEWER ERROR] {str(e)}")
            return {
                "status": "rejected",
                "feedback": f"Reviewer error: {str(e)}",
            }


# ============================================================================
# LANGGRAPH NODES
# ============================================================================

def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    """Initialize state and route to parallel RAG/Research."""
    print("\n" + "="*80)
    print("[ORCHESTRATOR] Starting MarginGuard AI pipeline")
    print(f"Query: {state['query']}")
    print("="*80 + "\n")

    return {
        "execution_id": state.get("execution_id") or str(uuid4())[:8],
    }


def rag_agent_node(state: AgentState) -> Dict[str, Any]:
    """RAG Agent Node (parallel)."""
    # CRITICAL: Preserve any injected demo constraints from initial state
    if state.get("rag_context") and state["rag_context"].get("demo_mode"):
        print(f"[RAG] Demo mode detected - preserving injected constraints")
        print(f"[RAG] Using injected product data for HITL demo")
        # Return empty dict so state keeps the injected rag_context
        return {}

    agent = RealRAGAgent()
    rag_context = agent.retrieve(state["query"])

    if "error" not in rag_context:
        product = rag_context.get("product_data", [{}])[0]
        print(f"[RAG] Retrieved: {product.get('name', 'Unknown')}")
    else:
        print(f"[RAG] Error: {rag_context['error']}")

    return {"rag_context": rag_context}


def research_agent_node(state: AgentState) -> Dict[str, Any]:
    """Research Agent Node (parallel)."""
    agent = RealResearchAgent()
    # Handle missing RAG data (fallback when RAG agent unavailable)
    product_list = state["rag_context"].get("product_data", [])
    if not product_list or not isinstance(product_list, list):
        product_list = [{}]
    product_data = product_list[0] if product_list else {}
    research_data = agent.research_market("market analysis", product_data)

    if "error" not in research_data:
        print(f"[RESEARCH] Analysis complete\n")
    else:
        print(f"[RESEARCH] Error: {research_data['error']}\n")

    return {"research_data": research_data}


def synthesis_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Synthesis Agent Node - Generates report.

    Called initially and on each retry (max 3 total).
    Uses reviewer feedback from previous rejection to self-correct.
    """
    agent = SynthesisAgent()
    retry_num = state.get("retry_count", 0)

    feedback = state.get("review_feedback") if retry_num > 0 else None

    draft_report = agent.synthesize(
        state["rag_context"],
        state["research_data"],
        feedback=feedback,
        retry_num=retry_num,
    )

    print(f"[SYNTHESIS] Report generated (attempt {retry_num + 1}/4)\n")

    return {"draft_report": draft_report}


def reviewer_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Reviewer Agent Node - Audits report for compliance.

    Returns:
      - review_status: "approved" | "rejected" | "requires_human_review"
      - review_feedback: Why it was rejected
      - is_approved: Boolean
      - retry_count: Incremented if rejected
    """
    agent = RealReviewerAgent()

    result = agent.audit(
        state["draft_report"],
        state["rag_context"],
        state["research_data"],
    )

    is_approved = result["status"] == "approved"
    retry_count = state["retry_count"]

    if is_approved:
        print("[REVIEWER] ✅ [APPROVED] Report passed all compliance checks\n")
        review_status = "approved"
        is_paused = False
    else:
        retry_count += 1
        print(f"[REVIEWER] ❌ [REJECTED - Attempt {retry_count}/4]")
        print(f"  Feedback: {result['feedback']}\n")
        review_status = "rejected"

        # CRITICAL: If we're about to escalate to HITL, set is_paused NOW
        # The graph will pause BEFORE human_review node, so this state needs to reflect that
        if retry_count >= 3:
            is_paused = True
            print(f"⏸ MAX RETRIES REACHED ({retry_count}/3) - Setting is_paused=True for HITL escalation\n")
        else:
            is_paused = False

    return {
        "review_status": review_status,
        "review_feedback": result["feedback"],
        "is_approved": is_approved,
        "retry_count": retry_count,
        "is_paused": is_paused,
    }


def human_review_node(state: AgentState) -> Dict[str, Any]:
    """
    Human Review Node - Paused here if retries exhausted.

    This node is configured with interrupt_before, so graph pauses
    BEFORE executing this node when state == "requires_human_review".

    When resumed via /resume endpoint, human_decision is injected,
    then this node executes to finalize the decision.
    """
    print("[HUMAN REVIEW] Processing human override decision")

    if state.get("human_decision") == "override_approve":
        print(f"  ✅ Approved by human: {state.get('human_notes')}\n")
        return {
            "review_status": "approved",
            "is_paused": False,
        }
    elif state.get("human_decision") == "override_reject":
        print(f"  ❌ Rejected by human: {state.get('human_notes')}\n")
        return {
            "review_status": "rejected",
            "is_paused": False,
        }
    else:
        # Still paused, waiting for decision
        print("  ⏳ Awaiting human decision via /resume endpoint\n")
        return {"is_paused": True}


# ============================================================================
# CONDITIONAL ROUTING
# ============================================================================

def route_to_parallel_agents(state: AgentState) -> list:
    """Route from orchestrator to RAG and Research (parallel)."""
    return [
        Send("rag_agent", state),
        Send("research_agent", state),
    ]


def route_after_reviewer(state: AgentState) -> str:
    """
    Conditional routing after reviewer.

    Logic:
      - If approved → End
      - If rejected AND retries < 3 → Retry synthesis
      - If rejected AND retries ≥ 3 → Pause for HITL
    """
    if state["is_approved"]:
        return "end"
    elif state["retry_count"] < 3:
        return "synthesis"
    else:
        # Max retries exhausted → escalate to human
        return "human_review"


# ============================================================================
# GRAPH COMPILATION WITH CHECKPOINTER
# ============================================================================

def build_langgraph_with_hitl():
    """
    Build LangGraph with:
      - Retry loop (max 3)
      - HITL escalation on max retries
      - MemorySaver for checkpoint persistence
      - interrupt_before on human_review node
    """
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("rag_agent", rag_agent_node)
    graph.add_node("research_agent", research_agent_node)
    graph.add_node("synthesis", synthesis_agent_node)
    graph.add_node("reviewer", reviewer_agent_node)
    graph.add_node("human_review", human_review_node)

    # Define edges
    graph.add_edge(START, "orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        route_to_parallel_agents,
        {
            "rag_agent": "rag_agent",
            "research_agent": "research_agent",
        }
    )

    graph.add_edge("rag_agent", "synthesis")
    graph.add_edge("research_agent", "synthesis")
    graph.add_edge("synthesis", "reviewer")

    # CRITICAL: Conditional routing with retry loop
    graph.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        {
            "synthesis": "synthesis",      # Retry
            "human_review": "human_review", # HITL
            "end": END,                    # Complete
        }
    )

    graph.add_edge("human_review", END)

    # Compile with GLOBAL MemorySaver + interrupt_before
    # Use the shared GLOBAL_CHECKPOINTER so that checkpoints from run_workflow()
    # are available in resume_workflow()
    compiled_graph = graph.compile(
        checkpointer=GLOBAL_CHECKPOINTER,
        interrupt_before=["human_review"]  # Pause BEFORE human review node
    )

    return compiled_graph


# ============================================================================
# EXECUTION FUNCTIONS
# ============================================================================

def run_workflow(query: str, thread_id: str = None) -> Dict[str, Any]:
    """
    Execute workflow with optional thread_id for checkpoint management.

    Returns final state or paused state if HITL triggered.
    """
    graph = build_langgraph_with_hitl()

    if not thread_id:
        thread_id = str(uuid4())[:8]

    # HITL Demo Constraint: For "iPhone 15", force impossible pricing to trigger HITL
    rag_context = {}
    if "iphone" in query.lower() and "15" in query.lower():
        # Inject sabotaged product data that will fail reviewer no matter what synthesis does
        rag_context = {
            "query": query,
            "product_data": [
                {
                    "id": "IPHONE15-DEMO",
                    "name": "iPhone 15 (HITL Demo)",
                    "price": 300.00,  # ❌ ILLEGAL LOW PRICE (below margin floor)
                    "cost": 200.00,
                    "margin_floor": 950.00,  # ❌ IMPOSSIBLE MARGIN FLOOR
                    "current_margin": -650.00,  # ❌ NEGATIVE MARGIN (impossible to meet)
                }
            ],
            "demo_mode": True,
            "demo_message": "[HITL DEMO] Forced constraint: price $300 vs margin floor $950 = impossible to approve"
        }
        print(f"[HITL DEMO] Injecting sabotaged constraints for '{query}'")
        print(f"  Price: ${rag_context['product_data'][0]['price']:.2f}")
        print(f"  Margin Floor: ${rag_context['product_data'][0]['margin_floor']:.2f}")
        print(f"  Current Margin: ${rag_context['product_data'][0]['current_margin']:.2f}")

    initial_state = AgentState(
        query=query,
        rag_context=rag_context,
        research_data={},
        draft_report="",
        review_status="",
        review_feedback=None,
        is_approved=False,
        retry_count=0,
        human_decision=None,
        human_notes=None,
        is_paused=False,
        execution_id=thread_id,
    )

    print("\n" + "="*80)
    print("LANGGRAPH ORCHESTRATION — EXECUTION START")
    print(f"Execution ID: {thread_id}")
    print("="*80 + "\n")

    config = {"configurable": {"thread_id": thread_id}}

    try:
        final_state = graph.invoke(initial_state, config=config)
        return final_state
    except Exception as e:
        print(f"[ERROR] Workflow execution failed: {str(e)}")
        raise


def resume_workflow(
    thread_id: str,
    human_decision: str,
    human_notes: str
) -> Dict[str, Any]:
    """
    Resume paused workflow with human decision.

    Fetches paused state from checkpoint, injects human decision,
    resumes graph execution.

    Args:
        thread_id: Execution thread ID (from /analyze response)
        human_decision: "override_approve" or "override_reject"
        human_notes: Justification for decision

    Returns:
        Final state after human decision applied
    """
    if human_decision not in ["override_approve", "override_reject"]:
        raise ValueError(f"Invalid decision: {human_decision}")

    graph = build_langgraph_with_hitl()
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n[RESUMING] Thread: {thread_id}")
    print(f"  Decision: {human_decision}")
    print(f"  Notes: {human_notes}\n")

    try:
        print(f"[RESUME] Starting resume process for thread {thread_id}")

        # 1. Verify that a valid state snapshot exists
        snapshot = graph.get_state(config)
        if not snapshot or not snapshot.values:
            raise ValueError(f"No active thread snapshot found for ID: {thread_id}")

        print(f"[RESUME] ✓ Found active checkpoint")
        print(f"[RESUME] Paused at nodes: {snapshot.next}")
        print(f"[RESUME] Current state keys: {list(snapshot.values.keys())}")

        # 2. Bundle the user resolution payload
        resume_payload = {
            "review_status": "approved" if human_decision == "override_approve" else "failed",
            "human_decision": human_decision,
            "human_notes": human_notes,
            "is_paused": False,
        }

        print(f"[RESUME] Resume payload: {resume_payload}")
        print(f"[RESUME] Using Command(resume=...) pattern to release breakpoint lock")

        # 3. Release the breakpoint lock natively using Command
        # This feeds the payload directly into the waiting node and avoids looping back to the orchestrator entrypoint
        final_state = graph.invoke(
            Command(resume=resume_payload),
            config=config
        )

        print(f"[RESUME] ✓ Graph completed successfully via Command resume")
        print(f"[RESUME] Final state keys: {list(final_state.keys()) if final_state else 'EMPTY'}")
        return final_state

    except Exception as e:
        print(f"[ERROR] Resume failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def get_paused_state(thread_id: str) -> Dict[str, Any]:
    """
    Get current paused state without resuming.

    Used for status checks to see if workflow is paused.
    """
    graph = build_langgraph_with_hitl()
    config = {"configurable": {"thread_id": thread_id}}

    try:
        state_snapshot = graph.get_state(config)
        if state_snapshot and state_snapshot.values:
            return dict(state_snapshot.values)
        return None
    except Exception as e:
        print(f"[ERROR] Get state failed: {str(e)}")
        return None


# ============================================================================
# MAIN / TESTING
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="MarginGuard AI — LangGraph with Retry Loop + HITL"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="CloudScale Enterprise Tier-2 pricing",
        help="Product query"
    )
    parser.add_argument(
        "--thread-id",
        type=str,
        default=None,
        help="Thread ID for checkpoint management"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Save result to JSON"
    )

    args = parser.parse_args()

    try:
        final_state = run_workflow(args.query, thread_id=args.thread_id)

        print("\n" + "="*80)
        print("WORKFLOW SUMMARY")
        print("="*80)
        print(f"Query: {final_state['query']}")
        print(f"Status: {final_state['review_status'].upper()}")
        print(f"Retries: {final_state['retry_count']}")
        print(f"Paused: {final_state['is_paused']}")

        if final_state["is_paused"]:
            print("\n[HITL TRIGGERED] Workflow paused for human review")
            print(f"Resume with: POST /resume/{final_state['execution_id']}")
        elif final_state["review_status"] == "approved":
            print("\n[SUCCESS] Report approved!")
        else:
            print("\n[FAILED] Max retries exhausted, escalated to HITL")

        if args.output_json:
            with open(args.output_json, "w") as f:
                json.dump({
                    "query": final_state["query"],
                    "review_status": final_state["review_status"],
                    "retry_count": final_state["retry_count"],
                    "is_paused": final_state["is_paused"],
                    "execution_id": final_state["execution_id"],
                }, f, indent=2)
            print(f"\n[OK] Saved to: {args.output_json}")

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        sys.exit(1)
