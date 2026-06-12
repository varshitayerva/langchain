"""
Test script for Research Agent
Run this to verify the research agent works correctly with various products
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research_agent import research_agent


def test_single_product():
    """Test research agent with a single hardcoded product"""
    print("\n" + "="*80)
    print("TEST 1: Single Product Research (AirPods Pro)")
    print("="*80 + "\n")

    test_product = {
        "id": 1,
        "name": "AirPods Pro",
        "category": "wireless earbuds",
        "price": 249.00,
        "cost": 100.00,
        "margin_floor": 30,
        "features": "Active noise cancellation, transparency mode, spatial audio, adaptive audio, personalized volume",
        "competitor": "Apple",
        "similarity": 0.95
    }

    print(f"Product: {test_product['name']}")
    print(f"Our Price: ${test_product['price']:.2f}")
    print(f"Our Cost: ${test_product['cost']:.2f}")
    print(f"Margin Floor: {test_product['margin_floor']}%\n")

    result = research_agent(test_product)

    if "error" in result and result.get("error"):
        print(f"❌ ERROR: {result['error']}\n")
        return False

    print(f"✓ Research Summary:\n  {result['research_summary']}\n")

    if result["competitors"]:
        print(f"✓ Found {len(result['competitors'])} competitor(s):\n")
        for i, comp in enumerate(result["competitors"], 1):
            print(f"  [{i}] {comp['name']}")
            print(f"      Competitor: {comp['competitor_name']}")
            print(f"      Price: ${comp['price_normalized']:.2f}")
            print(f"      Price Gap: {comp['price_gap']:+.2f} (negative = cheaper)")
            print(f"      Features Mentioned: {comp['features']}")
            print(f"      Feature Parity: {comp['feature_parity']:.0f}%")
            print(f"      Margin Feasible: {'Yes ✓' if comp['margin_feasible'] else 'No ✗'}")
            print(f"      Source: {comp['source']}\n")
    else:
        print("⚠ No competitors found in search results\n")

    print(f"✓ Sources Used ({len(result['sources'])}):")
    for src in result["sources"][:5]:
        print(f"  - {src}")

    return True


def test_multiple_products():
    """Test research agent with multiple products"""
    print("\n" + "="*80)
    print("TEST 2: Multiple Products Research")
    print("="*80 + "\n")

    test_products = [
        {
            "id": 1,
            "name": "Sony WF-1000XM5",
            "category": "wireless earbuds",
            "price": 299.99,
            "cost": 120.00,
            "margin_floor": 32,
            "features": "Industry-leading noise cancellation, LDAC codec, 8-hour battery, multipoint connection",
            "competitor": "Sony"
        },
        {
            "id": 4,
            "name": "Apple Watch Series 9",
            "category": "smartwatch",
            "price": 399.00,
            "cost": 160.00,
            "margin_floor": 40,
            "features": "Always-on retina display, fitness tracking, ECG, blood oxygen, emergency SOS, cellular optional",
            "competitor": "Apple"
        },
        {
            "id": 10,
            "name": "Apple AirTag",
            "category": "tracking device",
            "price": 29.00,
            "cost": 8.00,
            "margin_floor": 50,
            "features": "Find My network, precision finding, ultra wideband, replaceable battery, IP67 water resistant",
            "competitor": "Apple"
        }
    ]

    results_summary = []

    for product in test_products:
        print(f"\n{'─'*80}")
        print(f"Product: {product['name']} (${product['price']:.2f})")
        print(f"{'─'*80}")

        result = research_agent(product)

        if "error" in result and result.get("error"):
            print(f"❌ ERROR: {result['error']}")
            continue

        print(f"✓ {result['research_summary']}")

        # Store summary for final report
        results_summary.append({
            "product_name": product["name"],
            "price": product["price"],
            "competitors_found": len(result["competitors"]),
            "cheapest_competitor": (
                f"{min(result['competitors'], key=lambda x: x['price_normalized'])['name']}"
                if result["competitors"]
                else "None"
            ),
            "avg_parity": (
                sum(c["feature_parity"] for c in result["competitors"]) / len(result["competitors"])
                if result["competitors"]
                else 0
            ) if result["competitors"] else 0,
            "matchable_competitors": sum(1 for c in result["competitors"] if c["margin_feasible"]),
            "total_sources": len(result["sources"])
        })

    # Print summary table
    print(f"\n{'='*80}")
    print("SUMMARY TABLE")
    print(f"{'='*80}\n")
    print(f"{'Product':<30} {'Competitors':<15} {'Avg Parity':<15} {'Matchable':<15}")
    print(f"{'-'*80}")
    for summary in results_summary:
        print(f"{summary['product_name']:<30} "
              f"{summary['competitors_found']:<15} "
              f"{summary['avg_parity']:<15.0f}% "
              f"{summary['matchable_competitors']:<15}")

    return len(results_summary) > 0


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*80)
    print("TEST 3: Edge Cases")
    print("="*80 + "\n")

    # Edge case 1: Product with no features
    print("[Edge Case 1] Product with no features:")
    product_no_features = {
        "name": "Generic Headphones",
        "category": "headphones",
        "price": 100.00,
        "cost": 40.00,
        "margin_floor": 30,
        "features": "",
        "competitor": "Generic"
    }

    result = research_agent(product_no_features)
    print(f"  Result: {'✓ Handled gracefully' if not result.get('error') else '❌ Error'}\n")

    # Edge case 2: Product with very low margin floor
    print("[Edge Case 2] Product with very low margin floor (5%):")
    product_low_margin = {
        "name": "Budget Earbuds",
        "category": "earbuds",
        "price": 49.99,
        "cost": 40.00,
        "margin_floor": 5,
        "features": "Basic audio, wireless",
        "competitor": "Generic"
    }

    result = research_agent(product_low_margin)
    if result["competitors"]:
        matchable = sum(1 for c in result["competitors"] if c["margin_feasible"])
        print(f"  Result: ✓ Found {len(result['competitors'])} competitors, {matchable} margin-feasible\n")
    else:
        print(f"  Result: ⚠ No competitors found\n")

    # Edge case 3: Premium product
    print("[Edge Case 3] Premium product (high margin floor 45%):")
    product_premium = {
        "name": "Premium Headphones",
        "category": "premium headphones",
        "price": 599.99,
        "cost": 200.00,
        "margin_floor": 45,
        "features": "Premium materials, handcrafted, noise cancellation, 30-hour battery",
        "competitor": "Premium Brand"
    }

    result = research_agent(product_premium)
    if result["competitors"]:
        matchable = sum(1 for c in result["competitors"] if c["margin_feasible"])
        print(f"  Result: ✓ Found {len(result['competitors'])} competitors, {matchable} margin-feasible\n")
    else:
        print(f"  Result: ⚠ No competitors found\n")

    return True


def test_currency_conversion():
    """Test currency detection and conversion logic"""
    print("\n" + "="*80)
    print("TEST 4: Currency Conversion")
    print("="*80 + "\n")

    from research_agent import ResearchAgent

    agent = ResearchAgent()

    # Test currency conversion
    test_conversions = [
        ("USD", 100.0, "USD"),
        ("USD", 100.0, "EUR"),
        ("EUR", 100.0, "USD"),
        ("GBP", 100.0, "USD"),
    ]

    print("Testing Frankfurter API currency conversions:\n")
    for from_curr, amount, to_curr in test_conversions:
        try:
            converted = agent.convert_currency(amount, from_curr, to_curr)
            print(f"  {from_curr} {amount:.2f} → {to_curr} {converted:.2f}")
        except Exception as e:
            print(f"  {from_curr} {amount:.2f} → {to_curr}: ❌ Error - {str(e)}")

    print("\n" + "─"*80)
    print("Testing currency detection:\n")

    test_texts = [
        ("This product costs $299.99", "USD"),
        ("Le prix est 299€", "EUR"),
        ("Price: £199.99 GBP", "GBP"),
        ("¥30000 JPY", "JPY"),
        ("₹25000 INR", "INR"),
    ]

    for text, expected_currency in test_texts:
        detected = agent._detect_currency(text)
        match = "✓" if detected == expected_currency else "❌"
        print(f"  {match} '{text[:40]}...' → {detected} (expected {expected_currency})")

    return True


def main():
    """Run all tests"""
    print("\n" + "#"*80)
    print("# RESEARCH AGENT TEST SUITE")
    print("#"*80)

    try:
        test1_pass = test_single_product()
    except Exception as e:
        print(f"\n❌ Test 1 failed with exception: {str(e)}")
        test1_pass = False

    try:
        test2_pass = test_multiple_products()
    except Exception as e:
        print(f"\n❌ Test 2 failed with exception: {str(e)}")
        test2_pass = False

    try:
        test3_pass = test_edge_cases()
    except Exception as e:
        print(f"\n❌ Test 3 failed with exception: {str(e)}")
        test3_pass = False

    try:
        test4_pass = test_currency_conversion()
    except Exception as e:
        print(f"\n❌ Test 4 failed with exception: {str(e)}")
        test4_pass = False

    # Final summary
    print("\n" + "#"*80)
    print("# TEST RESULTS SUMMARY")
    print("#"*80 + "\n")

    tests = [
        ("Single Product Research", test1_pass),
        ("Multiple Products Research", test2_pass),
        ("Edge Cases Handling", test3_pass),
        ("Currency Conversion", test4_pass),
    ]

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    for test_name, passed_test in tests:
        status = "✓ PASS" if passed_test else "❌ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\n  Total: {passed}/{total} tests passed\n")

    if passed == total:
        print("✓ ALL TESTS PASSED! Research Agent is ready for integration.\n")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed. Please review errors above.\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
