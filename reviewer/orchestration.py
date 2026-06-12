"""
MarginGuard AI — Unified Multi-Agent Orchestration Pipeline
============================================================

Orchestrates Phases 2-5 in a single executable script:
  Phase 2: RAG Agent (Product & Policy Retrieval)
  Phase 3: Research Agent (Competitive Intelligence)
  Phase 4: Synthesis Agent (Report Generation)
  Phase 5: Reviewer Agent (Compliance Audit)

Usage:
  python orchestration.py --query "CloudScale Enterprise Tier-2 pricing"
"""

import sys
import os
import json
from typing import Dict, Any, Optional

# Add langchain folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'langchain'))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 80)
print("MARGINGUARD AI — MULTI-AGENT ORCHESTRATION PIPELINE")
print("=" * 80)
print()


# ============================================================================
# PHASE 2: RAG AGENT (Product & Policy Retrieval)
# ============================================================================

class MockRAGAgent:
    """
    Mock RAG Agent (Phase 2) — Returns hardcoded product data.
    In production, this queries pgvector database.
    """

    def retrieve(self, query: str) -> Dict[str, Any]:
        """
        Retrieve product and policy data for a query.

        Args:
            query: Product search query

        Returns:
            dict with product_data (list) and policy_snippet
        """
        print("[PHASE 2] RAG Agent — Retrieving Product Data")
        print(f"Query: {query}")
        print()

        # Mock product data (in production, from pgvector)
        rag_output = {
            "query": query,
            "product_data": [
                {
                    "id": "CS-ENT-02",
                    "name": "CloudScale Enterprise Tier-2",
                    "category": "Cloud Services",
                    "price": 105.00,
                    "cost": 80.00,
                    "margin_floor": "$100.00",
                    "features": "Advanced analytics, 99.9% SLA, auto-scaling, multi-region",
                    "similarity": 0.95,
                }
            ],
            "policy_snippet": "### Pricing Policy\nAll pricing recommendations must maintain or exceed the margin floor to preserve profitability.",
        }

        print(f"[OK] Retrieved product: {rag_output['product_data'][0]['name']}")
        print(f"[OK] Margin floor: {rag_output['product_data'][0]['margin_floor']}")
        print()

        return rag_output


# ============================================================================
# PHASE 3: RESEARCH AGENT (Competitive Intelligence)
# ============================================================================

class MockResearchAgent:
    """
    Mock Research Agent (Phase 3) — Returns competitive pricing data.
    In production, this queries Tavily Search API.
    """

    def research_market(self, query: str) -> Dict[str, Any]:
        """
        Research competitors via Tavily API.

        Args:
            query: Search query for market research

        Returns:
            dict with competitor intelligence
        """
        print("[PHASE 3] Research Agent — Researching Competitors")
        print(f"Query: {query}")
        print()

        # Mock research output (in production, from Tavily)
        research_output = {
            "competitor_name": "ApexCloud v2",
            "competitor_price_normalized": "$112.50",
            "features_found": ["SLA", "analytics", "auto-scaling", "multi-region"],
            "sources": ["https://apexcloud.com/pricing", "https://g2.com"],
        }

        print(f"[OK] Found competitor: {research_output['competitor_name']}")
        print(f"[OK] Competitor price: {research_output['competitor_price_normalized']}")
        print(f"[OK] Features found: {len(research_output['features_found'])}")
        print()

        return research_output


# ============================================================================
# PHASE 4: SYNTHESIS AGENT (Report Generation)
# ============================================================================

