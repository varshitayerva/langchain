# MarginGuard - START HERE 🚀

Welcome to MarginGuard! This is your entry point to the complete application.

## What is MarginGuard?

MarginGuard is a competitive analysis engine that:
- ✅ Uploads and parses company policies
- ✅ Analyzes competitor pricing and features
- ✅ Validates margin compliance
- ✅ Generates strategic recommendations
- ✅ Provides real-time execution monitoring

## 5-Minute Quick Start

### Terminal 1: Start Backend
```bash
cd api
pip install -r requirements.txt
python main.py
```
✅ Backend ready at http://localhost:8000

### Terminal 2: Start Frontend
```bash
cd frontend
npm install
npm start
```
✅ Frontend ready at http://localhost:3000

### Use the App
1. Open http://localhost:3000 in your browser
2. Upload any PDF as your policy
3. Enter "AirPods Pro" as the product
4. Click "Analyze Product"
5. Watch the pipeline console execute
6. Review results in 4 tabs

**Done!** You're now running MarginGuard locally.

---

## Documentation Index

### 📋 Quick References (Read These First)
1. **[SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md)** - Step-by-step setup verification
2. **[GETTING_STARTED.md](./GETTING_STARTED.md)** - 5-minute overview

### 📚 Detailed Guides
3. **[BUILD_SUMMARY.md](./BUILD_SUMMARY.md)** - What was built and where
4. **[FRONTEND_SETUP.md](./FRONTEND_SETUP.md)** - Frontend details and features
5. **[BACKEND_SETUP.md](./BACKEND_SETUP.md)** - Backend API endpoints
6. **[COMPLETE_BUILD_GUIDE.md](./COMPLETE_BUILD_GUIDE.md)** - Comprehensive reference

### 🔧 Project Docs
7. **[README.md](./README.md)** - Original project documentation
8. **[QUICKSTART.md](./QUICKSTART.md)** - Project quick start
9. **[ORCHESTRATION_GUIDE.md](./ORCHESTRATION_GUIDE.md)** - Multi-agent orchestration

### 📡 API Documentation
- **Interactive Docs**: http://localhost:8000/docs (when backend running)
- **ReDoc**: http://localhost:8000/redoc

---

## Project Structure

```
project-6/
│
├── frontend/                    # React dashboard (YOUR BUILD ✅)
│   ├── src/components/         # 15 React components
│   ├── package.json            # npm dependencies
│   └── tsconfig.json           # TypeScript config
│
├── api/                         # FastAPI backend (ALREADY EXISTS ✅)
│   ├── main.py                 # Complete server
│   └── requirements.txt         # Python dependencies
│
├── orchestration/              # Multi-agent pipeline
├── rag_agent/                  # RAG retrieval
├── researcher_agent/           # Research analysis
├── reviewer/                   # Policy validation
│
└── [Documentation files]
```

---

## What You Get

### Frontend (React + TypeScript)
- **Left Panel (35%)**
  - Policy document upload with drag-drop
  - Product query with autocomplete
  - Real-time pipeline execution console

- **Main Viewport (65%)**
  - **Overview Tab**: Key metrics & charts
  - **Competitors Tab**: Sortable data table
  - **Charts Tab**: Visualizations & compliance matrix
  - **Report Tab**: Executive summary & exports

### Backend (FastAPI)
- REST API with 5 main endpoints
- Async processing with background tasks
- CORS enabled for frontend
- Interactive API documentation

---

## Key Features

✨ **Upload & Parse**: Drag-drop PDF policies
📊 **Real-time Monitoring**: Watch 4-step pipeline execute
📈 **Interactive Charts**: Price gaps, margins, feature parity
🔍 **Competitor Analysis**: Sortable table with details
📋 **Executive Reports**: Formatted summaries & exports
🎨 **Purple Theme**: Beautiful gradient UI
📱 **Responsive**: Works on desktop, tablet, mobile
⚡ **Fast**: Async processing, in-memory caching

---

## Technology Stack

### Frontend
```
React 19 + TypeScript
├── Chart.js (visualizations)
├── Axios (HTTP)
└── CSS3 (styling)
```

### Backend
```
FastAPI (Python)
├── Uvicorn (server)
├── Pydantic (validation)
└── Multi-agent orchestration
```

---

## Common Tasks

### I just downloaded this. What do I do?
→ Follow [SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md)

### I want to understand the structure
→ Read [BUILD_SUMMARY.md](./BUILD_SUMMARY.md)

### I want frontend details
→ Read [FRONTEND_SETUP.md](./FRONTEND_SETUP.md)

### I want backend details
→ Read [BACKEND_SETUP.md](./BACKEND_SETUP.md)

### I want everything
→ Read [COMPLETE_BUILD_GUIDE.md](./COMPLETE_BUILD_GUIDE.md)

