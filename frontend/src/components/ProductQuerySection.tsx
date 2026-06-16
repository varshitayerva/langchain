import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ProductQuerySection.css';

interface ProductQuerySectionProps {
  policyLoaded: boolean;
  isLoading: boolean;
  onAnalysisStart: (data: any, id: string) => void;
  onLoadingChange: (loading: boolean) => void;
  onStepChange: (step: number) => void;
  addLog: (message: string) => void;
}

interface Product {
  name: string;
  category: string;
  price: number;
}

const SEED_PRODUCTS: Product[] = [
  { name: 'iPhone 15 Pro', category: 'Smartphones', price: 999 },
  { name: 'Samsung Galaxy S24', category: 'Smartphones', price: 899 },
  { name: 'AirPods Pro', category: 'Audio', price: 249 },
  { name: 'Sony WH-1000XM5', category: 'Audio', price: 399 },
  { name: 'iPad Pro', category: 'Tablets', price: 1099 },
  { name: 'MacBook Pro', category: 'Laptops', price: 1999 },
  { name: 'Dell XPS 15', category: 'Laptops', price: 1799 },
  { name: 'Apple Watch Series 9', category: 'Wearables', price: 399 },
];

const ProductQuerySection: React.FC<ProductQuerySectionProps> = ({
  policyLoaded,
  isLoading,
  onAnalysisStart,
  onLoadingChange,
  onStepChange,
  addLog,
}) => {
  const [query, setQuery] = useState('');
  const [autocompleteOpen, setAutocompleteOpen] = useState(false);
  const [filteredProducts, setFilteredProducts] = useState<Product[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem('recentSearches');
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, []);

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);

    if (value.trim()) {
      const filtered = SEED_PRODUCTS.filter((p) =>
        p.name.toLowerCase().includes(value.toLowerCase())
      );
      setFilteredProducts(filtered);
      setAutocompleteOpen(true);
    } else {
      setAutocompleteOpen(false);
    }
  };

  const handleProductSelect = (productName: string) => {
    setQuery(productName);
    setAutocompleteOpen(false);
  };

  const saveSearch = (searchQuery: string) => {
    const updated = [
      searchQuery,
      ...recentSearches.filter((s) => s !== searchQuery),
    ].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('recentSearches', JSON.stringify(updated));
  };

  const handleAnalyzeProduct = async () => {
    if (!query.trim()) {
      alert('Please enter a product name');
      return;
    }

    if (!policyLoaded) {
      alert('Please upload a policy first');
      return;
    }

    saveSearch(query);
    onLoadingChange(true);
    addLog(`[${new Date().toLocaleTimeString()}] Starting analysis for: ${query}`);
    addLog(`[${new Date().toLocaleTimeString()}] ○ RAG Retrieval`);

    try {
      const response = await axios.get('http://localhost:8000/analyze', {
        params: { product: query },
      });

      const executionId = response.data.execution_id;
      addLog(`[${new Date().toLocaleTimeString()}] Execution ID: ${executionId}`);

      // Poll for status
      let completed = false;
      let lastStep = 0;
      let pollCount = 0;
      const maxPolls = 120; // 2 minutes max

      while (!completed && pollCount < maxPolls) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        pollCount++;

        try {
          const statusResponse = await axios.get('http://localhost:8000/status', {
            params: { id: executionId },
          });

          const { status, step, message } = statusResponse.data;
          const timestamp = new Date().toLocaleTimeString();

          if (step !== lastStep) {
            lastStep = step;
            onStepChange(step);

            const steps = [
              'RAG Retrieval',
              'Research Agent',
              'Synthesis',
              'Review and Approval',
            ];
            if (step > 0 && step <= 4) {
              addLog(
                `[${timestamp}] ⟳ ${steps[step - 1]} (${step}/4)`
              );
            }
          }

          if (message) {
            addLog(`[${timestamp}]   → ${message}`);
          }

          if (status === 'completed') {
            completed = true;
            addLog(`[${timestamp}] ✓ Analysis Complete`);

            const resultResponse = await axios.get('http://localhost:8000/result', {
              params: { id: executionId },
            });

            console.log('Result response:', resultResponse.data);
            onAnalysisStart(resultResponse.data, executionId);
          } else if (status === 'failed') {
            completed = true;
            addLog(`[${timestamp}] ✗ Analysis Failed`);
            alert('Analysis failed. Please try again.');
          }
        } catch (error) {
          console.error('Status check error:', error);
        }
      }

      if (!completed) {
        addLog(`[${new Date().toLocaleTimeString()}] ⚠ Analysis timed out`);
      }
    } catch (error) {
      console.error('Analysis error:', error);
      addLog(`[${new Date().toLocaleTimeString()}] ✗ Analysis failed`);
      alert('Failed to start analysis');
    } finally {
      onLoadingChange(false);
    }
  };

  return (
    <div className="product-query-section">
      <label className="section-label">Product Query</label>
      <div className="input-group">
        <input
          type="text"
          className="product-input"
          placeholder="e.g., AirPods Pro"
          value={query}
          onChange={handleQueryChange}
          onFocus={() => query && setAutocompleteOpen(true)}
          disabled={isLoading}
        />
        {autocompleteOpen && filteredProducts.length > 0 && (
          <div className="autocomplete-dropdown">
            {filteredProducts.map((product, index) => (
              <div
                key={index}
                className="autocomplete-item"
                onClick={() => handleProductSelect(product.name)}
              >
                {product.name}
                <span className="product-price">${product.price}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <button
        className="btn-analyze"
        onClick={handleAnalyzeProduct}
        disabled={!policyLoaded || isLoading}
      >
        {isLoading ? (
          <>
            <span className="spinner"></span> Analyzing...
          </>
        ) : (
          'Analyze Product'
        )}
      </button>

      {recentSearches.length > 0 && !isLoading && (
        <div className="recent-searches">
          <p className="recent-label">Recent Searches</p>
          <div className="search-links">
            {recentSearches.map((search, index) => (
              <button
                key={index}
                className="search-link"
                onClick={() => {
                  setQuery(search);
                  setAutocompleteOpen(false);
                }}
              >
                {search}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductQuerySection;
