"""
MarginGuard AI — FastAPI Integration for Human-in-the-Loop (HITL) Pattern
=========================================================================

Provides REST endpoints for:
1. Starting analysis (POST /analyze)
2. Checking status (GET /analyze/status/{execution_id})
3. Resuming with human decision (POST /analyze/resume/{execution_id})

These endpoints integrate with the LangGraph HITL orchestrator to manage
paused workflow states and human compliance reviews.

Usage:
    from api.hitl_api import app, setup_hitl_endpoints
    from orchestration.hitl_orchestrator import build_hitl_graph

    # Build graph
    graph = build_hitl_graph()

    # Setup endpoints
    setup_hitl_endpoints(app, graph)

    # Run: uvicorn api.hitl_api:app --reload
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from orchestration.hitl_orchestrator import (
    build_hitl_graph,
    run_workflow,
    resume_workflow,
    get_workflow_status,
    AnalysisRequest,
    AnalysisResponse,
    StatusResponse,
    HumanDecisionRequest,
    ResumeResponse,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MarginGuard AI — HITL API",
    description="Pricing analysis pipeline with human-in-the-loop compliance review",
    version="2.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global graph instance
graph = None

# Execution store (in-memory for demo, use Redis/DB in production)
execution_store: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# 1. STARTUP & INITIALIZATION
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize graph on startup."""
    global graph
    logger.info("Initializing HITL orchestrator...")
    graph = build_hitl_graph()
    logger.info("HITL orchestrator ready")


# ============================================================================
# 2. ANALYSIS ENDPOINTS
# ============================================================================

@app.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Start Analysis",
    description="Initiate pricing analysis pipeline. Returns execution_id for tracking."
)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """
    Start a new pricing analysis.

    **Request:**
    ```json
    {
      "query": "iPhone 15 Pro pricing analysis",
      "save_result": true
    }
    ```

    **Response:**
    ```json
    {
      "execution_id": "a1b2c3d4-...",
      "status": "started",
      "message": "Analysis started for iPhone 15 Pro pricing analysis",
      "created_at": "2024-06-12T10:30:45.123456"
    }
    ```

    **Flow:**
    1. Validate request
    2. Run workflow in background
    3. Return immediately with execution_id
    4. Client polls /status for progress
    """
    logger.info(f"[API] Starting analysis: {request.query}")

    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )

    # Run workflow in background
    background_tasks.add_task(execute_workflow, request.query)

    created_at = datetime.utcnow().isoformat()

    return AnalysisResponse(
        execution_id="pending",  # Will be set when workflow starts
        status="started",
        message=f"Analysis started for: {request.query}",
        created_at=created_at
    )


def execute_workflow(query: str) -> None:
    """Background task to execute workflow."""
    try:
        result = run_workflow(graph, query)
        execution_store[result["execution_id"]] = result
        logger.info(f"Workflow stored: {result['execution_id']}")
    except Exception as e:
        logger.error(f"Background execution failed: {str(e)}")


@app.get(
    "/analyze/status/{execution_id}",
    response_model=StatusResponse,
    summary="Check Analysis Status",
    description="Poll execution status. Returns current step, progress, and state."
)
async def check_status(execution_id: str) -> StatusResponse:
    """
    Check status of an ongoing or completed analysis.

    **Response:**
    ```json
    {
      "execution_id": "a1b2c3d4-...",
      "status": "paused_for_human_review",
      "step": 4,
      "message": "Awaiting human compliance review",
      "progress": 80.0,
      "is_paused": true,
      "review_status": "requires_human_review",
      "review_feedback": "HUMAN REVIEW REQUIRED: Price within 2% of margin floor",
      "risk_factors": ["Price within 2% of margin floor"],
      "created_at": "2024-06-12T10:30:45.123456",
      "updated_at": "2024-06-12T10:30:52.654321"
    }
    ```

    **Status Values:**
    - `running` - Workflow in progress
    - `paused_for_human_review` - Awaiting human decision (HITL)
    - `completed` - Analysis done
    - `error` - Execution failed
    - `not_found` - Execution ID not found

    **When Paused:**
    Send human decision to: `POST /analyze/resume/{execution_id}`
    """
    logger.info(f"[API] Status check: {execution_id}")

    # Check local store first
    if execution_id in execution_store:
        stored_result = execution_store[execution_id]
        state = stored_result.get("result", {})
        status = stored_result.get("status", "unknown")
    else:
        # Fetch from graph
        status_result = get_workflow_status(graph, execution_id)
        if status_result.get("status") == "not_found":
            raise HTTPException(
                status_code=404,
                detail=f"Execution not found: {execution_id}"
            )
        state = status_result
        status = status_result.get("status")

    # Map status to step and progress
    step_map = {
        "running": (2, 50.0),
        "paused_for_human_review": (4, 80.0),
        "completed": (5, 100.0),
        "error": (0, 0.0)
    }
    step, progress = step_map.get(status, (0, 0.0))

    # Build response
    response_status = status
    if status == "paused_for_human_review":
        message = "Awaiting human compliance review"
    elif status == "completed":
        message = "Analysis completed successfully"
    elif status == "running":
        message = "Analysis in progress..."
    else:
        message = f"Status: {status}"

    return StatusResponse(
        execution_id=execution_id,
        status=response_status,
        step=step,
        message=message,
        progress=progress,
        is_paused=state.get("is_paused", False),
        review_status=state.get("review_status"),
        review_feedback=state.get("review_feedback"),
        risk_factors=state.get("risk_factors", []),
        created_at=state.get("created_at", datetime.utcnow().isoformat()),
        updated_at=state.get("updated_at", datetime.utcnow().isoformat())
    )