class MockSynthesisAgent:
    """
    Mock Synthesis Agent (Phase 4) — Generates pricing strategy reports.
    In production, this uses Qwen-14B or Grok LLM.
    """

    def synthesize(
        self,
        rag_output: Dict[str, Any],
        research_output: Dict[str, Any],
        feedback: Optional[str] = None
    ) -> str:
        """
        Generate pricing strategy report.

        Args:
            rag_output: Product and policy data from RAG
            research_output: Competitor intelligence from Research
            feedback: Reviewer feedback for refinement (optional)

        Returns:
            Markdown-formatted pricing strategy report
        """
        print("[PHASE 4] Synthesis Agent — Generating Report")
        print()

        product = rag_output["product_data"][0]
        competitor = research_output

        # Generate report
        report = f"""# Market Position & Pricing Strategy Report

## Executive Summary
{product['name']} is competitively positioned against {competitor['competitor_name']}.
Our pricing maintains healthy margins while remaining market-competitive.

## Market Analysis
{competitor['competitor_name']} is priced at {competitor['competitor_price_normalized']}/mo.
Our current positioning at ${product['price']:.2f}/mo allows us to compete effectively while protecting margin integrity.

## Recommended Action
Maintain price at ${product['price']:.2f}/mo. This strategy preserves our ${product['price'] - product['cost']:.0f}/mo margin advantage
(vs. cost floor of ${product['cost']:.2f}) while remaining competitive.

## DATA SUMMARY MATRIX
TARGET_PRODUCT_SKU: {product['id']}
TARGET_PRODUCT_NAME: {product['name']}
INTERNAL_BASE_COST: ${product['cost']:.2f}
INTERNAL_MARGIN_FLOOR: {product['margin_floor']}
LIVE_COMPETITOR_NAME: {competitor['competitor_name']}
LIVE_COMPETITOR_PRICE_NORMALIZED: {competitor['competitor_price_normalized']}
FINAL_RECOMMENDED_PRICE: ${product['price']:.2f}
STRATEGIC_ACTION_PLAN_INCLUDED: TRUE
"""

        print("[OK] Report generated with DATA SUMMARY MATRIX")
        print()

        return report


# ============================================================================
# PHASE 5: REVIEWER AGENT (Compliance Audit)
# ============================================================================

