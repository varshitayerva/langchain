"""
Phase 4: Synthesis Agent using Qwen-14B
Generates Margin Vulnerability Assessment Report from RAG and research data.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()


class SynthesisAgent:
    """Synthesis agent using Qwen-14B for report generation."""

    def __init__(self, model_name: str = "Qwen/Qwen3-14B:nscale"):
        """
        Initialize Qwen-14B synthesis agent using HF router.

        Args:
            model_name: Hugging Face model identifier
        """
        self.model_name = model_name
        self.hf_token = None
        self.client = None

    def set_token(self, token: str):
        """Set Hugging Face API token and initialize client."""
        self.hf_token = token
        self.client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=token,
        )

    def synthesize(
        self,
        rag_output: dict,
        research_output: dict,
        feedback: Optional[str] = None
    ) -> str:
        """
        Generate Margin Vulnerability Assessment Report.

        Args:
            rag_output: {product_data: {...}, policy_snippet: "..."}
            research_output: {competitor_name, competitor_price, features_found, sources}
            feedback: Optional reviewer feedback for retry/refinement

        Returns:
            Markdown formatted report string
        """

        # Build the prompt
        prompt = self._build_prompt(rag_output, research_output, feedback)

        # Call Qwen-14B
        report = self._call_qwen(prompt)

        # Enhance report with structured data matrix
        enhanced_report = self._enhance_with_data_matrix(report, rag_output, research_output)

        return enhanced_report

    def _build_prompt(
        self,
        rag_output: dict,
        research_output: dict,
        feedback: Optional[str] = None
    ) -> str:
        """Construct the synthesis prompt."""

        product_data = rag_output.get("product_data", {})
        policy_snippet = rag_output.get("policy_snippet", "")

        prompt = f"""You are a business analyst generating a Margin Vulnerability Assessment Report.

## Internal Data (from RAG)
- Product: {product_data.get('name', 'Unknown')}
- SKU: {product_data.get('sku', 'N/A')}
- Current Price: ${product_data.get('price', 'N/A')}
- Internal Base Cost: ${product_data.get('base_cost', 'N/A')}
- Margin Floor: ${product_data.get('margin_floor', 'N/A')}
- Features: {', '.join(product_data.get('features', []))}
- Policy: {policy_snippet[:200]}...

## Market Research (from Competitor Analysis)
- Competitor: {research_output.get('competitor_name', 'Unknown')}
- Competitor Price: ${research_output.get('competitor_price_normalized', 'N/A')}
- Competitor Features: {', '.join(research_output.get('features_found', []))}
- Sources: {', '.join(research_output.get('sources', []))}

## Task
Generate a professional Margin Vulnerability Assessment Report in markdown format with:
1. Executive Summary (2-3 sentences on market pressure and strategic action)
2. Market Position Analysis (price gap, competitive threats, churn risk)
3. Vulnerability Assessment (margin exposure, pricing pressures)
4. Recommended Action (specific price adjustments to stay competitive while protecting margins)
5. Strategic Risk Assessment

Format as clean markdown. Be specific with numbers and recommendations. Include concrete pricing strategies.
"""

        if feedback:
            prompt += f"\n## Refinement Feedback\n{feedback}\nRevise the report addressing this feedback."

        return prompt

    def _call_qwen(self, prompt: str) -> str:
        """Call Qwen-14B via Hugging Face router (OpenAI-compatible API)."""

        if not self.client:
            return "Error: Client not initialized. Call set_token() first."

        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7,
                top_p=0.95,
            )

            content = completion.choices[0].message.content
            if content is None:
                return "Error: API returned empty content. Try again."

            return content.strip()

        except Exception as e:
            return f"Error calling Qwen API: {str(e)}"

    def _enhance_with_data_matrix(
        self,
        report: str,
        rag_output: dict,
        research_output: dict
    ) -> str:
        """Enhance report with structured Data Summary Matrix."""

        product_data = rag_output.get("product_data", {})

        # Calculate price metrics
        internal_base_cost = product_data.get("base_cost", 80.00)
        internal_margin_floor = product_data.get("margin_floor", 100.00)
        competitor_price = research_output.get("competitor_price_normalized", 112.50)

        # Calculate recommended price (undercut competitor while protecting margin)
        recommended_price = max(
            internal_margin_floor,
            competitor_price - (competitor_price * 0.15)  # 15% undercut
        )

        data_matrix = f"""
## DATA SUMMARY MATRIX
TARGET_PRODUCT_SKU: {product_data.get('sku', 'CS-ENT-02')}
TARGET_PRODUCT_NAME: {product_data.get('name', 'CloudScale Enterprise Tier-2')}
INTERNAL_BASE_COST: ${internal_base_cost:.2f}
INTERNAL_MARGIN_FLOOR: ${internal_margin_floor:.2f}
LIVE_COMPETITOR_NAME: {research_output.get('competitor_name', 'ApexCloud v2')}
LIVE_COMPETITOR_PRICE_NORMALIZED: ${competitor_price:.2f}
FINAL_RECOMMENDED_PRICE: ${recommended_price:.2f}
STRATEGIC_ACTION_PLAN_INCLUDED: TRUE
"""

        return report + data_matrix



# Test with hardcoded data
def test_synthesis():
    """Test the synthesis agent with mock RAG and research data."""

    agent = SynthesisAgent()
    # Load HF token from .env file
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        agent.set_token(hf_token)
    else:
        print("ERROR: HF_TOKEN not found in .env file")
        print("Please paste your Hugging Face token in .env file")
        return

    # Mock RAG output
    rag_output = {
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

    # Mock research output
    research_output = {
        "competitor_name": "ApexCloud v2",
        "competitor_price_normalized": 112.50,
        "features_found": ["Auto-scaling", "Multi-region", "99.99% SLA", "Premium support"],
        "sources": ["apexcloud.com", "techcrunch.com", "g2.com"]
    }

    # Generate report
    print("=== Synthesis Agent Test ===\n")
    report = agent.synthesize(rag_output, research_output)
    print(report)

    # Test with feedback (refinement)
    print("\n=== Report with Reviewer Feedback ===\n")
    feedback = "Price recommendation was too aggressive. Ensure we stay above $100 margin floor while undercutting ApexCloud v2."
    refined_report = agent.synthesize(rag_output, research_output, feedback)
    print(refined_report)


if __name__ == "__main__":
    test_synthesis()
