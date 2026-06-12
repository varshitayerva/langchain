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

  const handleAnalysisStart = useCallback((data: AnalysisData, id: string) => {
    setAnalysisData(data);
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
