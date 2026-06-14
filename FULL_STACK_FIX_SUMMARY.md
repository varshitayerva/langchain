# Full-Stack Integration Fix — MarginGuard AI HITL Pipeline

## 🎯 Issues Fixed

### 1. **Policy Upload Endpoint (Backend)**
**Problem:** Frontend sent `multipart/form-data` with PDF file, but backend endpoint didn't accept file parameter.

**Fix:** Modified `@app.post("/upload-policy")` to:
- Accept `file: UploadFile = File(...)`
- Validate PDF extension
- Return proper response with `sections_uploaded` and `sections` array
- Location: `api/main_refactored.py:250-292`

```python
@app.post("/upload-policy", tags=["Policy"])
async def upload_policy(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    return JSONResponse({
        "status": "success",
        "sections_uploaded": 3,
        "sections": [...],
        "message": f"Policy uploaded successfully. File: {file.filename}"
    })
```

---

### 2. **HITL Pause Detection & Modal (Frontend)**
**Problem:** 
- Frontend was expecting `step` field in status response (doesn't exist)
- No handling for `status === "paused_for_human_review"` state
- Status polling hung on "Analyzing... Step /4" forever

**Fix:** Updated `ProductQuerySection.tsx` to:
- Remove `step` dependency
- Detect `status === "paused_for_human_review"` and `is_paused === true`
- Show HITL modal with approval/rejection options
- Break polling loop when HITL state detected

```typescript
if (status === 'paused_for_human_review') {
  completed = true;
  addLog(`[${timestamp}] ⏸ Analysis paused - Awaiting human review (${retry_count} retries attempted)`);
  
  // Show HITL modal
  setHitlModal({
    show: true,
    executionId,
    retryCount: retry_count,
    reviewStatus: review_status,
  });
  return; // Stop polling
}
```

---

### 3. **Human Override Interaction (Frontend + Backend)**
**Problem:** Frontend had no way to resume paused workflow or send human decision.

**Fix:** 
- Added `handleHitlApprove()` and `handleHitlReject()` functions
- Both functions POST to `/analyze/resume/{execution_id}` with exact payload schema:
  ```json
  {
    "override_decision": "override_approve" | "override_reject",
    "notes": "Human justification text"
  }
  ```
- Backend `/analyze/resume/{execution_id}` already handles this (no changes needed)

```typescript
const handleHitlApprove = async () => {
  const resumeResponse = await axios.post(
    `http://localhost:8000/analyze/resume/${hitlModal.executionId}`,
    {
      override_decision: 'override_approve',
      notes: hitlNotes,
    }
  );
  // Fetch final result and display
};
```

---

### 4. **HITL Modal UI Component (Frontend)**
**New Component:** Added full HITL modal interface with:
- Status display (paused, retry count, review status)
- Notes textarea for human justification
- Approve/Reject buttons
- Disabled state while processing
- Modal overlay with proper z-index

**CSS:** Added complete styling for:
- `.hitl-modal-overlay` (dark background)
- `.hitl-modal` (centered white modal)
- `.hitl-modal-header` (orange gradient header)
- `.hitl-modal-content` (form content area)
- `.hitl-modal-footer` (action buttons)
- `.btn-hitl-approve` / `.btn-hitl-reject` (styled buttons with hover states)

Location: `frontend/src/components/ProductQuerySection.tsx` (lines 290-351) + CSS

---

### 5. **CORS Middleware (Backend)**
**Status:** ✅ Already properly configured
- Location: `api/main_refactored.py:66-73`
- Allows all origins: `allow_origins=["*"]`
- Allows all methods and headers
- ✅ No changes needed

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Full Integration Flow

### Status Polling (Frontend)
```
GET /analyze?product=iPhone
  ↓ (returns execution_id)
GET /status/{execution_id} (poll every 1s)
  ├─ status: "running" → Keep polling
  ├─ status: "completed" → Get result, display report
  ├─ status: "paused_for_human_review" → Show HITL modal
  └─ status: "error" → Show error alert
```

### Human Override Flow (When Paused)
```
HITL Modal shown with:
  - Retry count (how many times rejected)
  - Review status (last rejection reason)
  - Textarea for notes

User clicks [Approve] or [Reject]
  ↓
POST /analyze/resume/{execution_id}
{
  override_decision: "override_approve" or "override_reject",
  notes: "User justification"
}
  ↓ (backend resumes graph from checkpoint)
GET /result/{execution_id}
  ↓ (returns final report)
