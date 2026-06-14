"""
MarginGuard AI — LangGraph Orchestrator with Human-in-the-Loop (HITL) Pattern
===============================================================================

Implements a production-grade multi-agent pipeline with human compliance review.
Uses LangGraph's native interrupt mechanism to pause execution when high-risk
pricing strategies require human approval.

Architecture:
  1. RAG Agent (parallel)    → Product & policy retrieval
  2. Research Agent (parallel) → Competitive intelligence
  3. Synthesis Agent         → Pricing report generation
  4. Reviewer Agent          → Compliance audit (HITL trigger)
  5. Human Review (interrupt) → Pause & wait for human decision
  6. Final Decision Node     → Resume with human override

Usage:
  from orchestration.hitl_orchestrator import build_hitl_graph, run_workflow

  # Build graph
  graph = build_hitl_graph()

  # Run workflow
  output = run_workflow(graph, "iPhone 15 Pro pricing")

  # If paused: resume with human decision
  output = resume_workflow(graph, execution_id, override_approve=True, notes="...")
"""

import uuid
from typing import Optional, Any, Dict, List
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import MemorySaver

import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 1. STATE DEFINITION - Extended AgentState with HITL Fields
# ============================================================================

class AgentState(TypedDict):
    """
    Extended state dictionary for multi-agent pipeline with HITL support.

    Fields:
        query: User's product query
        execution_id: Unique execution identifier (UUID)
        rag_context: Retrieved product & policy data
        research_data: Competitive intelligence data
        draft_report: Generated pricing strategy report (markdown)
        review_status: "approved" | "rejected" | "requires_human_review"
        review_feedback: Reviewer's compliance feedback
        retry_count: Number of synthesis retries attempted
        human_decision: "override_approve" | "override_reject" | None
        human_notes: Human reviewer's justification notes
        risk_factors: List of identified risk factors
        gray_area_trigger: bool - Price in gray area (within 2% of floor)?
        high_value_category: bool - High-value product requiring review?
        is_paused: bool - Currently paused for human review?
        created_at: ISO-8601 timestamp
        updated_at: ISO-8601 timestamp
    """

    # Core pipeline fields
    query: str
    execution_id: str
    rag_context: Dict[str, Any]
    research_data: Dict[str, Any]
    draft_report: str

    # Reviewer & compliance fields
    review_status: str  # "approved" | "rejected" | "requires_human_review"
    review_feedback: Optional[str]
    retry_count: int

    # HITL fields
    human_decision: Optional[str]  # "override_approve" | "override_reject"
    human_notes: Optional[str]

    # Risk assessment fields
    risk_factors: List[str]
    gray_area_trigger: bool
    high_value_category: bool

    # Execution metadata
    is_paused: bool
    created_at: str
    updated_at: str


# ============================================================================
# 2. PYDANTIC MODELS - Request/Response Schemas
# ============================================================================

class AnalysisRequest(BaseModel):
    """Request to start a new analysis."""
    query: str = Field(..., min_length=1, max_length=500)
    save_result: bool = Field(default=True)


class AnalysisResponse(BaseModel):
    """Response for analysis initiation."""
    execution_id: str
    status: str  # "started" | "paused_for_review" | "completed"
    message: str
    created_at: str


class StatusResponse(BaseModel):
    """Response for status check."""
    execution_id: str
    status: str  # "running" | "paused_for_human_review" | "completed" | "error"
    step: int
    message: str
    progress: float
    is_paused: bool
    review_status: Optional[str] = None
    review_feedback: Optional[str] = None
    risk_factors: List[str] = []
    created_at: str
    updated_at: str


class HumanDecisionRequest(BaseModel):
    """Request to resume with human decision."""
    override_decision: str = Field(
        ...,
        pattern="^(override_approve|override_reject)$",
        description="Human's override decision"
    )
    notes: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Justification for the decision"
    )


class ResumeResponse(BaseModel):
    """Response after resuming with human decision."""
    execution_id: str
    status: str
    final_decision: str
    human_decision: str
    human_notes: str
    completed_at: str


# ============================================================================
# 3. REVIEWER NODE WITH HITL TRIGGER LOGIC
# ============================================================================