### I'm stuck on something
→ Check troubleshooting in [SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md)

### I want to customize it
→ Sections in [COMPLETE_BUILD_GUIDE.md](./COMPLETE_BUILD_GUIDE.md) cover this

### I want to deploy it
→ Section in [COMPLETE_BUILD_GUIDE.md](./COMPLETE_BUILD_GUIDE.md)

---

## Prerequisites

Before starting, ensure you have:

```bash
# Check Python
python --version      # Should be 3.9+

# Check Node
node --version       # Should be 14+
npm --version        # Should be 6+

# Create .env file in project root
echo "ANTHROPIC_API_KEY=your_key" > .env
```

---

## Quick Start Verification

After running both servers, test in browser console:

```javascript
// Should return 200 and healthy status
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log)
```

---

## File Locations

| What | Where |
|------|-------|
| Frontend | `frontend/src/` |
| Backend | `api/main.py` |
| Styles | `frontend/src/**/*.css` |
| API Endpoints | `api/main.py` |
| Config | `.env` (create this) |

---

## Important Notes

⚠️ **Backend is in `api/`, not `backend/`**
- Don't use the empty `backend/` folder
- All backend code is in `api/main.py`
- Frontend points to `http://localhost:8000`

✅ **No code duplication**
- Single source of truth for each component
- Existing orchestration modules reused
- Clean separation of concerns

🎯 **Ready to use immediately**
- No additional setup needed
- Just install and run
- API docs available at `/docs`

---

## What's Included

### ✅ Frontend (Complete)
- 10 React components
- 10 CSS files
- Full TypeScript support
- All specified features

### ✅ Backend (Existing)
- FastAPI server in `api/main.py`
- Multi-agent orchestration
- All required endpoints
- Interactive documentation

### ✅ Documentation (Complete)
- Setup guides
- API documentation
- Component reference
- Troubleshooting guide

---

## Next Steps

1. **[SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md)** (10 minutes)
   Follow the step-by-step checklist

2. **[GETTING_STARTED.md](./GETTING_STARTED.md)** (5 minutes)
   Understand the basic flow

3. **[FRONTEND_SETUP.md](./FRONTEND_SETUP.md)** or **[BACKEND_SETUP.md](./BACKEND_SETUP.md)** (15 minutes)
   Deep dive into your area of interest

4. **Start coding!** 🎉
   Customize colors, add features, deploy

---

## Feature Checklist

- ✅ React dashboard with 35/65 layout
- ✅ Policy PDF upload with parsing
- ✅ Product query with autocomplete
- ✅ Real-time pipeline console
- ✅ Overview tab with metrics & charts
- ✅ Competitors tab with sortable table
- ✅ Charts tab with 4 visualizations
- ✅ Report tab with executive summary
- ✅ Export to PDF/clipboard/email
- ✅ Loading states & spinners
- ✅ Responsive design
- ✅ Purple gradient theme
- ✅ FastAPI backend with 5 endpoints
- ✅ Async processing
- ✅ CORS enabled
- ✅ API documentation
- ✅ Full integration

---

## Support

### Docs Quick Links
- **Setup**: [SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md)
- **Getting Started**: [GETTING_STARTED.md](./GETTING_STARTED.md)
- **Build Summary**: [BUILD_SUMMARY.md](./BUILD_SUMMARY.md)
- **Frontend**: [FRONTEND_SETUP.md](./FRONTEND_SETUP.md)
- **Backend**: [BACKEND_SETUP.md](./BACKEND_SETUP.md)
- **Complete**: [COMPLETE_BUILD_GUIDE.md](./COMPLETE_BUILD_GUIDE.md)

### Online Resources
- API Docs: http://localhost:8000/docs
- React: https://react.dev
- FastAPI: https://fastapi.tiangolo.com

### If Stuck
1. Check [SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md) troubleshooting
2. Review relevant documentation above
3. Check http://localhost:8000/docs for API details
4. Review browser console for errors (F12)
5. Check backend terminal for server errors

---

## Success! 🎉

You now have a fully functional competitive analysis platform running locally.

**What's Next?**
- Customize the theme
- Add new metrics
- Integrate with your database
- Deploy to production
- Build additional features

**Happy analyzing!** 📊

---

## Document Guide

```
START_HERE.md              ← You are here
│
├─ SETUP_CHECKLIST.md      ← Follow this first (10 min)
├─ GETTING_STARTED.md      ← Then this (5 min)
│
├─ BUILD_SUMMARY.md        ← Understand structure
├─ FRONTEND_SETUP.md       ← Frontend reference
├─ BACKEND_SETUP.md        ← Backend reference
├─ COMPLETE_BUILD_GUIDE.md ← Everything in detail
│
└─ Other docs...
```

---

**Welcome to MarginGuard! Let's get started.** 🚀
