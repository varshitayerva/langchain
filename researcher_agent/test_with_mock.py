"""
Test Research Agent with Mock RAG data - no live Tavily API calls.
This demonstrates the flow: RAG Output → Research Agent → Research Output
"""

import json
from mock_data import (
    get_mock_rag_output,
    get_single_product_from_rag,
    MOCK_RAG_OUTPUT,
    MOCK_RAG_OUTPUT_SMARTWATCH,
    MOCK_RAG_OUTPUT_HEADPHONES
)


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80 + "\n")


def display_rag_output(rag_output, max_products=3):
    """Display RAG output structure"""
    print(f"[RAG Query]: {rag_output['query']}\n")

    products = rag_output.get("product_data", [])
    print(f"[RAG Products]: {len(products)} items\n")

    for i, product in enumerate(products[:max_products]):
        print(f"  [{i}] {product['name']}")
        print(f"      Price: ${product['price']:.2f} | Cost: ${product['cost']:.2f} | Margin Floor: {product['margin_floor']}%")
        print(f"      Category: {product['category']}")
        print(f"      Similarity: {product.get('similarity', 'N/A')}")
        print()


def display_single_product(product):
    """Display a single product details"""
    print(f"Product Details:")
    print(f"  Name: {product['name']}")
    print(f"  Category: {product['category']}")
    print(f"  Price: ${product['price']:.2f}")
    print(f"  Cost: ${product['cost']:.2f}")
    print(f"  Margin Floor: {product['margin_floor']}%")
    print(f"  Features: {product['features']}")
    print(f"  Competitor: {product['competitor']}")
    print()


