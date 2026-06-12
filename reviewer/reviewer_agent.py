import os
import json
import re
from typing import Optional, Union, Dict, Any
from langchain_xai import ChatXAI
from dotenv import load_dotenv

# Load variables from the local .env file
load_dotenv()

XAI_API_KEY = os.getenv("XAI_API_KEY")
if not XAI_API_KEY:
    raise ValueError("XAI_API_KEY environment variable is not set")

llm = ChatXAI(model="grok-2-latest", temperature=0.0)


def parse_currency(value: Union[str, float]) -> float:
    """
    Parse currency value from string or float format.

    Handles formats like "$100.00", "100.00", "$100", "100", etc.

    Args:
        value: Currency value as string or float

    Returns:
        float: Parsed numeric value
    """
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        # Remove currency symbols and commas
        cleaned = re.sub(r'[\$,]', '', value.strip())
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    return 0.0


def extract_product_data(rag_output: dict) -> Dict[str, Any]:
    """
    Safely extract product data from rag_output.
    Handles both list (production) and dict (mock) formats.

    Args:
        rag_output: RAG agent output dictionary

    Returns:
        dict: Extracted product data with keys: name, sku, margin_floor
    """
    product_data_raw = rag_output.get("product_data", {})

    # Handle list format (production PostgreSQL output)
    if isinstance(product_data_raw, list):
        if not product_data_raw:
            return {
                "name": "Unknown",
                "sku": "Unknown",
                "margin_floor": "Unknown",
                "margin_floor_numeric": 0.0,
            }
        product = product_data_raw[0]
    # Handle dict format (mock/test data)
    elif isinstance(product_data_raw, dict):
        product = product_data_raw
    else:
        return {
            "name": "Unknown",
            "sku": "Unknown",
            "margin_floor": "Unknown",
            "margin_floor_numeric": 0.0,
        }

    # Extract values, handling both 'id' and 'sku' keys
    product_name = product.get("name", "Unknown")
    product_sku = product.get("id", product.get("sku", "Unknown"))
    margin_floor = product.get("margin_floor", "Unknown")
    margin_floor_numeric = parse_currency(margin_floor)

    return {
        "name": product_name,
        "sku": product_sku,
        "margin_floor": margin_floor,
        "margin_floor_numeric": margin_floor_numeric,
    }


def review(report: str, rag_output: dict, research_output: dict) -> dict:
    """
    Phase 5 Reviewer Agent — Standalone LLM audit function.

    Validates a pricing strategy report against financial guardrails,
    identity alignment, and structural completeness.
    Handles both production (list) and mock (dict) product_data schemas.

    Args:
        report: Markdown string containing the pricing strategy and DATA SUMMARY MATRIX.
        rag_output: Dict with 'product_data' (list or dict) and 'policy_snippet'.
        research_output: Dict with 'competitor_name', 'competitor_price_normalized'.

    Returns:
        Dict with keys:
          - status: "approved" or "rejected"
          - feedback: None if approved, or detailed rejection reason if rejected.
    """

    # Fast-fail structural check: Missing DATA SUMMARY MATRIX
    if "### DATA SUMMARY MATRIX" not in report and "## DATA SUMMARY MATRIX" not in report:
        return {
            "status": "rejected",
            "feedback": "STRUCTURAL FAILURE: Report missing DATA SUMMARY MATRIX block. Synthesis agent must include structured data matrix.",
        }

    # Safely extract product data (handles both list and dict formats)
    try:
        product_info = extract_product_data(rag_output)
        product_name = product_info["name"]
        product_sku = product_info["sku"]
        margin_floor = product_info["margin_floor"]
        margin_floor_numeric = product_info["margin_floor_numeric"]
    except Exception as e:
        return {
            "status": "rejected",
            "feedback": f"RAG SCHEMA ERROR: Could not parse product_data: {str(e)}",
        }

    # Extract research data
    competitor_name = research_output.get("competitor_name", "Unknown")
    competitor_price_raw = research_output.get("competitor_price_normalized", "Unknown")
    competitor_price_numeric = parse_currency(competitor_price_raw)

    # Build the audit prompt with JSON output constraint
    audit_prompt = f"""You are the Senior Compliance and Market Auditor for MarginGuard AI.
Your sole responsibility is to protect corporate profitability and data accuracy by auditing the generated 'Pricing Strategy Memo' against our raw source documents.

=== RAG CONTEXT (Internal Catalog Rules) ===
Product Name: {product_name}
Product SKU/ID: {product_sku}
Absolute Margin Floor: {margin_floor}

=== RESEARCH CONTEXT (Live Competitor Data) ===
Competitor Name: {competitor_name}
Competitor Normalized Price: {competitor_price_raw}

=== GENERATED DRAFT REPORT TO AUDIT ===
{report}

=== CRITICAL AUDIT RULES ===

1. FINANCIAL GUARDRAIL CHECK:
   - Extract 'FINAL_RECOMMENDED_PRICE' from the DATA SUMMARY MATRIX.
   - Verify it is >= {margin_floor}.
   - If FINAL_RECOMMENDED_PRICE < {margin_floor}, mark as rejected with fatal profitability violation.

2. IDENTITY ALIGNMENT CHECK:
   - Product SKU in report must exactly match: {product_sku}
   - Competitor name in report must exactly match: {competitor_name}
   - Any hallucination or mismatch = reject.

3. STRUCTURAL COMPLETENESS CHECK:
   - Report must include "Executive Summary" and "Recommended Action" sections.
   - Data-only reports with no substantive analysis = reject.

=== OUTPUT REQUIREMENTS (STRICT JSON) ===
You MUST output ONLY a valid JSON object in this exact format (no markdown, no extra text):

{{"status": "approved", "feedback": null}}

OR

{{"status": "rejected", "feedback": "- Violation 1 description\\n- Violation 2 description\\n- Violation 3 description"}}

The feedback field must be a markdown-formatted bullet list if rejected, or null if approved.
Do not output anything except the JSON object. Perform the audit now and respond with ONLY the JSON."""

    try:
        response = llm.invoke(audit_prompt)
        audit_result = response.content.strip()

        # Parse JSON response
        parsed = json.loads(audit_result)

        # Validate response structure
        if not isinstance(parsed, dict) or "status" not in parsed or "feedback" not in parsed:
            return {
                "status": "rejected",
                "feedback": f"LLM OUTPUT FORMAT ERROR: Invalid JSON structure received: {audit_result}",
            }

        return {
            "status": parsed.get("status", "rejected"),
            "feedback": parsed.get("feedback"),
        }

    except json.JSONDecodeError as e:
        return {
            "status": "rejected",
            "feedback": f"LLM JSON PARSE ERROR: Response was not valid JSON: {str(e)}",
        }
    except Exception as e:
        return {
            "status": "rejected",
            "feedback": f"LLM INVOCATION ERROR: Audit failed: {str(e)}",
        }