def reviewer_audit(
    report: str,
    rag_output: Dict[str, Any],
    research_output: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Audit pricing report for compliance.

    Args:
        report: Markdown report from Synthesis Agent
        rag_output: Product and policy data
        research_output: Competitor intelligence

    Returns:
        dict with is_approved (bool) and feedback
    """
    print("[PHASE 5] Reviewer Agent — Auditing Report")
    print()

    # Try to import reviewer_agent module with XAI API key check
    sys.path.insert(0, os.path.dirname(__file__))

    xai_api_key = os.getenv("XAI_API_KEY")

    if xai_api_key:
        try:
            from reviewer_agent import review
            result = review(report, rag_output, research_output)
        except Exception as e:
            print(f"[WARNING] Live reviewer failed: {str(e)}")
            print("[INFO] Using mock reviewer fallback")
            result = _mock_reviewer_audit(report, rag_output, research_output)
    else:
        print("[INFO] XAI_API_KEY not set - Using mock reviewer")
        result = _mock_reviewer_audit(report, rag_output, research_output)

    status = result.get("status", "unknown") if result else "unknown"
    feedback = result.get("feedback", "") if result else ""

    if status == "approved":
        print("[APPROVED] Report passed all compliance checks")
        print("  - Financial guardrail: PASSED")
        print("  - Identity alignment: PASSED")
        print("  - Structural completeness: PASSED")
    else:
        print("[REJECTED] Report failed compliance checks")
        if feedback:
            print(f"Feedback:\n{feedback}")

    print()

    return {
        "is_approved": status == "approved",
        "status": status,
        "feedback": feedback,
    }


def _mock_reviewer_audit(
    report: str,
    rag_output: Dict[str, Any],
    research_output: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Mock Reviewer Agent — Performs basic compliance checks without LLM.

    Args:
        report: Report to audit
        rag_output: Product data
        research_output: Research data

    Returns:
        dict with audit result
    """
    # Extract product and competitor info
    product = rag_output["product_data"][0]
    competitor = research_output

    # Check for DATA SUMMARY MATRIX
    if "### DATA SUMMARY MATRIX" not in report and "## DATA SUMMARY MATRIX" not in report:
        return {
            "status": "rejected",
            "feedback": "Missing DATA SUMMARY MATRIX section"
        }

    # Check for required sections
    has_summary = "## Executive Summary" in report or "### Executive Summary" in report
    has_action = "## Recommended Action" in report or "### Recommended Action" in report

    if not has_summary or not has_action:
        return {
            "status": "rejected",
            "feedback": "Missing Executive Summary or Recommended Action sections"
        }

    # Extract price from report
    import re
    price_match = re.search(r'FINAL_RECOMMENDED_PRICE:\s*\$?([\d.]+)', report)

    if price_match:
        try:
            recommended_price = float(price_match.group(1))

            # Parse margin floor
            margin_floor_str = product.get("margin_floor", "$100.00")
            margin_floor_str = margin_floor_str.replace("$", "").replace(",", "")
            margin_floor = float(margin_floor_str)

            # Check financial guardrail
            if recommended_price < margin_floor:
                return {
                    "status": "rejected",
                    "feedback": f"Price ${recommended_price} is below margin floor ${margin_floor}"
                }

            # Check identity alignment
            if product["id"] not in report or product["name"] not in report:
                return {
                    "status": "rejected",
                    "feedback": "Product SKU or name mismatch"
                }

            if competitor["competitor_name"] not in report:
                return {
                    "status": "rejected",
                    "feedback": "Competitor name mismatch"
                }

            # All checks passed
            return {
                "status": "approved",
                "feedback": None
            }
        except ValueError:
            return {
                "status": "rejected",
                "feedback": "Could not parse recommended price"
            }
    else:
        return {
            "status": "rejected",
            "feedback": "Could not find FINAL_RECOMMENDED_PRICE in report"
        }



# ============================================================================
# ORCHESTRATION PIPELINE
# ============================================================================

def run_pipeline(query: str) -> Dict[str, Any]:
    """
    Execute the complete MarginGuard AI pipeline.

    Flow: Query → RAG → Research → Synthesis → Reviewer

    Args:
        query: Product query

    Returns:
        dict with final output including report and approval status
    """

    print("=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)
    print()

    # ========================================================================
    # PHASE 2: RAG
    # ========================================================================
    rag_agent = MockRAGAgent()
    rag_output = rag_agent.retrieve(query)

    # ========================================================================
    # PHASE 3: RESEARCH
    # ========================================================================
    research_agent = MockResearchAgent()
    product_name = rag_output["product_data"][0].get("name", "")
    research_output = research_agent.research_market(
        f"{product_name} pricing competitive analysis"
    )

    # ========================================================================
    # PHASE 4: SYNTHESIS
    # ========================================================================
    synthesis_agent = MockSynthesisAgent()
    report = synthesis_agent.synthesize(rag_output, research_output)

    # ========================================================================
    # PHASE 5: REVIEWER
    # ========================================================================
    reviewer_result = reviewer_audit(report, rag_output, research_output)

    # ========================================================================
    # FINAL OUTPUT
    # ========================================================================
    print("=" * 80)
    print("PIPELINE EXECUTION COMPLETE")
    print("=" * 80)
    print()

    output = {
        "query": query,
        "rag_output": rag_output,
        "research_output": research_output,
        "report": report,
        "reviewer_result": reviewer_result,
        "is_approved": reviewer_result["is_approved"],
    }

    return output


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="MarginGuard AI — Unified Multi-Agent Orchestration"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="CloudScale Enterprise Tier-2 pricing strategies against live market alternatives",
        help="Product query for pipeline"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Save output to JSON file"
    )

    args = parser.parse_args()

    # Run pipeline
    output = run_pipeline(args.query)

    # Display final report
    print()
    print("=" * 80)
    print("FINAL PRICING STRATEGY REPORT")
    print("=" * 80)
    print()
    print(output["report"])
    print()

    # Display approval status
    print("=" * 80)
    print("COMPLIANCE AUDIT RESULT")
    print("=" * 80)
    print()
    if output["is_approved"]:
        print("[SUCCESS] REPORT APPROVED")
        print("Status: Ready for output")
    else:
        print("[FAILED] REPORT REJECTED")
        print(f"Feedback: {output['reviewer_result']['feedback']}")
    print()

    # Save to JSON if requested
    if args.output_json:
        # Convert non-serializable objects
        output_clean = {
            "query": output["query"],
            "report": output["report"],
            "is_approved": output["is_approved"],
            "approval_status": output["reviewer_result"]["status"],
            "feedback": output["reviewer_result"]["feedback"],
        }

        with open(args.output_json, "w") as f:
            json.dump(output_clean, f, indent=2)

        print(f"[OK] Output saved to: {args.output_json}")
        print()

    # Exit with appropriate code
    sys.exit(0 if output["is_approved"] else 1)
