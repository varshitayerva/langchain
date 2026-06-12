# MarginGuard AI — Quick Start Testing Guide

## Overview

All four agents are ready for testing. Follow the steps below based on what you want to test.

---

## ✅ Test 1: Synthesis Agent (No Dependencies)

**Status:** Works immediately  
**Why:** Uses mock HF router client (doesn't require actual HF token)

```bash
cd langchain/synthesis_agent
python synthesis_agent.py
```

**Expected Output:**
```
SYNTHESIS AGENT DUAL-SCHEMA SYSTEM VERIFICATION
[TEST 1] Testing PostgreSQL list normalization parameters...
[TEST 2] Testing Legacy/Mock flat dictionary normalization parameters...
[TEST 3] LangGraph Node Wrapper dictionary initialization update checking...
Node Wrapper State parsing pipeline verified successfully.
```

---

## ✅ Test 2: Reviewer Agent (With XAI_API_KEY)

**Status:** Ready but needs API key  
**Why:** Requires xAI Grok API for compliance auditing

### Step 1: Get XAI API Key

1. Go to [https://console.xai.com](https://console.xai.com)
2. Create account or log in
3. Generate API key
4. Copy the key

### Step 2: Add to .env

```bash
# Edit .env in project root
XAI_API_KEY=<your-key-from-step-1>
```

### Step 3: Run Tests

```bash
cd /root/project
python reviewer_agent.py
```

**Expected Output:**
```
================================================================================
TEST 1: PRODUCTION FORMAT (List) - REJECTION CASE
================================================================================
{
  "status": "rejected",
  "feedback": "- CRITICAL FINANCIAL GUARDRAIL VIOLATION..."
}

================================================================================
TEST 2: MOCK FORMAT (Dict) - REJECTION CASE
================================================================================
{
  "status": "rejected",
  "feedback": "- CRITICAL FINANCIAL GUARDRAIL VIOLATION..."
}

TEST 3: PRODUCTION FORMAT (List) - APPROVAL CASE
================================================================================
{
  "status": "approved",
  "feedback": null
}
...
```

---

## ⚠️ Test 3: RAG Agent (Requires Postgres Setup)

**Status:** Code verified, database unavailable  
**Why:** Needs local Postgres + pgvector database

### Option A: Docker Setup (Recommended)

```bash
# Start Postgres with pgvector
docker run --name pgvector \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  ankane/pgvector

# In another terminal, run ingestion
cd langchain/rag_agent
python ingestion.py
```

### Option B: Local Postgres

1. Install Postgres locally
2. Create database: `fde_langchain`
3. Install pgvector extension
4. Run ingestion script

### Test

```bash
cd langchain/rag_agent
python rag_agent.py
```

---

## ⚠️ Test 4: Research Agent (Requires Tavily API)

**Status:** Code verified, internet required  
**Why:** Needs Tavily Search API access

### Setup

```bash
# Verify TAVILY_API_KEY in .env
# Key should already be present from earlier setup
echo $TAVILY_API_KEY
```

### Test

```bash
cd langchain/researcher_agent
python research_agent.py
```

---

## 🔄 Full Pipeline Integration (Phase 6)

Once all prerequisites are met, the full pipeline will look like:

```
python langchain_orchestration.py --query "CloudScale Enterprise Tier-2 pricing"
```

This will:
1. RAG: Fetch product + policy data from Postgres
2. Research: Search competitors via Tavily
3. Synthesis: Generate pricing memo with reviewer feedback loop
4. Reviewer: Audit compliance
5. Output: Final approved report

---

## 📊 Testing Checklist

- [ ] Synthesis Agent test passes (no deps)
- [ ] XAI_API_KEY added to .env
- [ ] Reviewer Agent test passes (with XAI key)
- [ ] Postgres + pgvector setup (optional, for RAG)
- [ ] RAG Agent test passes (with Postgres)
- [ ] TAVILY_API_KEY verified
- [ ] Research Agent test passes
- [ ] Phase 6 orchestration script ready

---

## 🐛 Troubleshooting

### Error: "XAI_API_KEY environment variable is not set"
**Solution:** Add `XAI_API_KEY=your-key` to `.env` in the project root

### Error: "connection to server at localhost:5432 failed"
**Solution:** Start Postgres or use Docker setup (see Test 3)

### Error: "TAVILY_API_KEY not found"
**Solution:** Verify TAVILY_API_KEY in `.env` file

### Error: "HF_TOKEN missing" (Synthesis agent)
**Solution:** This is expected and doesn't block testing. Agent uses stub client.

---

## 📝 Key Files

| File | Purpose | Location |
|------|---------|----------|
| `reviewer_agent.py` | Phase 5 agent + tests | `reviewer/` |
| `synthesis_agent.py` | Phase 4 agent + tests | `langchain/synthesis_agent/` |
| `rag_agent.py` | Phase 2 agent + tests | `langchain/rag_agent/` |
| `research_agent.py` | Phase 3 agent | `langchain/researcher_agent/` |
| `AGENT_TEST_REPORT.md` | Full test results | `reviewer/` |

---

## 🚀 Next Steps

1. **Immediate:** Add XAI_API_KEY and run Reviewer tests
2. **Short-term:** Set up Postgres for RAG testing
3. **Phase 6:** Integrate all agents into LangGraph orchestration
4. **Production:** Deploy with real databases and APIs

