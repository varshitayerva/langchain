#!/usr/bin/env python3
"""
MarginGuard API Test Script

Run this to test the backend API without the frontend.
Usage:
    python test_api.py
"""

import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000"


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def test_health():
    """Test health endpoint"""
    print("🧪 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Response: {json.dumps(response.json(), indent=2)}\n")
            return True
        else:
            print(f"✗ Unexpected status: {response.status_code}\n")
            return False
    except Exception as e:
        print(f"✗ Error: {e}\n")
        print("   Make sure backend is running: cd api && python main.py\n")
        return False


def test_upload_policy():
    """Test policy upload"""
    print("🧪 Testing policy upload...")

    try:
        # Create test file
        test_content = """COMPANY POLICY DOCUMENT

1. PRICING POLICY
All pricing must follow market-based pricing strategies. Minimum margin floor is 25%.

2. FEATURE PARITY REQUIREMENTS
Products must maintain at least 70% feature parity with competitive offerings.

3. COMPLIANCE RULES
All competitive pricing decisions must be reviewed by policy team.
"""

        with open("test_policy.txt", "w") as f:
            f.write(test_content)

        with open("test_policy.txt", "rb") as f:
            files = {"file": f}
            response = requests.post(f"{BASE_URL}/upload-policy", files=files, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Sections uploaded: {data.get('sections_uploaded', 0)}")
            print(f"✓ Message: {data.get('message', '')}\n")
            return True
        else:
            print(f"✗ Status: {response.status_code}")
            print(f"✗ Response: {response.text}\n")
            return False
    except Exception as e:
        print(f"✗ Error: {e}\n")
        return False


def test_analysis():
    """Test full analysis flow"""
    print("🧪 Starting analysis...")

    try:
        # Start analysis
        response = requests.get(
            f"{BASE_URL}/analyze",
            params={"product": "AirPods Pro"},
            timeout=10
        )

        if response.status_code != 200:
            print(f"✗ Failed to start analysis: {response.status_code}")
            print(f"✗ Response: {response.text}\n")
            return False

        data = response.json()
        execution_id = data.get("execution_id")
        print(f"✓ Analysis started")
        print(f"✓ Execution ID: {execution_id}\n")

        # Poll status
        print("🧪 Polling status (waiting for completion)...\n")
        last_step = 0

        for attempt in range(120):  # Try for up to 2 minutes
            try:
                response = requests.get(
                    f"{BASE_URL}/status",
                    params={"id": execution_id},
                    timeout=5
                )

                if response.status_code != 200:
                    continue

                status_data = response.json()
                current_step = status_data.get("step", 0)
                status = status_data.get("status", "unknown")
                message = status_data.get("message", "")
                progress = status_data.get("progress", 0)

                # Print only when step changes
                if current_step != last_step:
                    print(f"  Step {current_step}/4: {message} ({progress:.0f}%)")
                    last_step = current_step

                if status == "completed":
                    print(f"\n✓ Analysis completed!\n")
                    return True, execution_id
                elif status == "failed":
                    print(f"\n✗ Analysis failed: {message}\n")
                    return False, None

            except Exception as e:
                print(f"  (polling... attempt {attempt + 1})")
                pass

            time.sleep(1)

        print(f"\n✗ Analysis timed out (>2 minutes)\n")
        return False, None

    except Exception as e:
        print(f"✗ Error: {e}\n")
        return False, None


def test_results(execution_id):
    """Fetch and display results"""
    print("🧪 Fetching results...")

    try:
        response = requests.get(
            f"{BASE_URL}/result",
            params={"id": execution_id},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            status = result.get("status")

            if status == "success":
                data = result.get("data", {})
                print(f"✓ Status: {status}")
                print(f"✓ Product: {data.get('product_query', 'N/A')}")

                research_results = data.get('research_results', [])
                print(f"✓ Competitors found: {len(research_results)}")

                if research_results:
                    print(f"\n📊 Competitor Sample:")
                    comp = research_results[0]
                    print(f"   - Name: {comp.get('competitor_name', 'N/A')}")
                    print(f"   - Price: ${comp.get('price_normalized', 0):.2f}")
                    print(f"   - Feature Parity: {comp.get('feature_parity', 0)}%")
                    print(f"   - Margin Feasible: {comp.get('margin_feasible', False)}\n")

                return True
            else:
                print(f"✗ Status: {status}")
                if "error" in result:
                    print(f"✗ Error: {result['error']}\n")
                return False
        else:
            print(f"✗ Status: {response.status_code}\n")
            return False

    except Exception as e:
        print(f"✗ Error: {e}\n")
        return False


def main():
    """Run all tests"""
    print_header("MarginGuard API Test Suite")

    # Test 1: Health
    if not test_health():
        print("❌ Backend is not running!")
        print("   Please start it: cd api && python main.py")
        sys.exit(1)

    # Test 2: Upload
    if not test_upload_policy():
        print("⚠️  Upload test failed")

    # Test 3 & 4: Analysis and Results
    success, execution_id = test_analysis()

    if success and execution_id:
        if test_results(execution_id):
            print_header("✓ All tests passed!")
            print("🎉 MarginGuard is working correctly!\n")
        else:
            print_header("⚠️  Analysis completed but result fetch failed")
    else:
        print_header("✗ Analysis test failed")
        print("   Check backend logs for errors\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        sys.exit(1)
