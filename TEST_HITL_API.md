# Testing MarginGuard HITL API

## ✅ API is Running!

Your backend is started and ready. Now let's test it correctly.

---

## 🚨 Common Mistake

```bash
# ❌ WRONG - GET request
curl http://localhost:8000/analyze

# Error: 405 Method Not Allowed
```

---

## ✅ Correct Way to Test

### Test 1: Health Check (GET is OK here)

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "orchestrator": "ready",
  "timestamp": "2024-06-12T10:30:45.123456"
}
```

---

### Test 2: Start Analysis (POST required)

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "CloudScale Enterprise Tier-2 pricing",
    "save_result": true
  }'
```

**Expected Response:**
```json
{
  "execution_id": "a1b2c3d4",
  "status": "started",
  "message": "Analysis started. ID: a1b2c3d4",
  "created_at": "2024-06-12T10:30:45.123456"
}
```

**Save the execution_id** from the response (you'll need it next).

---

### Test 3: Poll Status (GET is OK)

```bash
# Replace a1b2c3d4 with your actual execution_id
curl http://localhost:8000/status/a1b2c3d4
```

**Expected Response (while running):**
```json
{
  "execution_id": "a1b2c3d4",
  "status": "running",
  "is_paused": false,
  "retry_count": 0,
  "created_at": "2024-06-12T10:30:45.123456",
  "updated_at": "2024-06-12T10:30:50.654321"
}
```

**Expected Response (if paused for HITL):**
```json
{
  "execution_id": "a1b2c3d4",
  "status": "paused_for_human_review",
  "is_paused": true,
  "retry_count": 3,
  "review_status": "rejected",
  "created_at": "2024-06-12T10:30:45.123456",
  "updated_at": "2024-06-12T10:31:15.987654"
}
```

---

### Test 4: Resume with Human Decision (POST required)

When status is `paused_for_human_review`:

```bash
curl -X POST http://localhost:8000/analyze/resume/a1b2c3d4 \
  -H "Content-Type: application/json" \
  -d '{
    "override_decision": "override_approve",
    "notes": "Approved by CFO. Acceptable risk given market conditions."
  }'
```

**Expected Response:**
```json
{
  "execution_id": "a1b2c3d4",
  "status": "completed",
  "final_decision": "approved",
  "human_override": "override_approve",
  "human_notes": "Approved by CFO...",
  "completed_at": "2024-06-12T10:31:45.987654"
}
```

---

### Test 5: Get Final Result (GET is OK)

```bash
curl http://localhost:8000/result/a1b2c3d4
```

**Expected Response (when completed):**
```json
{
  "execution_id": "a1b2c3d4",
  "status": "success",
  "query": "CloudScale Enterprise Tier-2 pricing",
  "review_status": "approved",
  "retry_count": 3,
  "draft_report": "# Market Position & Pricing Strategy Report\n...",
  "review_feedback": null
}
```

---

## 📋 Complete Workflow Example

```bash
#!/bin/bash

# Step 1: Start analysis
echo "1️⃣ Starting analysis..."
RESPONSE=$(curl -s -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "CloudScale Enterprise Tier-2 pricing",
    "save_result": true
  }')

EXEC_ID=$(echo $RESPONSE | grep -o '"execution_id":"[^"]*' | cut -d'"' -f4)
echo "Execution ID: $EXEC_ID"
echo

# Step 2: Poll status until paused or completed
echo "2️⃣ Polling status..."
while true; do
  STATUS=$(curl -s http://localhost:8000/status/$EXEC_ID)
  STATE=$(echo $STATUS | grep -o '"status":"[^"]*' | cut -d'"' -f4)
  PAUSED=$(echo $STATUS | grep -o '"is_paused":[^,}]*' | cut -d':' -f2)
  
  echo "Status: $STATE, Paused: $PAUSED"
  
  if [ "$STATE" = "paused_for_human_review" ] || [ "$STATE" = "completed" ]; then
    break
  fi
  
  sleep 1
done
echo

# Step 3: If paused, resume with human decision
if [ "$STATE" = "paused_for_human_review" ]; then
  echo "3️⃣ Resuming with human decision..."
  RESUME=$(curl -s -X POST http://localhost:8000/analyze/resume/$EXEC_ID \
    -H "Content-Type: application/json" \
    -d '{
      "override_decision": "override_approve",
      "notes": "Approved by pricing committee"
    }')
  echo $RESUME | jq '.'
  echo
fi

# Step 4: Get final result
echo "4️⃣ Getting final result..."
curl -s http://localhost:8000/result/$EXEC_ID | jq '.'
```

---

## 🐍 Python Testing

```python
import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Step 1: Start analysis
print("1️⃣ Starting analysis...")
response = requests.post(
    f"{BASE_URL}/analyze",
    json={
        "query": "CloudScale Enterprise Tier-2 pricing",
        "save_result": True
    }
)
data = response.json()
execution_id = data["execution_id"]
print(f"Execution ID: {execution_id}\n")

# Step 2: Poll status
print("2️⃣ Polling status...")
while True:
    status = requests.get(f"{BASE_URL}/status/{execution_id}").json()
    print(f"Status: {status['status']}, Paused: {status['is_paused']}")
    
    if status['status'] in ["paused_for_human_review", "completed"]:
        break
    
    time.sleep(1)
print()

# Step 3: If paused, resume
if status['status'] == "paused_for_human_review":
    print("3️⃣ Resuming with human decision...")
    resume = requests.post(
        f"{BASE_URL}/analyze/resume/{execution_id}",
        json={
            "override_decision": "override_approve",
            "notes": "Approved by CFO"
        }
    ).json()
    print(json.dumps(resume, indent=2))
    print()

# Step 4: Get result
print("4️⃣ Getting final result...")
result = requests.get(f"{BASE_URL}/result/{execution_id}").json()
print(json.dumps(result, indent=2))
```

---

## 📍 Endpoint Reference

| Method | Endpoint | Purpose | Body Required |
|--------|----------|---------|---|
| POST | `/analyze` | Start analysis | ✅ Yes |
| GET | `/status/{id}` | Check progress | ❌ No |
| GET | `/result/{id}` | Get result | ❌ No |
| POST | `/analyze/resume/{id}` | Resume with decision | ✅ Yes |
| GET | `/health` | Health check | ❌ No |
| GET | `/info` | API info | ❌ No |

---

## ✅ Checklist

- [x] API is running on localhost:8000
- [ ] `POST /analyze` with valid query
- [ ] Poll `GET /status/{id}` every 1 second
- [ ] If paused, `POST /analyze/resume/{id}` with decision
- [ ] Check `GET /result/{id}` when completed

---

## 🎯 Expected Flow

```
User/Client
  ↓
POST /analyze → Returns execution_id
  ↓
GET /status (poll every 1s)
  ├─ status: "running"
  │  └─ Keep polling
  ├─ status: "paused_for_human_review"
  │  └─ POST /analyze/resume with decision
  └─ status: "completed"
     └─ GET /result to see full report
```

---

## 🚀 You're All Set!

Your HITL API is running correctly. Use the examples above to test all endpoints.

**Next:** 
- Test with different queries
- Monitor for HITL triggers
- Update frontend to handle paused state

Happy testing! 🎉