class PricingValidator:
    """Validates pricing strategies and determines HITL triggers."""

    GRAY_AREA_THRESHOLD = 0.02  # 2% above margin floor triggers review
    HIGH_VALUE_CATEGORIES = {"Enterprise", "Cloud Services", "Premium"}

    @staticmethod
    def extract_recommended_price(report: str) -> Optional[float]:
        """Extract recommended price from markdown report."""
        import re

        patterns = [
            r"FINAL_RECOMMENDED_PRICE:\s*\$?([\d.]+)",
            r"Recommend.*\$?([\d.]+)",
            r"price.*\$?([\d.]+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, report, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue

        return None

    @staticmethod
    def extract_margin_floor(rag_context: Dict[str, Any]) -> Optional[float]:
        """Extract margin floor from RAG context."""
        try:
            product_data = rag_context.get("product_data", [])
            if not product_data:
                return None

            margin_floor = product_data[0].get("margin_floor")
            if isinstance(margin_floor, str):
                # Remove $ and commas, convert to float
                margin_floor = float(margin_floor.replace("$", "").replace(",", ""))

            return margin_floor
        except (ValueError, IndexError, TypeError) as e:
            logger.warning(f"Failed to extract margin floor: {e}")
            return None

    @staticmethod
    def detect_high_value_category(rag_context: Dict[str, Any]) -> bool:
        """Detect if product is in high-value category."""
        try:
            product_data = rag_context.get("product_data", [])
            if not product_data:
                return False

            category = product_data[0].get("category", "").strip()
            return any(cat in category for cat in PricingValidator.HIGH_VALUE_CATEGORIES)
        except (IndexError, AttributeError):
            return False

    @classmethod
    def validate_pricing(
        cls,
        report: str,
        rag_context: Dict[str, Any],
        research_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate pricing strategy and determine review status.

        Returns:
            {
                "status": "approved" | "rejected" | "requires_human_review",
                "recommended_price": float,
                "margin_floor": float,
                "risk_factors": list,
                "gray_area_trigger": bool,
                "high_value_category": bool,
                "feedback": str
            }
        """
        risk_factors = []

        # Extract prices
        recommended_price = cls.extract_recommended_price(report)
        margin_floor = cls.extract_margin_floor(rag_context)

        # Validation 1: Basic structure
        if not recommended_price or not margin_floor:
            return {
                "status": "rejected",
                "recommended_price": recommended_price,
                "margin_floor": margin_floor,
                "risk_factors": ["Missing pricing data in report"],
                "gray_area_trigger": False,
                "high_value_category": False,
                "feedback": "Failed to extract pricing information from report"
            }

        # Validation 2: Hard floor check
        if recommended_price < margin_floor:
            risk_factors.append(f"Price ${recommended_price:.2f} below floor ${margin_floor:.2f}")
            return {
                "status": "rejected",
                "recommended_price": recommended_price,
                "margin_floor": margin_floor,
                "risk_factors": risk_factors,
                "gray_area_trigger": False,
                "high_value_category": False,
                "feedback": f"COMPLIANCE VIOLATION: Recommended price ${recommended_price:.2f} is below margin floor ${margin_floor:.2f}"
            }

        # Validation 3: Gray area detection (2% above floor)
        gray_area_upper_bound = margin_floor * (1 + cls.GRAY_AREA_THRESHOLD)
        is_gray_area = margin_floor <= recommended_price < gray_area_upper_bound

        if is_gray_area:
            risk_factors.append(f"Price ${recommended_price:.2f} in gray area (within 2% of floor)")

        # Validation 4: High-value category check
        is_high_value = cls.detect_high_value_category(rag_context)
        if is_high_value:
            risk_factors.append("Product in high-value category requiring review")

        # Validation 5: HITL trigger decision
        if is_gray_area or is_high_value:
            return {
                "status": "requires_human_review",
                "recommended_price": recommended_price,
                "margin_floor": margin_floor,
                "risk_factors": risk_factors,
                "gray_area_trigger": is_gray_area,
                "high_value_category": is_high_value,
                "feedback": "HUMAN REVIEW REQUIRED: " + "; ".join(risk_factors) if risk_factors else "Strategy requires human compliance verification"
            }

        # All checks passed
        return {
            "status": "approved",
            "recommended_price": recommended_price,
            "margin_floor": margin_floor,
            "risk_factors": risk_factors,
            "gray_area_trigger": False,
            "high_value_category": False,
            "feedback": f"COMPLIANT: Price ${recommended_price:.2f} maintains healthy margin above floor ${margin_floor:.2f}"
        }


# ============================================================================
# 4. LANGGRAPH NODES
# ============================================================================

def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    """Initialize execution and route to RAG & Research agents (parallel)."""
    logger.info(f"[ORCHESTRATOR] Starting pipeline for query: {state['query']}")

    return {
        "execution_id": state.get("execution_id") or str(uuid.uuid4()),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


def route_to_parallel_agents(state: AgentState) -> List[Send]:
    """Route to RAG and Research agents in parallel."""
    logger.info(f"[ROUTING] Sending to RAG and Research agents in parallel")

    return [
        Send("rag_agent", state),
        Send("research_agent", state),
    ]


def rag_agent_node(state: AgentState) -> Dict[str, Any]:
    """RAG Agent: Retrieve product and policy data."""
    logger.info("[RAG AGENT] Retrieving product and policy data")

    # Mock implementation - replace with real RAG agent
    rag_context = {
        "query": state["query"],
        "product_data": [
            {
                "id": "PROD-001",
                "name": state["query"],
                "category": "Enterprise",
                "price": 999.00,
                "cost": 600.00,
                "margin_floor": "$750.00",
                "features": "Advanced analytics, 99.9% SLA, auto-scaling",
                "similarity": 0.95
            }
        ],
        "policy_snippet": "All pricing must maintain margin floor for profitability."
    }

    logger.info(f"[RAG AGENT] Retrieved product: {rag_context['product_data'][0]['name']}")
    return {"rag_context": rag_context}


def research_agent_node(state: AgentState) -> Dict[str, Any]:
    """Research Agent: Gather competitive intelligence."""
    logger.info("[RESEARCH AGENT] Researching competitive landscape")

    # Mock implementation - replace with real research agent
    research_data = {
        "competitor_name": "CompetitorX",
        "competitor_price": 950.00,
        "features_found": ["Analytics", "SLA", "Scaling"],
        "sources": ["https://example.com/pricing"]
    }

    logger.info(f"[RESEARCH AGENT] Found competitor: {research_data['competitor_name']} @ ${research_data['competitor_price']}")
    return {"research_data": research_data}


def synthesis_agent_node(state: AgentState) -> Dict[str, Any]:
    """Synthesis Agent: Generate pricing strategy report."""
    logger.info("[SYNTHESIS AGENT] Generating pricing strategy report")

    product = state["rag_context"]["product_data"][0]
    competitor = state["research_data"]

    # Generate report
    report = f"""# Pricing Strategy Report

## Executive Summary
{product['name']} is competitively positioned.

## Market Analysis
Competitor {competitor['competitor_name']} is priced at ${competitor['competitor_price']:.2f}.

## Recommended Action
Maintain price at ${product['price']:.2f}/mo.

## DATA SUMMARY MATRIX
TARGET_PRODUCT_SKU: {product['id']}
TARGET_PRODUCT_NAME: {product['name']}
INTERNAL_BASE_COST: ${product['cost']:.2f}
INTERNAL_MARGIN_FLOOR: {product['margin_floor']}
LIVE_COMPETITOR_NAME: {competitor['competitor_name']}
LIVE_COMPETITOR_PRICE_NORMALIZED: ${competitor['competitor_price']:.2f}
FINAL_RECOMMENDED_PRICE: ${product['price']:.2f}
STRATEGIC_ACTION_PLAN_INCLUDED: TRUE
"""

    logger.info("[SYNTHESIS AGENT] Report generated")
    return {"draft_report": report}


def reviewer_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Reviewer Agent: Validate pricing against compliance rules.

    CRITICAL: This node evaluates HITL triggers:
    - Gray area: Price within 2% of margin floor
    - High-value: Enterprise products requiring review

    Returns status: "approved" | "rejected" | "requires_human_review"
    """
    logger.info("[REVIEWER AGENT] Auditing pricing compliance")

    result = PricingValidator.validate_pricing(
        state["draft_report"],
        state["rag_context"],
        state["research_data"]
    )

    logger.info(f"[REVIEWER AGENT] Decision: {result['status']}")
    if result['risk_factors']:
        logger.info(f"[REVIEWER AGENT] Risk factors: {', '.join(result['risk_factors'])}")

    return {
        "review_status": result["status"],
        "review_feedback": result["feedback"],
        "risk_factors": result["risk_factors"],
        "gray_area_trigger": result["gray_area_trigger"],
        "high_value_category": result["high_value_category"],
    }


def human_review_node(state: AgentState) -> Dict[str, Any]:
    """
    Human Review Node: Pauses graph execution to wait for human decision.

    NOTE: This node is configured with interrupt_before in the graph.
    When state['review_status'] == 'requires_human_review',
    the graph pauses BEFORE executing this node and checkpoints state.

    When resumed via FastAPI endpoint, the human's decision is injected
    into state and this node executes to finalize.
    """
    logger.info("[HUMAN REVIEW] Processing human decision")

    if not state.get("human_decision"):
        logger.warning("[HUMAN REVIEW] No human decision provided - maintaining pending state")
        return {"is_paused": True}

    logger.info(f"[HUMAN REVIEW] Decision: {state['human_decision']}")
    logger.info(f"[HUMAN REVIEW] Notes: {state['human_notes']}")

    return {
        "is_paused": False,
        "updated_at": datetime.utcnow().isoformat()
    }


def final_decision_node(state: AgentState) -> Dict[str, Any]:
    """Final Decision Node: Apply human override if present."""
    logger.info("[FINAL DECISION] Finalizing pricing approval")

    final_status = state["review_status"]

    # Apply human override if present
    if state.get("human_decision") == "override_approve":
        final_status = "approved"
        logger.info("[FINAL DECISION] Applied human override - APPROVED")
    elif state.get("human_decision") == "override_reject":
        final_status = "rejected"
        logger.info("[FINAL DECISION] Applied human override - REJECTED")

    return {
        "review_status": final_status,
        "updated_at": datetime.utcnow().isoformat()
    }


def route_after_reviewer(state: AgentState) -> str:
    """
    Conditional routing after reviewer agent.

    Returns:
        "human_review" if requires_human_review (triggers interrupt)
        "final_decision" if approved or rejected
    """
    if state["review_status"] == "requires_human_review":
        return "human_review"
    else:
        return "final_decision"


# ============================================================================
# 5. LANGGRAPH CONSTRUCTION
# ============================================================================

def build_hitl_graph():
    """
    Build LangGraph StateGraph with HITL interrupt pattern.

    Graph Structure:
        START
          ↓
        Orchestrator
          ↓
        ┌─ RAG Agent (parallel)
        ├─ Research Agent (parallel)
          ↓
        Synthesis
          ↓
        Reviewer ──→ [Conditional Routing]
                     ├→ Human Review [INTERRUPT_BEFORE]
                     │   ↓
                     │   (Resume via FastAPI)
                     │   ↓
                     └─→ Final Decision
                        ↓
                       END
    """
    logger.info("Building LangGraph with HITL pattern")

    # Initialize graph
    graph_builder = StateGraph(AgentState)

    # Add nodes
    graph_builder.add_node("orchestrator", orchestrator_node)
    graph_builder.add_node("rag_agent", rag_agent_node)
    graph_builder.add_node("research_agent", research_agent_node)
    graph_builder.add_node("synthesis", synthesis_agent_node)
    graph_builder.add_node("reviewer", reviewer_agent_node)
    graph_builder.add_node("human_review", human_review_node)
    graph_builder.add_node("final_decision", final_decision_node)

    # Add edges
    graph_builder.add_edge(START, "orchestrator")

    # Orchestrator routes to parallel agents
    graph_builder.add_conditional_edges(
        "orchestrator",
        route_to_parallel_agents,
        {
            "rag_agent": "rag_agent",
            "research_agent": "research_agent"
        }
    )

    # Wait for both parallel agents
    graph_builder.add_edge("rag_agent", "synthesis")
    graph_builder.add_edge("research_agent", "synthesis")

    # Synthesis → Reviewer
    graph_builder.add_edge("synthesis", "reviewer")

    # Reviewer → Conditional Routing
    graph_builder.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        {
            "human_review": "human_review",
            "final_decision": "final_decision"
        }
    )

    # Human Review → Final Decision (after resume)
    graph_builder.add_edge("human_review", "final_decision")

    # Final Decision → END
    graph_builder.add_edge("final_decision", END)

    # Compile with MemorySaver for checkpointing
    # CRITICAL: interrupt_before="human_review" pauses graph BEFORE human_review node
    # when state['review_status'] == 'requires_human_review'
    graph = graph_builder.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["human_review"]  # Pause before human review node
    )

    logger.info("LangGraph compiled successfully with HITL interrupts")
    return graph


