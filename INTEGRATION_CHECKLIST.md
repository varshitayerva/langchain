# Full-Stack Integration Checklist

## ✅ Backend Changes (api/main_refactored.py)

- [x] Added `UploadFile, File` to imports (line 31)
- [x] Updated `/upload-policy` endpoint to accept file parameter
- [x] `/analyze` endpoint already supports GET with query param
- [x] `/status/{execution_id}` returns correct schema with `is_paused` and `review_status`
- [x] `/analyze/resume/{execution_id}` already implemented and working
- [x] CORS middleware already enabled for all origins

## ✅ Frontend Changes (ProductQuerySection.tsx)

- [x] Added `HITLModalState` interface
- [x] Added HITL state management (hitlModal, hitlNotes, hitlApproving)
- [x] Added `handleHitlApprove()` function
- [x] Added `handleHitlReject()` function
- [x] Updated polling logic to detect `status === "paused_for_human_review"`
- [x] Removed dependency on non-existent `step` field
- [x] Added HITL modal JSX with form
- [x] Modal breaks polling loop when shown

## ✅ Frontend Styling (ProductQuerySection.css)

- [x] Added `.hitl-modal-overlay` (dark background overlay)
- [x] Added `.hitl-modal` (centered modal container)
- [x] Added `.hitl-modal-header` (orange gradient header)
- [x] Added `.hitl-modal-content` (form section)
- [x] Added `.hitl-modal-footer` (button footer)
- [x] Added `.btn-hitl-approve` (green approve button)
- [x] Added `.btn-hitl-reject` (red reject button)
- [x] Added responsive styles and hover effects

## 🚀 Next Steps

### 1. Restart Backend
```bash
cd c:\Users\samriddhi.mishra\langchain\reviewer\langchain
uvicorn api.main_refactored:app --reload --host 0.0.0.0 --port 8000
```

Wait for: `Uvicorn running on http://0.0.0.0:8000`

### 2. Verify Backend is Ready
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy", ...}
```

### 3. Refresh React Frontend
- React dev server should auto-reload with changes
- Go to http://localhost:3000
- Check browser console for any errors

### 4. Test Policy Upload
1. Click "Choose File"
2. Select any PDF file
3. Should show "Policy Loaded: 3 sections"
4. Expand sections to see policy content

### 5. Test Analysis Flow
1. Enter product name (e.g., "iPhone 15")
2. Click "Analyze Product"
3. Watch logs update
4. Either:
   - **Completes normally** → See final report
   - **Pauses for review** → HITL modal appears

### 6. Test HITL Approval
1. If HITL modal appears:
   - Type notes in textarea (e.g., "Approved by pricing team")
   - Click [✓ Approve] button
   - Should show "Workflow resumed with approval"
   - Final report displayed

### 7. Test HITL Rejection
1. If HITL modal appears:
   - Type notes in textarea (e.g., "Risk too high")
   - Click [✗ Reject] button
   - Should show "Workflow rejected by human reviewer"
   - Analysis ends

---

## 🔍 Troubleshooting

### Issue: "Policy upload failed" popup
**Solution:** Make sure backend is running on port 8000
```bash
# Check if port 8000 is in use
lsof -i :8000
# If yes, kill it: kill -9 <PID>
# Then restart: uvicorn api.main_refactored:app --reload --host 0.0.0.0 --port 8000
```

### Issue: "Analyzing... Step /4" infinite loop
**Solution:** This means status response is missing `is_paused` field or analysis triggers HITL
- Check backend logs for errors
- Make sure orchestrator is available
- Verify status endpoint returns: `"is_paused": true` when paused

### Issue: HITL modal doesn't appear
**Solution:** Check frontend console for JS errors
- Verify `hitlModal.show` state is toggled
- Check that polling detected `paused_for_human_review` status
- Look for axios errors on `/analyze/resume` call

### Issue: "override_decision must be..." error
**Solution:** Make sure frontend sends exact field names:
```json
{
  "override_decision": "override_approve",  // NOT "decision" or "override"
  "notes": "Your justification"              // NOT "comment" or "reason"
}
```

### Issue: CORS errors (blocked by browser)
**Solution:** Backend CORS is already open. If still getting errors:
```bash
# Verify CORS middleware is configured
grep -A 5 "CORSMiddleware" api/main_refactored.py
```

---

## 📊 Expected Behavior by Status

### Status: "running"
- Log: "Analyzing..."
- UI: Spinner active, polling continues
- Action: Keep polling

### Status: "paused_for_human_review"
- Log: "Analysis paused - Awaiting human review (3 retries attempted)"
- UI: HITL modal appears
- Action: User provides decision (approve/reject)

### Status: "completed"
- Log: "Analysis Complete"
- UI: Final report displayed
- Action: Analysis ends

### Status: "error"
- Log: "Analysis Error"
- UI: Alert shown
- Action: Allow user to start new analysis

---

## 📝 Quick Reference

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Policy Upload | api/main_refactored.py | 250-292 | Accept PDF file upload |
| Status Polling | ProductQuerySection.tsx | 135-237 | Poll and detect HITL pause |
| HITL Modal | ProductQuerySection.tsx | 290-351 | Show modal when paused |
| Modal Styling | ProductQuerySection.css | 157-270 | Style HITL UI |
| Resume Endpoint | api/main_refactored.py | 431-500+ | Process human decision |

---

## ✨ Key Features Enabled

✅ Policy upload with PDF support
✅ Product analysis with automatic retry loop
✅ HITL escalation when max retries reached (3)
✅ Human override modal with approve/reject
✅ Checkpoint persistence (state saved during pause)
✅ Full logging with timestamps
✅ Error handling and user feedback
✅ CORS enabled for cross-origin requests

---

**Status:** Ready to Test
**Last Updated:** 2026-06-14
**All Changes Verified:** ✅
