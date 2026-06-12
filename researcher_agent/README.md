# Research Agent - Phase 3

This module implements the **Research Agent** for the MarginGuard multi-agent pipeline. It takes a single product from the RAG retrieval and searches for competitor offerings using Tavily Search and currency normalization via Frankfurter.

## Overview

The Research Agent:
1. **Searches** for competitors using Tavily Search API
2. **Extracts** competitor pricing, features, and availability from search results
3. **Normalizes** prices to USD using Frankfurter currency conversion API
4. **Calculates** feature parity (% match with our product's features)
5. **Evaluates** if competitor pricing is achievable while maintaining margin floor
6. **Returns** structured competitor data for downstream synthesis

## Files

- `research_agent.py` — Core implementation with `ResearchAgent` class and `research_agent()` function
- `config.py` — Configuration and environment variables
- `__init__.py` — Package initialization
- `README.md` — This file

## Usage

### As a Standalone Function

```python
from research_agent import research_agent

# Product data from RAG retrieval
product = {
    "id": 1,
    "name": "AirPods Pro",
    "category": "wireless earbuds",
    "price": 249.00,
    "cost": 100.00,
    "margin_floor": 30,
    "features": "Active noise cancellation, transparency mode, spatial audio",
    "competitor": "Apple"
}

# Research the product
result = research_agent(product)
print(result["research_summary"])
print(result["competitors"])
```

### Output Format

```python
{
    "product_name": "AirPods Pro",
    "our_price": 249.00,
    "our_features": "Active noise cancellation, transparency mode, spatial audio",
    
    "competitors": [
        {
            "name": "Samsung Galaxy Buds2 Pro",
            "competitor_name": "Samsung",
            "price_usd": 229.99,
            "price_normalized": 229.99,
            "features": "Active noise cancellation, transparency mode",
            "feature_parity": 75.0,  # % of our features they have
            "price_gap": -19.01,  # negative = they're cheaper
            "margin_feasible": True,  # can we match their price?
            "source": "https://samsung.com/..."
        },
        # ... up to 3 competitors
    ],
    
    "research_summary": "Found 2 competitors. Cheapest is Samsung at $229.99 (-$19.01). Feature parity 75%. Margin feasible: 2/2",
    "sources": ["https://samsung.com/...", "https://..."]
}
```

## Key Features

### 1. Tavily Search Integration
- Searches for competitor products with a query like: `"AirPods Pro wireless earbuds price features"`
- Returns up to 5 results, extracts title, content, and source URL
- Parses results heuristically to extract competitor name, price, and features

### 2. Currency Conversion
- Uses **Frankfurter API** (free, no authentication needed)
- Detects currency from search results (USD, EUR, GBP, JPY, INR, CAD, AUD)
- Converts all prices to USD for consistent comparison
- Example: `€249.99` → `$275.20` (using current exchange rates)

### 3. Feature Parity Calculation
- Compares competitor's mentioned features against our product's feature list
- Counts how many of our features appear in competitor's description
- Returns parity as a percentage: `len(matched_features) / len(our_features) * 100`
- Used by Synthesis Agent to determine pricing flexibility

### 4. Margin Feasibility Check
- Uses the formula: `Margin % = (Price - Cost) / Price * 100`
- Checks if we can match competitor's price while staying above `margin_floor`
- Example: If competitor is $229.99, our cost is $100, margin floor is 30%:
  - Our margin at their price: `(229.99 - 100) / 229.99 * 100 = 56.6%` ✓ Feasible

### 5. Price Gap Calculation
- Calculates: `price_gap = competitor_price - our_price`
- Negative gap = they're cheaper, positive = we're cheaper
- Used by Synthesis Agent to assess competitive urgency

## Environment Setup

### Prerequisites
```bash
# Install dependencies
pip install tavily-python requests python-dotenv

# OR use existing requirements.txt (already includes these)
pip install -r ../rag_agent/requirements.txt
```

### Environment Variables

Add these to your `.env` file (in project root):

```env
# Tavily Search API Key (required)
TAVILY_API_KEY=your_api_key_here

# Note: Frankfurter is free and doesn't require an API key
```

### Getting Tavily API Key

1. Go to https://tavily.com
2. Sign up (free tier available)
3. Copy your API key
4. Add to `.env`

## Testing

### Run the test suite
```bash
python research_agent.py
```

Expected output:
```
[TEST] Research Agent Testing...

Testing with product: AirPods Pro

[RESEARCH] Found X competitor(s). Cheapest: ... Margin feasibility: ...

[COMPETITORS] Found:
  Name: Samsung Galaxy Buds2 Pro
  Competitor: Samsung
  Price: $229.99 (gap: -19.01)
  Features: Active noise cancellation, transparency mode
  Feature Parity: 75%
  Margin Feasible: True
  Source: https://...

[SUCCESS] Research Agent test complete!
```

### Manual Testing with Custom Products

```python
from research_agent import research_agent

# Test with multiple products
test_products = [
    {
        "name": "Sony WF-1000XM5",
        "category": "wireless earbuds",
        "price": 299.99,
        "cost": 120.00,
        "margin_floor": 32,
        "features": "Industry-leading noise cancellation, LDAC codec, 8-hour battery"
    },
    {
        "name": "Apple Watch Series 9",
        "category": "smartwatch",
        "price": 399.00,
        "cost": 160.00,
        "margin_floor": 40,
        "features": "Always-on retina display, fitness tracking, ECG, blood oxygen"
    }
]

for product in test_products:
    result = research_agent(product)
    print(f"\n{product['name']}: {result['research_summary']}")
```

## Data Flow

```
Product from RAG
    ↓
[ResearchAgent.research_product()]
    ↓
    ├─ Tavily Search → Search Results
    │   ↓
    │   ├─ Extract competitor name (brand detection)
    │   ├─ Extract price (regex patterns)
    │   ├─ Detect currency (EUR, GBP, USD, etc.)
    │   └─ Extract features (keyword matching)
    │
    ├─ Currency Conversion (Frankfurter)
    │   └─ Convert all prices to USD
    │
    ├─ Feature Parity Calculation
    │   └─ % match with our features
    │
    └─ Margin Feasibility Check
        └─ Can we match their price?
    
    ↓
Research Output Dict
    ├─ product_name
    ├─ our_price
    ├─ competitors (up to 3)
    ├─ research_summary
    └─ sources
    
    ↓ (fed to Synthesis Agent)
```

## Error Handling

The Research Agent gracefully handles:
- **Missing Tavily API Key** — Raises `ValueError` at initialization
- **Tavily Search Failures** — Returns empty competitors list, logs error
- **Currency Conversion Errors** — Falls back to original amount, logs warning
- **Price Extraction Failures** — Skips that result, tries next
- **No Competitors Found** — Returns empty competitors list with summary: "No direct competitors found"

## Integration Points

### Upstream (from RAG Agent)
- Receives `product_data` dict with keys: `name`, `category`, `price`, `cost`, `margin_floor`, `features`, `competitor`

### Downstream (to Synthesis Agent)
- Outputs `research_output` dict that Synthesis Agent uses to generate the draft report
- Synthesis uses:
  - `research_summary` — for context on competitive landscape
  - `competitors` — detailed competitive analysis
  - `price_gap` — to determine if price matching is urgent
  - `margin_feasible` — to recommend achievable pricing strategies

## Next Steps (When Integrated into LangGraph)

Once this agent works standalone, it will be integrated into the LangGraph as:
1. A **node** in the computational graph
2. **Input**: Retrieved product from RAG node
3. **Output**: research_output fed to Synthesis node
4. **Retry Logic**: None at this stage (reviewer handles retries at the synthesis level)

See `/rag_agent/PHASES.md` for the full integration plan.

## Performance Notes

- **Tavily Search**: ~2-5 seconds per query
- **Currency Conversion**: ~0.5 seconds per call
- **Feature Parity**: <100ms (local string matching)
- **Total per product**: ~3-5 seconds

For parallel processing of multiple products in LangGraph, consider connection pooling and batching.

## Troubleshooting

### "TAVILY_API_KEY environment variable not set"
- Check `.env` file exists in project root
- Verify `TAVILY_API_KEY=...` is present
- Restart your Python process after adding it

### "No competitors found" or empty results
- Check if Tavily is working: try a different search query manually
- Verify your Tavily account has API credits
- Try a broader search term (e.g., "wireless earbuds price" instead of exact product name)

### Currency conversion returning original amount
- Frankfurter API might be down or rate-limited
- Check your internet connection
- Try converting manually: `convert_currency(100, "EUR", "USD")`

### Feature parity showing 0%
- Check the `features` field in product_data isn't empty
- Verify feature names match what's in competitor descriptions
- Try shortening feature names (e.g., "noise cancellation" vs "Active noise cancellation")

---

**Author**: Shruti  
**Phase**: 3 (Research Agent - Standalone Function)  
**Status**: Ready for LangGraph Integration  
**Last Updated**: 2026-06-12
