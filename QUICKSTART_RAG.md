# Quick Start: RAG Pipeline (5 minutes)

Get MarginGuard running with real policy storage in PostgreSQL.

## Prerequisites
- PostgreSQL installed (see [POSTGRES_SETUP.md](POSTGRES_SETUP.md) if needed)
- Python 3.9+
- Node.js 18+ (for frontend)

## 1. Setup Database (2 min)

```bash
cd api
pip install psycopg2-binary sentence-transformers
python init_db.py
```

Expected output:
```
[HH:MM:SS] OK       Created database 'marginGuard'
[HH:MM:SS] OK       Enabled pgvector extension
[HH:MM:SS] OK       Created 'policies' table
[HH:MM:SS] OK       Created 'products' table
[HH:MM:SS] OK       Seeded 3 sample products
✅ Database initialization complete!
```

## 2. Configure API (1 min)

Create `api/.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=marginGuard
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

Replace `DB_PASSWORD` with your PostgreSQL password.

## 3. Install & Start API (2 min)

```bash
cd api
pip install -r requirements.txt
python app.py
```

Expected:
```
✓ Database initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 4. Test RAG Pipeline

### Option A: Upload Policy & Analyze

```bash
# Terminal 1: API still running

# Terminal 2: Test upload
curl -X POST http://localhost:8000/upload-policy \
  -F "file=@/path/to/your/policy.txt"

# Response should show sections uploaded and stored
```

### Option B: Quick Test Script

```bash
cd api
python test_api.py
```

This will:
1. ✅ Check API health
2. ✅ Upload sample policy
3. ✅ Start analysis
4. ✅ Show real RAG results (from database!)

## 5. Try Frontend (Optional)

```bash
# Terminal 3
cd frontend
npm install
npm run dev
```

Then:
1. Open http://localhost:5173
2. Upload a policy (stores in PostgreSQL)
3. Analyze a product (uses real policies from DB)
4. Check pipeline console for RAG retrieval logs

## What's Happening Under the Hood?

```
Upload Policy
    ↓
Parse into sections
    ↓
Generate embeddings (sentence-transformers)
    ↓
Store in PostgreSQL with vectors
    ↓
Index for fast search

---

Analyze Product
    ↓
RAG Step 1: Vector similarity search
    ↓
Find matching policies from database
    ↓
Return real policy snippets (not mock!)
```

## Verify Database

```bash
# Check if policies stored
psql marginGuard
SELECT COUNT(*) FROM policies;

# Check products
SELECT name, price FROM products LIMIT 3;

# Exit
\q
```

## Troubleshooting

### "database 'marginGuard' does not exist"
```bash
python init_db.py
```

### "pgvector not found"
- macOS: `brew install pgvector`
- See [POSTGRES_SETUP.md](POSTGRES_SETUP.md) section 2

### "sentence-transformers timeout"
- First run downloads 90MB model
- On slower internet, this takes 1-2 minutes
- Model caches locally after first download

### "Cannot connect to database"
```bash
# Check PostgreSQL is running
# Windows: Services → PostgreSQL
# macOS: brew services list
# Linux: sudo systemctl status postgresql
```

## Key Files

| File | Purpose |
|------|---------|
| `api/db.py` | Database layer with vector search |
| `api/config.py` | Configuration (loads from .env) |
| `api/app.py` | API with RAG integration |
| `api/init_db.py` | Database initialization script |

## Next Steps

- Read [RAG_INTEGRATION.md](RAG_INTEGRATION.md) for full details
- Check [POSTGRES_SETUP.md](POSTGRES_SETUP.md) for advanced setup
- Run `python test_api.py` to verify everything works
- Customize embedding model in `api/config.py`

## Performance Expectations

| Operation | Time |
|-----------|------|
| Upload policy | <1 second |
| Analyze product | 8 seconds (4 steps × 2s each) |
| Vector search | <50ms |
| Embedding generation | ~100ms per section (first run downloads model) |

## Success Indicators

✅ Database initialized
✅ API started successfully
✅ Policy uploads show "stored in database"
✅ Analysis results include real policies (not "No policies found")
✅ Test script shows RAG data in results

---

**You're ready!** 🚀 The system now stores your policies in PostgreSQL and retrieves them via vector similarity search.
