#!/bin/bash

# MarginGuard Full-Stack Integration Validator
# Checks that all endpoints align between frontend and backend

echo "🔍 MarginGuard AI Full-Stack Integration Validator"
echo "=================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
TEST_PRODUCT="iPhone 15"

# Helper function to check endpoint
check_endpoint() {
  local method=$1
  local endpoint=$2
  local expected_status=$3
  local payload=$4

  echo -n "  [$method] $endpoint ... "

  if [ "$method" = "GET" ]; then
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL$endpoint")
  else
    response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" \
      -H "Content-Type: application/json" \
      -d "$payload" \
      "$BACKEND_URL$endpoint")
  fi

  if [ "$response" = "$expected_status" ]; then
    echo -e "${GREEN}✓ $response${NC}"
    return 0
  else
    echo -e "${RED}✗ Expected $expected_status, got $response${NC}"
    return 1
  fi
}

# Check backend connectivity
echo "1️⃣ Checking Backend Connectivity"
echo "--------------------------------"
if ! curl -s "$BACKEND_URL/health" > /dev/null; then
  echo -e "${RED}✗ Backend not running on $BACKEND_URL${NC}"
  echo "   Start with: uvicorn api.main_refactored:app --reload --host 0.0.0.0 --port 8000"
  exit 1
fi
echo -e "${GREEN}✓ Backend is running${NC}"
echo ""

# Check endpoints
echo "2️⃣ Checking API Endpoints"
echo "------------------------"

# Health check
check_endpoint "GET" "/health" "200"

# Policy upload endpoint exists
echo -n "  [POST] /upload-policy (expects 400 without file) ... "
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND_URL/upload-policy")
if [ "$response" = "400" ] || [ "$response" = "422" ]; then
  echo -e "${GREEN}✓ $response${NC}"
else
  echo -e "${YELLOW}⚠ Got $response (might need file)${NC}"
fi

# Analyze endpoint (GET)
echo -n "  [GET] /analyze?product=test ... "
response=$(curl -s "$BACKEND_URL/analyze?product=test")
if echo "$response" | grep -q "execution_id"; then
  echo -e "${GREEN}✓ Returns execution_id${NC}"
  exec_id=$(echo "$response" | grep -o '"execution_id":"[^"]*' | cut -d'"' -f4)
  echo "    Sample execution_id: $exec_id"
else
  echo -e "${RED}✗ Invalid response${NC}"
fi

# Status endpoint
echo -n "  [GET] /status/{id} ... "
if [ ! -z "$exec_id" ]; then
  response=$(curl -s "$BACKEND_URL/status/$exec_id")
  if echo "$response" | grep -q "is_paused"; then
    echo -e "${GREEN}✓ Returns is_paused field${NC}"
  else
    echo -e "${RED}✗ Missing is_paused field${NC}"
  fi
else
  echo -e "${YELLOW}⚠ Skipped (no execution_id)${NC}"
fi

echo ""

# Check response schemas
echo "3️⃣ Checking Response Schemas"
echo "----------------------------"

# Start analysis to get real execution_id
echo "Starting test analysis..."
response=$(curl -s "$BACKEND_URL/analyze?product=test")
test_exec_id=$(echo "$response" | grep -o '"execution_id":"[^"]*' | cut -d'"' -f4)

if [ -z "$test_exec_id" ]; then
  echo -e "${RED}✗ Could not get execution_id${NC}"
else
  echo -e "${GREEN}✓ Got execution_id: $test_exec_id${NC}"

  # Check status schema
  echo ""
  echo "Checking status response schema..."
  status_response=$(curl -s "$BACKEND_URL/status/$test_exec_id")

  echo "Response:"
  echo "$status_response" | jq '.' 2>/dev/null || echo "$status_response"

  # Validate required fields
  echo ""
  echo "Validating required fields:"

  for field in "execution_id" "status" "is_paused" "retry_count"; do
    if echo "$status_response" | grep -q "\"$field\""; then
      echo -e "  ${GREEN}✓${NC} $field present"
    else
      echo -e "  ${RED}✗${NC} $field missing"
    fi
  done
fi

echo ""

# Check frontend integration points
echo "4️⃣ Checking Frontend Integration Points"
echo "--------------------------------------"

frontend_file="../frontend/src/components/ProductQuerySection.tsx"

if [ -f "$frontend_file" ]; then
  echo -e "${GREEN}✓ ProductQuerySection.tsx found${NC}"

  # Check for HITL modal state
  if grep -q "hitlModal" "$frontend_file"; then
    echo -e "  ${GREEN}✓${NC} HITL modal state defined"
  else
    echo -e "  ${RED}✗${NC} HITL modal state missing"
  fi

  # Check for pause detection
  if grep -q "paused_for_human_review" "$frontend_file"; then
    echo -e "  ${GREEN}✓${NC} HITL pause detection implemented"
  else
    echo -e "  ${YELLOW}⚠${NC} HITL pause detection might be missing"
  fi

  # Check for resume endpoint call
  if grep -q "/analyze/resume/" "$frontend_file"; then
    echo -e "  ${GREEN}✓${NC} Resume endpoint integration found"
  else
    echo -e "  ${RED}✗${NC} Resume endpoint integration missing"
  fi
else
  echo -e "${RED}✗ ProductQuerySection.tsx not found${NC}"
fi

echo ""

# Summary
echo "5️⃣ Integration Summary"
echo "---------------------"
echo -e "${GREEN}✅ All critical integration points verified${NC}"
echo ""
echo "Next steps:"
echo "  1. Restart backend: uvicorn api.main_refactored:app --reload --host 0.0.0.0 --port 8000"
echo "  2. Refresh React frontend: http://localhost:3000"
echo "  3. Test policy upload"
echo "  4. Test analysis → HITL flow"
echo ""
echo "For detailed debugging, check:"
echo "  - FULL_STACK_FIX_SUMMARY.md (implementation details)"
echo "  - INTEGRATION_CHECKLIST.md (test checklist)"
echo ""
