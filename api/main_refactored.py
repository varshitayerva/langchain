"""
MarginGuard AI — FastAPI Backend with HITL Resume Endpoints
===========================================================

REFACTORED for automatic retry loop + HITL escalation:
  POST /analyze              - Start analysis
  GET /status/{id}           - Check progress
  GET /result/{id}           - Get result
  POST /resume/{id}          - Resume with human decision (NEW)
  GET /health                - Health check
  GET /info                  - API info

When retry_count reaches 3 and report still rejected:
  - Workflow pauses (interrupt_before)
  - State checkpointed to MemorySaver
  - Status endpoint shows "paused_for_human_review"
  - Client calls /resume with override_approve or override_reject
  - Graph resumes from checkpoint with human decision applied

Usage:
  uvicorn main_refactored:app --reload --host 0.0.0.0 --port 8000
"""

import sys
import os
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import refactored orchestrator
ORCHESTRATOR_AVAILABLE = False
try:
    from orchestration.langgraph_orchestrator_refactored import (
        run_workflow,
        resume_workflow,
        get_paused_state,
        AgentState,
    )
    ORCHESTRATOR_AVAILABLE = True
except Exception as e:
    print(f"[WARN] Orchestrator not available: {e}")

# ============================================================================
# FASTAPI SETUP
# ============================================================================

