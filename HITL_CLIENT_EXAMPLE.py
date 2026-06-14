"""
MarginGuard AI — HITL Client Example
====================================

Demonstrates complete client-side integration with the HITL API.
Shows how to:
1. Start analysis
2. Poll for status
3. Detect when paused for human review
4. Display review UI
5. Submit human decision
6. Handle resume and completion

Usage:
    python HITL_CLIENT_EXAMPLE.py
"""

import asyncio
import httpx
import json
from typing import Optional, Dict, Any
from datetime import datetime


class MarginGuardHITLClient:
    """Client for MarginGuard HITL API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)

    async def start_analysis(self, query: str, save_result: bool = True) -> str:
        """
        Start a new pricing analysis.

        Args:
            query: Product query (e.g., "iPhone 15 Pro pricing analysis")
            save_result: Whether to save result to file

        Returns:
            execution_id for tracking

        Raises:
            httpx.HTTPError if request fails
        """
        print(f"\n📊 Starting analysis: {query}")

        response = await self.client.post(
            "/analyze",
            json={"query": query, "save_result": save_result}
        )
        response.raise_for_status()

        data = response.json()
        execution_id = data["execution_id"]

        print(f"✅ Analysis started")
        print(f"   Execution ID: {execution_id}")

        return execution_id

    async def poll_status(
        self,
        execution_id: str,
        poll_interval: float = 1.0,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Poll for status until completion or HITL pause.

        Args:
            execution_id: Execution to monitor
            poll_interval: Seconds between polls
            timeout: Max seconds to wait

        Returns:
            Final status response

        Raises:
            TimeoutError if polling exceeds timeout
            httpx.HTTPError if request fails
        """
        print(f"\n⏳ Polling status (interval={poll_interval}s, timeout={timeout}s)")

        elapsed = 0
        while elapsed < timeout:
            response = await self.client.get(f"/analyze/status/{execution_id}")
            response.raise_for_status()

            status_data = response.json()
            current_status = status_data["status"]

            # Print progress
            progress = status_data.get("progress", 0)
            step = status_data.get("step", 0)
            message = status_data.get("message", "")

            print(f"   [{elapsed:.1f}s] Step {step}/5 ({progress:.0f}%) - {message}")

            # Check if paused for review
            if status_data.get("is_paused") or current_status == "paused_for_human_review":
                print(f"\n⚠️  PAUSED FOR HUMAN REVIEW")
                print(f"   Review Status: {status_data.get('review_status')}")
                print(f"   Feedback: {status_data.get('review_feedback')}")

                if status_data.get("risk_factors"):
                    print(f"   Risk Factors:")
                    for risk in status_data["risk_factors"]:
                        print(f"     - {risk}")

                return status_data

            # Check if completed
            if current_status == "completed":
                print(f"\n✅ ANALYSIS COMPLETED")
                print(f"   Review Status: {status_data.get('review_status')}")
                return status_data

            # Check for errors
            if current_status == "error":
                print(f"\n❌ ERROR")
                print(f"   Message: {status_data.get('message')}")
                return status_data

            # Wait before next poll
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Status polling exceeded {timeout}s timeout")

    async def resume_with_decision(
        self,
        execution_id: str,
        override_decision: str,
        notes: str
    ) -> Dict[str, Any]:
        """
        Resume paused workflow with human decision.

        Args:
            execution_id: Paused execution ID
            override_decision: "override_approve" or "override_reject"
            notes: Human's justification

        Returns:
            Resume response with final decision

        Raises:
            ValueError if invalid decision
            httpx.HTTPError if request fails
        """
        if override_decision not in ["override_approve", "override_reject"]:
            raise ValueError(
                f"Invalid decision: {override_decision}. "
                "Must be 'override_approve' or 'override_reject'"
            )

        if not notes or len(notes) < 1 or len(notes) > 1000:
            raise ValueError("Notes must be 1-1000 characters")

        print(f"\n🔄 Resuming workflow with human decision")
        print(f"   Decision: {override_decision}")
        print(f"   Notes: {notes[:50]}...")

        response = await self.client.post(
            f"/analyze/resume/{execution_id}",
            json={
                "override_decision": override_decision,
                "notes": notes
            }
        )
        response.raise_for_status()

        data = response.json()
        print(f"\n✅ WORKFLOW RESUMED")
        print(f"   Final Decision: {data.get('final_decision')}")
        print(f"   Human Decision: {data.get('human_decision')}")

        return data

    async def run_complete_workflow(
        self,
        query: str,
        auto_approve_if_paused: bool = False
    ) -> Dict[str, Any]:
        """
        Run complete workflow: start → poll → resume if needed → wait for completion.

        Args:
            query: Product query
            auto_approve_if_paused: Auto-approve if paused (for testing)

        Returns:
            Final completion status
        """
        print("\n" + "=" * 80)
        print("MARGINGUARD HITL CLIENT — COMPLETE WORKFLOW")
        print("=" * 80)
        print(f"Query: {query}")
        print(f"Auto-approve if paused: {auto_approve_if_paused}")

        # Step 1: Start analysis
        execution_id = await self.start_analysis(query)

        # Step 2: Poll for status
        status = await self.poll_status(execution_id)

        # Step 3: If paused, handle human review
        if status.get("is_paused") or status["status"] == "paused_for_human_review":
            if auto_approve_if_paused:
                # Auto-approve for testing
                print("\n[AUTO-APPROVE] Simulating human approval...")
                final_status = await self.resume_with_decision(
                    execution_id,
                    "override_approve",
                    "Auto-approved by test client"
                )

                # Poll again for completion
                final_status = await self.poll_status(execution_id)
            else:
                print("\n⚠️  HUMAN REVIEW REQUIRED")
                print("   Please call: resume_with_decision(execution_id, decision, notes)")
                return status

        print("\n" + "=" * 80)
        print("WORKFLOW COMPLETE")
        print("=" * 80)
        print(f"Final Status: {status.get('review_status')}")
        print(f"Timestamp: {datetime.utcnow().isoformat()}")

        return status

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def example_1_auto_approved():
    """
    Example 1: Workflow that auto-approves (no HITL).
    Price well above margin floor → no human review needed.
    """
    print("\n" + "🔷" * 40)
    print("EXAMPLE 1: AUTO-APPROVED (No HITL)")
    print("🔷" * 40)

    client = MarginGuardHITLClient()

    try:
        result = await client.run_complete_workflow(
            "Standard product pricing",
            auto_approve_if_paused=False
        )
        print(f"\nResult: {result.get('review_status')}")

    finally:
        await client.close()


