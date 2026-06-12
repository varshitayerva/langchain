"""
Graph Generator for Margin Vulnerability Analysis
Converts synthesis report data into visual charts
"""

import json
from typing import Dict, List


class GraphGenerator:
    """Generate visualization data for dashboard display"""

    def __init__(self):
        self.charts = {}

    def generate_all_charts(self, rag_output: dict, research_output: dict) -> Dict:
        """
        Generate all charts from RAG and research data.

        Returns JSON-compatible dict with chart configurations
        """

        product_data = rag_output.get("product_data", {})

        charts = {
            "price_comparison": self._price_comparison_chart(product_data, research_output),
            "margin_analysis": self._margin_analysis_chart(product_data),
            "feature_comparison": self._feature_comparison_chart(product_data, research_output),
            "risk_level": self._risk_level_chart(product_data, research_output),
            "vulnerability_timeline": self._vulnerability_timeline_chart(product_data, research_output)
        }

        return charts

    def _price_comparison_chart(self, product_data: dict, research_output: dict) -> Dict:
        """
        Chart Type: Bar Chart
        Shows: Your price vs Competitor price
        """

        your_price = product_data.get("price", 0)
        competitor_price = research_output.get("competitor_price_normalized", 0)

        price_gap = your_price - competitor_price
        price_gap_percent = ((price_gap / competitor_price) * 100) if competitor_price > 0 else 0

        return {
            "type": "bar_chart",
            "title": "Price Comparison Analysis",
            "description": f"Your product is ${abs(price_gap):.2f} {'higher' if price_gap > 0 else 'lower'} ({price_gap_percent:.1f}%)",
            "data": [
                {
                    "label": product_data.get("name", "Your Product"),
                    "price": round(your_price, 2),
                    "color": "#FF6B6B"
                },
                {
                    "label": research_output.get("competitor_name", "Competitor"),
                    "price": round(competitor_price, 2),
                    "color": "#4ECDC4"
                }
            ],
            "metrics": {
                "your_price": round(your_price, 2),
                "competitor_price": round(competitor_price, 2),
                "gap": round(price_gap, 2),
                "gap_percentage": round(price_gap_percent, 1)
            }
        }

    def _margin_analysis_chart(self, product_data: dict) -> Dict:
        """
        Chart Type: Gauge Chart
        Shows: Current margin vs minimum margin floor
        """

        price = product_data.get("price", 0)
        margin_floor = product_data.get("margin_floor", 0)
        current_margin = price - margin_floor
        margin_percentage = ((current_margin / price) * 100) if price > 0 else 0
        floor_percentage = ((margin_floor / price) * 100) if price > 0 else 0

        return {
            "type": "gauge_chart",
            "title": "Margin Health Status",
            "description": f"Current margin: ${current_margin:.2f} ({margin_percentage:.1f}%)",
            "data": {
                "current_margin": round(current_margin, 2),
                "margin_floor": round(margin_floor, 2),
                "margin_percentage": round(margin_percentage, 1),
                "floor_percentage": round(floor_percentage, 1),
                "safe_zone": margin_percentage > floor_percentage + 10
            },
            "status": "SAFE" if margin_percentage > floor_percentage + 10 else "CRITICAL",
            "color": "#2ECC71" if margin_percentage > floor_percentage + 10 else "#E74C3C"
        }

    def _feature_comparison_chart(self, product_data: dict, research_output: dict) -> Dict:
        """
        Chart Type: Radar Chart
        Shows: Your features vs Competitor features
        """

        your_features = product_data.get("features", [])
        competitor_features = research_output.get("features_found", [])

        # Common features between products
        common_features = set(your_features) & set(competitor_features)
        unique_your_features = set(your_features) - set(competitor_features)
        unique_competitor = set(competitor_features) - set(your_features)

        return {
            "type": "radar_chart",
            "title": "Feature Comparison",
            "description": f"Your advantages: {len(unique_your_features)} unique features",
            "data": {
                "your_features": list(your_features),
                "competitor_features": list(competitor_features),
                "common_features": list(common_features),
                "unique_yours": list(unique_your_features),
                "unique_competitor": list(unique_competitor),
                "feature_advantage": len(unique_your_features) - len(unique_competitor)
            },
            "counts": {
                "your_total": len(your_features),
                "competitor_total": len(competitor_features),
                "common": len(common_features),
                "unique_yours": len(unique_your_features),
                "unique_competitor": len(unique_competitor)
            }
        }

    def _risk_level_chart(self, product_data: dict, research_output: dict) -> Dict:
        """
        Chart Type: Donut Chart / Risk Meter
        Shows: Risk Level (LOW/MEDIUM/HIGH)
        """

        your_price = product_data.get("price", 0)
        competitor_price = research_output.get("competitor_price_normalized", 0)
        margin_floor = product_data.get("margin_floor", 0)

        price_gap_percent = ((your_price - competitor_price) / competitor_price * 100) if competitor_price > 0 else 0
        margin_safety = ((your_price - margin_floor) / your_price * 100) if your_price > 0 else 0

        # Risk calculation
        if price_gap_percent > 25:
            risk_level = "HIGH"
            risk_score = 8
        elif price_gap_percent > 15:
            risk_level = "MEDIUM"
            risk_score = 5
        else:
            risk_level = "LOW"
            risk_score = 2

        return {
            "type": "donut_chart",
            "title": "Market Vulnerability Risk Level",
            "description": f"Risk Score: {risk_score}/10",
            "data": {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "price_gap_percent": round(price_gap_percent, 1),
                "margin_safety": round(margin_safety, 1),
                "recommendation": self._get_risk_recommendation(risk_level)
            },
            "risk_factors": {
                "price_gap": {"value": price_gap_percent, "impact": "HIGH" if price_gap_percent > 20 else "MEDIUM"},
                "margin_pressure": {"value": 100 - margin_safety, "impact": "MEDIUM"},
                "competitive_threat": {"value": risk_score * 10, "impact": risk_level}
            }
        }

    def _vulnerability_timeline_chart(self, product_data: dict, research_output: dict) -> Dict:
        """
        Chart Type: Line Chart / Timeline
        Shows: Vulnerability trajectory if prices change
        """

        your_price = product_data.get("price", 0)
        competitor_price = research_output.get("competitor_price_normalized", 0)
        margin_floor = product_data.get("margin_floor", 0)

        # Simulate price scenarios
        scenarios = []
        for competitor_drop in range(0, 31, 5):  # 0% to 30% drop
            new_comp_price = competitor_price * (1 - competitor_drop / 100)
            gap = your_price - new_comp_price
            gap_percent = (gap / new_comp_price * 100) if new_comp_price > 0 else 0

            scenarios.append({
                "competitor_price_drop": competitor_drop,
                "new_competitor_price": round(new_comp_price, 2),
                "price_gap": round(gap, 2),
                "gap_percentage": round(gap_percent, 1),
                "margin_safe": your_price - gap > margin_floor
            })

        return {
            "type": "line_chart",
            "title": "Vulnerability Trajectory (If Competitor Cuts Price)",
            "description": "How your position changes if competitor reduces price",
            "data": scenarios,
            "warning_point": next(
                (s["competitor_price_drop"] for s in scenarios if not s["margin_safe"]),
                None
            ),
            "breakeven_scenario": f"Competitor needs to drop {next((s['competitor_price_drop'] for s in scenarios if not s['margin_safe']), 'N/A')}% to threaten margin"
        }

    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level"""
        recommendations = {
            "LOW": "Maintain current strategy. Monitor market trends quarterly.",
            "MEDIUM": "Implement defensive pricing strategy. Prepare backup options.",
            "HIGH": "Urgent action required. Consider price reduction or feature upgrade."
        }
        return recommendations.get(risk_level, "Analyze further")

    def export_for_dashboard(self, charts: Dict) -> str:
        """Export charts as JSON for frontend dashboard"""
        return json.dumps(charts, indent=2)


# Test function
if __name__ == "__main__":
    generator = GraphGenerator()

    rag_output = {
        "product_data": {
            "name": "Wireless Earbuds Pro",
            "price": 129.99,
            "margin_floor": 45.00,
            "features": ["ANC", "30h battery", "IP67", "Multi-device"]
        },
        "policy_snippet": "Cannot discount below 65% MSRP"
    }

    research_output = {
        "competitor_name": "SoundMax Elite",
        "competitor_price_normalized": 99.99,
        "features_found": ["ANC", "20h battery", "IP54"],
        "sources": ["amazon.com", "bestbuy.com"]
    }

    charts = generator.generate_all_charts(rag_output, research_output)
    print(generator.export_for_dashboard(charts))