app = FastAPI(
    title="MarginGuard AI — HITL Edition",
    version="2.1.0",
    description="Multi-agent pricing with retry loop + human-in-the-loop",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATA MODELS
# ============================================================================

class AnalysisRequest(BaseModel):
    """Request to start analysis."""
    query: str = Field(
        ...,
        description="Product query",
        example="CloudScale Enterprise Tier-2 pricing"
    )
    save_result: bool = Field(default=True)


class HumanDecisionRequest(BaseModel):
    """Request to resume with human decision."""
    override_decision: str = Field(
        ...,
        description="override_approve or override_reject",
        example="override_approve"
    )
    notes: str = Field(
        ...,
        description="Justification for decision",
        example="Approved by pricing committee. Acceptable risk given market conditions."
    )


class AnalysisResponse(BaseModel):
    """Response when analysis starts."""
    execution_id: str
    status: str
    message: str
    created_at: str


class StatusResponse(BaseModel):
    """Response for status check."""
    execution_id: str
    status: str  # "running" | "paused_for_human_review" | "completed" | "error"
    is_paused: bool
    review_status: Optional[str] = None
    retry_count: int = 0
    risk_factors: list = []
    created_at: str
    updated_at: str


class ResumeResponse(BaseModel):
    """Response after resume."""
    execution_id: str
    status: str
    final_decision: str
    human_override: str
    human_notes: str
    completed_at: str


# ============================================================================
# EXECUTION CACHE & PERSISTENCE
# ============================================================================

execution_cache: Dict[str, Dict[str, Any]] = {}
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def get_execution_info(execution_id: str) -> Optional[Dict[str, Any]]:
    """Get execution info from cache."""
    return execution_cache.get(execution_id)


def create_execution(query: str) -> str:
    """Create new execution entry."""
    execution_id = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()

    execution_cache[execution_id] = {
        "execution_id": execution_id,
        "query": query,
        "status": "running",
        "is_paused": False,
        "review_status": None,
        "retry_count": 0,
        "final_state": None,
        "created_at": now,
        "updated_at": now,
    }

    return execution_id


def update_execution(
    execution_id: str,
    status: str = None,
    is_paused: bool = None,
    review_status: str = None,
    retry_count: int = None,
    final_state: Dict[str, Any] = None,
):
    """Update execution cache."""
    if execution_id not in execution_cache:
        return

    if status:
        execution_cache[execution_id]["status"] = status
    if is_paused is not None:
        execution_cache[execution_id]["is_paused"] = is_paused
    if review_status:
        execution_cache[execution_id]["review_status"] = review_status
    if retry_count is not None:
        execution_cache[execution_id]["retry_count"] = retry_count
    if final_state:
        execution_cache[execution_id]["final_state"] = final_state

    execution_cache[execution_id]["updated_at"] = datetime.now().isoformat()


# ============================================================================
# BACKGROUND TASK: RUN WORKFLOW
# ============================================================================

def run_workflow_task(execution_id: str, query: str, save_result: bool = True):
    """Run workflow in background."""
    try:
        if not ORCHESTRATOR_AVAILABLE:
            update_execution(
                execution_id,
                status="error",
            )
            return

        # Run workflow (may pause if HITL triggered)
        final_state = run_workflow(query, thread_id=execution_id)

        # Check if paused
        is_paused = final_state.get("is_paused", False)

        # Update cache
        update_execution(
            execution_id,
            status="paused_for_human_review" if is_paused else "completed",
            is_paused=is_paused,
            review_status=final_state.get("review_status"),
            retry_count=final_state.get("retry_count", 0),
            final_state=final_state,
        )

        # Save result if completed
        if save_result and not is_paused:
            result_file = os.path.join(RESULTS_DIR, f"{execution_id}.json")
            with open(result_file, "w") as f:
                json.dump({
                    "query": query,
                    "review_status": final_state.get("review_status"),
                    "retry_count": final_state.get("retry_count"),
                    "draft_report": final_state.get("draft_report"),
                    "review_feedback": final_state.get("review_feedback"),
                }, f, indent=2)

    except Exception as e:
        error_msg = str(e)
        update_execution(
            execution_id,
            status="error",
        )
        print(f"[ERROR] Workflow task failed for {execution_id}: {error_msg}")
        import traceback
        traceback.print_exc()


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/upload-policy", tags=["Policy"])
async def upload_policy(file: UploadFile = File(...)):
    """
    Upload and parse company policy document.

    Accepts PDF file and returns policy sections.
    Mock implementation returns static sections.
    In production, would parse PDF and extract actual policy sections.

    Request:
      - file: PDF file (multipart/form-data)

    Returns:
      - status: "success"
      - sections_uploaded: number of policy sections
      - sections: Array of {title, content} objects
      - message: confirmation message
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    return JSONResponse({
        "status": "success",
        "sections_uploaded": 3,
        "sections": [
            {
                "title": "Pricing Policy",
                "content": "All pricing must maintain margin floor guardrails. Minimum margin floor is 30% to ensure profitability and risk management."
            },
            {
                "title": "Compliance Requirements",
                "content": "All pricing strategies must be audited for compliance with regional regulations and internal policies. Quarterly reviews required."
            },
            {
                "title": "Market Guidelines",
                "content": "Pricing should remain competitive in the market while protecting margins. Monitor competitor pricing quarterly."
            }
        ],
        "message": f"Policy uploaded successfully. File: {file.filename}"
    })


@app.get("/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_product_get(
    product: str = Query(..., description="Product name or query"),
    background_tasks: BackgroundTasks = None
):
    """
    Start pricing analysis pipeline (GET endpoint for UI).

    Query Parameters:
      - product: Product name or query (e.g., "iPhone 15 Pro")

    Returns execution_id immediately. Workflow runs in background.
    """
    if not product or len(product.strip()) == 0:
        raise HTTPException(status_code=400, detail="Product query cannot be empty")

    execution_id = create_execution(product)
    now = datetime.now().isoformat()

    # Run workflow in background
    background_tasks.add_task(
        run_workflow_task,
        execution_id,
        product,
        True,
    )

    return AnalysisResponse(
        execution_id=execution_id,
        status="started",
        message=f"Analysis started. ID: {execution_id}",
        created_at=now,
    )


@app.post("/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_product(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Start pricing analysis pipeline (POST endpoint).

    Returns execution_id immediately. Workflow runs in background.
    Use /status endpoint to check progress.

    If retry_count reaches 3 and report still rejected:
      - Workflow pauses automatically
      - Status endpoint shows "paused_for_human_review"
      - Call /resume endpoint to provide human override decision
    """
    if not request.query or len(request.query.strip()) == 0:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    execution_id = create_execution(request.query)
    now = datetime.now().isoformat()

    # Run workflow in background
    background_tasks.add_task(
        run_workflow_task,
        execution_id,
        request.query,
        request.save_result,
    )

    return AnalysisResponse(
        execution_id=execution_id,
        status="started",
        message=f"Analysis started. ID: {execution_id}",
        created_at=now,
    )


@app.get("/status/{execution_id}", response_model=StatusResponse, tags=["Analysis"])
async def get_status(execution_id: str):
    """
    Get execution status and progress.

    Returns:
      - status: "running" | "paused_for_human_review" | "completed" | "error"
      - is_paused: True if waiting for human review
      - retry_count: Number of retries attempted (0-3)
      - risk_factors: Why paused (for human review context)

    If paused, call POST /resume/{id} to provide override decision.
    """
    exec_info = get_execution_info(execution_id)

    if not exec_info:
        raise HTTPException(status_code=404, detail="Execution not found")

    return StatusResponse(
        execution_id=execution_id,
        status=exec_info["status"],
        is_paused=exec_info["is_paused"],
        review_status=exec_info.get("review_status"),
        retry_count=exec_info.get("retry_count", 0),
        risk_factors=[],  # Could populate from final_state
        created_at=exec_info["created_at"],
        updated_at=exec_info["updated_at"],
    )


@app.get("/result/{execution_id}", tags=["Analysis"])
async def get_result(execution_id: str):
    """
    Get analysis result.

    Returns:
      - review_status: "approved" | "rejected"
      - draft_report: Markdown pricing report
      - retry_count: Attempts made (0-3)
      - review_feedback: Why rejected (if applicable)

    If still paused for human review:
      - Returns 202 Accepted
      - Call POST /resume/{id} first
    """
    exec_info = get_execution_info(execution_id)

    if not exec_info:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Still running or paused
    if exec_info["status"] in ["running", "paused_for_human_review"]:
        raise HTTPException(
            status_code=202,
            detail=f"Still processing: {exec_info['status']}"
        )

    # Error
    if exec_info["status"] == "error":
        raise HTTPException(status_code=500, detail="Analysis failed")

    # Completed
    final_state = exec_info.get("final_state", {})
    return JSONResponse({
        "execution_id": execution_id,
        "status": "success",
        "query": exec_info["query"],
        "review_status": final_state.get("review_status"),
        "retry_count": final_state.get("retry_count"),
        "draft_report": final_state.get("draft_report"),
        "review_feedback": final_state.get("review_feedback"),
    })


@app.post("/analyze/resume/{execution_id}", response_model=ResumeResponse, tags=["HITL"])
async def resume_with_decision(
    execution_id: str,
    request: HumanDecisionRequest
):
    """
    Resume paused workflow with human override decision.

    Endpoint: POST /analyze/resume/{execution_id}

    Call this when status is "paused_for_human_review" (max retries reached).

    Request Body:
      {
        "override_decision": "override_approve" | "override_reject",
        "notes": "Justification text"
      }

    Response:
      {
        "execution_id": "a1b2c3d4",
        "status": "completed",
        "final_decision": "approved" | "rejected",
        "human_override": "override_approve" | "override_reject",
        "human_notes": "...",
        "completed_at": "2024-06-12T..."
      }

    Flow:
      1. Validate execution exists and is paused
      2. Fetch paused state from checkpoint (thread_id = execution_id)
      3. Inject human_decision + human_notes into state
      4. Resume graph execution from checkpoint
      5. Apply human override decision
      6. Return final decision with completion timestamp
    """
    print(f"[RESUME] Received resume request for execution_id: {execution_id}")
    print(f"[RESUME] override_decision: {request.override_decision}")
    print(f"[RESUME] notes: {request.notes}")

    exec_info = get_execution_info(execution_id)

    if not exec_info:
        print(f"[RESUME ERROR] Execution not found: {execution_id}")
        raise HTTPException(status_code=404, detail="Execution not found")

    print(f"[RESUME] Current execution state: status={exec_info['status']}, is_paused={exec_info['is_paused']}")

    if not exec_info["is_paused"]:
        print(f"[RESUME ERROR] Workflow not paused. Status: {exec_info['status']}")
        raise HTTPException(
            status_code=400,
            detail=f"Workflow not paused. Current status: {exec_info['status']}"
        )

    # Validate decision format
    if request.override_decision not in ["override_approve", "override_reject"]:
        raise HTTPException(
            status_code=400,
            detail="override_decision must be 'override_approve' or 'override_reject'"
        )

    if not request.notes or len(request.notes.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="notes cannot be empty"
        )

    try:
        # Resume workflow from checkpoint with human decision
        print(f"[RESUME] Resuming workflow from checkpoint...")
        final_state = resume_workflow(
            thread_id=execution_id,
            human_decision=request.override_decision,
            human_notes=request.notes,
        )
        print(f"[RESUME] Workflow resumed. Final state: {final_state.get('review_status')}")

        # Update execution cache
        update_execution(
            execution_id,
            status="completed",
            is_paused=False,
            review_status=final_state.get("review_status"),
            final_state=final_state,
        )
        print(f"[RESUME] Cache updated")

        # Persist result to file
        result_file = os.path.join(RESULTS_DIR, f"{execution_id}_resumed.json")
        with open(result_file, "w") as f:
            json.dump({
                "query": exec_info["query"],
                "human_override": request.override_decision,
                "human_notes": request.notes,
                "final_decision": final_state.get("review_status"),
                "draft_report": final_state.get("draft_report"),
            }, f, indent=2)
        print(f"[RESUME] Result saved to file")

        # Return response
        response = ResumeResponse(
            execution_id=execution_id,
            status="completed",
            final_decision=final_state.get("review_status"),
            human_override=request.override_decision,
            human_notes=request.notes,
            completed_at=datetime.now().isoformat(),
        )
        print(f"[RESUME] SUCCESS: Returning resume response")
        return response

    except Exception as e:
        print(f"[RESUME ERROR] Exception during resume: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Resume failed: {str(e)}"
        )


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "orchestrator_available": ORCHESTRATOR_AVAILABLE,
        "version": "2.1.0",
    })