def test_rag_to_research_flow():
    """Test the complete flow from RAG output to Research Agent"""

    print_section("TEST 1: RAG Output Structure (From Sowmya)")

    # Get RAG output from Sowmya's rag_agent
    rag_output = get_mock_rag_output("earbuds")
    display_rag_output(rag_output)

    print_section("TEST 2: Extract Single Product from RAG (Your Input)")

    # Extract a single product from RAG output
    product_index = 0
    product = get_single_product_from_rag(rag_output, product_index)
    display_single_product(product)

    print_section("TEST 3: Show Expected Research Agent Output Structure")

    # Show what your research_agent() should output
    expected_output = {
        "product_name": product["name"],
        "our_price": product["price"],
        "our_features": product["features"],
        "competitors": [
            {
                "name": "Samsung Galaxy Buds2 Pro",
                "competitor_name": "Samsung",
                "price_usd": 229.99,
                "price_normalized": 229.99,
                "features": "Active noise cancellation, ambient sound",
                "feature_parity": 75.0,
                "price_gap": -19.01,  # negative = they're cheaper
                "margin_feasible": True,
                "source": "https://samsung.com/..."
            },
            {
                "name": "Sony WF-1000XM5",
                "competitor_name": "Sony",
                "price_usd": 299.99,
                "price_normalized": 299.99,
                "features": "Industry-leading noise cancellation, LDAC codec",
                "feature_parity": 85.0,
                "price_gap": 50.00,  # positive = we're cheaper
                "margin_feasible": True,
                "source": "https://sony.com/..."
            }
        ],
        "research_summary": "Found 2 competitors. Samsung is 8% cheaper with 75% feature parity. Sony is premium at +20%.",
        "sources": ["https://samsung.com/...", "https://sony.com/..."]
    }

    print("Your research_agent() should return:")
    print(json.dumps(expected_output, indent=2))

    print_section("TEST 4: Data Flow Diagram")

    print("""
    INPUT (from Sowmya's RAG Agent):
    - RAG Query: "wireless earbuds with noise cancellation"
    - Products Retrieved: [AirPods Pro, Samsung Galaxy Buds2 Pro, Sony WF-1000XM5]
    - Policy Snippet: [pricing rules, margin requirements]

    YOUR RESEARCH AGENT (takes 1 product at a time):
    - Input: AirPods Pro dict
      - Calls Tavily: Search "AirPods Pro wireless earbuds price features"
      - Parses Results: Extract competitor names, prices, features
      - Converts Currency: EUR >> USD (via Frankfurter)
      - Calculates: Feature parity %, margin feasibility
      - Returns: research_output dict
    - Output: { competitors: [...], research_summary: "...", sources: [...] }

    OUTPUT (to Pavan's Synthesis Agent):
    - product_name: "AirPods Pro"
    - our_price: 249.00
    - competitors: [Samsung, Sony, etc] (up to 3)
    - research_summary: "Found 2 competitors..."
    - sources: [URLs for citations]
    """)

    print_section("TEST 5: Testing Multiple Categories")

    categories = [
        ("earbuds", "Wireless Earbuds"),
        ("smartwatch", "Smartwatches"),
        ("headphones", "Over-Ear Headphones"),
        ("budget", "Budget Tracking Devices")
    ]

    for category_key, category_name in categories:
        rag_output = get_mock_rag_output(category_key)
        products = rag_output.get("product_data", [])

        print(f"\n[{category_name}] Category:")
        print(f"  Query: {rag_output['query']}")
        print(f"  Products to research: {len(products)}")

        for product in products[:2]:  # Show first 2
            print(f"    - {product['name']} (${product['price']:.2f})")

    print_section("TEST 6: Margin Feasibility Check (Your Logic)")

    # Demonstrate margin calculation
    test_products = [
        {
            "name": "AirPods Pro",
            "price": 249.00,
            "cost": 100.00,
            "margin_floor": 30
        },
        {
            "name": "Samsung Buds",
            "price": 229.99,
            "cost": 92.00,
            "margin_floor": 35
        }
    ]

    print("Checking if we can match competitor prices:\n")

    for product in test_products:
        our_price = product["price"]
        our_cost = product["cost"]
        margin_floor = product["margin_floor"]

        # Try matching a cheaper competitor
        competitor_price = our_price * 0.9  # 10% cheaper

        if competitor_price <= our_cost:
            feasible = False
            reason = "Below cost"
        else:
            margin = ((competitor_price - our_cost) / competitor_price) * 100
            feasible = margin >= margin_floor
            reason = f"Margin {margin:.1f}% {'>' if feasible else '<'} floor {margin_floor}%"

        status = "FEASIBLE" if feasible else "NOT FEASIBLE"
        print(f"  {product['name']}")
        print(f"    Current price: ${our_price:.2f}")
        print(f"    Competitor price (90%): ${competitor_price:.2f}")
        print(f"    {reason}")
        print(f"    Status: {status}\n")

    print_section("TEST 7: Feature Parity Calculation (Your Logic)")

    our_features = "Active noise cancellation, transparency mode, spatial audio, adaptive audio, personalized volume"
    competitor_features = "Active noise cancellation, ambient sound, water resistance, touch controls"

    print(f"Our Features ({len(our_features.split(','))} total):")
    for f in our_features.split(","):
        print(f"  - {f.strip()}")

    print(f"\nCompetitor Features:")
    for f in competitor_features.split(","):
        print(f"  - {f.strip()}")

    # Simple matching
    our_feature_list = [f.strip().lower() for f in our_features.split(",")]
    competitor_list = competitor_features.lower()

    matched = sum(1 for f in our_feature_list if f in competitor_list)
    parity = (matched / len(our_feature_list)) * 100

    print(f"\nFeature Parity Calculation:")
    print(f"  Matched features: {matched}/{len(our_feature_list)}")
    print(f"  Parity %: {parity:.0f}%")


if __name__ == "__main__":
    print("\n" + "#"*80)
    print("# RESEARCH AGENT - RAG INTEGRATION TEST")
    print("# Testing the flow: RAG Output >> Research Agent >> Synthesis Input")
    print("#"*80)

    test_rag_to_research_flow()

    print("\n" + "#"*80)
    print("# TESTS COMPLETE")
    print("#"*80 + "\n")

    print("Next Steps:")
    print("  1. Run: python research_agent.py (tests with mock data)")
    print("  2. Update: research_agent.py with Tavily API integration")
    print("  3. Test: with real competitor searches")
    print()