@app.post(
    "/analyze/resume/{execution_id}",
    response_model=ResumeResponse,
    summary="Resume with Human Decision",
    description="Resume paused workflow with human compliance decision."
)
async def resume_with_decision(
    execution_id: str,
    request: HumanDecisionRequest
) -> ResumeResponse:
    """
    Resume a paused workflow with human decision.

    **Request:**
    ```json
    {
      "override_decision": "override_approve",
      "notes": "Approved per management consensus on pricing strategy"
    }
    ```

    **Response:**
    ```json
    {
      "execution_id": "a1b2c3d4-...",
      "status": "completed",
      "final_decision": "approved",
      "human_decision": "override_approve",
      "human_notes": "Approved per management consensus on pricing strategy",
      "completed_at": "2024-06-12T10:31:15.987654"
    }
    ```

    **Validation:**
    - Execution must be in paused state
    - override_decision must be "override_approve" or "override_reject"
    - notes required (1-1000 characters)

    **Flow:**
    1. Validate paused state
    2. Inject human decision into paused graph state
    3. Resume execution to completion
    4. Return final decision
    """
    logger.info(f"[API] Resuming with decision: {execution_id}")

    # Validate execution exists and is paused
    status_result = get_workflow_status(graph, execution_id)

    if status_result.get("status") == "not_found":
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found: {execution_id}"
        )

    if status_result.get("status") != "paused_for_human_review":
        raise HTTPException(
            status_code=400,
            detail=f"Execution not paused. Current status: {status_result.get('status')}"
        )

    # Resume workflow with human decision
    try:
        result = resume_workflow(
            graph,
            execution_id,
            request.override_decision,
            request.notes
        )

        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("message")
            )

        final_state = result.get("result", {})

        return ResumeResponse(
            execution_id=execution_id,
            status="completed",
            final_decision=final_state.get("review_status", "unknown"),
            human_decision=request.override_decision,
            human_notes=request.notes,
            completed_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Resume failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume workflow: {str(e)}"
        )


# ============================================================================
# 3. SYSTEM ENDPOINTS
# ============================================================================

@app.get(
    "/health",
    summary="Health Check",
    description="Verify API and orchestrator health."
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
    ```json
    {
      "status": "healthy",
      "orchestrator": "ready",
      "timestamp": "2024-06-12T10:30:45.123456"
    }
    ```
    """
    return {
        "status": "healthy",
        "orchestrator": "ready" if graph else "not initialized",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get(
    "/info",
    summary="API Information",
    description="Get API version and capabilities."
)
async def api_info() -> Dict[str, Any]:
    """Get API information and capabilities."""
    return {
        "title": "MarginGuard AI — HITL API",
        "version": "2.1.0",
        "features": [
            "Multi-agent pricing analysis",
            "Real-time competitive intelligence",
            "Compliance audit with HITL",
            "Gray-area price detection",
            "High-value category review",
            "Automatic retry logic",
            "Human override capability"
        ],
        "endpoints": {
            "analyze": {
                "method": "POST",
                "path": "/analyze",
                "description": "Start new analysis"
            },
            "status": {
                "method": "GET",
                "path": "/analyze/status/{execution_id}",
                "description": "Check analysis status"
            },
            "resume": {
                "method": "POST",
                "path": "/analyze/resume/{execution_id}",
                "description": "Resume paused workflow"
            },
            "health": {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        },
        "hitl_enabled": True,
        "orchestrator_type": "LangGraph"
    }


@app.get("/")
async def root() -> Dict[str, Any]:
    """Welcome endpoint."""
    return {
        "message": "Welcome to MarginGuard AI HITL API",
        "version": "2.1.0",
        "docs": "/docs",
        "quick_start": {
            "1_analyze": "POST /analyze",
            "2_status": "GET /analyze/status/{execution_id}",
            "3_resume": "POST /analyze/resume/{execution_id}"
        }
    }


# ============================================================================
# 4. ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc)
        }
    )


# ============================================================================
# 5. HELPER FUNCTIONS
# ============================================================================

def setup_hitl_endpoints(app_instance: FastAPI, graph_instance) -> None:
    """
    Setup HITL endpoints on an existing FastAPI app.

    Usage:
        from fastapi import FastAPI
        from orchestration.hitl_orchestrator import build_hitl_graph
        from api.hitl_api import setup_hitl_endpoints

        app = FastAPI()
        graph = build_hitl_graph()
        setup_hitl_endpoints(app, graph)
    """
    global graph
    graph = graph_instance


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting MarginGuard AI HITL API server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