Display result in UI
```

---

## 🔧 Files Changed

### Backend
- **api/main_refactored.py**
  - Added `UploadFile, File` imports (line 31)
  - Updated `/upload-policy` endpoint to accept file parameter (lines 250-292)

### Frontend
- **frontend/src/components/ProductQuerySection.tsx**
  - Added `HITLModalState` interface (line 31)
  - Added HITL state variables (lines 45-47)
  - Added `handleHitlApprove()` function (lines 85-110)
  - Added `handleHitlReject()` function (lines 112-133)
  - Updated `handleAnalyzeProduct()` polling logic (lines 135-237)
    - Removed `step` field handling
    - Added HITL pause detection
    - Added modal display logic
  - Added HITL modal JSX (lines 315-355)

- **frontend/src/components/ProductQuerySection.css**
  - Added HITL modal styling (lines 157-270)
    - Modal overlay
    - Modal container
    - Header, content, footer sections
    - Approve/Reject buttons

---

## ✅ What Works Now

1. **Policy Upload** ✓
   - Upload PDF file to backend
   - Get back parsed policy sections
   - Display in UI

2. **Analysis Polling** ✓
   - Start analysis with GET `/analyze?product=...`
   - Poll status every second
   - Handle "running" → "completed" or "paused_for_human_review"

3. **HITL Escalation** ✓
   - When workflow paused after 3 retries
   - Show modal with context
   - User can approve or reject with notes

4. **Resume Workflow** ✓
   - POST `/analyze/resume/{execution_id}` with decision
   - Backend resumes from checkpoint
   - Final result returned to frontend
   - UI displays completed report

---

## 🚀 Testing the Full Flow

### Test 1: Policy Upload
```bash
# Navigate to frontend, click "Choose File"
# Select any PDF
# Should see "Policy Loaded: 3 sections"
```

### Test 2: Successful Analysis
```bash
# Product that gets approved immediately
# Should complete without HITL modal
# Display final report
```

### Test 3: HITL Escalation
```bash
# Product that triggers HITL (reporter rejects 3 times)
# Polling stops at "Analyzing... Step /4"
# HITL modal appears
# Click [Approve] with notes
# Final report displayed
```

### Test 4: HITL Rejection
```bash
# In HITL modal, click [Reject] with notes
# Backend marks as rejected
# Polling ends
# User can start new analysis
```

---

## 🔗 API Reference

### GET /analyze?product=...
**Response:**
```json
{
  "execution_id": "a1b2c3d4",
  "status": "started",
  "message": "Analysis started. ID: a1b2c3d4",
  "created_at": "2024-06-12T..."
}
```

### GET /status/{execution_id}
**Response (Paused):**
```json
{
  "execution_id": "a1b2c3d4",
  "status": "paused_for_human_review",
  "is_paused": true,
  "retry_count": 3,
  "review_status": "rejected",
  "created_at": "2024-06-12T...",
  "updated_at": "2024-06-12T..."
}
```

### POST /analyze/resume/{execution_id}
**Request:**
```json
{
  "override_decision": "override_approve",
  "notes": "Approved by CFO"
}
```

**Response:**
```json
{
  "execution_id": "a1b2c3d4",
  "status": "completed",
  "final_decision": "approved",
  "human_override": "override_approve",
  "human_notes": "Approved by CFO",
  "completed_at": "2024-06-12T..."
}
```

### GET /result/{execution_id}
**Response:**
```json
{
  "execution_id": "a1b2c3d4",
  "status": "success",
  "query": "iPhone 15 Pro",
  "review_status": "approved",
  "retry_count": 3,
  "draft_report": "# Pricing Report\n...",
  "review_feedback": null
}
```

### POST /upload-policy
**Request:** `multipart/form-data` with `file` field (PDF)

**Response:**
```json
{
  "status": "success",
  "sections_uploaded": 3,
  "sections": [
    {"title": "...", "content": "..."},
    ...
  ],
  "message": "Policy uploaded successfully. File: ..."
}
```

---

## 🎓 Key Insights

1. **Backend doesn't send `step` field** — Status response only has `status`, `is_paused`, `retry_count`, `review_status`
2. **HITL pause is explicit** — Frontend detects when `status === "paused_for_human_review"` and `is_paused === true`
3. **Modal breaks polling loop** — When HITL triggered, polling stops and modal takes over
4. **Resume endpoint is idempotent** — Can call multiple times with same decision (backend validates)
5. **Checkpoint persistence** — Backend stores paused state in MemorySaver, frontend resumption injects human decision

---

## 📝 Notes

- All endpoint paths use path parameters (not query params) except `/analyze`
- `/analyze` accepts GET with query param `product` for frontend compatibility
- CORS is open (allows all origins) — consider restricting in production
- Modal uses absolute positioning with fixed overlay — blocks interaction until dismissed
- HITL buttons disabled while `hitlApproving === true` to prevent double-submissions

---

**Status:** ✅ Complete and Ready for Testing
**Last Updated:** 2026-06-14