@app.get("/info", tags=["System"])
async def info():
    """API information and capabilities."""
    return JSONResponse({
        "title": "MarginGuard AI — HITL Edition",
        "version": "2.1.0",
        "features": [
            "Multi-agent pricing analysis",
            "Automatic retry loop (max 3)",
            "HITL escalation on max retries",
            "Thread-based checkpoint persistence",
            "Manual override via /resume endpoint",
        ],
        "endpoints": {
            "POST /analyze": "Start analysis",
            "GET /status/{id}": "Check progress",
            "GET /result/{id}": "Get result",
            "POST /resume/{id}": "Resume with human decision (NEW)",
            "GET /health": "Health check",
        },
    })


@app.get("/", tags=["System"])
async def root():
    """Welcome endpoint."""
    return JSONResponse({
        "message": "Welcome to MarginGuard AI — HITL Edition",
        "version": "2.1.0",
        "quick_start": {
            "1_start": "POST /analyze with {'query': '...'}",
            "2_check": "GET /status/{execution_id}",
            "3_if_paused": "POST /resume/{execution_id} with override decision",
            "4_result": "GET /result/{execution_id}",
        },
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "timestamp": datetime.now().isoformat(),
        },
    )


# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("=" * 80)
    print("MarginGuard AI — HITL Edition")
    print("=" * 80)
    print(f"[OK] API started at http://0.0.0.0:8000")
    print(f"[OK] Docs at http://0.0.0.0:8000/docs")
    print(f"[OK] Orchestrator available: {ORCHESTRATOR_AVAILABLE}")
    print(f"[OK] Features: Retry loop + HITL escalation + /resume endpoint")
    print("=" * 80)
    print()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main_refactored:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
