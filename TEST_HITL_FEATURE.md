# Testing the HITL (Human-in-the-Loop) Feature

## 🎯 What Is HITL?

When the automated reviewer rejects a pricing report **3 times**, the workflow pauses and waits for a human decision instead of failing:

```
Analysis Start
  ↓
Synthesis (attempt 1) → Reviewer rejects
  ↓
Synthesis (attempt 2) with feedback → Reviewer rejects
  ↓
Synthesis (attempt 3) with feedback → Reviewer rejects
  ↓
⏸ PAUSE: Show HITL Modal
  ↓
Human clicks [Approve] or [Reject]
  ↓
Workflow resumes/completes
```

---

## 🧪 How to Trigger HITL (Make Reviewer Reject)

### Option 1: Modify Reviewer to Reject (Recommended)

The reviewer is in `orchestration/langgraph_orchestrator_refactored.py`. Let me show you how to make it intentionally reject:

**Locate the reviewer at line ~220:**

```python
class RealReviewerAgent:
    """Phase 5: Reviewer Agent - Audits for compliance."""

    def audit(self, report: str, rag_context: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        if review is None:
            return {"status": "approved", "feedback": None}  # ← Currently always approves
```

**Change it to intentionally reject (for testing):**

```python
def audit(self, report: str, rag_context: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
    if review is None:
        # For HITL testing: Always reject to trigger human review after 3 attempts
        return {
            "status": "rejected",
            "feedback": "Price does not meet margin floor requirements. Human review needed."
        }
```

### Option 2: Use Query Parameter to Trigger Rejection

Or modify it to reject based on query content:

```python
def audit(self, report: str, rag_context: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
    if review is None:
        # Reject if query contains "test" to enable testing
        query = rag_context.get('query', '').lower() if isinstance(rag_context, dict) else ''
        if 'test' in query or 'hitl' in query:
            return {
                "status": "rejected",
                "feedback": "Test mode: Intentionally rejecting to demonstrate HITL escalation."
            }
        return {"status": "approved", "feedback": None}
```

---

## 📋 Testing Steps

### Step 1: Make Reviewer Reject

Edit `orchestration/langgraph_orchestrator_refactored.py` around line 220:

```python
def audit(self, report: str, rag_context: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
    if review is None:
        return {
            "status": "rejected",
            "feedback": "Demo mode: Rejecting to test HITL escalation"
        }
```

Save the file.

### Step 2: Restart Backend

```bash
# Press Ctrl+C to stop
# Then restart:
uvicorn api.main_refactored:app --reload --host 0.0.0.0 --port 8000
```

Watch the console — you should see the changes reload.

### Step 3: Refresh Frontend

In browser, press `Ctrl+Shift+R` (hard refresh)

### Step 4: Start Analysis

1. Make sure policy is loaded
2. Enter product name: `iPhone 15` (or any product)
3. Click "Analyze Product"

### Step 5: Watch the Console Logs

In **backend terminal**, you should see:

```
================================================================================
LANGGRAPH ORCHESTRATION — EXECUTION START
Execution ID: 12345678
================================================================================

[ORCHESTRATOR] Starting MarginGuard AI pipeline
Query: iphone 15

[RAG] Error: RAG not available
[RESEARCH] Error: Product name not provided

[SYNTHESIS] Report generated (attempt 1/4)
[REVIEWER] ❌ [REJECTED] Demo mode: Rejecting to test HITL escalation

[SYNTHESIS] Report regenerated with feedback (attempt 2/4)
[REVIEWER] ❌ [REJECTED] Demo mode: Rejecting to test HITL escalation

[SYNTHESIS] Report regenerated with feedback (attempt 3/4)
[REVIEWER] ❌ [REJECTED] Demo mode: Rejecting to test HITL escalation

⏸ PAUSING FOR HUMAN REVIEW - Max retries (3) reached
```

### Step 6: HITL Modal Appears

In the **React frontend**, instead of showing the final report, you should see:

