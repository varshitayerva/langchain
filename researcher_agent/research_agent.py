import requests
from typing import Optional, List
from tavily import TavilyClient
import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from rag_agent.config import TAVILY_API_KEY
except ImportError:
    from dotenv import load_dotenv
    load_dotenv()
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


class ResearchAgent:
    def __init__(self):
        """Initialize research agent with Tavily client"""
        if not TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY environment variable not set. Add it to .env file.")
        self.tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        self.frankfurter_base = "https://api.frankfurter.dev/v2/rates"

    def convert_currency(self, amount: float, from_currency: str = "USD", to_currency: str = "USD") -> float:
        """
        Convert amount from one currency to another using Frankfurter API.

        Args:
            amount: Amount to convert
            from_currency: Source currency code (default: USD)
            to_currency: Target currency code (default: USD)

        Returns:
            Converted amount in target currency
        """
        if from_currency == to_currency:
            return amount

        try:
            params = {
                "from": from_currency,
                "to": to_currency
            }
            response = requests.get(self.frankfurter_base, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if "rates" in data and to_currency in data["rates"]:
                rate = data["rates"][to_currency]
                return round(amount * rate, 2)
            else:
                # If conversion fails, return original amount
                return amount
        except Exception as e:
            print(f"[WARN] Currency conversion failed: {str(e)}, using original amount")
            return amount

    def extract_features_from_text(self, text: str, our_features: str) -> tuple:
        """
        Extract features mentioned in text and calculate feature parity percentage.

        Args:
            text: Text describing competitor's product
            our_features: Our product's feature list

        Returns:
            (list of matched features, parity percentage)
        """
        our_features_list = [f.strip().lower() for f in our_features.split(",")]
        matched_features = []

        text_lower = text.lower()
        for feature in our_features_list:
            if feature in text_lower:
                matched_features.append(feature)

        # Calculate parity as percentage of our features found in competitor's description
        parity = (len(matched_features) / len(our_features_list) * 100) if our_features_list else 0
        return matched_features, round(parity, 0)

    def check_margin_feasibility(self, competitor_price: float, our_cost: float, margin_floor: int) -> bool:
        """
        Check if we can match competitor's price while maintaining margin floor.

        Margin formula: (Price - Cost) / Price * 100

        Args:
            competitor_price: Competitor's price
            our_cost: Our product's cost
            margin_floor: Minimum margin percentage required

        Returns:
            True if we can match the price and maintain margin floor
        """
        if competitor_price <= our_cost:
            return False

        margin = ((competitor_price - our_cost) / competitor_price) * 100
        return margin >= margin_floor

    def research_product(self, product_data: dict) -> dict:
        """
        Research competitors for a given product using Tavily Search.

        Args:
            product_data: Product dict from RAG retrieval with keys:
                - name: Product name
                - category: Product category
                - price: Our product's price
                - cost: Our product's cost
                - margin_floor: Minimum margin percentage
                - features: Product features
                - competitor: Our competitor name

        Returns:
            dict with competitors, research summary, and sources
        """
        try:
            product_name = product_data.get("name", "")
            category = product_data.get("category", "")
            our_price = product_data.get("price", 0)
            our_cost = product_data.get("cost", 0)
            margin_floor = product_data.get("margin_floor", 30)
            our_features = product_data.get("features", "")

            if not product_name:
                return {
                    "error": "Product name not provided",
                    "product_name": "",
                    "competitors": [],
                    "research_summary": "",
                    "sources": []
                }

            # Build Tavily search query
            search_query = f"{product_name} {category} price features"

            # Search for competitors
            tavily_response = self.tavily_client.search(
                query=search_query,
                include_answer=False,
                max_results=5
            )

            competitors = []
            sources = set()

            # Process Tavily results
            if tavily_response.get("results"):
                for result in tavily_response.get("results", [])[:5]:
                    # Extract basic info from search result
                    title = result.get("title", "")
                    content = result.get("content", "")
                    url = result.get("url", "")

                    sources.add(url)

                    # Try to extract competitor name and price from content
                    # This is heuristic-based; in production, you'd use a more robust parser
                    competitor_info = self._parse_competitor_info(
                        title,
                        content,
                        our_features,
                        our_price,
                        our_cost,
                        margin_floor
                    )

                    if competitor_info:
                        competitor_info["source"] = url
                        competitors.append(competitor_info)

            # Generate research summary
            if competitors:
                cheapest = min(competitors, key=lambda x: x["price_normalized"])
                most_featured = max(competitors, key=lambda x: x["feature_parity"])

                summary = f"Found {len(competitors)} competitor(s). "
                summary += f"Cheapest: {cheapest['name']} at ${cheapest['price_normalized']:.2f} "
                summary += f"({cheapest['price_gap']:+.2f} vs ours). "
                summary += f"Most featured: {most_featured['name']} ({most_featured['feature_parity']:.0f}% parity). "
                summary += f"Margin feasibility: {sum(1 for c in competitors if c['margin_feasible'])}/{len(competitors)} matchable."
            else:
                summary = "No direct competitors found in search results."

            return {
                "product_name": product_name,
                "our_price": our_price,
                "our_features": our_features,
                "competitors": competitors[:3],  # Top 3 competitors
                "research_summary": summary,
                "sources": sorted(list(sources))
            }

        except Exception as e:
            return {
                "error": f"Research failed: {str(e)}",
                "product_name": product_data.get("name", ""),
                "competitors": [],
                "research_summary": "",
                "sources": []
            }

    def _parse_competitor_info(self, title: str, content: str, our_features: str,
                              our_price: float, our_cost: float, margin_floor: int) -> Optional[dict]:
        """
        Parse competitor information from search result title and content.

        Args:
            title: Search result title
            content: Search result content
            our_features: Our product features
            our_price: Our product price
            our_cost: Our product cost
            margin_floor: Minimum margin percentage

        Returns:
            dict with competitor info or None if parsing fails
        """
        try:
            # Extract competitor name (usually in title before product name)
            competitor_name = self._extract_competitor_name(title)
            if not competitor_name:
                return None

            # Extract price from content (look for $ patterns)
            price_found = self._extract_price(content)
            if price_found is None:
                return None

            # Detect currency and convert to USD if needed
            currency = self._detect_currency(content)
            price_normalized = self.convert_currency(price_found, currency, "USD")

            # Extract features and calculate parity
            matched_features, feature_parity = self.extract_features_from_text(content, our_features)

            # Check margin feasibility
            margin_feasible = self.check_margin_feasibility(price_normalized, our_cost, margin_floor)

            # Calculate price gap
            price_gap = price_normalized - our_price

            return {
                "name": title.split("|")[0].strip() if "|" in title else title[:50],
                "competitor_name": competitor_name,
                "price_usd": price_found,
                "price_normalized": price_normalized,
                "features": ", ".join(matched_features[:5]) if matched_features else "Not found",
                "feature_parity": feature_parity,
                "price_gap": round(price_gap, 2),
                "margin_feasible": margin_feasible
            }
        except Exception as e:
            return None

    def _extract_competitor_name(self, title: str) -> Optional[str]:
        """
        Extract competitor brand name from search result title.
        Common brands: Apple, Samsung, Sony, Bose, Anker, Google, Microsoft, etc.
        """
        brands = [
            "Apple", "Samsung", "Sony", "Bose", "Anker", "Google", "Microsoft",
            "Garmin", "Fitbit", "JBL", "Sennheiser", "Beats", "Skullcandy",
            "Jabra", "Bang & Olufsen", "Astro", "HyperX"
        ]

        for brand in brands:
            if brand.lower() in title.lower():
                return brand

        # Fallback: try to extract first word if it looks like a brand
        words = title.split()
        if words:
            return words[0]

        return None

    def _extract_price(self, content: str) -> Optional[float]:
        """
        Extract price value from content.
        Looks for patterns like $299, $29.99, etc.
        """
        import re

        # Pattern for prices like $299.99 or $299
        price_patterns = [
            r'\$(\d+(?:,\d{3})*\.?\d*)',  # $299 or $299.99 or $1,299.99
            r'USD\s*(\d+(?:,\d{3})*\.?\d*)',  # USD 299
            r'(\d+(?:,\d{3})*\.?\d*)\s*(?:USD|dollars?)',  # 299 USD
        ]

        for pattern in price_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(",", "")
                try:
                    return float(price_str)
                except ValueError:
                    continue

        return None

    def _detect_currency(self, content: str) -> str:
        """
        Detect currency from content text.
        Returns currency code (USD, EUR, GBP, etc.)
        """
        currencies = {
            "USD": ["$", "USD", "dollar", "dollars"],
            "EUR": ["€", "EUR", "euro", "euros"],
            "GBP": ["£", "GBP", "pound", "pounds"],
            "JPY": ["¥", "JPY", "yen"],
            "INR": ["₹", "INR", "rupee", "rupees"],
            "CAD": ["CAD", "canadian dollar"],
            "AUD": ["AUD", "australian dollar"],
        }

        content_lower = content.lower()

        # Check for explicit currency mentions (higher priority)
        for currency, keywords in currencies.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    return currency

        # Default to USD if no currency found
        return "USD"


def research_agent(product_data: dict) -> dict:
    """
    Standalone research agent function.

    Args:
        product_data: Single product dict from RAG retrieval

    Returns:
        dict with competitor data, research summary, and sources
    """
    agent = ResearchAgent()
    return agent.research_product(product_data)


def research_from_rag_output(rag_output: dict) -> List[dict]:
    """
    Process all products from RAG output and research each one.

    Args:
        rag_output: Output from rag_agent.retrieve() with:
            - query: search query
            - product_data: list of product dicts
            - policy_snippet: policy text

    Returns:
        List of research_output dicts (one per product in RAG output)
    """
    results = []
    products = rag_output.get("product_data", [])

    for product in products:
        research_result = research_agent(product)
        results.append(research_result)

    return results


# Test the research agent
if __name__ == "__main__":
    print("\n[TEST] Research Agent Testing with Mock RAG Data...\n")

    # Import mock data
    from mock_data import get_mock_rag_output, get_single_product_from_rag

    # Test 1: Single product
    print("="*80)
    print("TEST 1: Single Product Research")
    print("="*80 + "\n")

    rag_output = get_mock_rag_output("earbuds")
    product = get_single_product_from_rag(rag_output, 0)

    print(f"Product: {product['name']}")
    print(f"Price: ${product['price']:.2f} | Cost: ${product['cost']:.2f} | Margin Floor: {product['margin_floor']}%\n")

    result = research_agent(product)

    if "error" in result:
        print(f"[ERROR] {result['error']}\n")
    else:
        print(f"[RESEARCH] {result['research_summary']}\n")

        if result["competitors"]:
            print("[COMPETITORS] Found:")
            for comp in result["competitors"]:
                print(f"\n  Name: {comp['name']}")
                print(f"  Competitor: {comp['competitor_name']}")
                print(f"  Price: ${comp['price_normalized']:.2f} (gap: {comp['price_gap']:+.2f})")
                print(f"  Feature Parity: {comp['feature_parity']:.0f}%")
                print(f"  Margin Feasible: {comp['margin_feasible']}")
        else:
            print("[COMPETITORS] No competitors found")

        print(f"\n[SOURCES] {len(result['sources'])} sources")

    # Test 2: Multiple products from RAG output
    print("\n" + "="*80)
    print("TEST 2: Processing RAG Output with Multiple Products")
    print("="*80 + "\n")

    rag_output = get_mock_rag_output("smartwatch")
    print(f"Query: {rag_output['query']}")
    print(f"Products: {len(rag_output['product_data'])} items\n")

    research_results = research_from_rag_output(rag_output)

    for i, (product, research) in enumerate(zip(rag_output["product_data"], research_results)):
        print(f"[{i+1}] {product['name']} - ${product['price']:.2f}")
        if "error" not in research:
            summary = research['research_summary'][:80]
            print(f"    [OK] {summary}...")
        else:
            print(f"    [ERROR] {research.get('error', 'Unknown error')}")
        print()

    print("[SUCCESS] Research Agent test complete!\n")
