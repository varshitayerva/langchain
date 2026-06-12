# MarginGuard - Competitive Analysis Engine

A comprehensive AI-powered platform for analyzing competitor pricing, features, and policy compliance in real-time. Built with React frontend and FastAPI backend using multi-agent orchestration.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [System Flow](#system-flow)
- [Agents](#agents)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 14+
- npm 6+

### Setup & Run

**Terminal 1: Backend**
```bash
cd api
pip install -r requirements.txt
python app.py
```
✅ Backend runs on: `http://localhost:8000`

**Terminal 2: Frontend**
```bash
cd frontend
npm install
npm start
```
✅ Frontend runs on: `http://localhost:3000`

### Test
```bash
python test_api.py
```

---

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (3000)                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Left Panel (35%)        │  Main Viewport (65%)      │   │
│  │  - Policy Upload         │  - Overview Tab           │   │
│  │  - Product Query         │  - Competitors Tab        │   │
│  │  - Pipeline Console      │  - Charts Tab             │   │
│  │                          │  - Report Tab             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                    HTTP (Axios Requests)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (8000)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Layer                                           │   │
│  │  - /upload-policy    - Policy caching               │   │
│  │  - /analyze          - Start analysis pipeline      │   │
│  │  - /status           - Real-time progress polling   │   │
│  │  - /result           - Fetch final results          │   │
│  │  - /health           - Health checks                │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Analysis Pipeline (Background Tasks)                │   │
│  │  Step 1 → Step 2 → Step 3 → Step 4                  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Execution State Management                          │   │
│  │  - In-memory caching                                 │   │
│  │  - Real-time status updates                          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Structure

#### Frontend Components
```
frontend/src/
├── App.tsx
│   └── Main application coordinator
│
├── components/
│   ├── LeftPanel.tsx (35% width)
│   │   ├── PolicyUploadSection    - PDF upload & management
│   │   ├── ProductQuerySection    - Product input & autocomplete
│   │   └── PipelineConsole        - Real-time execution logs
│   │
│   └── MainViewport.tsx (65% width)
│       ├── Tab Navigation
│       └── Tab Content
│           ├── OverviewTab        - Metrics & summary
│           ├── CompetitorsTab     - Sortable table
│           ├── ChartsTab          - Visualizations
│           └── ReportTab          - Executive summary
```

#### Backend Structure
```
api/
├── app.py                 - Main FastAPI application
├── main.py               - Original implementation (deprecated)
├── requirements.txt      - Python dependencies
└── README.md            - API documentation
```

---

## 🔄 System Flow

### 1. User Initiates Analysis

```
User Interface
      │
      ├─ Uploads PDF Policy
      │        │
      │        ▼
      │  POST /upload-policy
      │        │
      │        ▼
      │  Policy Cached in Memory
      │        │
      └─ Enters Product Name
           │
           ▼
      GET /analyze?product=X
           │
           ▼
      Returns execution_id
           │
           ▼
   Frontend Stores ID
```

### 2. Real-Time Status Polling

```
Frontend (Every 1 second)
      │
      ├─ GET /status?id=execution_id
      │        │
      │        ▼
      │  Backend Returns:
      │  {
      │    status: "running",
      │    step: 2,
      │    message: "Analyzed 5 competitors",
      │    progress: 50.0
      │  }
      │        │
      │        ▼
      │  Frontend Updates:
      │  - Console logs
      │  - Progress indicator
      │  - Step counter
      │        │
      └─ Repeat until status = "completed"
```

### 3. Analysis Pipeline Execution

```
Backend (Background Task)
      │
      ├─ Step 1: RAG Retrieval (2 sec)
      │   - Load product data
      │   - Match policy constraints
      │   - Return candidates
      │
      ├─ Step 2: Research Agent (3 sec)
      │   - Analyze competitors
      │   - Extract features
      │   - Calculate parity
      │
      ├─ Step 3: Synthesis (2 sec)
      │   - Combine insights
      │   - Generate summary
      │   - Calculate metrics
      │
      └─ Step 4: Review & Approval (2 sec)
          - Validate compliance
          - Generate report
          - Mark as complete
```

### 4. Results Retrieval & Display

```
Frontend Polling Detects Completion
      │
      ├─ GET /result?id=execution_id
      │        │
      │        ▼
      │  Returns Full Result Object
      │  {
      │    product_query: "iPhone 15 Pro",
      │    rag_output: {...},
      │    research_results: [...]
      │  }
      │        │
      │        ▼
      │  Frontend Distributes Data
      │  ├─ Overview Tab: Metrics & Chart
      │  ├─ Competitors Tab: Table Data
      │  ├─ Charts Tab: Visualizations
      │  └─ Report Tab: Summary
      │        │
      │        ▼
      │  User Views Results
```

---

## 🤖 Agents

### Architecture Overview

The system uses a multi-stage analysis pipeline with specialized agents:

```
Product Query
      │
      ▼
┌─────────────────────┐
│  RAG Agent          │
│  (Retrieval)        │
└─────────────────────┘
      │
      │ Product Data
      ▼
┌─────────────────────┐
│  Research Agent     │
│  (Analysis)         │
└─────────────────────┘
      │
      │ Competitor Data
      ▼
┌─────────────────────┐
│  Synthesis          │
│  (Combination)      │
└─────────────────────┘
      │
      │ Insights
      ▼
┌─────────────────────┐
│  Reviewer Agent     │
│  (Validation)       │
└─────────────────────┘
      │
      │ Final Report
      ▼
   Results
```

### 1. RAG Retrieval Agent

**Location**: `/rag_agent/`

**Purpose**: Retrieve and filter product data based on policy constraints

**Responsibilities**:
- Access product knowledge base
- Filter by policy requirements
- Extract relevant product information
- Return candidate products

**Input**:
```python
{
    "product_query": "iPhone 15 Pro",
    "policy_constraints": {
        "margin_floor": 25,
        "feature_parity_threshold": 70
    }
}
```

**Output**:
```python
{
    "product_data": [
        {
            "id": "prod_1",
            "name": "iPhone 15 Pro",
            "category": "Smartphones",
            "price": 999,
            "cost": 400,
            "margin_floor": 25,
            "features": ["A17 Pro", "Camera", "Design"],
            "competitor": "Apple"
        }
    ],
    "policy_snippet": "Margin floor must be 25%..."
}
```

**Key Files**:
- `rag_agent/agent.py` - Main agent logic
- `rag_agent/retrieval.py` - Vector search
- `rag_agent/embeddings.py` - Embedding generation

**Status**: ✅ Functional (Mock data in testing)

**Features**:
- Vector similarity search
- Policy-aware filtering
- Product knowledge base
- Semantic matching

---

### 2. Research Agent

**Location**: `/researcher_agent/`

**Purpose**: Analyze competitors and calculate competitive metrics

**Responsibilities**:
- Identify competitor products
- Extract pricing information
- Calculate feature parity
- Determine price gaps
- Assess margin feasibility
- Research market trends

**Input**:
```python
{
    "product": "iPhone 15 Pro",
    "rag_output": {
        "product_data": [...],
        "policy_snippet": "..."
    }
}
```

**Output**:
```python
{
    "competitors": [
        {
            "competitor_name": "Samsung Galaxy S24",
            "price_normalized": 899,
            "feature_parity": 85,  # %
            "price_gap": -100,
            "margin_feasible": true,
            "source": "https://..."
        }
    ],
    "research_summary": "Analysis found 5 competitors..."
}
```

**Key Files**:
- `researcher_agent/agent.py` - Main agent logic
- `researcher_agent/analyzer.py` - Analysis engine
- `researcher_agent/competitor_research.py` - Research methods

**Status**: ✅ Integrated

**Key Metrics**:
- **Feature Parity**: % of competitor features matched
- **Price Gap**: Difference from your product price
- **Margin Feasible**: Whether margin floor is maintainable

---

### 3. Synthesis Agent

**Location**: `/orchestration/`

**Purpose**: Combine insights from RAG and Research for strategic recommendations

**Responsibilities**:
- Aggregate competitor data
- Calculate summary statistics
- Identify market trends
- Generate strategic insights
- Produce recommendations

**Input**:
```python
{
    "product_query": "iPhone 15 Pro",
    "rag_output": {...},
    "research_output": {...}
}
```

**Output**:
```python
{
    "market_analysis": {
        "total_competitors": 5,
        "average_price": 379,
        "price_range": [279, 399],
        "avg_feature_parity": 75,
        "margin_feasible_count": 5
    },
    "insights": [
        "Market is competitive with 5 players",
        "Average price gap is $50",
        "Feature parity critical for positioning"
    ],
    "recommendations": [
        "Consider price matching for Sony",
        "Improve feature gaps vs Bose"
    ]
}
```

**Key Files**:
- `orchestration/orchestrator.py` - Main orchestration
- `orchestration/langgraph_orchestrator.py` - LangGraph integration

**Status**: ✅ Functional

**Features**:
- Multi-agent coordination
- Insight generation
- Recommendation engine
- Market trend analysis

---

### 4. Reviewer Agent

**Location**: `/reviewer/`

**Purpose**: Validate analysis against policy and generate final approval

**Responsibilities**:
- Validate against company policy
- Check margin compliance
- Verify feature requirements
- Generate approval decision
- Create final report
- Provide compliance summary

**Input**:
```python
{
    "synthesis_output": {...},
    "policy_constraints": {...}
}
```

**Output**:
```python
{
    "approval_status": "APPROVED",
    "compliance_checks": {
        "margin_floor": true,
        "feature_parity": true,
        "policy_adherence": true
    },
    "recommendations": [
        "Approved for price matching with Sony",
        "Monitor Bose quarterly"
    ],
    "final_report": "Executive summary markdown..."
}
```

**Key Files**:
- `reviewer/agent.py` - Main agent logic
- `reviewer/compliance_checker.py` - Compliance validation
- `reviewer/report_generator.py` - Report generation

**Status**: ✅ Integrated

**Features**:
- Policy compliance checking
- Margin validation
- Feature requirement verification
- Report generation

---

## 📡 API Endpoints

### 1. Upload Policy

**Endpoint**: `POST /upload-policy`

**Purpose**: Upload and parse company policy document

**Request**:
```bash
curl -X POST http://localhost:8000/upload-policy \
  -F "file=@policy.pdf"
```

**Response**:
```json
{
  "status": "success",
  "sections_uploaded": 3,
  "sections": [
    {
      "title": "Pricing Policy",
      "content": "All pricing must maintain 25% margin floor..."
    }
  ],
  "message": "Policy uploaded successfully with 3 sections"
}
```

---

### 2. Start Analysis

**Endpoint**: `GET /analyze?product=<product_name>`

**Purpose**: Initiate competitive analysis pipeline

**Request**:
```bash
curl "http://localhost:8000/analyze?product=iPhone%2015%20Pro"
```

**Response**:
```json
{
  "execution_id": "ae846418-546b-4e9c-afb1-a3695b63a5ea",
  "status": "started",
  "message": "Analysis started for iPhone 15 Pro"
}
```

---

### 3. Check Status

**Endpoint**: `GET /status?id=<execution_id>`

**Purpose**: Poll real-time analysis progress

**Request**:
```bash
curl "http://localhost:8000/status?id=ae846418-546b-4e9c-afb1-a3695b63a5ea"
```

**Response**:
```json
{
  "status": "running",
  "step": 2,
  "message": "Analyzed 5 competitors",
  "progress": 50.0
}
```

**Step Progression**:
- **Step 1**: RAG Retrieval (Product data retrieval)
- **Step 2**: Research Agent (Competitor analysis)
- **Step 3**: Synthesis (Insight combination)
- **Step 4**: Review & Approval (Final validation)

---

### 4. Get Results

**Endpoint**: `GET /result?id=<execution_id>`

**Purpose**: Retrieve completed analysis results

**Request**:
```bash
curl "http://localhost:8000/result?id=ae846418-546b-4e9c-afb1-a3695b63a5ea"
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "product_query": "iPhone 15 Pro",
    "rag_output": {
      "product_data": [...],
      "policy_snippet": "..."
    },
    "research_results": [
      {
        "competitor_name": "Samsung Galaxy S24",
        "price_normalized": 899,
        "feature_parity": 85,
        "price_gap": -100,
        "margin_feasible": true,
        "source": "https://..."
      }
    ]
  }
}
```

---

### 5. Health Check

**Endpoint**: `GET /health`

**Purpose**: Verify API health and status

**Request**:
```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-06-12T15:41:22.123456",
  "active_executions": 1
}
```

---

## 📁 Project Structure

```
project-6/
│
├── frontend/                    # React Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── LeftPanel.tsx             # 35% sidebar
│   │   │   ├── PolicyUploadSection.tsx   # PDF upload
│   │   │   ├── ProductQuerySection.tsx   # Product input
│   │   │   ├── PipelineConsole.tsx       # Execution logs
│   │   │   ├── MainViewport.tsx          # 65% main area
│   │   │   └── tabs/
│   │   │       ├── OverviewTab.tsx
│   │   │       ├── CompetitorsTab.tsx
│   │   │       ├── ChartsTab.tsx
│   │   │       └── ReportTab.tsx
│   │   ├── App.tsx
│   │   └── App.css
│   ├── package.json
│   └── tsconfig.json
│
├── api/                         # FastAPI Backend
│   ├── app.py                   # Main API (use this!)
│   ├── main.py                  # Original (deprecated)
│   ├── requirements.txt
│   └── README.md
│
├── orchestration/               # Multi-Agent Orchestration
│   ├── orchestrator.py
│   ├── langgraph_orchestrator.py
│   └── README.md
│
├── rag_agent/                   # RAG Retrieval Agent
│   ├── agent.py
│   ├── embeddings.py
│   ├── retrieval.py
│   └── README.md
│
├── researcher_agent/            # Research Analysis Agent
│   ├── agent.py
│   ├── analyzer.py
│   ├── competitor_research.py
│   └── README.md
│
├── reviewer/                    # Review & Approval Agent
│   ├── agent.py
│   ├── compliance_checker.py
│   ├── report_generator.py
│   └── README.md
│
├── START_HERE.md               # Entry point
├── QUICK_TEST.md               # Testing guide
├── test_api.py                 # Automated tests
└── README.md                   # This file
```

---

## 🛠️ Technology Stack

### Frontend
| Technology | Purpose |
|-----------|---------|
| React 19 | UI Framework |
| TypeScript | Type Safety |
| Chart.js | Data Visualization |
| Axios | HTTP Client |
| CSS3 | Styling |

### Backend
| Technology | Purpose |
|-----------|---------|
| FastAPI | Web Framework |
| Python 3.9+ | Runtime |
| Uvicorn | ASGI Server |
| Pydantic | Data Validation |
| AsyncIO | Async Processing |

### Architecture Patterns
| Pattern | Usage |
|---------|-------|
| Multi-Agent | Specialized processing steps |
| Pipeline | Sequential analysis flow |
| State Management | In-memory execution tracking |
| Background Tasks | Async analysis execution |
| Real-time Polling | Frontend status updates |

---

## 📊 Data Flow Example

### Complete User Journey

```
1. User uploads "company_policy.pdf"
   └─ POST /upload-policy
      └─ Returns: 3 policy sections cached

2. User enters "iPhone 15 Pro"
   └─ GET /analyze?product=iPhone%2015%20Pro
      └─ Returns: execution_id (ae846418-...)

3. Frontend polls /status every 1 second
   └─ Step 1/4: RAG Retrieval
      - Retrieved 3 products from knowledge base
   
   └─ Step 2/4: Research Agent
      - Analyzed 5 competitors
   
   └─ Step 3/4: Synthesis
      - Generated recommendations
   
   └─ Step 4/4: Review & Approval
      - Analysis complete

4. Frontend fetches /result?id=execution_id
   └─ Returns full result object with:
      - Product query
      - RAG output (product data)
      - Research results (competitors)

5. Frontend displays results across 4 tabs:
   └─ Overview: Metrics & chart
   └─ Competitors: Sortable table
   └─ Charts: 4 visualizations
   └─ Report: Executive summary
```

---

## 🎯 Key Features

### Frontend
- ✅ 35/65 responsive layout
- ✅ Policy PDF upload with drag-drop
- ✅ Real-time pipeline console
- ✅ 4-tab analysis interface
- ✅ Interactive charts & tables
- ✅ Export functionality
- ✅ Product autocomplete

### Backend
- ✅ Policy caching
- ✅ Async analysis pipeline
- ✅ Real-time status updates
- ✅ Multi-agent orchestration
- ✅ Mock data for testing
- ✅ CORS enabled
- ✅ API documentation

### Analysis
- ✅ 4-step pipeline
- ✅ Competitor research
- ✅ Feature parity analysis
- ✅ Margin compliance checking
- ✅ Policy validation
- ✅ Strategic recommendations

---

## 📈 Performance

| Metric | Expected |
|--------|----------|
| App Load | <5 seconds |
| Policy Upload | <2 seconds |
| Analysis Duration | 8-10 seconds |
| Chart Rendering | <2 seconds |
| Status Update Latency | <100ms |

---

## 🔐 Security

- ✅ CORS enabled for development
- ✅ Input validation on all endpoints
- ✅ Policy data cached in memory
- ✅ No sensitive data exposure
- ⚠️ Production: Add authentication, HTTPS, rate limiting

---

## 📚 Additional Resources

- **API Docs**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc
- **Frontend Setup**: See `START_HERE.md`
- **Testing Guide**: See `QUICK_TEST.md`
- **Test Script**: Run `python test_api.py`

---

## 🎉 Getting Started

1. Read `START_HERE.md` (2 minutes)
2. Read `QUICK_TEST.md` (3 minutes)
3. Start both servers (as shown in Quick Start)
4. Open http://localhost:3000
5. Upload a PDF policy
6. Enter product name (e.g., "iPhone 15 Pro")
7. Click "Analyze Product"
8. View results in tabs

---

## 📝 Notes

- Mock data is used for testing - integrate real agents for production
- Analysis timing is simulated - actual timing depends on data size
- Results are stored in-memory - add database for persistence
- CORS allows all origins - restrict in production

---

**Built with ❤️ for competitive analysis excellence**

## Project Structure

```
rag_agent/
├── __init__.py           # Package initialization
├── rag_agent.py          # Core RAG logic
├── config.py             # Configuration (DB, API keys)
├── seed_data.py          # Product & policy data
├── ingestion.py          # Setup & data loading
└── requirements.txt      # Dependencies
```

## How It Works

### 1. **Vector Embedding**
- Queries and documents are converted to 384-dim embeddings
- Uses `sentence-transformers` (all-MiniLM-L6-v2)

### 2. **Similarity Search**
- Searches PostgreSQL pgvector for closest matches
- Uses cosine similarity with IVF indexing

### 3. **Result Retrieval**
- Returns top-K products ranked by relevance
- Retrieves related policy snippets

### Example Flow

```
User Query: "wireless earbuds under $250"
     ↓
Generate Embedding (384-dim vector)
     ↓
Search pgvector Index
     ↓
Return Top 3 Products + Policy Rules
     ↓
{
  "product_data": [
    {"name": "AirPods Pro", "price": 249.0, "similarity": 0.68},
    {"name": "Sony WF-1000XM5", "price": 299.99, "similarity": 0.67},
    ...
  ],
  "policy_snippet": "..."
}
```

## Configuration

Edit `config.py` to customize:

```python
# Database
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_NAME = "fde_langchain"

# LLM
GROQ_API_KEY = "your_api_key"
GROQ_MODEL = "mixtral-8x7b-32768"

# Embeddings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
```

## Database Setup

### Create PostgreSQL Database
```bash
psql -U postgres -c "CREATE DATABASE fde_langchain;"
```

### Enable pgvector Extension
```bash
psql -U postgres -d fde_langchain -c "CREATE EXTENSION vector;"
```

### Alternative: Use Docker
```bash
docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 ankane/pgvector
```

## Seed Data

Comes with 10 pre-loaded products:

**Wireless Earbuds:**
- AirPods Pro ($249)
- Sony WF-1000XM5 ($299.99)
- Samsung Galaxy Buds2 Pro ($229.99)

**Smartwatches:**
- Apple Watch Series 9 ($399)
- Samsung Galaxy Watch 6 ($299.99)
- Garmin Epix Gen 2 ($499.99)

**Over-Ear Headphones:**
- Sony WH-1000XM5 ($399.99)
- Bose QuietComfort 45 ($379.95)
- Anker Soundcore Space Q45 ($99.99)

**Tracking Devices:**
- Apple AirTag ($29)

Plus comprehensive pricing policies with margin floors, price matching rules, and competitive response timelines.

## API Reference

### `rag_retrieve(query: str, top_k: int = 3) -> dict`

Retrieve products and policies for a query.

**Parameters:**
- `query` (str): Natural language product query
- `top_k` (int): Number of products to return (default: 3)

**Returns:**
```python
{
    "query": "wireless earbuds",
    "product_data": [
        {
            "id": 1,
            "name": "Sony WF-1000XM5",
            "category": "wireless earbuds",
            "price": 299.99,
            "cost": 120.0,
            "margin_floor": 32,
            "features": "...",
            "competitor": "Sony",
            "similarity": 0.69
        },
        ...
    ],
    "policy_snippet": "..."
}
```

### `RAGAgent` Class

For more control:

```python
from rag_agent import RAGAgent

agent = RAGAgent()
result = agent.retrieve("your query", top_k=5)
```

## Performance

- **Query Latency:** ~500ms (embedding + vector search)
- **Throughput:** 100+ queries/sec
- **Vector Search:** Sub-millisecond with IVF indexes

## Testing

Run the included tests:

```bash
python rag_agent.py
```

Tests 3 sample queries and displays:
- Relevant products with similarity scores
- Retrieved policy snippets
- Execution time

## Integration with LangChain

Use in your LangChain pipeline:

```python
from rag_agent import RAGAgent
from langchain.tools import Tool

rag = RAGAgent()

tool = Tool(
    name="product_search",
    func=lambda q: rag.retrieve(q),
    description="Search for products by query"
)

# Add to your LangChain agent
```

## Troubleshooting

### "Connection refused" on port 5432
```bash
# Start PostgreSQL
# Or use Docker:
docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 ankane/pgvector
```

### "pgvector extension not found"
```bash
psql -U postgres -d fde_langchain
CREATE EXTENSION vector;
```

### "Module not found"
```bash
pip install -r requirements.txt
```

### Slow queries
- Rebuild indexes: `REINDEX TABLE products;`
- Check database stats: `ANALYZE;`

## Future Enhancements

- [ ] Add more seed data
- [ ] Multi-language support
- [ ] Custom embedding models
- [ ] Caching layer
- [ ] Real-time index updates
- [ ] Web API wrapper
- [ ] Advanced filtering (price, category)

## Contributing

1. Create a feature branch
2. Add tests for new features
3. Submit a pull request

## License

MIT License

## Support

For issues or questions, open a GitHub issue or contact the team.

---

**Built for product intelligence and competitive analysis** 🚀