```
┌─────────────────────────────────────┐
│ ⏸ Human Review Required             │
├─────────────────────────────────────┤
│ The pricing report was rejected      │
│ 3 times. Please review and make a    │
│ final decision.                      │
│                                      │
│ Status: rejected                     │
│ Retries: 3/3                         │
│                                      │
│ Your Decision Notes:                 │
│ ┌──────────────────────────────────┐│
│ │ [Text area for your notes]        ││
│ └──────────────────────────────────┘│
│                                      │
│ [✓ Approve]  [✗ Reject]              │
└─────────────────────────────────────┘
```

### Step 7: Make a Decision

**Option A: Click Approve**

1. Type in textarea: `"Approved by pricing team. Risk acceptable."`
2. Click `[✓ Approve]` button
3. Watch backend logs:
   ```
   POST /analyze/resume/12345678 with human decision
   [HITL] Human override: override_approve
   [HITL] Workflow resumed and completed
   ```
4. Frontend shows final report

**Option B: Click Reject**

1. Type in textarea: `"Rejected - pricing too risky"`
2. Click `[✗ Reject]` button
3. Watch backend logs:
   ```
   POST /analyze/resume/12345678 with human decision
   [HITL] Human override: override_reject
   [HITL] Workflow marked as rejected
   ```
4. Analysis ends (no report shown)

---

## 🔍 What to Look For

### Backend Console Indicators

✅ **HITL Triggered:**
```
⏸ PAUSING FOR HUMAN REVIEW - Max retries (3) reached
```

✅ **Status Endpoint Returns:**
```json
{
  "status": "paused_for_human_review",
  "is_paused": true,
  "retry_count": 3
}
```

✅ **Human Decision Processed:**
```
[HITL] Human override: override_approve
[HITL] Graph resumed from checkpoint
```

### Frontend Indicators

✅ **HITL Modal Shows:** Orange header with "⏸ Human Review Required"
✅ **Retry Count Display:** Shows "Retries: 3/3"
✅ **Buttons Enabled:** Can only click when notes are entered
✅ **Approval Success:** Shows final report after approval

---

## 📊 Full Flow Visualization

### Approval Flow (When HITL → Approve)
```
Analysis Start
  ↓ (GET /analyze)
Poll Status (1s intervals)
  ├─ Status: running
  ├─ Status: running
  ├─ ... (3 rejections happen)
  ├─ Status: paused_for_human_review ← ⚠️
  │   └─ is_paused: true
  │   └─ retry_count: 3
  └─ HITL Modal appears
      ↓
    User enters notes
      ↓
    Click [✓ Approve]
      ↓ (POST /analyze/resume/{id})
    Workflow resumed from checkpoint
      ↓
    GET /result/{id}
      ↓
    Final report displayed ✅
```

### Rejection Flow (When HITL → Reject)
```
[Same until HITL Modal appears]

HITL Modal appears
  ↓
User enters notes
  ↓
Click [✗ Reject]
  ↓ (POST /analyze/resume/{id})
Workflow marked as rejected
  ↓
Modal closes
  ↓
Analysis ends ❌
(No report shown)
```

---

## 🧬 Code Changes for Testing

### Make Reviewer Always Reject

**File:** `orchestration/langgraph_orchestrator_refactored.py`
**Line:** ~220

```python
class RealReviewerAgent:
    def audit(self, report: str, rag_context: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        if review is None:
            return {
                "status": "rejected",
                "feedback": "HITL Test Mode: Intentional rejection to demonstrate escalation"
            }
        # ... rest of code
```

### Conditional Rejection (Only for Test Queries)

```python
def audit(self, report: str, rag_context: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
    if review is None:
        # Only reject if testing HITL
        if isinstance(rag_context, dict) and 'query' in rag_context:
            query = str(rag_context.get('query', '')).lower()
            if 'test' in query or 'hitl' in query:
                return {
                    "status": "rejected",
                    "feedback": "Test: Rejecting for HITL demonstration"
                }
        return {"status": "approved", "feedback": None}
```

Then test with product: `"iPhone 15 HITL test"` or `"test product"`

---

## 🎓 What HITL Demonstrates