async def example_2_gray_area_hitl():
    """
    Example 2: Workflow that pauses (HITL triggered).
    Price in gray area (within 2% of floor) → requires human review.
    """
    print("\n" + "🔷" * 40)
    print("EXAMPLE 2: GRAY AREA (HITL Triggered)")
    print("🔷" * 40)

    client = MarginGuardHITLClient()

    try:
        result = await client.run_complete_workflow(
            "CloudScale Enterprise pricing",
            auto_approve_if_paused=True  # Auto-approve for demo
        )
        print(f"\nResult: {result.get('review_status')}")

    finally:
        await client.close()


async def example_3_manual_human_review():
    """
    Example 3: Manual human review flow.
    Demonstrates full control over human decision process.
    """
    print("\n" + "🔷" * 40)
    print("EXAMPLE 3: MANUAL HUMAN REVIEW")
    print("🔷" * 40)

    client = MarginGuardHITLClient()

    try:
        # Start analysis
        execution_id = await client.start_analysis(
            "High-value Enterprise SaaS pricing"
        )

        # Poll for status
        status = await client.poll_status(execution_id)

        # If paused, human reviews and makes decision
        if status.get("is_paused"):
            print("\n👤 HUMAN REVIEW IN PROGRESS")
            print("   Risk factors to consider:")
            for risk in status.get("risk_factors", []):
                print(f"     • {risk}")

            print("\n   Feedback from reviewer:")
            print(f"     {status.get('review_feedback')}")

            # Simulate human making decision
            decision = input("\n   Approve? (y/n): ").lower().strip()

            if decision == "y":
                override_decision = "override_approve"
                notes = "Approved by pricing committee - acceptable risk given enterprise value"
            else:
                override_decision = "override_reject"
                notes = "Rejected - requires pricing adjustment below current threshold"

            # Resume workflow
            final = await client.resume_with_decision(
                execution_id,
                override_decision,
                notes
            )

            print(f"\n✅ Final decision applied: {final.get('final_decision')}")

    finally:
        await client.close()


