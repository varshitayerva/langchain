"""
MarginGuard AI — FastAPI Backend
=================================

Multi-agent pricing strategy pipeline with LangGraph orchestration.

Product managers spend hours checking if competitors undercut prices or ship comparable features.
MarginGuard automates detection + feasibility-checking via a multi-agent pipeline with:
  - Automatic RAG retrieval (products & policies)
  - Market research (competitors)
  - Report synthesis (pricing strategies)
  - Compliance review (margin validation)
  - Reflection loop (automatic retries)

API Endpoints:
  POST /analyze      - Start pricing analysis
  GET /status/{id}   - Check execution progress
  GET /result/{id}   - Get final pricing report
  GET /health        - Health check

Usage:
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import sys
import os
import uuid
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from threading import Thread

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# LangGraph is optional for basic functionality
LANGGRAPH_AVAILABLE = False
try:
    from orchestration.langgraph_orchestrator import (
        run_workflow,
        build_langgraph,
        AgentState,
    )
    LANGGRAPH_AVAILABLE = True
except Exception:
    pass

# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="MarginGuard AI",
    version="2.0.0",
    description="Multi-agent pricing strategy system with automatic compliance review",
    docs_url="/docs",
    redoc_url="/redoc",
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
    """Request model for pricing analysis."""
    query: str = Field(
        ...,
        description="Product query (e.g., 'CloudScale Enterprise Tier-2 pricing')",
        json_schema_extra={"example": "CloudScale Enterprise Tier-2 pricing"}
    )
    save_result: bool = Field(
        default=True,
        description="Whether to save result to JSON file"
    )


class ExecutionState(BaseModel):
    """Represents execution state in cache."""
    execution_id: str
    status: str  # "pending", "running", "completed", "error"
    created_at: str
    updated_at: str
    step: int = 0
    message: str = ""
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Response model for analysis start."""
    execution_id: str
    status: str
    message: str
    created_at: str
    check_status_url: str
    get_result_url: str


class StatusResponse(BaseModel):
    """Response model for status check."""
    execution_id: str
    status: str
    step: int
    message: str
    progress: float
    created_at: str
    updated_at: str
    error: Optional[str] = None


class ResultResponse(BaseModel):
    """Response model for final result."""
    execution_id: str
    status: str
    query: str
    review_status: str
    retry_count: int
    draft_report: str
    rag_context: Optional[Dict[str, Any]] = None
    research_data: Optional[Dict[str, Any]] = None
    review_feedback: Optional[str] = None
    completed_at: str


# ============================================================================
# EXECUTION CACHE
# ============================================================================

execution_cache: Dict[str, ExecutionState] = {}
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def get_execution(execution_id: str) -> Optional[ExecutionState]:
    """Get execution state from cache."""
    return execution_cache.get(execution_id)


def create_execution(query: str) -> str:
    """Create new execution entry."""
    execution_id = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()

    execution_cache[execution_id] = ExecutionState(
        execution_id=execution_id,
        status="pending",
        created_at=now,
        updated_at=now,
        step=0,
        message="Queued for processing",
        progress=0.0,
    )

    return execution_id


def update_execution(
    execution_id: str,
    status: str = None,
    step: int = None,
    message: str = None,
    progress: float = None,
    result: Dict[str, Any] = None,
    error: str = None,
):
    """Update execution state."""
    if execution_id not in execution_cache:
        return

    state = execution_cache[execution_id]
    state.updated_at = datetime.now().isoformat()

    if status:
        state.status = status
    if step is not None:
        state.step = step
    if message:
        state.message = message
    if progress is not None:
        state.progress = progress
    if result:
        state.result = result
    if error:
        state.error = error


# ============================================================================
# BACKGROUND TASK: RUN WORKFLOW
# ============================================================================

