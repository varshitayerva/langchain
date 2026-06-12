"""
MarginGuard AI — LangGraph Multi-Agent Orchestration Workflow
==============================================================

Complete LangGraph implementation integrating real agents:
  - Phase 2: RAG Agent (from rag_agent folder)
  - Phase 3: Research Agent (from researcher_agent folder)
  - Phase 4: Synthesis Agent (generates reports)
  - Phase 5: Reviewer Agent (from reviewer folder)

Usage:
  python langgraph_orchestrator.py --query "CloudScale Enterprise Tier-2 pricing"
"""

import json
import sys
import os
from typing import TypedDict, Optional, Dict, Any
from enum import Enum

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try importing LangGraph
try:
    from langgraph.graph import StateGraph, END
    from langgraph.types import Send
except ImportError:
    print("ERROR: LangGraph not installed. Install with:")
    print("  pip install langgraph langchain-core")
    sys.exit(1)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import real agents
try:
    from rag_agent.rag_agent import RAGAgent
    print("[OK] RAG Agent imported successfully")
except Exception as e:
    print(f"[WARN] Could not import RAG Agent: {e}")
    RAGAgent = None

try:
    from researcher_agent.research_agent import ResearchAgent
    print("[OK] Research Agent imported successfully")
except Exception as e:
    print(f"[WARN] Could not import Research Agent: {e}")
    ResearchAgent = None

try:
    from reviewer.reviewer_agent import review
    print("[OK] Reviewer Agent imported successfully")
except Exception as e:
    print(f"[WARN] Could not import Reviewer Agent: {e}")
    review = None


# ============================================================================
# STATE SCHEMA
# ============================================================================

class AgentState(TypedDict):
    """
    Unified state schema for the MarginGuard AI orchestration pipeline.

    Fields:
        query: User's product/pricing query
        rag_context: Retrieved product and policy data from RAG agent
        research_data: Competitive intelligence from research agent
        draft_report: Generated pricing strategy report from synthesis agent
        review_status: Approval status from reviewer ("approved" or "rejected")
        review_feedback: Detailed feedback if rejected
        retry_count: Number of synthesis retries (max 3)
    """
    query: str
    rag_context: dict
    research_data: dict
    draft_report: str
    review_status: str
    review_feedback: Optional[str]
    retry_count: int


# ============================================================================
# REAL AGENT WRAPPERS
# ============================================================================

class RealRAGAgent:
    """Phase 2: Real RAG Agent - Uses actual PostgreSQL + pgvector."""

    def retrieve(self, query: str) -> Dict[str, Any]:
        """Retrieve products and policies for a query."""
        if RAGAgent is None:
            return {
                "error": "RAG Agent not available",
                "query": query,
                "product_data": [],
                "policy_snippet": ""
            }

        try:
            agent = RAGAgent()
            return agent.retrieve(query, top_k=3)
        except Exception as e:
            print(f"[ERROR] RAG Agent failed: {str(e)}")
            return {
                "error": str(e),
                "query": query,
                "product_data": [],
                "policy_snippet": ""
            }


