# RAG Agent - Quick Start Guide

Get up and running with the RAG Agent in **2 minutes**.

## Prerequisites

✅ Python 3.9+  
✅ PostgreSQL with pgvector  
✅ Groq API key (free: https://console.groq.com)

## Step 1: Configure Environment (1 minute)

```bash
cd rag_agent

# Copy example environment file
cp .env.example .env

# Edit .env and add your Groq API key
# Open .env and replace:
# GROQ_API_KEY=gsk_your_api_key_here
# with your actual API key from https://console.groq.com
```

**Your `.env` file should look like:**
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=fde_langchain

GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=mixtral-8x7b-32768
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Step 2: Install Dependencies (30 seconds)

```bash
pip install -r requirements.txt
```

## Step 3: Setup Database (1 minute)

### Option A: Local PostgreSQL

```bash
# Make sure PostgreSQL is running
psql -U postgres -c "CREATE DATABASE fde_langchain;"
psql -U postgres -d fde_langchain -c "CREATE EXTENSION vector;"

# Then load seed data
python ingestion.py
```

### Option B: Docker (Recommended)

```bash
# Start PostgreSQL with pgvector
docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 ankane/pgvector &

# Wait 3 seconds, then load data
sleep 3
python ingestion.py
```

## Step 4: Verify Database Setup

**Output should show:**
```
[*] Starting ingestion pipeline...
[+] pgvector extension enabled
[+] Tables created: products, policies
[+] Ingested 10 products with embeddings
[+] Ingested policy document with embeddings
[+] Ingestion complete!
```

## Step 5: Test It (30 seconds)

```bash
python rag_agent.py
```

**Expected output:**
```
[TEST] RAG Agent Testing...

Query: wireless earbuds with noise cancellation
[PRODUCTS] Top Results:
  - AirPods Pro ($249.0, similarity: 0.68)
  - Sony WF-1000XM5 ($299.99, similarity: 0.67)
  - Samsung Galaxy Buds2 Pro ($229.99, similarity: 0.63)

[POLICY] Relevant Rules:
  ### Margin Floor Requirements
  All products must maintain a minimum gross margin...

[SUCCESS] RAG Agent test complete!
```

## Step 6: Use It in Your Code

```python
from rag_agent import rag_retrieve

# Simple one-liner
result = rag_retrieve("wireless earbuds under $250")

# Access the data
print("Products found:")
for product in result['product_data']:
    print(f"  - {product['name']}: ${product['price']}")
    print(f"    Similarity: {product['similarity']:.2f}")

print("\nApplicable Policies:")
print(result['policy_snippet'])
```

## Common Queries to Try

```python
# Query 1: Budget earbuds
rag_retrieve("affordable wireless earbuds under 250")

# Query 2: Premium smartwatch
rag_retrieve("premium smartwatch with fitness tracking")

# Query 3: Noise cancelling headphones
rag_retrieve("over-ear headphones with active noise cancellation")

# Query 4: Get pricing rules
rag_retrieve("margin floor price matching policy")
```

## Configuration

If you need to change settings, edit `config.py`:

```python
# Database connection
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_NAME = "fde_langchain"

# LLM (Groq)
GROQ_API_KEY = "gsk_your_key_here"
GROQ_MODEL = "mixtral-8x7b-32768"

# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
```

## Troubleshooting

### PostgreSQL Connection Failed
```bash
# Check if PostgreSQL is running
psql -U postgres -c "\l"

# If not running, start it:
# macOS: brew services start postgresql
# Windows: net start PostgreSQL
# Linux: sudo service postgresql start
```

### pgvector Extension Not Found
```bash
psql -U postgres -d fde_langchain
CREATE EXTENSION vector;
\dx  # List extensions
```

### Port 5432 Already in Use
```bash
# Kill the process using port 5432
# macOS/Linux: lsof -ti:5432 | xargs kill -9
# Windows: netstat -ano | findstr :5432
```

### Module Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## File Structure

```
rag_agent/
├── rag_agent.py      ← Main agent code
├── config.py         ← Configuration (update this)
├── seed_data.py      ← 10 sample products
├── ingestion.py      ← Database setup (run once)
├── __init__.py       ← Package init
└── requirements.txt  ← Dependencies
```

## What Each File Does

| File | Purpose |
|------|---------|
| `rag_agent.py` | Core RAG logic - vector search & retrieval |
| `config.py` | DB credentials, API keys, model names |
| `seed_data.py` | 10 products + pricing policy data |
| `ingestion.py` | Creates tables, loads embeddings (run once) |
| `requirements.txt` | Python package dependencies |

## Architecture

```
User Query
    ↓
rag_retrieve("wireless earbuds")
    ↓
Generate 384-dim embedding using sentence-transformers
    ↓
Search PostgreSQL pgvector using cosine similarity
    ↓
Retrieve top-3 products + policy snippets
    ↓
Return JSON with results
```

## Integration Checklist

- [ ] PostgreSQL running on localhost:5432
- [ ] pgvector extension created
- [ ] Ingestion script ran successfully
- [ ] `rag_agent.py` test passes
- [ ] Can import `rag_retrieve` in your code
- [ ] Queries return relevant products

## Next Steps

1. **Integrate with LangChain** - Add RAG as a tool in your LangChain agent
2. **Add More Products** - Expand `seed_data.py` with your product catalog
3. **Build API Wrapper** - Create FastAPI endpoint to expose RAG agent
4. **Add Filtering** - Filter by price range, category, etc.
5. **Fine-tune Embeddings** - Train custom embedding model on your domain

## Getting Help

1. Check `README.md` for detailed documentation
2. Review `rag_agent.py` source code
3. Run `python rag_agent.py` to see working examples
4. Check config in `config.py`

---

**Questions?** Open an issue or contact the team! 🚀
