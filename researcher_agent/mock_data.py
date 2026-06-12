"""
Mock data for testing Research Agent with RAG output format.
This simulates what comes from Sowmya's RAG Agent.
"""

# Mock RAG output (as if coming from rag_agent.retrieve())
MOCK_RAG_OUTPUT = {
    "query": "wireless earbuds with noise cancellation",
    "product_data": [
        {
            "id": 1,
            "name": "AirPods Pro",
            "category": "wireless earbuds",
            "price": 249.00,
            "cost": 100.00,
            "margin_floor": 30,
            "features": "Active noise cancellation, transparency mode, spatial audio, adaptive audio, personalized volume",
            "competitor": "Apple",
            "similarity": 0.95
        },
        {
            "id": 2,
            "name": "Samsung Galaxy Buds2 Pro",
            "category": "wireless earbuds",
            "price": 229.99,
            "cost": 92.00,
            "margin_floor": 35,
            "features": "Active noise cancellation, ambient sound, IPX7 water resistance, touch controls",
            "competitor": "Samsung",
            "similarity": 0.89
        },
        {
            "id": 3,
            "name": "Sony WF-1000XM5",
            "category": "wireless earbuds",
            "price": 299.99,
            "cost": 120.00,
            "margin_floor": 32,
            "features": "Industry-leading noise cancellation, LDAC codec, 8-hour battery, multipoint connection",
            "competitor": "Sony",
            "similarity": 0.87
        }
    ],
    "policy_snippet": """### Margin Floor Requirements
All products must maintain a minimum gross margin of the specified margin floor percentage.
Margin calculation: (Price - Cost) / Price * 100

### Price Matching Rules
1. We can match competitor prices if the resulting margin is >= margin floor
2. We cannot price below our cost + 5% handling buffer
3. Price changes must be approved if they reduce margin below 35%

### Feature Parity Requirements
- If competitor has feature parity within 5% of our feature set, price difference must not exceed 10%
- If competitor has 10-30% more features, we can price up to 15% higher
- If competitor has >30% more features, we must match or undercut by 5%"""
}

# Mock smartwatch products
MOCK_RAG_OUTPUT_SMARTWATCH = {
    "query": "affordable smartwatch under $400",
    "product_data": [
        {
            "id": 4,
            "name": "Apple Watch Series 9",
            "category": "smartwatch",
            "price": 399.00,
            "cost": 160.00,
            "margin_floor": 40,
            "features": "Always-on retina display, fitness tracking, ECG, blood oxygen, emergency SOS, cellular optional",
            "competitor": "Apple",
            "similarity": 0.92
        },
        {
            "id": 5,
            "name": "Samsung Galaxy Watch 6",
            "category": "smartwatch",
            "price": 299.99,
            "cost": 120.00,
            "margin_floor": 38,
            "features": "AMOLED display, heart rate monitor, sleep tracking, water resistant, 40+ watch faces",
            "competitor": "Samsung",
            "similarity": 0.88
        },
        {
            "id": 6,
            "name": "Garmin Epix Gen 2",
            "category": "smartwatch",
            "price": 499.99,
            "cost": 200.00,
            "margin_floor": 35,
            "features": "AMOLED display, multi-GNSS, 11-day battery, training metrics, maps, music storage",
            "competitor": "Garmin",
            "similarity": 0.85
        }
    ],
    "policy_snippet": """### Margin Floor Requirements
All products must maintain a minimum gross margin of the specified margin floor percentage.

### Competitive Response Timeline
- Premium tier products (>$200): Response within 14 days
- Mid-tier products ($100-200): Response within 7 days
- Budget tier products (<$100): Response within 3 days"""
}

