import React, { useState, useRef } from 'react';
import PolicyUploadSection from './PolicyUploadSection';
import ProductQuerySection from './ProductQuerySection';
import PipelineConsole from './PipelineConsole';
import './LeftPanel.css';

interface LeftPanelProps {
  policy: any;
  onPolicyUpload: (data: any) => void;
  onAnalysisStart: (data: any, id: string) => void;
  onLoadingChange: (loading: boolean) => void;
  onStepChange: (step: number) => void;
  isLoading: boolean;
  currentStep: number;
  policyLoaded: boolean;
}

const LeftPanel: React.FC<LeftPanelProps> = ({
  policy,
  onPolicyUpload,
  onAnalysisStart,
  onLoadingChange,
  onStepChange,
  isLoading,
  currentStep,
  policyLoaded,
}) => {
  const [logs, setLogs] = useState<string[]>([]);
  const logsEndRef = useRef<HTMLDivElement | null>(null);

  const addLog = (message: string) => {
    setLogs((prev) => {
      const updated = [...prev, message];
      return updated.length > 100 ? updated.slice(-100) : updated;
    });
  };

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [logs]);

  return (
    <div className="left-panel">
      <PolicyUploadSection policy={policy} onPolicyUpload={onPolicyUpload} />
      <ProductQuerySection
        policyLoaded={policyLoaded}
        isLoading={isLoading}
        onAnalysisStart={onAnalysisStart}
        onLoadingChange={onLoadingChange}
        onStepChange={onStepChange}
        addLog={addLog}
      />
      <PipelineConsole logs={logs} logsEndRef={logsEndRef} />
    </div>
  );
};

export default LeftPanel;
