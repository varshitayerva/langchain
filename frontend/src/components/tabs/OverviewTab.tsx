import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import './TabStyles.css';

ChartJS.register(ArcElement, Tooltip, Legend);

interface OverviewTabProps {
  data: any;
}

const OverviewTab: React.FC<OverviewTabProps> = ({ data }) => {
  if (!data?.data) {
    return <div className="tab-container">No data available</div>;
  }

  const { research_results } = data.data;
  const competitors = research_results || [];

  // Calculate metrics
  const totalCompetitors = competitors.length;
  const lowestPrice = competitors.length
    ? Math.min(...competitors.map((c: any) => c.price_normalized || 0))
    : 0;
  const avgParity =
    competitors.length
      ? (
          competitors.reduce((sum: number, c: any) => sum + (c.feature_parity || 0), 0) /
          competitors.length
        ).toFixed(1)
      : 0;
  const marginFeasible = competitors.filter((c: any) => c.margin_feasible).length;

  // Prepare doughnut chart data
  const chartData = {
    labels: competitors.map((c: any) => c.competitor_name),
    datasets: [
      {
        data: competitors.map((c: any) => c.feature_parity || 0),
        backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#ff6b6b', '#4caf50'],
        borderColor: '#ffffff',
        borderWidth: 2,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
    },
  };

  return (
    <div className="tab-container">
      <div className="metrics-grid">
        <div className="metric-card gradient-primary">
          <div className="metric-value">{totalCompetitors}</div>
          <div className="metric-label">Competitors Found</div>
        </div>
        <div className="metric-card gradient-primary">
          <div className="metric-value">${lowestPrice.toFixed(2)}</div>
          <div className="metric-label">Lowest Price</div>
        </div>
        <div className="metric-card gradient-primary">
          <div className="metric-value">{avgParity}%</div>
          <div className="metric-label">Avg Feature Parity</div>
        </div>
        <div className="metric-card gradient-primary">
          <div className="metric-value">
            {marginFeasible}/{totalCompetitors}
          </div>
          <div className="metric-label">Margin Feasible</div>
        </div>
      </div>

      <div className="research-summaries">
        {competitors.map((competitor: any, index: number) => (
          <div key={index} className="summary-card">
            <div className="summary-header">
              <h4>{competitor.competitor_name}</h4>
              <span className="parity-score">{competitor.feature_parity}% Parity</span>
            </div>
            <p className="summary-text">{competitor.source}</p>
          </div>
        ))}
      </div>

      {competitors.length > 0 && (
        <div className="chart-container">
          <h3>Feature Parity Distribution</h3>
          <div className="chart-wrapper">
            <Doughnut data={chartData} options={chartOptions} />
          </div>
        </div>
      )}
    </div>
  );
};

export default OverviewTab;
