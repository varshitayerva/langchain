# RAG Pipeline Integration Guide

## Overview

MarginGuard now includes a full **Retrieval-Augmented Generation (RAG)** pipeline that stores your policies in PostgreSQL and uses vector search to retrieve relevant information during competitive analysis.

## What Changed

### Before (Mock Mode)
```
Upload Policy → Stored in memory → Analysis uses hardcoded mock data
```

### After (RAG Mode)
```
Upload Policy → Stored in PostgreSQL with embeddings → 
Analysis uses real policies via vector similarity search
```

## Architecture

### Database Layer (`api/db.py`)

The `Database` class handles:

1. **Vector Embeddings**
   - Converts text to embeddings using `sentence-transformers`
   - Model: `all-MiniLM-L6-v2` (lightweight, 90MB)
   - Embedding dimension: 384

2. **Policy Storage**
   - Parses uploaded PDFs/TXT into sections
   - Generates embeddings for each section
   - Stores in PostgreSQL `policies` table

3. **Vector Search**
   - Uses pgvector's `<=>` operator for cosine similarity
   - Returns top-K most similar policies
   - Fast lookup with IVFFLAT indexes

### API Endpoints

**POST /upload-policy** (Updated)
```json
Request:
  multipart/form-data with PDF/TXT file

Response:
  {
    "status": "success",
    "sections_uploaded": 3,
    "sections": [
      {
        "title": "Pricing Policy",
        "content": "..."
      }
    ],
    "message": "Policy uploaded successfully (stored in database)"
  }
```

**GET /analyze?product=X** (Updated to use RAG)
```
Step 1: RAG Retrieval
  → Searches stored policies
  → Returns relevant sections
  
Step 2-4: Research, Synthesis, Review (unchanged)
```

**GET /result?id=X** (Returns real RAG data)
```json
{
  "rag_output": {
    "product_data": [...],  // From vector search
    "policy_snippet": "..." // Relevant policies from DB
  },
  "research_results": [...]
}
```

## Setup Instructions

### 1. Install PostgreSQL

See [POSTGRES_SETUP.md](./POSTGRES_SETUP.md) for detailed instructions.

### 2. Quick Database Setup

```bash
cd api
python init_db.py
```

This will:
- ✅ Create `marginGuard` database
- ✅ Enable pgvector extension
- ✅ Create policies & products tables
- ✅ Seed sample products

### 3. Configure `.env`

Create `api/.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=marginGuard
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

Key additions:
- `psycopg2-binary` - PostgreSQL driver
- `sentence-transformers` - Embeddings
- `pgvector` - Vector search

### 5. Start the API

```bash
python app.py
```

Expected output:
```
✓ Database initialized successfully
Uvicorn running on http://0.0.0.0:8000
```

## How It Works

### Upload Policy Flow

```python
# user uploads policy.pdf

# 1. Parse into sections
sections = parse_policy_document(content)
# Result:
# [
#   {"title": "Pricing Policy", "content": "..."},
#   {"title": "Compliance", "content": "..."}
# ]

# 2. Store with embeddings
database.store_policy("policy.pdf", sections)
# Generates embeddings for each section
# Stores in PostgreSQL

# 3. Available for RAG retrieval
```

### Analysis Flow (RAG Enabled)

```python
# user analyzes "AirPods Pro"

# Step 1: RAG Retrieval
products = database.search_products("AirPods Pro", top_k=3)
policies = database.search_policies("AirPods Pro", top_k=2)

# Step 2: Research Agent
# (research competitors)

# Step 3: Synthesis
# (combine insights)

# Step 4: Review & Approval
# (validate against policies from Step 1)
```

## Vector Search Example

### In Python

```python
from db import db

# Search policies
policies = db.search_policies("pricing discount", top_k=2)
# Returns: [
#   {
#     "section": "Pricing Policy",
#     "content": "All pricing must...",
#     "similarity": 0.92
#   }
# ]

# Search products
products = db.search_products("wireless earbuds under 300", top_k=3)
# Returns: [
#   {
#     "id": 1,
#     "name": "AirPods Pro",
#     "price": 249,
#     "similarity": 0.88
#   }
# ]
```

### In SQL (Direct Database Query)

```sql
-- Search for policies matching "margin floor"
SELECT section_title, content
FROM policies
ORDER BY embedding <=> ('margin floor'::text)::vector
LIMIT 2;

-- Search for products similar to "noise cancelling"
SELECT name, category, price
FROM products
ORDER BY embedding <=> ('noise cancelling'::text)::vector
LIMIT 5;
```

## Testing

### Test API with Real Policies

```bash
# 1. Start backend
cd api
python app.py