1. **Automated Retry Loop**
   - System retries synthesis 3 times automatically
   - Each retry incorporates reviewer feedback for self-correction

2. **Intelligent Escalation**
   - After max retries, doesn't fail hard
   - Pauses and waits for human judgment
   - Checkpoint preserves all state

3. **Human Override**
   - Human can override system decision
   - Provides justification notes
   - Decision gets applied and workflow completes

4. **Better Than Hard Failure**
   - Old system: After 3 rejections → `sys.exit(1)` 🔴
   - New system: Pauses for human override 🟢

---

## 📝 Example Scenario

### Scenario: Aggressive Pricing Strategy

**Setup:**
- Product: `"iPhone 15"`
- Reviewer rejects anything with margin < 40%

**What Happens:**

1. **Attempt 1:** Synthesis suggests $799/mo
   - Reviewer: ❌ "Margin too low (28%)"

2. **Attempt 2:** Synthesis (with feedback) suggests $899/mo
   - Reviewer: ❌ "Still too low (32%)"

3. **Attempt 3:** Synthesis (with feedback) suggests $999/mo
   - Reviewer: ❌ "Barely meets floor (39%)"

4. **Escalation:** HITL modal appears
   - Human reads all three versions
   - Sees the strategy evolution
   - Decides: `$999/mo is acceptable given market conditions`
   - Clicks [✓ Approve]

5. **Result:** Report approved with human note
   - Final report shows all three iterations
   - Decision timestamp and human notes included

---

## 🚀 Complete Demo Script

```bash
# 1. Terminal 1: Start backend
cd c:\Users\samriddhi.mishra\langchain\reviewer\langchain
uvicorn api.main_refactored:app --reload --host 0.0.0.0 --port 8000

# 2. Edit orchestrator (in another editor):
# vim orchestration/langgraph_orchestrator_refactored.py
# Change line ~220 to return rejected status
# Save file

# 3. Wait for auto-reload:
# "Reloader process started"

# 4. Browser: Hard refresh
# Ctrl+Shift+R

# 5. Upload policy
# Click "Choose File" → Select PDF → See "Policy Loaded: 3 sections"

# 6. Analyze with HITL trigger
# Product: "iPhone 15"
# Click "Analyze Product"

# 7. Watch progression
# Console logs show:
# - Attempt 1: [REVIEWER] ❌ [REJECTED]
# - Attempt 2: [REVIEWER] ❌ [REJECTED]
# - Attempt 3: [REVIEWER] ❌ [REJECTED]
# - ⏸ PAUSING FOR HUMAN REVIEW

# 8. HITL Modal appears
# Type notes: "Approved by pricing team"
# Click [✓ Approve]

# 9. Workflow resumes
# Final report displayed
```

---

## 🎬 Live Demo Talking Points

1. **"The old system would fail after 3 rejections with sys.exit(1)"**
   - Point to old behavior in git history
   - Explain hard failures are bad

2. **"Our new system escalates to humans gracefully"**
   - Show HITL modal appearing
   - Highlight retry count: "3/3"
   - Show notes textarea

3. **"The human can override with full context"**
   - Point to synthesis + reviewer feedback
   - Show what notes they entered
   - Explain this preserves domain knowledge

4. **"The workflow resumes from checkpoint"**
   - Show backend logs: "Graph resumed from checkpoint"
   - Explain state persistence
   - No lost data, no re-execution

5. **"Compare to manual processes"**
   - Old: Email back-and-forth, manual spreadsheets
   - New: Click one button, get modal, decide, done
   - Faster, auditable, documented

---

## ✅ Verification Checklist

- [ ] Backend shows 3 rejected attempts
- [ ] HITL modal appears on frontend
- [ ] Modal shows correct retry count (3/3)
- [ ] Notes textarea is required
- [ ] Buttons disabled until notes entered
- [ ] Approve button triggers workflow resume
- [ ] Reject button ends analysis
- [ ] Final report shows after approve
- [ ] Backend logs show checkpoint resume
- [ ] Human decision is saved/persisted

---

**Ready to demo HITL? Start with Step 1 above!**
