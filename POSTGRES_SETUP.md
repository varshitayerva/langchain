# MarginGuard Postgres Setup Guide

This guide explains how to set up PostgreSQL for MarginGuard's RAG pipeline.

## Prerequisites

- PostgreSQL 14+ installed
- pgvector extension
- Python 3.9+

## 1. Install PostgreSQL

### Windows
- Download from: https://www.postgresql.org/download/windows/
- During installation, remember your password for the `postgres` user
- Default port: 5432

### macOS
```bash
brew install postgresql
brew services start postgresql
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib postgresql-client
sudo systemctl start postgresql
```

## 2. Install pgvector Extension

pgvector enables vector similarity search for RAG retrieval.

### Windows (in PostgreSQL terminal)
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### macOS/Linux
```bash
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Then in PostgreSQL
CREATE EXTENSION IF NOT EXISTS vector;
```

## 3. Create Database

### Using psql (PostgreSQL CLI)

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE marginGuard;

# Connect to new database
\c marginGuard

# Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

# Verify
\dx  # Should show pgvector in the list
```

## 4. Configure MarginGuard

### Create `.env` file in the `api/` folder

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_NAME=marginGuard

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Optional: LLM API Keys
GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here
```

Replace `your_postgres_password` with the password you set during PostgreSQL installation.

## 5. Install Python Dependencies

```bash
cd api
pip install -r requirements.txt
```

This will install:
- **FastAPI**: REST API framework
- **psycopg2-binary**: PostgreSQL driver
- **sentence-transformers**: For embeddings
- **pgvector**: PostgreSQL vector extension for Python

## 6. Initialize Database Schema

The API automatically creates tables on startup. Just run:

```bash
cd api
python app.py
```

You should see:
```
✓ Database initialized successfully
```

## 7. Test the Connection

### Option A: Using the test script
```bash
cd api
python test_api.py
```

### Option B: Using psql
```bash
# Check tables exist
psql -U postgres -d marginGuard -c "\dt"

# Should show:
#       Schema |   Name   | Type  |  Owner
# ───────────────────────────────────────
#  public | policies | table | postgres
#  public | products | table | postgres
```

## How It Works

### 1. Policy Upload
- When you upload a policy PDF/TXT, it's:
  - Parsed into sections
  - Converted to embeddings using sentence-transformers
  - Stored in the `policies` table with embeddings

```sql
SELECT section_title, content, embedding FROM policies LIMIT 1;
```

### 2. Product Search
- The database pre-seeds with competitor products
- Each product has an embedding for vector search
- When analyzing, the RAG agent finds similar products

```sql
SELECT name, price, features FROM products LIMIT 5;
```

### 3. Vector Similarity Search
- Uses pgvector's `<=>` operator for cosine similarity
- Finds closest policies/products to the query
- Fast using IVFFLAT index

```sql
-- Example: Find policies most similar to a query
SELECT section_title, content 
FROM policies 
ORDER BY embedding <=> 'query_vector'::vector 
LIMIT 2;
```

## Troubleshooting

### Error: "database "marginGuard" does not exist"
```bash
# Reconnect as postgres and create it
psql -U postgres
CREATE DATABASE marginGuard;
\c marginGuard
CREATE EXTENSION IF NOT EXISTS vector;
```

### Error: "extension "vector" does not exist"
- Install pgvector first (see section 2)
- Then enable it in your database

### Error: "could not connect to server"
```bash
# Check PostgreSQL is running
# Windows: Check Services
# macOS: brew services list
# Linux: sudo systemctl status postgresql
```

### Error: "sentence-transformers download timeout"
- The first run downloads a 90MB embedding model
- Make sure you have internet connection
- Model caches locally in `~/.cache/huggingface`

## Data Flow

```
Frontend (React)
    ↓
    POST /upload-policy
    ↓
[app.py]
    ↓
    Parse PDF/TXT → Split into sections
    ↓
[db.py - Database class]
    ↓
    Generate embeddings
    ↓
PostgreSQL (policies table)
    
---

Product Query
    ↓
    GET /analyze?product=X
    ↓
[app.py - run_mock_analysis]
    ↓
Step 1: RAG Retrieval
    ↓
[db.py - search_policies() & search_products()]
    ↓
Vector similarity search in PostgreSQL
    ↓
Return matched policies + products
```

## Next Steps

1. ✅ Start PostgreSQL
2. ✅ Create `marginGuard` database
3. ✅ Create `.env` file
4. ✅ Install dependencies
5. ✅ Run `python app.py`
6. ✅ Upload a policy in the frontend
7. ✅ Run analysis - results now come from your actual policies!

## Performance Tips

### Increase Vector Search Speed
```sql
-- Rebuild indexes if needed
REINDEX INDEX products_embedding_idx;
REINDEX INDEX policies_embedding_idx;
```

### Monitor Queries
```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1 second
SELECT pg_reload_conf();
```

### Check Database Size
```sql
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables 
WHERE schemaname != 'pg_catalog';
```

## References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [PostgreSQL Vector Type](https://github.com/pgvector/pgvector/blob/master/README.md)
- [Sentence Transformers](https://www.sbert.net/)
- [Vector Search Best Practices](https://www.postgresql.org/docs/current/indexes.html)
