"""
MarginGuard Frontend-Compatible API

Simple API that works with the React frontend.
Run with: uvicorn app:app --reload --host 0.0.0.0 --port 8000
"""

import os
import sys
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="MarginGuard API",
    description="Competitive Analysis Engine",
    version="1.0.0"
)

# CORS enabled
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
execution_states: Dict[str, Dict[str, Any]] = {}
policy_cache: Dict[str, Any] = {}

# ============================================================================
# Data Models
# ============================================================================

class PolicyResponse(BaseModel):
    status: str
    sections_uploaded: int
    sections: list
    message: str

class AnalysisStartResponse(BaseModel):
    execution_id: str
    status: str
    message: str

class StatusResponse(BaseModel):
    status: str
    step: int
    message: str
    progress: float

class ResultResponse(BaseModel):
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "healthy",
        "service": "MarginGuard API",
        "version": "1.0.0"
    }

@app.post("/upload-policy", response_model=PolicyResponse)
async def upload_policy(file: UploadFile = File(...)):
    """Upload policy document"""
    try:
        # Mock sections for any file
        sections = [
            {
                "title": "Pricing Policy",
                "content": "All pricing must follow market-based pricing strategies with margin floors of 25%."
            },
            {
                "title": "Feature Parity Requirements",
                "content": "Products must maintain 70% feature parity with competitive offerings."
            },
            {
                "title": "Compliance Rules",
                "content": "All competitive pricing decisions must be reviewed before implementation."
            }
        ]

        policy_cache["current"] = {
            "filename": file.filename,
            "upload_time": datetime.now().isoformat(),
            "sections": sections
        }

        return PolicyResponse(
            status="success",
            sections_uploaded=len(sections),
            sections=sections,
            message=f"Policy uploaded successfully with {len(sections)} sections"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/analyze")
async def start_analysis(product: str, background_tasks: BackgroundTasks) -> AnalysisStartResponse:
    """Start analysis for a product"""
    if not policy_cache.get("current"):
        raise HTTPException(status_code=400, detail="No policy loaded")

    if not product.strip():
        raise HTTPException(status_code=400, detail="Product name required")

    execution_id = str(uuid.uuid4())

    execution_states[execution_id] = {
        "status": "pending",
        "step": 0,
        "message": "Initializing analysis...",
        "product": product,
        "start_time": datetime.now().isoformat()
    }

    # Schedule background analysis
    background_tasks.add_task(run_mock_analysis, execution_id, product)

    return AnalysisStartResponse(
        execution_id=execution_id,
        status="started",
        message=f"Analysis started for {product}"
    )

@app.get("/status", response_model=StatusResponse)
async def get_status(id: str) -> StatusResponse:
    """Get analysis status"""
    if id not in execution_states:
        raise HTTPException(status_code=404, detail="Execution not found")

    state = execution_states[id]
    progress = (state.get("step", 0) / 4) * 100

    return StatusResponse(
        status=state["status"],
        step=state.get("step", 0),
        message=state.get("message", ""),
        progress=progress
    )

@app.get("/result", response_model=ResultResponse)
async def get_result(id: str) -> ResultResponse:
    """Get analysis results"""
    if id not in execution_states:
        raise HTTPException(status_code=404, detail="Execution not found")

    state = execution_states[id]

    if state["status"] == "completed":
        return ResultResponse(
            status="success",
            data=state.get("result")
        )
    elif state["status"] == "failed":
        return ResultResponse(
            status="error",
            error=state.get("error", "Analysis failed")
        )
    else:
        return ResultResponse(status="pending", data=None)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_executions": len([s for s in execution_states.values() if s["status"] == "running"])
    }

# ============================================================================
# Mock Analysis Function
# ============================================================================

async def run_mock_analysis(execution_id: str, product: str):
    """Run mock analysis with 4 steps"""
    import asyncio

    try:
        state = execution_states[execution_id]
        state["status"] = "running"

        # Step 1: RAG Retrieval
        state["step"] = 1
        state["message"] = "Starting RAG Retrieval..."
        await asyncio.sleep(2)
        state["message"] = "Retrieved 3 products from knowledge base"

        # Step 2: Research Agent
        state["step"] = 2
        state["message"] = "Running Research Agent..."
        await asyncio.sleep(2)
        state["message"] = "Analyzed 5 competitors"

        # Step 3: Synthesis
        state["step"] = 3
        state["message"] = "Synthesizing results..."
        await asyncio.sleep(2)
        state["message"] = "Generated recommendations"

        # Step 4: Review
        state["step"] = 4
        state["message"] = "Final review and approval..."
        await asyncio.sleep(2)
        state["message"] = "Analysis complete"

        # Mock result data
        state["result"] = {
            "product_query": product,
            "rag_output": {
                "product_data": [
                    {
                        "id": "prod_1",
                        "name": product,
                        "category": "Electronics",
                        "price": 249,
                        "cost": 100,
                        "margin_floor": 25,
                        "features": ["Feature A", "Feature B", "Feature C"],
                        "competitor": "Our Company"
                    }
                ],
                "policy_snippet": "Pricing must maintain 25% margin floor..."
            },
            "research_results": [
                {
                    "competitor_name": "Sony XM5",
                    "price_normalized": 399,
                    "feature_parity": 85,
                    "price_gap": 150,
                    "margin_feasible": True,
                    "source": "https://example.com"
                },
                {
                    "competitor_name": "Bose QC45",
                    "price_normalized": 379,
                    "feature_parity": 75,
                    "price_gap": 130,
                    "margin_feasible": True,
                    "source": "https://example.com"
                },
                {
                    "competitor_name": "Sennheiser Momentum",
                    "price_normalized": 399,
                    "feature_parity": 80,
                    "price_gap": 150,
                    "margin_feasible": True,
                    "source": "https://example.com"
                },
                {
                    "competitor_name": "Audio-Technica ATH",
                    "price_normalized": 299,
                    "feature_parity": 65,
                    "price_gap": 50,
                    "margin_feasible": True,
                    "source": "https://example.com"
                },
                {
                    "competitor_name": "JBL Elite",
                    "price_normalized": 279,
                    "feature_parity": 70,
                    "price_gap": 30,
                    "margin_feasible": True,
                    "source": "https://example.com"
                }
            ]
        }

        state["status"] = "completed"

    except Exception as e:
        state["status"] = "failed"
        state["error"] = str(e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    )
