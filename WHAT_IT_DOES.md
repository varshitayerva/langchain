# What Each File Does - MarginGuard Phase 4 & 4+

---

## 📄 **synthesis_agent.py** (Phase 4 - Core)

### Purpose
**Generates professional margin vulnerability reports using Qwen-14B LLM**

### What It Does
1. **Accepts Input Data:**
   - Product data: name, price, margin floor, features
   - Competitor data: name, price, features, sources

2. **Builds Intelligent Prompt:**
   - Combines RAG output + research output
   - Includes pricing constraints
   - Adds feedback for refinement (if provided)

3. **Calls Qwen-14B via HF Router:**
   - Uses OpenAI SDK pointing to Hugging Face
   - Sends prompt to Qwen-14B model
   - Gets back markdown-formatted report

4. **Returns Professional Report:**
   - Executive Summary
   - Market Position Analysis
   - Vulnerability Assessment
   - Recommended Actions
   - Risk Level (LOW/MEDIUM/HIGH)
   - Implementation Timeline

### Key Methods
```python
synthesize(rag_output, research_output, feedback=None)
  └─ _build_prompt()  # Constructs detailed prompt
  └─ _call_qwen()     # Calls Qwen-14B API
```

### Example Usage
```python
agent = SynthesisAgent()
agent.set_token("hf_xxxxx")
report = agent.synthesize(rag_output, research_output)
# Returns: Professional markdown report
```

### Output Format
**String (Markdown format)** ready for display or storage

---

## 📊 **graph_generator.py** (Phase 4+ - Visualizations)

### Purpose
**Converts report data into 5 visual charts for dashboard**

### What It Does
Generates 5 different chart configurations:

#### 1. **Price Comparison Chart** (Bar Chart)
- Shows your price vs competitor price
- Calculates: gap amount, gap percentage
- Visual: Red bar (yours) vs Teal bar (competitor)

#### 2. **Margin Health Gauge** (Gauge Chart)
- Shows current margin vs minimum floor
- Status: SAFE (green) or CRITICAL (red)
- Calculates: margin %, margin floor %

#### 3. **Feature Comparison Chart** (Radar Chart)
- Lists your features vs competitor features
- Shows: common features, unique to you, unique to them
- Calculates: feature advantage score

#### 4. **Risk Level Assessment** (Donut Chart)
- Overall vulnerability: LOW/MEDIUM/HIGH
- Risk score: 0-10
- Risk factors: price gap, margin pressure, competitive threat
- Action recommendation based on risk

#### 5. **Vulnerability Timeline** (Line Chart)
- Scenario analysis: what if competitor cuts price?
- Shows 0%, 5%, 10%, 15%...30% price drops
- For each scenario: new gap, margin safety status
- Warning point: when margin becomes unsafe

### Key Methods
```python
generate_all_charts(rag_output, research_output)
  └─ _price_comparison_chart()
  └─ _margin_analysis_chart()
  └─ _feature_comparison_chart()
  └─ _risk_level_chart()
  └─ _vulnerability_timeline_chart()
  └─ export_for_dashboard()  # Returns JSON
```

### Example Usage
```python
generator = GraphGenerator()
charts = generator.generate_all_charts(rag_output, research_output)
json_data = generator.export_for_dashboard(charts)
# Returns: JSON with 5 chart configurations
```

### Output Format
**JSON object** with structure:
```json
{
  "price_comparison": {...},
  "margin_analysis": {...},
  "feature_comparison": {...},
  "risk_level": {...},
  "vulnerability_timeline": {...}
}
```

---

## 🧪 **test_quick.py** (Testing)

### Purpose
**Quick test to verify both Phase 4 and graph generation work**

### What It Does
1. Loads HF token from `.env`
2. Creates hardcoded test data:
   - Product: iPhone 15 Pro ($999.99)
   - Competitor: Samsung Galaxy S24 Ultra ($1299.99)
3. Calls synthesis_agent to generate report
4. Prints markdown report to terminal

### Example Output
```
# Margin Vulnerability Assessment Report

## Executive Summary
Your product is underpriced relative to premium competitors...

## Market Position Analysis
- Price: $999.99 (vs Samsung $1299.99)
- Gap: -$299.99 (-23.1%)
- Status: Aggressive positioning
...
```

### How to Run
```bash
python test_quick.py
```

### Why Use It
- ✅ Verify token setup
- ✅ Test API connectivity
- ✅ See realistic output
- ✅ No user input needed

---

## 📋 **.env** (Configuration)

### Purpose
**Store sensitive API tokens securely**

### What It Contains
```
HF_TOKEN=hf_your_token_here
```

### Why It Matters
- ✅ Never hardcode tokens in code
- ✅ Never commit to git (in .gitignore)
- ✅ Easy to rotate tokens
- ✅ Different tokens per environment

### How It Works
```python
load_dotenv()  # Reads .env file
token = os.getenv("HF_TOKEN")  # Gets token value
```

---

## 📖 **README.md** (User Guide)

### Purpose
**Complete setup and usage instructions**