# 2. Upload a policy (in separate terminal)
curl -X POST http://localhost:8000/upload-policy \
  -F "file=@policy.pdf"

# 3. Analyze product
curl "http://localhost:8000/analyze?product=AirPods%20Pro"

# 4. Check results
curl "http://localhost:8000/result?id=<execution_id>"
```

### Using Test Script

```bash
cd api
python test_api.py
```

The test will:
- ✅ Check API health
- ✅ Upload sample policy
- ✅ Start analysis
- ✅ Poll status
- ✅ Fetch results (with real RAG data!)

## Performance

### Embedding Generation
- First run: ~30 seconds (downloads model)
- Subsequent runs: ~100ms per policy section

### Vector Search
- Typical query: <50ms (with IVFFLAT index)
- Scales to 1M+ policies

### Memory Usage
- Embedding model: ~90MB RAM
- Vector indexes: ~1MB per 10K vectors

## Troubleshooting

### Issue: "database 'marginGuard' does not exist"
```bash
# Run setup script
python init_db.py
```

### Issue: "pgvector extension not found"
See [POSTGRES_SETUP.md](./POSTGRES_SETUP.md) section 2

### Issue: "sentence-transformers download timeout"
- First run downloads 90MB model
- Check internet connection
- Model caches in `~/.cache/huggingface/`

### Issue: Analysis returns "No policies found"
```bash
# Check if policies were stored
curl -X POST http://localhost:8000/upload-policy -F "file=@policy.pdf"
# Verify in database
psql marginGuard -c "SELECT COUNT(*) FROM policies;"
```

## Advanced Configuration

### Use Different Embedding Model

Edit `api/config.py`:
```python
# Faster (33MB, lower quality)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Better quality (438MB)
EMBEDDING_MODEL = "all-mpnet-base-v2"

# Production-grade (429MB)
EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1.5"
```

### Adjust Vector Search Parameters

Edit `api/db.py` search methods:
```python
# Increase results
def search_policies(self, query: str, top_k: int = 5):  # was 2
    ...

# Adjust IVFFLAT index for speed vs quality
# lists = 10  (faster, less accurate)
# lists = 100 (slower, more accurate)
```

### Enable Query Logging

```sql
-- In PostgreSQL
ALTER SYSTEM SET log_min_duration_statement = 100;
SELECT pg_reload_conf();

-- View logs
tail -f /var/log/postgresql/postgresql.log
```

## Data Schema

### Policies Table
```sql
CREATE TABLE policies (
  id SERIAL PRIMARY KEY,
  section_title VARCHAR(255),       -- "Pricing Policy", "Compliance", etc.
  content TEXT,                      -- Full section text
  embedding vector(384),             -- Vector embedding for search
  filename VARCHAR(255),             -- Source file
  upload_time TIMESTAMP              -- When uploaded
);

CREATE INDEX policies_embedding_idx
ON policies USING ivfflat (embedding vector_cosine_ops);
```

### Products Table
```sql
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),                 -- "AirPods Pro"
  category VARCHAR(100),             -- "wireless earbuds"
  price DECIMAL(10, 2),              -- 249.00
  cost DECIMAL(10, 2),               -- 100.00
  margin_floor INTEGER,              -- 30
  features TEXT,                     -- Feature description
  competitor VARCHAR(100),           -- Company name
  embedding vector(384),             -- Vector embedding
  created_at TIMESTAMP               -- Created time
);

CREATE INDEX products_embedding_idx
ON products USING ivfflat (embedding vector_cosine_ops);
```

## Integration with Frontend

The frontend (`frontend/src/components/ProductQuerySection.tsx`) already works with the RAG-enabled API:

```typescript
// No changes needed! The API contract remains the same:

// 1. Upload policy (stores in DB)
await axios.post('/upload-policy', formData)

// 2. Start analysis (uses RAG)
await axios.get('/analyze', { params: { product: query } })

// 3. Get results (includes real RAG data)
await axios.get('/result', { params: { id: executionId } })
```

The RAG retrieval happens transparently in the backend.

## Next Steps

1. ✅ Follow POSTGRES_SETUP.md to install PostgreSQL
2. ✅ Run `python init_db.py` to create database
3. ✅ Create `api/.env` with your credentials
4. ✅ Start the API: `python app.py`
5. ✅ Start the frontend: `npm run dev`
6. ✅ Upload a policy - it's now stored in PostgreSQL!
7. ✅ Analyze products - results use your real policies

## Questions?

- Check the logs: `python app.py` shows database initialization
- Run tests: `python test_api.py`
- Debug SQL directly: `psql marginGuard`