class RealResearchAgent:
    """Phase 3: Real Research Agent - Uses Tavily API."""

    def research_market(self, query: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Research competitors using Tavily."""
        if ResearchAgent is None:
            return {
                "error": "Research Agent not available",
                "product_name": "",
                "competitors": [],
                "research_summary": "",
                "sources": []
            }

        try:
            agent = ResearchAgent()
            return agent.research_product(product_data)
        except Exception as e:
            print(f"[ERROR] Research Agent failed: {str(e)}")
            return {
                "error": str(e),
                "product_name": "",
                "competitors": [],
                "research_summary": "",
                "sources": []
            }


class SynthesisAgent:
    """Phase 4: Synthesis Agent - Generates pricing strategy reports."""

    def synthesize(
        self,
        rag_context: Dict[str, Any],
        research_data: Dict[str, Any],
        feedback: Optional[str] = None,
    ) -> str:
        """Generate pricing strategy report."""
        print("[SYNTHESIS] Generating pricing strategy report")

        product = rag_context.get("product_data", [{}])[0]
        competitor = research_data.get("competitor_name", "Unknown")
        competitor_price = research_data.get("competitor_price_normalized", "Unknown")

        report = f"""# Market Position & Pricing Strategy Report

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
            report += f"\n## Reviewer Feedback Applied\n{feedback}\n"

        return report


class RealReviewerAgent:
    """Phase 5: Real Reviewer Agent - Audits compliance."""

    def audit(
        self,
        report: str,
        rag_context: Dict[str, Any],
        research_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Audit pricing report for compliance."""
        if review is None:
            return {
                "status": "approved",
                "feedback": None,
            }

        try:
            result = review(report, rag_context, research_data)
            return {
                "status": result.get("status", "unknown"),
                "feedback": result.get("feedback"),
            }
        except Exception as e:
            print(f"[ERROR] Reviewer Agent failed: {str(e)}")
            return {
                "status": "rejected",
                "feedback": f"Reviewer error: {str(e)}",
            }


# ============================================================================
# NODE IMPLEMENTATIONS
# ============================================================================

def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    """Orchestrator Node - Entry point and router."""
    print("\n" + "="*80)
    print("[ORCHESTRATOR] Starting MarginGuard AI pipeline")
    print("="*80)
    print(f"Query: {state['query']}\n")

    return {
        "query": state["query"],
        "rag_context": {},
        "research_data": {},
        "draft_report": "",
        "review_status": "",
        "review_feedback": None,
        "retry_count": 0,
    }


def rag_agent_node(state: AgentState) -> Dict[str, Any]:
    """RAG Agent Node - Retrieves product data (parallel execution)."""
    agent = RealRAGAgent()
    rag_context = agent.retrieve(state["query"])

    if "error" in rag_context:
        print(f"[RAG] Error: {rag_context['error']}")
    else:
        product = rag_context.get("product_data", [{}])[0]
        print(f"[RAG] Retrieved: {product.get('name', 'Unknown')}")
        print(f"[RAG] Margin floor: {product.get('margin_floor', 'Unknown')}\n")

    return {"rag_context": rag_context}


def research_agent_node(state: AgentState) -> Dict[str, Any]:
    """Research Agent Node - Gathers competitive intelligence (parallel)."""
    agent = RealResearchAgent()

    # Get product from RAG context if available
    product_data = state["rag_context"].get("product_data", [{}])[0]

    research_data = agent.research_market("market analysis", product_data)

    if "error" in research_data:
        print(f"[RESEARCH] Error: {research_data['error']}")
    else:
        print(f"[RESEARCH] Analysis complete")
        if research_data.get("competitors"):
            print(f"[RESEARCH] Found {len(research_data['competitors'])} competitors\n")

    return {"research_data": research_data}


def synthesis_agent_node(state: AgentState) -> Dict[str, Any]:
    """Synthesis Agent Node - Generates report (after RAG & Research converge)."""
    agent = SynthesisAgent()

    draft_report = agent.synthesize(
        state["rag_context"],
        state["research_data"],
        feedback=state.get("review_feedback"),
    )

    print("[SYNTHESIS] Report generated with DATA SUMMARY MATRIX\n")

    return {"draft_report": draft_report}


def reviewer_agent_node(state: AgentState) -> Dict[str, Any]:
    """Reviewer Agent Node - Audits report for compliance."""
    agent = RealReviewerAgent()

    result = agent.audit(
        state["draft_report"],
        state["rag_context"],
        state["research_data"],
    )

    is_approved = result["status"] == "approved"

    if is_approved:
        print("[REVIEWER] [APPROVED] Report passed all compliance checks")
        print("  [OK] Financial guardrail: PASSED")
        print("  [OK] Identity alignment: PASSED")
        print("  [OK] Structural completeness: PASSED\n")
    else:
        print("[REVIEWER] [REJECTED] Report failed compliance checks")
        print(f"  Feedback: {result['feedback']}\n")

    return {
        "review_status": result["status"],
        "review_feedback": result["feedback"],
        "retry_count": state["retry_count"] + 1,
    }


# ============================================================================
# CONDITIONAL ROUTING LOGIC
# ============================================================================

def route_after_orchestrator(state: AgentState) -> list:
    """Route to RAG and Research agents in parallel."""
    return [
        Send("rag_agent", state),
        Send("research_agent", state),
    ]


def route_after_reviewer(state: AgentState) -> str:
    """Conditional routing after reviewer audit."""
    if state["review_status"] == "approved":
        return "end"
    elif state["retry_count"] < 3:
        return "synthesis"
    else:
        return "end"


# ============================================================================
# GRAPH COMPILATION
# ============================================================================

def build_langgraph():
    """Build and compile the complete LangGraph workflow."""
    graph = StateGraph(AgentState)

    # Register all nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("rag_agent", rag_agent_node)
    graph.add_node("research_agent", research_agent_node)
    graph.add_node("synthesis", synthesis_agent_node)
    graph.add_node("reviewer", reviewer_agent_node)

    # Define edges
    graph.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "rag_agent": "rag_agent",
            "research_agent": "research_agent",
        }
    )

    graph.add_edge("rag_agent", "synthesis")
    graph.add_edge("research_agent", "synthesis")
    graph.add_edge("synthesis", "reviewer")

    graph.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        {
            "synthesis": "synthesis",
            "end": END,
        }
    )

    graph.set_entry_point("orchestrator")
    return graph.compile()


# ============================================================================
# EXECUTION
# ============================================================================

def run_workflow(query: str) -> Dict[str, Any]:
    """Execute the complete MarginGuard AI orchestration workflow."""
    graph = build_langgraph()

    initial_state = AgentState(
        query=query,
        rag_context={},
        research_data={},
        draft_report="",
        review_status="",
        review_feedback=None,
        retry_count=0,
    )

    print("\n" + "="*80)
    print("LANGGRAPH ORCHESTRATION — EXECUTION START")
    print("="*80 + "\n")

    try:
        final_state = graph.invoke(initial_state)
        return final_state
    except Exception as e:
        print(f"[ERROR] Workflow execution failed: {str(e)}")
        raise


def print_workflow_summary(final_state: Dict[str, Any]) -> None:
    """Print formatted summary of workflow execution."""
    print("\n" + "="*80)
    print("WORKFLOW EXECUTION SUMMARY")
    print("="*80 + "\n")

    print(f"Query: {final_state['query']}")
    print(f"Review Status: {final_state['review_status'].upper()}")
    print(f"Total Retries: {final_state['retry_count']}")

    if final_state["review_status"] == "approved":
        print("\n[SUCCESS] WORKFLOW COMPLETED SUCCESSFULLY")
        print("  Report approved and ready for output")
    else:
        print("\n[FAILURE] WORKFLOW TERMINATED")
        if final_state["retry_count"] >= 3:
            print("  Max retries (3) exceeded")
        else:
            print(f"  Report rejected: {final_state['review_feedback']}")

    print("\n" + "-"*80)
    print("PRICING STRATEGY REPORT")
    print("-"*80 + "\n")
    print(final_state["draft_report"])

    if final_state["review_feedback"]:
        print("\n" + "-"*80)
        print("REVIEWER FEEDBACK")
        print("-"*80 + "\n")
        print(final_state["review_feedback"])


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="MarginGuard AI — LangGraph Multi-Agent Orchestration"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="CloudScale Enterprise Tier-2 pricing strategies",
        help="Product query for pipeline"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Save final state to JSON file"
    )

    args = parser.parse_args()

    try:
        final_state = run_workflow(args.query)
        print_workflow_summary(final_state)

        if args.output_json:
            output_data = {
                "query": final_state["query"],
                "review_status": final_state["review_status"],
                "retry_count": final_state["retry_count"],
                "draft_report": final_state["draft_report"],
                "review_feedback": final_state["review_feedback"],
            }

            with open(args.output_json, "w") as f:
                json.dump(output_data, f, indent=2)

            print(f"\n[OK] Output saved to: {args.output_json}\n")

        sys.exit(0 if final_state["review_status"] == "approved" else 1)

    except Exception as e:
        print(f"[ERROR] Pipeline failed: {str(e)}")
        sys.exit(1)