async def example_4_error_handling():
    """
    Example 4: Error handling and edge cases.
    """
    print("\n" + "🔷" * 40)
    print("EXAMPLE 4: ERROR HANDLING")
    print("🔷" * 40)

    client = MarginGuardHITLClient()

    try:
        # Test 1: Invalid query
        print("\nTest 1: Empty query")
        try:
            await client.start_analysis("")
        except Exception as e:
            print(f"✅ Caught error: {type(e).__name__}")

        # Test 2: Invalid execution ID
        print("\nTest 2: Invalid execution ID")
        try:
            await client.poll_status("invalid-id")
        except Exception as e:
            print(f"✅ Caught error: {type(e).__name__}")

        # Test 3: Invalid resume decision
        print("\nTest 3: Invalid resume decision")
        try:
            await client.resume_with_decision(
                "some-id",
                "invalid_decision",
                "test"
            )
        except ValueError as e:
            print(f"✅ Caught error: {e}")

        # Test 4: Empty notes
        print("\nTest 4: Empty notes")
        try:
            await client.resume_with_decision(
                "some-id",
                "override_approve",
                ""
            )
        except ValueError as e:
            print(f"✅ Caught error: {e}")

        print("\n✅ All error cases handled correctly")

    finally:
        await client.close()


async def example_5_stress_test():
    """
    Example 5: Stress test - multiple concurrent workflows.
    """
    print("\n" + "🔷" * 40)
    print("EXAMPLE 5: CONCURRENT WORKFLOWS")
    print("🔷" * 40)

    queries = [
        "iPhone 15 Pro pricing",
        "CloudScale Enterprise Tier-2",
        "Premium Smartwatch pricing",
    ]

    client = MarginGuardHITLClient()

    try:
        # Start all analyses concurrently
        print("\nStarting 3 concurrent analyses...")
        execution_ids = []

        for query in queries:
            exec_id = await client.start_analysis(query)
            execution_ids.append(exec_id)

        # Poll all concurrently
        print("\nPolling all 3 concurrently...")
        results = await asyncio.gather(*[
            client.poll_status(exec_id)
            for exec_id in execution_ids
        ])

        # Summary
        paused = sum(1 for r in results if r.get("is_paused"))
        completed = sum(1 for r in results if r["status"] == "completed")

        print(f"\n✅ Concurrent Results:")
        print(f"   Paused: {paused}")
        print(f"   Completed: {completed}")

    finally:
        await client.close()


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run all examples."""
    import sys

    examples = {
        "1": ("Auto-Approved", example_1_auto_approved),
        "2": ("Gray Area (HITL)", example_2_gray_area_hitl),
        "3": ("Manual Human Review", example_3_manual_human_review),
        "4": ("Error Handling", example_4_error_handling),
        "5": ("Concurrent Workflows", example_5_stress_test),
    }

    print("\n" + "=" * 80)
    print("MARGINGUARD HITL CLIENT — EXAMPLE MENU")
    print("=" * 80)
    print("\nAvailable examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print(f"  0. All examples")

    choice = input("\nSelect example (0-5): ").strip()

    if choice == "0":
        for name, func in examples.values():
            await func()
    elif choice in examples:
        name, func = examples[choice]
        await func()
    else:
        print(f"Invalid choice: {choice}")
        sys.exit(1)


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