def reviewer_node(state: dict) -> dict:
    """
    LangGraph node wrapper for the Reviewer Agent.

    Extracts values from state, runs review(), updates approval flags,
    and increments retry count on rejection.

    Args:
        state: Dict with keys 'report', 'rag_output', 'research_output', 'retry_count'.

    Returns:
        Dict with mutated keys: 'is_approved', 'feedback', 'retry_count'.
    """
    report = state.get("report", "")
    rag_output = state.get("rag_output", {})
    research_output = state.get("research_output", {})
    retry_count = state.get("retry_count", 0)

    result = review(report, rag_output, research_output)

    is_approved = result["status"] == "approved"
    feedback = result["feedback"]

    return {
        "is_approved": is_approved,
        "feedback": feedback,
        "retry_count": retry_count + 1 if not is_approved else retry_count,
    }


if __name__ == "__main__":
    # TEST 1: Production format (list) - Rejection case
    print("=" * 80)
    print("TEST 1: PRODUCTION FORMAT (List) - REJECTION CASE")
    print("=" * 80)

    prod_rag_output = {
        "query": "CloudScale Enterprise Tier-2 pricing",
        "product_data": [
            {
                "id": "CS-ENT-02",
                "name": "CloudScale Enterprise Tier-2",
                "category": "Cloud Services",
                "price": 105.00,
                "cost": 80.00,
                "margin_floor": "$100.00",
                "features": "Advanced analytics, 99.9% SLA, auto-scaling",
                "competitor": "ApexCloud v2",
                "similarity": 0.95,
            }
        ],
        "policy_snippet": "### Pricing Policy\nAll pricing recommendations must maintain or exceed the margin floor to preserve profitability.",
    }

    prod_research_output = {
        "competitor_name": "ApexCloud v2",
        "competitor_price_normalized": "$112.50",
        "features_found": ["SLA", "analytics"],
        "sources": ["https://apexcloud.com/pricing"],
    }

    bad_report = """# Margin Vulnerability Assessment Report

## Executive Summary
We are currently priced at a premium to ApexCloud v2. To capture immediate market share, we must undercut them aggressively.

## Market Position Analysis
ApexCloud v2 dominates the mid-market with aggressive pricing at $112.50/mo. Our current positioning prevents competitive penetration.

## Recommended Action
We recommend aggressive downward price adjustments to $95.00/mo to undercut competitor baselines and capture market share quickly.

## DATA SUMMARY MATRIX
TARGET_PRODUCT_SKU: CS-ENT-02
TARGET_PRODUCT_NAME: CloudScale Enterprise Tier-2
INTERNAL_BASE_COST: $80.00
INTERNAL_MARGIN_FLOOR: $100.00
LIVE_COMPETITOR_NAME: ApexCloud v2
LIVE_COMPETITOR_PRICE_NORMALIZED: $112.50
FINAL_RECOMMENDED_PRICE: $95.00
STRATEGIC_ACTION_PLAN_INCLUDED: TRUE
"""

    result_prod_bad = review(bad_report, prod_rag_output, prod_research_output)
    print(json.dumps(result_prod_bad, indent=2))
    print()

    # TEST 2: Mock format (dict) - Rejection case
    print("=" * 80)
    print("TEST 2: MOCK FORMAT (Dict) - REJECTION CASE")
    print("=" * 80)

    mock_rag_output = {
        "product_data": {
            "name": "CloudScale Enterprise Tier-2",
            "sku": "CS-ENT-02",
            "price": 129.99,
            "base_cost": 80.00,
            "margin_floor": 100.00,
            "features": ["Auto-scaling", "Multi-region", "99.99% SLA", "Enterprise support"],
        },
        "policy_snippet": "Product margin must stay above $100 per unit. Pricing strategy must maintain competitiveness against ApexCloud."
    }

    mock_research_output = {
        "competitor_name": "ApexCloud v2",
        "competitor_price_normalized": 112.50,
        "features_found": ["Auto-scaling", "Multi-region", "99.99% SLA", "Premium support"],
        "sources": ["apexcloud.com", "techcrunch.com", "g2.com"]
    }

    result_mock_bad = review(bad_report, mock_rag_output, mock_research_output)
    print(json.dumps(result_mock_bad, indent=2))
    print()

    # TEST 3: Production format - Approval case
    print("=" * 80)
    print("TEST 3: PRODUCTION FORMAT (List) - APPROVAL CASE")
    print("=" * 80)

    good_report = """# Market Position & Pricing Strategy Report

## Executive Summary
CloudScale Enterprise Tier-2 is competitively positioned against ApexCloud v2. Our pricing maintains healthy margins while remaining market-competitive and sustainable for long-term growth.

## Market Analysis
ApexCloud v2 is priced at $112.50/mo. Our current positioning at $105.00/mo allows us to compete effectively while protecting margin integrity and profitability targets.

## Recommended Action
Maintain price at $105.00/mo. This strategy preserves our $25/mo margin advantage (vs. cost floor of $80) while remaining competitive in the market.

## DATA SUMMARY MATRIX
TARGET_PRODUCT_SKU: CS-ENT-02
TARGET_PRODUCT_NAME: CloudScale Enterprise Tier-2
INTERNAL_BASE_COST: $80.00
INTERNAL_MARGIN_FLOOR: $100.00
LIVE_COMPETITOR_NAME: ApexCloud v2
LIVE_COMPETITOR_PRICE_NORMALIZED: $112.50
FINAL_RECOMMENDED_PRICE: $105.00
STRATEGIC_ACTION_PLAN_INCLUDED: TRUE
"""

    result_prod_good = review(good_report, prod_rag_output, prod_research_output)
    print(json.dumps(result_prod_good, indent=2))
    print()

    # TEST 4: Mock format - Approval case
    print("=" * 80)
    print("TEST 4: MOCK FORMAT (Dict) - APPROVAL CASE")
    print("=" * 80)

    result_mock_good = review(good_report, mock_rag_output, mock_research_output)
    print(json.dumps(result_mock_good, indent=2))
    print()

    # TEST 5: LangGraph node wrapper with production format
    print("=" * 80)
    print("TEST 5: LANGGRAPH NODE WRAPPER (Production Format)")
    print("=" * 80)

    state = {
        "query": "CloudScale Enterprise Tier-2 pricing",
        "report": bad_report,
        "rag_output": prod_rag_output,
        "research_output": prod_research_output,
        "retry_count": 1,
        "is_approved": False,
        "feedback": None,
    }

    node_result = reviewer_node(state)
    print(f"Updated State Keys:")
    print(json.dumps(node_result, indent=2))
    print(f"\nRetry Count Incremented: {state['retry_count']} → {node_result['retry_count']}")
    print()

    # TEST 6: Fast-fail test
    print("=" * 80)
    print("TEST 6: FAST-FAIL (Missing DATA SUMMARY MATRIX)")
    print("=" * 80)

    broken_report = """# Broken Report

## Executive Summary
This report is missing the required data matrix.

## Recommended Action
No recommendation without proper data structure.
"""

    result_broken = review(broken_report, prod_rag_output, prod_research_output)
    print(json.dumps(result_broken, indent=2))
    print("=" * 80)
