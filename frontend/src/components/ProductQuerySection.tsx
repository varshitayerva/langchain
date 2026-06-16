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

interface HITLModalState {
  show: boolean;
  executionId: string;
  retryCount: number;
  reviewStatus: string | null;
}

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
  const [hitlModal, setHitlModal] = useState<HITLModalState>({ show: false, executionId: '', retryCount: 0, reviewStatus: null });
  const [hitlNotes, setHitlNotes] = useState('');
  const [hitlApproving, setHitlApproving] = useState(false);

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

  const handleHitlApprove = async () => {
    if (!hitlNotes.trim()) {
      alert('Please provide notes for your decision');
      return;
    }

    setHitlApproving(true);

    try {
      const timestamp = new Date().toLocaleTimeString();
      addLog(`[${timestamp}] 🔄 Resuming workflow with human approval...`);

      const resumeResponse = await axios.post(
        `http://localhost:8000/analyze/resume/${hitlModal.executionId}`,
        {
          override_decision: 'override_approve',
          notes: hitlNotes,
        }
      );

      console.log('Resume response:', resumeResponse.data);
      addLog(`[${timestamp}] ✓ Workflow resumed with approval`);

      // Fetch final result
      const resultResponse = await axios.get(
        `http://localhost:8000/result/${hitlModal.executionId}`
      );

      console.log('Result response:', resultResponse.data);
      onAnalysisStart(resultResponse.data, hitlModal.executionId);
      setHitlModal({ show: false, executionId: '', retryCount: 0, reviewStatus: null });
      setHitlNotes('');
    } catch (error: any) {
      console.error('HITL approval error:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      alert(`Failed to resume workflow: ${error.response?.data?.detail || error.message}`);
    } finally {
      setHitlApproving(false);
    }
  };

  const handleHitlReject = async () => {
    if (!hitlNotes.trim()) {
      alert('Please provide notes for your decision');
      return;
    }

    setHitlApproving(true);

    try {
      const timestamp = new Date().toLocaleTimeString();
      addLog(`[${timestamp}] 🔄 Resuming workflow with human rejection...`);

      const resumeResponse = await axios.post(
        `http://localhost:8000/analyze/resume/${hitlModal.executionId}`,
        {
          override_decision: 'override_reject',
          notes: hitlNotes,
        }
      );

      addLog(`[${timestamp}] ✗ Workflow rejected by human reviewer`);

      setHitlModal({ show: false, executionId: '', retryCount: 0, reviewStatus: null });
      setHitlNotes('');
      onLoadingChange(false);
    } catch (error) {
      console.error('HITL rejection error:', error);
      alert('Failed to process rejection. Please try again.');
    } finally {
      setHitlApproving(false);
    }
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

    try {
      const response = await axios.get(`http://localhost:8000/analyze?product=${encodeURIComponent(query)}`);

      const executionId = response.data.execution_id;
      addLog(`[${new Date().toLocaleTimeString()}] Execution ID: ${executionId}`);

      // Poll for status
      let completed = false;
      let pollCount = 0;
      const maxPolls = 120; // 2 minutes max

      while (!completed && pollCount < maxPolls) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        pollCount++;

        try {
          const statusResponse = await axios.get(`http://localhost:8000/status/${executionId}`);

          const { status, is_paused, retry_count, review_status } = statusResponse.data;
          const timestamp = new Date().toLocaleTimeString();

          if (status === 'paused_for_human_review') {
            completed = true;
            addLog(`[${timestamp}] ⏸ Analysis paused - Awaiting human review (${retry_count} retries attempted)`);
            addLog(`[${timestamp}] Last status: ${review_status}`);

            // Stop the loader spinner
            onLoadingChange(false);

            // Show HITL modal
            setHitlModal({
              show: true,
              executionId,
              retryCount: retry_count,
              reviewStatus: review_status,
            });
            return; // Stop polling
          } else if (status === 'completed') {
            completed = true;
            addLog(`[${timestamp}] ✓ Analysis Complete`);

            const resultResponse = await axios.get(`http://localhost:8000/result/${executionId}`);

            console.log('Result response:', resultResponse.data);
            onAnalysisStart(resultResponse.data, executionId);
          } else if (status === 'error') {
            completed = true;
            addLog(`[${timestamp}] ✗ Analysis Error`);
            alert('Analysis encountered an error. Please try again.');
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
        <label htmlFor="product-query-input" className="sr-only">Product Query</label>
        <input
          id="product-query-input"
          type="text"
          className="product-input"
          placeholder="e.g., AirPods Pro"
          value={query}
          onChange={handleQueryChange}
          onFocus={() => query && setAutocompleteOpen(true)}
          disabled={isLoading}
          title="Enter a product name to analyze"
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

      {/* HITL Modal */}
      {hitlModal.show && (
        <div className="hitl-modal-overlay">
          <div className="hitl-modal">
            <div className="hitl-modal-header">
              <h3>⏸ Human Review Required</h3>
              <p>The pricing report was rejected {hitlModal.retryCount} times. Please review and make a final decision.</p>
            </div>

            <div className="hitl-modal-content">
              <p className="hitl-info">
                <strong>Status:</strong> {hitlModal.reviewStatus}
              </p>
              <p className="hitl-info">
                <strong>Retries:</strong> {hitlModal.retryCount}/3
              </p>

              <label htmlFor="hitl-notes-textarea" className="hitl-label">Your Decision Notes:</label>
              <textarea
                id="hitl-notes-textarea"
                className="hitl-textarea"
                value={hitlNotes}
                onChange={(e) => setHitlNotes(e.target.value)}
                placeholder="Provide justification for your decision..."
                disabled={hitlApproving}
                title="Enter your justification for approving or rejecting the report"
              />
            </div>

            <div className="hitl-modal-footer">
              <button
                className="btn-hitl-approve"
                onClick={handleHitlApprove}
                disabled={hitlApproving || !hitlNotes.trim()}
              >
                {hitlApproving ? 'Processing...' : '✓ Approve'}
              </button>
              <button
                className="btn-hitl-reject"
                onClick={handleHitlReject}
                disabled={hitlApproving || !hitlNotes.trim()}
              >
                {hitlApproving ? 'Processing...' : '✗ Reject'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductQuerySection;
