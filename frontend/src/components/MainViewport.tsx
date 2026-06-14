import React, { useState } from 'react';
import OverviewTab from './tabs/OverviewTab';
import CompetitorsTab from './tabs/CompetitorsTab';
import ChartsTab from './tabs/ChartsTab';
import ReportTab from './tabs/ReportTab';
import './MainViewport.css';

interface MainViewportProps {
  data: any;
  isLoading: boolean;
  currentStep: number;
  executionId: string | null;
}

const MainViewport: React.FC<MainViewportProps> = ({
  data,
  isLoading,
  currentStep,
  executionId,
}) => {
  const [activeTab, setActiveTab] = useState('overview');

  if (!data && !isLoading) {
    return (
      <div className="main-viewport">
        <div className="empty-state-container">
          <h2>Welcome to MarginGuard</h2>
          <p>Upload a company policy document on the left panel to get started</p>
          <ol className="empty-state-steps">
            <li>Upload your company policy PDF</li>
            <li>Enter a product name to analyze</li>
            <li>Review competitive analysis results</li>
          </ol>
        </div>
      </div>
    );
  }

  return (
    <div className="main-viewport">
      <div className="tab-navigation">
        <button
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab-button ${activeTab === 'competitors' ? 'active' : ''}`}
          onClick={() => setActiveTab('competitors')}
        >
          Competitors
        </button>
        <button
          className={`tab-button ${activeTab === 'charts' ? 'active' : ''}`}
          onClick={() => setActiveTab('charts')}
        >
          Charts
        </button>
        <button
          className={`tab-button ${activeTab === 'report' ? 'active' : ''}`}
          onClick={() => setActiveTab('report')}
        >
          Report
        </button>
      </div>

      <div className="tab-content">
        {isLoading && (
          <div className="loading-overlay">
            <div className="loading-content">
              <div className="spinner"></div>
              <p>Analyzing... Step {currentStep}/4</p>
            </div>
          </div>
        )}

        {activeTab === 'overview' && <OverviewTab data={data} />}
        {activeTab === 'competitors' && <CompetitorsTab data={data} />}
        {activeTab === 'charts' && <ChartsTab data={data} />}
        {activeTab === 'report' && <ReportTab data={data} />}
      </div>
    </div>
  );
};

export default MainViewport;
