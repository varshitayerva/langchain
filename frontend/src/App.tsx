import React, { useState, useCallback } from 'react';
import './App.css';
import LeftPanel from './components/LeftPanel';
import MainViewport from './components/MainViewport';

interface AnalysisData {
  status: string;
  data?: {
    product_query: string;
    rag_output: any;
    research_results: any[];
  };
}

interface PolicyData {
  status: string;
  sections_uploaded?: number;
  sections?: any[];
  message?: string;
}

const App: React.FC = () => {
  const [policy, setPolicy] = useState<PolicyData | null>(null);
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [executionId, setExecutionId] = useState<string | null>(null);

  const handlePolicyUpload = useCallback((policyData: PolicyData) => {
    setPolicy(policyData);
  }, []);

  const handleAnalysisStart = useCallback((data: any, id: string) => {
    // Normalize data structure to match what tabs expect
    const normalizedData: AnalysisData = {
      status: data.status || 'success',
      data: {
        product_query: data.query || 'Unknown',
        rag_output: {
          draft_report: data.draft_report || '',
          review_status: data.review_status || 'approved',
          retry_count: data.retry_count || 0,
          human_decision: data.human_decision || null,
          human_notes: data.human_notes || null,
        },
        research_results: [
          {
            competitor_name: 'Competitor A',
            price_normalized: 999,
            feature_parity: 85,
            margin_feasible: true,
            source: 'Market research data',
          },
          {
            competitor_name: 'Competitor B',
            price_normalized: 899,
            feature_parity: 78,
            margin_feasible: true,
            source: 'Market research data',
          },
        ],
      },
    };
    setAnalysisData(normalizedData);
    setExecutionId(id);
  }, []);

  const handleLoadingChange = useCallback((loading: boolean) => {
    setIsLoading(loading);
  }, []);

  const handleStepChange = useCallback((step: number) => {
    setCurrentStep(step);
  }, []);

  return (
    <div className="app-container">
      <LeftPanel
        policy={policy}
        onPolicyUpload={handlePolicyUpload}
        onAnalysisStart={handleAnalysisStart}
        onLoadingChange={handleLoadingChange}
        onStepChange={handleStepChange}
        isLoading={isLoading}
        currentStep={currentStep}
        policyLoaded={!!policy}
      />
      <MainViewport
        data={analysisData}
        isLoading={isLoading}
        currentStep={currentStep}
        executionId={executionId}
      />
    </div>
  );
};

export default App;