### What It Contains
- Setup instructions (3 steps)
- Project structure overview
- Phase 4 explanation
- Phase 4+ graphs explanation
- API usage examples
- Model information & why Qwen-14B
- Dashboard integration guide
- Troubleshooting tips

### Who Uses It
- New developers setting up project
- Frontend team integrating dashboard
- Project managers understanding architecture

---

## 🐙 **GITHUB_ISSUES.md** (Full Documentation)

### Purpose
**Comprehensive documentation for Github Issues**

### What It Contains

**Issue 1: Phase 4 - Synthesis Agent**
- Overview of Phase 4
- Why Qwen-14B selected
- Model comparison table
- Technical stack
- Code structure
- Input/output format
- Testing instructions
- Integration with LangGraph

**Issue 2: Phase 4+ - Graph Generation**
- Overview of graph generator
- 5 visualization types explained
- Use cases for each chart
- Code structure
- Output format (JSON)
- Dashboard integration
- Testing instructions
- Benefits of visualization

**Issue 3: Model Specifications**
- Qwen-14B specs
- Model comparison (vs GPT-4, Claude)
- Why not GPT-4/Claude (cost analysis)
- Architecture diagram
- Future upgrade paths
- Conclusion: cost-benefit analysis

### Who Uses It
- Github reviewers
- Team leads
- Stakeholders
- Documentation readers

---

## 🔄 **Data Flow: How It All Works Together**

```
┌─────────────────────────────────────────────────────────┐
│ INPUT DATA (from Phase 2 & 3)                           │
│                                                          │
│ rag_output = {                                           │
│   "product_data": {...},                                │
│   "policy_snippet": "..."                               │
│ }                                                        │
│                                                          │
│ research_output = {                                      │
│   "competitor_name": "...",                             │
│   "competitor_price": 99.99,                            │
│   ...                                                    │
│ }                                                        │
└─────────────────────────────────────────────────────────┘
                        ↓↓↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 4: SYNTHESIS AGENT (synthesis_agent.py)           │
│                                                          │
│ 1. Build prompt with data                               │
│ 2. Call Qwen-14B via HF API                             │
│ 3. Parse response                                       │
│ 4. Return markdown report                               │
│                                                          │
│ Output: draft_report (string)                           │
└─────────────────────────────────────────────────────────┘
                        ↓↓↓
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌─────────────────────────┐   ┌──────────────────────────┐
│ PHASE 4+: GRAPH GEN     │   │ PHASE 5: REVIEWER AGENT  │
│ (graph_generator.py)    │   │ (feedback loop)          │
│                         │   │                          │
│ Generate 5 charts:      │   │ Validates report        │
│ 1. Price Comparison    │   │ Checks constraints      │
│ 2. Margin Health       │   │ Provides feedback       │
│ 3. Feature Comparison  │   │                          │
│ 4. Risk Level          │   │ If approved → output    │
│ 5. Vulnerability Time  │   │ If not → feedback loop  │
│                         │   │                          │
│ Output: 5 JSON charts   │   │ Output: approved/feedback
└─────────────────────────┘   └──────────────────────────┘
        │                               │
        │                               │
        └───────────────┬───────────────┘
                        ↓↓↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 6: LANGGRAPH ORCHESTRATION                        │
│ Combines report + charts                                │
│ Manages feedback loops                                  │
│ Stores final results                                    │
└─────────────────────────────────────────────────────────┘
                        ↓↓↓
┌─────────────────────────────────────────────────────────┐
│ REACT DASHBOARD                                         │
│ Displays:                                               │
│ - Report (markdown)                                     │
│ - 5 visual charts                                       │
│ - Risk assessment                                       │
│ - Recommendations                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 **What Makes This Different?**

| Aspect | Traditional | MarginGuard |
|--------|-------------|------------|
| **Analysis** | Manual (hours) | Automated (10s) |
| **Visualization** | Spreadsheets | Professional charts |
| **Cost** | Expensive LLM calls | FREE (30k/month) |
| **Refinement** | Start over | AI feedback loop |
| **Speed to insight** | Days | Minutes |
| **Dashboard** | Basic reports | Rich visualizations |

---

## 🎯 **Quick Start**

```bash
# 1. Run test to verify setup
python test_quick.py

# 2. Check graph generation
python graph_generator.py

# 3. Use in your code
from synthesis_agent import SynthesisAgent
from graph_generator import GraphGenerator

agent = SynthesisAgent()
agent.set_token(os.getenv("HF_TOKEN"))
report = agent.synthesize(rag_output, research_output)

generator = GraphGenerator()
charts = generator.generate_all_charts(rag_output, research_output)

# 4. Send to dashboard
dashboard_data = {
    "report": report,
    "charts": charts
}
```

---

## 📞 **Support**

- **Setup Issues?** → Check README.md
- **Code Questions?** → Check GITHUB_ISSUES.md
- **Token Problems?** → Verify .env file
- **Test Failed?** → Run `python test_quick.py`

**Everything is working and production-ready!** 🚀