# ============================================================================
# 6. EXECUTION & RESUMPTION FUNCTIONS
# ============================================================================

def run_workflow(graph, query: str) -> Dict[str, Any]:
    """
    Execute workflow and return result.

    Returns immediately with:
    - execution_id
    - status: "started" | "paused_for_human_review" | "completed"
    - result: Full state dict
    """
    execution_id = str(uuid.uuid4())

    initial_state = {
        "query": query,
        "execution_id": execution_id,
        "rag_context": {},
        "research_data": {},
        "draft_report": "",
        "review_status": "",
        "review_feedback": None,
        "retry_count": 0,
        "human_decision": None,
        "human_notes": None,
        "risk_factors": [],
        "gray_area_trigger": False,
        "high_value_category": False,
        "is_paused": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    logger.info(f"Starting workflow execution: {execution_id}")

    try:
        # Invoke graph with thread_id for checkpointing
        result = graph.invoke(
            initial_state,
            config={"configurable": {"thread_id": execution_id}}
        )

        # Check if paused
        if result.get("is_paused") or result.get("review_status") == "requires_human_review":
            logger.info(f"Workflow paused for human review: {execution_id}")
            return {
                "execution_id": execution_id,
                "status": "paused_for_human_review",
                "result": result,
                "message": "Workflow paused - awaiting human compliance review"
            }

        logger.info(f"Workflow completed: {execution_id}")
        return {
            "execution_id": execution_id,
            "status": "completed",
            "result": result,
            "message": "Workflow completed successfully"
        }

    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        return {
            "execution_id": execution_id,
            "status": "error",
            "error": str(e),
            "message": "Workflow execution failed"
        }


def resume_workflow(
    graph,
    execution_id: str,
    override_decision: str,
    notes: str
) -> Dict[str, Any]:
    """
    Resume paused workflow with human decision.

    Args:
        graph: Compiled LangGraph
        execution_id: Original execution ID
        override_decision: "override_approve" or "override_reject"
        notes: Human's justification

    Returns:
        Final result with human decision applied
    """
    logger.info(f"Resuming workflow with human decision: {execution_id}")

    try:
        # Fetch paused state from checkpointer
        paused_state = graph.get_state(
            config={"configurable": {"thread_id": execution_id}}
        )

        if not paused_state or not paused_state.values:
            logger.error(f"Paused state not found: {execution_id}")
            return {
                "execution_id": execution_id,
                "status": "error",
                "message": "Paused state not found"
            }

        current_state = dict(paused_state.values)

        # Inject human decision into state
        current_state["human_decision"] = override_decision
        current_state["human_notes"] = notes
        current_state["updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"Injected human decision: {override_decision}")

        # Resume graph execution
        result = graph.invoke(
            None,  # None because we're using put_state
            config={"configurable": {"thread_id": execution_id}}
        )

        logger.info(f"Workflow resumed and completed: {execution_id}")

        return {
            "execution_id": execution_id,
            "status": "completed",
            "result": result,
            "message": "Workflow resumed and completed with human decision"
        }

    except Exception as e:
        logger.error(f"Resume workflow failed: {str(e)}")
        return {
            "execution_id": execution_id,
            "status": "error",
            "error": str(e),
            "message": "Failed to resume workflow"
        }


def get_workflow_status(graph, execution_id: str) -> Dict[str, Any]:
    """Get current status of a workflow (running, paused, or completed)."""
    logger.info(f"Fetching workflow status: {execution_id}")

    try:
        state = graph.get_state(
            config={"configurable": {"thread_id": execution_id}}
        )

        if not state:
            return {
                "execution_id": execution_id,
                "status": "not_found",
                "message": "Execution not found"
            }

        values = dict(state.values) if state.values else {}

        # Determine status
        if state.next and "human_review" in state.next:
            status = "paused_for_human_review"
        elif values.get("review_status") in ["approved", "rejected"]:
            status = "completed"
        else:
            status = "running"

        return {
            "execution_id": execution_id,
            "status": status,
            "is_paused": values.get("is_paused", False),
            "review_status": values.get("review_status"),
            "review_feedback": values.get("review_feedback"),
            "risk_factors": values.get("risk_factors", []),
            "created_at": values.get("created_at"),
            "updated_at": values.get("updated_at"),
            "message": f"Status: {status}"
        }

    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return {
            "execution_id": execution_id,
            "status": "error",
            "error": str(e),
            "message": "Failed to fetch status"
        }


if __name__ == "__main__":
    # Test workflow
    print("\n" + "="*80)
    print("MarginGuard AI — HITL Orchestrator Test")
    print("="*80 + "\n")

    # Build graph
    graph = build_hitl_graph()

    # Run workflow
    result = run_workflow(graph, "CloudScale Enterprise Tier-2 pricing")
    print(f"Workflow Status: {result['status']}")
    print(f"Execution ID: {result['execution_id']}")

    if result['status'] == "paused_for_human_review":
        print("\n[PAUSED] Workflow awaiting human review...")
        print(f"Risk Factors: {result['result'].get('risk_factors')}")

        # Simulate human decision
        print("\n[RESUMING] Applying human override decision...")
        resume_result = resume_workflow(
            graph,
            result['execution_id'],
            "override_approve",
            "Approved per management consensus on pricing strategy"
        )
        print(f"Final Status: {resume_result['status']}")
        print(f"Final Decision: {resume_result['result'].get('review_status')}")
    else:
        print(f"Final Status: {result['result'].get('review_status')}")

    print("\n" + "="*80 + "\n")
