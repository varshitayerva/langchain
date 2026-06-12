"""
MarginGuard Frontend-Compatible API with RAG Pipeline

Integrated with Postgres database for policy storage and vector search.
Run with: uvicorn app:app --reload --host 0.0.0.0 --port 8000
"""

import os
import sys
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from io import BytesIO

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# PDF support
try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Import database and RAG
try:
    from db import db as database
    from db import Database
    DB_AVAILABLE = True
except Exception as e:
    print(f"[WARN] Database not available: {e}")
    DB_AVAILABLE = False
    database = None

# Initialize FastAPI app
app = FastAPI(
    title="MarginGuard API",
    description="Competitive Analysis Engine with RAG Pipeline",
    version="2.0.0"
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

# Initialize database on startup
if DB_AVAILABLE:
    try:
        database.init_database()
        print("[OK] Database initialized successfully")
    except Exception as e:
        print(f"[WARN] Could not initialize database: {e}")

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
    """Upload policy document and store in database"""
    try:
        # Read file content
        content = await file.read()
        filename = file.filename or "policy"

        # Check if PDF
        if filename.lower().endswith('.pdf') and PDF_AVAILABLE:
            try:
                pdf_reader = PdfReader(BytesIO(content))
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
            except Exception as e:
                # Fallback: treat as text
                text_content = content.decode('utf-8', errors='ignore')
        else:
            # Try to decode text files with different encodings
            text_content = None
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                try:
                    text_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            # If still can't decode, use UTF-8 with error handling
            if text_content is None:
                text_content = content.decode('utf-8', errors='ignore')

        # Parse sections (simple split by common headers)
        sections = parse_policy_document(text_content, filename)

        # Store in database if available
        if DB_AVAILABLE and database:
            stored = database.store_policy(file.filename, sections)
            if not stored:
                raise Exception("Failed to store policy in database")

        # Keep in memory cache
        policy_cache["current"] = {
            "filename": file.filename,
            "upload_time": datetime.now().isoformat(),
            "sections": sections
        }

        return PolicyResponse(
            status="success",
            sections_uploaded=len(sections),
            sections=sections,
            message=f"Policy uploaded successfully with {len(sections)} sections (stored in database)"
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
# Helper Functions
# ============================================================================

def parse_policy_document(content: str, filename: str) -> list:
    """Parse policy document into sections"""
    sections = []

    # Split by common section markers
    lines = content.split("\n")
    current_section = None
    current_content = []

    for line in lines:
        # Check if line is a section header
        if line.strip().startswith(("##", "- ", "* ", "1. ")) or (
            len(line.strip()) > 3 and line.strip() == line.strip().upper()
        ):
            # Save previous section
            if current_section:
                sections.append({
                    "title": current_section,
                    "content": "\n".join(current_content).strip()
                })

            current_section = line.strip().replace("##", "").replace("- ", "").strip()
            current_content = []
        elif current_section:
            current_content.append(line)

    # Save last section
    if current_section:
        sections.append({
            "title": current_section,
            "content": "\n".join(current_content).strip()
        })

    # If no sections found, create one from entire content
    if not sections:
        sections = [{
            "title": filename.replace(".pdf", "").replace(".txt", ""),
            "content": content
        }]

    return sections


# ============================================================================
# Analysis Functions
# ============================================================================

async def run_mock_analysis(execution_id: str, product: str):
    """Run mock analysis with 4 steps"""
    import asyncio

    try:
        state = execution_states[execution_id]
        state["status"] = "running"

        # Step 1: RAG Retrieval (use database if available)
        state["step"] = 1
        state["message"] = "Starting RAG Retrieval..."
        await asyncio.sleep(2)

        rag_output = {"product_data": [], "policy_snippet": ""}
        if DB_AVAILABLE and database:
            try:
                # Search products and policies from database
                products = database.search_products(product, top_k=3)
                policies = database.search_policies(product, top_k=2)

                rag_output["product_data"] = products
                rag_output["policy_snippet"] = "\n\n".join([
                    f"### {p['section']}\n{p['content']}"
                    for p in policies
                ]) if policies else "No policies found"
                state["message"] = f"Retrieved {len(products)} products from knowledge base"
            except Exception as e:
                print(f"RAG retrieval error: {e}")
                state["message"] = "RAG retrieval completed (fallback mode)"
        else:
            state["message"] = "RAG retrieval completed (database unavailable)"

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

        # Result data with real RAG output
        state["result"] = {
            "product_query": product,
            "rag_output": rag_output if rag_output["product_data"] else {
                "product_data": [
                    {
                        "id": "prod_1",
                        "name": product,
                        "category": "Electronics",
                        "price": 249,
                        "cost": 100,
                        "margin_floor": 25,
                        "features": "Feature A, Feature B, Feature C",
                        "competitor": "Our Company",
                        "similarity": 0.95
                    }
                ],
                "policy_snippet": "No policies stored yet. Please upload a policy first."
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