# Mock headphones products
MOCK_RAG_OUTPUT_HEADPHONES = {
    "query": "premium over-ear headphones with noise cancellation",
    "product_data": [
        {
            "id": 7,
            "name": "Sony WH-1000XM5 Headphones",
            "category": "over-ear headphones",
            "price": 399.99,
            "cost": 160.00,
            "margin_floor": 33,
            "features": "Industry-leading ANC, 30-hour battery, multipoint connection, lightweight design",
            "competitor": "Sony",
            "similarity": 0.91
        },
        {
            "id": 8,
            "name": "Bose QuietComfort 45",
            "category": "over-ear headphones",
            "price": 379.95,
            "cost": 150.00,
            "margin_floor": 32,
            "features": "Acoustic noise cancelling, comfortable design, 24-hour battery, USB-C charging",
            "competitor": "Bose",
            "similarity": 0.88
        },
        {
            "id": 9,
            "name": "Anker Soundcore Space Q45",
            "category": "over-ear headphones",
            "price": 99.99,
            "cost": 40.00,
            "margin_floor": 45,
            "features": "Adaptive ANC, 50-hour battery, quick charge, spatial audio, lightweight",
            "competitor": "Anker",
            "similarity": 0.82
        }
    ],
    "policy_snippet": """### Approval Levels
- Margin reduction 0-5%: Automatic approval if features competitive
- Margin reduction 5-10%: Product manager approval required
- Margin reduction >10%: CFO + Product manager approval required
- Below margin floor: BLOCKED - no approval possible"""
}

# Mock budget products
MOCK_RAG_OUTPUT_BUDGET = {
    "query": "affordable tracking device under $50",
    "product_data": [
        {
            "id": 10,
            "name": "Apple AirTag",
            "category": "tracking device",
            "price": 29.00,
            "cost": 8.00,
            "margin_floor": 50,
            "features": "Find My network, precision finding, ultra wideband, replaceable battery, IP67 water resistant",
            "competitor": "Apple",
            "similarity": 0.94
        }
    ],
    "policy_snippet": """### Margin Floor Requirements
All products must maintain a minimum gross margin of the specified margin floor percentage."""
}


def get_mock_rag_output(category: str = "earbuds"):
    """
    Get mock RAG output for testing based on category.

    Args:
        category: One of "earbuds", "smartwatch", "headphones", "budget"

    Returns:
        Mock RAG output dict matching the schema
    """
    category_map = {
        "earbuds": MOCK_RAG_OUTPUT,
        "smartwatch": MOCK_RAG_OUTPUT_SMARTWATCH,
        "headphones": MOCK_RAG_OUTPUT_HEADPHONES,
        "budget": MOCK_RAG_OUTPUT_BUDGET,
    }

    return category_map.get(category.lower(), MOCK_RAG_OUTPUT)


def get_single_product_from_rag(rag_output: dict, product_index: int = 0) -> dict:
    """
    Extract a single product from RAG output.

    Args:
        rag_output: RAG output dict from Sowmya's rag_agent
        product_index: Index of product in product_data list

    Returns:
        Single product dict
    """
    products = rag_output.get("product_data", [])
    if product_index < len(products):
        return products[product_index]
    raise IndexError(f"Product index {product_index} out of range (max: {len(products)-1})")


if __name__ == "__main__":
    print("\n[MOCK DATA] Available categories:")
    print("  - earbuds (3 products)")
    print("  - smartwatch (3 products)")
    print("  - headphones (3 products)")
    print("  - budget (1 product)\n")

    print("[SAMPLE] Earbuds - First product:")
    earbuds_rag = get_mock_rag_output("earbuds")
    first_product = get_single_product_from_rag(earbuds_rag, 0)
    print(f"  {first_product['name']} - ${first_product['price']:.2f}")
    print(f"  Category: {first_product['category']}")
    print(f"  Margin Floor: {first_product['margin_floor']}%\n")

    print("[SAMPLE] All earbuds products:")
    for i, product in enumerate(earbuds_rag["product_data"]):
        print(f"  [{i}] {product['name']} - ${product['price']:.2f}")
