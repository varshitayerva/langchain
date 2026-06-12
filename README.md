# MarginGuard - Multi-Agent Margin Vulnerability Detection Pipeline

## Project Overview
MarginGuard is a multi-agent LLM pipeline that detects margin vulnerabilities and feasibility constraints in near-real-time using:
- **Phase 2**: RAG Agent (internal data retrieval)
- **Phase 3**: Research Agent (competitor analysis)
- **Phase 4**: Synthesis Agent (report generation with Qwen-14B)
- **Phase 4+**: Graph Generator (visualization/charts)
- **Phase 5**: Reviewer Agent (validation with feedback loop)
- **Phase 6**: LangGraph Integration (orchestration)

---

## Setup Instructions

### 1. Install Dependencies
```bash
pip install python-dotenv requests transformers torch openai
```

### 2. Get Hugging Face Token
1. Go to https://huggingface.co/settings/tokens
2. Create a new FREE token (30,000 free inferences/month)
3. Copy the token

### 3. Configure Environment
Edit `.env` file and paste your token:
```bash
# .env
HF_TOKEN=hf_your_token_here
```

**IMPORTANT:** Never commit `.env` to git (it's in `.gitignore`)

---

## Project Structure
```
chall4/
├── synthesis_agent.py      ← Phase 4: Report generation with Qwen-14B
├── graph_generator.py      ← Phase 4+: Chart/graph generation for dashboard
├── test_quick.py           ← Quick test with hardcoded data
├── .env                    ← Your HF token (DO NOT COMMIT)
├── .gitignore             ← Git ignore rules
├── REPORT_OUTPUT_FORMAT.md ← Example report output structure
├── WHAT_IT_DOES.md        ← Full documentation for Github
└── README.md              ← This file
```

---

## Phase 4: Synthesis Agent

### What It Does
1. Takes product data (from RAG) + competitor data (from research)
2. Builds a detailed prompt for Qwen-14B
3. Sends to Hugging Face API via your free token
4. Returns a professional markdown report with analysis
5. Appends DATA SUMMARY MATRIX with structured pricing metrics

### Running Phase 4
```bash
python test_quick.py
```

### Example Output
See `REPORT_OUTPUT_FORMAT.md` for comprehensive report structure including:
- Executive Summary with market pressure analysis
- Market Position Analysis with price gaps
- Vulnerability Assessment with margin exposure
- Recommended Action with specific pricing strategies
- DATA SUMMARY MATRIX with key business metrics

---

## Phase 4+: Graph Generator

### What It Does
Converts synthesis report data into **5 visual charts** for dashboard display:

#### 1. **Price Comparison Chart** (Bar Chart)
Shows your price vs competitor price with gap analysis
```json
{
  "type": "bar_chart",
  "your_price": 129.99,
  "competitor_price": 99.99,
  "gap": "$30 (30%)"
}
```

#### 2. **Margin Health Gauge** (Gauge Chart)
Shows current margin vs minimum floor (SAFE/CRITICAL)
```json
{
  "type": "gauge_chart",
  "current_margin": 84.99,
  "margin_floor": 45.00,
  "status": "SAFE"
}
```

#### 3. **Feature Comparison Chart** (Radar Chart)
Shows your features vs competitor features with advantage count
```json
{
  "type": "radar_chart",
  "your_features": 4,
  "competitor_features": 3,
  "unique_yours": 3,
  "feature_advantage": "+1"
}
```

#### 4. **Risk Level Assessment** (Donut Chart)
Shows overall vulnerability (LOW/MEDIUM/HIGH with 0-10 score)
```json
{
  "type": "donut_chart",
  "risk_level": "MEDIUM",
  "risk_score": 5,
  "recommendation": "Implement defensive pricing..."
}
```

#### 5. **Vulnerability Timeline** (Line Chart)
Shows how position changes if competitor cuts prices
```json
{
  "type": "line_chart",
  "scenarios": [
    {"competitor_drop": "0%", "gap": "$30", "margin_safe": true},
    {"competitor_drop": "10%", "gap": "$40", "margin_safe": true},
    {"competitor_drop": "20%", "gap": "$50", "margin_safe": true}
  ]
}
```

### Running Graph Generator
```bash
python graph_generator.py
```

**Output:** JSON with all 5 chart configurations (ready for React dashboard)

### Usage in Code
```python
from graph_generator import GraphGenerator

generator = GraphGenerator()
charts = generator.generate_all_charts(rag_output, research_output)
json_export = generator.export_for_dashboard(charts)

# Send to React dashboard
```

---

## API Usage

### Synthesis Agent Only
```python
from synthesis_agent import SynthesisAgent
import os

agent = SynthesisAgent()
agent.set_token(os.getenv("HF_TOKEN"))

rag_output = {
    "product_data": {
        "name": "CloudScale Enterprise Tier-2",
        "sku": "CS-ENT-02",
        "price": 129.99,
        "base_cost": 80.00,
        "margin_floor": 100.00,
        "features": ["Auto-scaling", "Multi-region", "99.99% SLA", "Enterprise support"]
    },
    "policy_snippet": "Product margin must stay above $100 per unit"
}

research_output = {
    "competitor_name": "ApexCloud v2",
    "competitor_price_normalized": 112.50,
    "features_found": ["Auto-scaling", "Multi-region", "99.99% SLA", "Premium support"],
    "sources": ["apexcloud.com", "techcrunch.com", "g2.com"]
}

# Generate report
report = agent.synthesize(rag_output, research_output)
print(report)

# Refine with feedback
feedback = "Ensure we stay above $100 margin floor while undercutting competitor..."
refined = agent.synthesize(rag_output, research_output, feedback)
```

### Synthesis + Graphs Together
```python
from synthesis_agent import SynthesisAgent
from graph_generator import GraphGenerator
import os

# Phase 4: Generate report
agent = SynthesisAgent()
agent.set_token(os.getenv("HF_TOKEN"))
report = agent.synthesize(rag_output, research_output)

# Phase 4+: Generate charts
generator = GraphGenerator()
charts = generator.generate_all_charts(rag_output, research_output)

# Send both to dashboard
dashboard_payload = {
    "report": report,
    "charts": charts
}
```

---

## Model Information

### Qwen-14B Specifications
- **Model ID:** Qwen/Qwen3-14B:nscale
- **Provider:** Alibaba Cloud (via Hugging Face)
- **Parameters:** 14 Billion
- **API:** OpenAI-compatible (via HF router)
- **Cost:** FREE (30,000 requests/month)
- **Speed:** 5-10 seconds per report
- **Open Source:** Yes (Apache 2.0)

### Why Qwen-14B?
| Feature | Qwen-14B | GPT-4 | Claude 3 |
|---------|----------|-------|---------|
| Cost | FREE | $$$$ | $$$$ |
| Speed | 5-10s | 3-5s | 4-6s |
| Report Quality | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Open Source | ✅ | ❌ | ❌ |
| Self-hosting | ✅ | ❌ | ❌ |

---

## Free Tier Limits
- **30,000 requests/month** (~1,000 reports/day)
- Perfect for development and testing
- No credit card required
- Zero cost until you scale

---

## Dashboard Integration

### Phase 6: LangGraph Flow
```
RAG (Phase 2) → Research (Phase 3) → Synthesis (Phase 4) → Graphs → Reviewer (Phase 5) → Approve/Reject
```

### React Component Example
```jsx
import { BarChart, GaugeChart, RadarChart, DonutChart, LineChart } from 'chart-library';

function Dashboard({ report, charts }) {
  return (
    <div className="dashboard">
      <h1>Margin Vulnerability Analysis</h1>
      
      <div className="report">
        <ReactMarkdown>{report}</ReactMarkdown>
      </div>
      
      <div className="charts">
        <BarChart data={charts.price_comparison} />
        <GaugeChart data={charts.margin_analysis} />
        <RadarChart data={charts.feature_comparison} />
        <DonutChart data={charts.risk_level} />
        <LineChart data={charts.vulnerability_timeline} />
      </div>
    </div>
  );
}
```

---

## Troubleshooting

### "HF_TOKEN not found"
- Check `.env` file exists in this directory
- Verify token is pasted correctly
- Token should start with `hf_`

### "Connection error"
- Check internet connection
- Verify Hugging Face API is accessible
- Fallback to local Qwen inference (requires GPU)

### Empty or None response
- Retry the request
- Check HF API status
- Verify token has sufficient quota

---

## Next Phases

### Phase 5: Reviewer Agent
Validates reports and sends feedback back for refinement.

### Phase 6: LangGraph Integration
Connects all phases in an automated pipeline with feedback loops.

---

## Files Documentation

See `WHAT_IT_DOES.md` for:
- Detailed Phase 4 implementation
- Graph generator specifications
- Model selection rationale
- Cost analysis
- Integration architecture

---

## Questions?
1. Check `.env` setup
2. Ensure token is valid
3. Run `python test_quick.py` to test
4. Check `WHAT_IT_DOES.md` for detailed documentation