def run_workflow_task(execution_id: str, query: str, save_result: bool = True):
    """Run LangGraph workflow in background."""
    try:
        if not LANGGRAPH_AVAILABLE:
            update_execution(
                execution_id,
                status="error",
                error="LangGraph orchestrator not available"
            )
            return

        # Step 1: Initialize
        update_execution(
            execution_id,
            status="running",
            step=1,
            message="Initializing orchestrator...",
            progress=10.0,
        )

        # Step 2: Run workflow
        update_execution(
            execution_id,
            step=2,
            message="Executing RAG agent (retrieving products & policies)...",
            progress=25.0,
        )

        final_state = run_workflow(query)

        update_execution(
            execution_id,
            step=3,
            message="Executing research and synthesis agents...",
            progress=50.0,
        )

        # Step 3: Compile result
        update_execution(
            execution_id,
            step=4,
            message="Auditing report for compliance...",
            progress=75.0,
        )

        result = {
            "query": final_state["query"],
            "review_status": final_state["review_status"],
            "retry_count": final_state["retry_count"],
            "draft_report": final_state["draft_report"],
            "rag_context": final_state.get("rag_context", {}),
            "research_data": final_state.get("research_data", {}),
            "review_feedback": final_state.get("review_feedback"),
            "completed_at": datetime.now().isoformat(),
        }

        # Save result if requested
        if save_result:
            result_file = os.path.join(RESULTS_DIR, f"{execution_id}.json")
            with open(result_file, "w") as f:
                json.dump(result, f, indent=2)

        update_execution(
            execution_id,
            status="completed",
            step=5,
            message="Analysis complete!",
            progress=100.0,
            result=result,
        )

    except Exception as e:
        update_execution(
            execution_id,
            status="error",
            error=str(e),
        )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Start pricing analysis",
    description="Start a new pricing strategy analysis pipeline",
    tags=["Analysis"],
)
async def analyze_product(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Start a new pricing analysis.

    Example:
    ```json
    {
        "query": "CloudScale Enterprise Tier-2 pricing strategies",
        "save_result": true
    }
    ```

    Returns execution_id to track progress.
    """
    # Validate query
    if not request.query or len(request.query.strip()) == 0:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Create execution
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
        message=f"Analysis started with ID: {execution_id}",
        created_at=now,
        check_status_url=f"/status/{execution_id}",
        get_result_url=f"/result/{execution_id}",
    )


@app.get(
    "/status/{execution_id}",
    response_model=StatusResponse,
    summary="Get execution status",
    description="Check the progress of an ongoing analysis",
    tags=["Analysis"],
)
async def get_status(execution_id: str):
    """
    Get execution status and progress.

    Returns:
      - status: "pending" | "running" | "completed" | "error"
      - step: 1-5 (orchestrator → reviewer)
      - progress: 0-100%
      - message: Human-readable step description
    """
    execution = get_execution(execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return StatusResponse(
        execution_id=execution.execution_id,
        status=execution.status,
        step=execution.step,
        message=execution.message,
        progress=execution.progress,
        created_at=execution.created_at,
        updated_at=execution.updated_at,
        error=execution.error,
    )


@app.get(
    "/result/{execution_id}",
    response_model=ResultResponse,
    summary="Get analysis result",
    description="Retrieve the final pricing strategy report",
    tags=["Analysis"],
)
async def get_result(execution_id: str):
    """
    Get final analysis result.

    Returns:
      - review_status: "approved" | "rejected"
      - draft_report: Markdown pricing strategy report
      - retry_count: Number of retries (0-3)
      - review_feedback: Why report was rejected (if applicable)
    """
    execution = get_execution(execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    if execution.status == "pending" or execution.status == "running":
        raise HTTPException(
            status_code=202,
            detail=f"Analysis still processing: {execution.message}"
        )

    if execution.status == "error":
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {execution.error}"
        )

    result = execution.result
    return ResultResponse(
        execution_id=execution.execution_id,
        status="success",
        query=result["query"],
        review_status=result["review_status"],
        retry_count=result["retry_count"],
        draft_report=result["draft_report"],
        rag_context=result.get("rag_context"),
        research_data=result.get("research_data"),
        review_feedback=result.get("review_feedback"),
        completed_at=result["completed_at"],
    )


@app.get(
    "/result/{execution_id}/download",
    summary="Download result as JSON",
    description="Download the analysis result as a JSON file",
    tags=["Analysis"],
)
async def download_result(execution_id: str):
    """Download result as JSON file."""
    result_file = os.path.join(RESULTS_DIR, f"{execution_id}.json")

    if not os.path.exists(result_file):
        raise HTTPException(status_code=404, detail="Result file not found")

    return FileResponse(
        result_file,
        media_type="application/json",
        filename=f"analysis_{execution_id}.json",
    )


@app.get(
    "/health",
    summary="Health check",
    description="Check if API is running",
    tags=["System"],
)
async def health_check():
    """
    Health check endpoint.

    Returns status and available features.
    """
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "langgraph_available": LANGGRAPH_AVAILABLE,
        "version": "2.0.0",
    })


@app.get(
    "/info",
    summary="API information",
    description="Get API information and capabilities",
    tags=["System"],
)
async def info():
    """Get API information."""
    return JSONResponse({
        "title": "MarginGuard AI",
        "version": "2.0.0",
        "description": "Multi-agent pricing strategy system",
        "features": [
            "RAG Agent (Product & Policy Retrieval)",
            "Research Agent (Competitive Intelligence)",
            "Synthesis Agent (Report Generation)",
            "Reviewer Agent (Compliance Audit)",
            "Reflection Loop (Automatic Retries)",
            "Parallel Execution (2x speedup)",
        ],
        "endpoints": {
            "POST /analyze": "Start pricing analysis",
            "GET /status/{id}": "Check progress",
            "GET /result/{id}": "Get report",
            "GET /result/{id}/download": "Download as JSON",
            "GET /health": "Health check",
            "GET /info": "This endpoint",
        },
        "langgraph_available": LANGGRAPH_AVAILABLE,
    })


@app.get(
    "/executions",
    summary="List recent executions",
    description="Get list of recent analyses (for debugging)",
    tags=["System"],
)
async def list_executions(limit: int = Query(10, ge=1, le=100)):
    """List recent executions (for debugging)."""
    recent = list(execution_cache.items())[-limit:]
    return JSONResponse({
        "total": len(execution_cache),
        "recent": [
            {
                "id": state.execution_id,
                "status": state.status,
                "created_at": state.created_at,
                "progress": state.progress,
            }
            for _, state in recent
        ]
    })


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["System"])
async def root():
    """
    Welcome to MarginGuard AI.

    Quick start:
      1. POST /analyze with your query
      2. GET /status/{id} to check progress
      3. GET /result/{id} to get the report

    Full documentation available at /docs
    """
    return JSONResponse({
        "message": "Welcome to MarginGuard AI",
        "version": "2.0.0",
        "docs": "/docs",
        "quick_start": {
            "1_start": "POST /analyze",
            "2_monitor": "GET /status/{execution_id}",
            "3_retrieve": "GET /result/{execution_id}",
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
# STARTUP / SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("=" * 80)
    print("MarginGuard AI — FastAPI Backend")
    print("=" * 80)
    print(f"[OK] API started at http://0.0.0.0:8000")
    print(f"[OK] Docs at http://0.0.0.0:8000/docs")
    print(f"[OK] LangGraph available: {LANGGRAPH_AVAILABLE}")
    print(f"[OK] Results directory: {RESULTS_DIR}")
    print("=" * 80)
    print()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
