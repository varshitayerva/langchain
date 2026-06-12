# Quick Start: Research Agent

Get up and running with the research agent in 5 minutes.

## Setup

1. **Add API Key to .env** (project root):
```env
TAVILY_API_KEY=your_api_key_here
```

2. **Run Tests**:
```bash
cd researcher_agent
python test_research.py
```

Expected output:
```
[TEST] Research Agent Testing...
✓ Single Product Research (AirPods Pro)
✓ Multiple Products Research
✓ Edge Cases
✓ Currency Conversion
✓ ALL TESTS PASSED
```

## Use It

```python
from researcher_agent import research_agent

# Product from RAG retrieval
product = {
    "name": "AirPods Pro",
    "category": "wireless earbuds",
    "price": 249.00,
    "cost": 100.00,
    "margin_floor": 30,
    "features": "Active noise cancellation, transparency mode, spatial audio"
}

# Research competitors
result = research_agent(product)

# Use the output
print(result["research_summary"])
for competitor in result["competitors"]:
    print(f"- {competitor['name']}: ${competitor['price_normalized']}")
```

## Output Fields

| Field | Type | Example |
|-------|------|---------|
| `product_name` | str | "AirPods Pro" |
| `our_price` | float | 249.00 |
| `competitors` | list | 3 competitor dicts |
| `competitors[].price_normalized` | float | 229.99 |
| `competitors[].feature_parity` | float | 75.0 (%) |
| `competitors[].price_gap` | float | -19.01 (cheaper) |
| `competitors[].margin_feasible` | bool | True/False |
| `research_summary` | str | "Found 2 competitors..." |
| `sources` | list | URLs |

## Troubleshooting

**"TAVILY_API_KEY not set"** → Add to `.env` and restart Python  
**"No competitors found"** → Tavily may be rate-limited; try again later  
**"Currency conversion failed"** → Frankfurter API down; falls back gracefully  

## Test Details

Run individual test functions:
```bash
python -c "from test_research import test_single_product; test_single_product()"
python -c "from test_research import test_currency_conversion; test_currency_conversion()"
```

See `README.md` for detailed documentation.
