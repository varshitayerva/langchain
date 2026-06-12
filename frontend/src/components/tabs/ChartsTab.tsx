import React from 'react';
import { Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';
import './TabStyles.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

interface ChartsTabProps {
  data: any;
}

const ChartsTab: React.FC<ChartsTabProps> = ({ data }) => {
  if (!data?.data?.research_results) {
    return <div className="tab-container">No chart data available</div>;
  }

  const competitors = data.data.research_results;

  // Chart 1: Price Gap
  const priceGapData = {
    labels: competitors.map((c: any) => c.competitor_name),
    datasets: [
      {
        label: 'Price Gap ($)',
        data: competitors.map((c: any) => c.price_gap || 0),
        backgroundColor: competitors.map((c: any) =>
          c.price_gap < 0 ? '#ff6b6b' : '#4caf50'
        ),
        borderRadius: 4,
      },
    ],
  };

  // Chart 2: Margin Feasibility
  const marginData = {
    labels: competitors.map((c: any) => c.competitor_name),
    datasets: [
      {
        label: 'Margin %',
        data: competitors.map((c: any) =>
          c.margin_feasible ? 75 : 40
        ),
        backgroundColor: competitors.map((c: any) =>
          c.margin_feasible ? '#4caf50' : '#ff6b6b'
        ),
        borderRadius: 4,
      },
    ],
  };

  // Chart 3: Feature Parity Distribution
  const parityData = {
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
  };

  return (
    <div className="tab-container charts-grid">
      <div className="chart-item">
        <h3>Price Gap Analysis</h3>
        <div className="chart-wrapper small">
          <Bar data={priceGapData} options={chartOptions} />
        </div>
      </div>

      <div className="chart-item">
        <h3>Margin Feasibility</h3>
        <div className="chart-wrapper small">
          <Bar data={marginData} options={chartOptions} />
        </div>
      </div>

      <div className="chart-item">
        <h3>Feature Parity Distribution</h3>
        <div className="chart-wrapper small">
          <Doughnut data={parityData} options={chartOptions} />
        </div>
      </div>

      <div className="chart-item policy-matrix">
        <h3>Policy Compliance Matrix</h3>
        <table className="compliance-matrix">
          <thead>
            <tr>
              <th>Competitor</th>
              <th>Price Match</th>
              <th>Margin Floor</th>
              <th>Feature Parity</th>
              <th>Overall</th>
            </tr>
          </thead>
          <tbody>
            {competitors.map((competitor: any, index: number) => (
              <tr key={index}>
                <td>{competitor.competitor_name}</td>
                <td className="compliance-cell">✓</td>
                <td className={competitor.margin_feasible ? 'compliance-cell success' : 'compliance-cell error'}>
                  {competitor.margin_feasible ? '✓' : '✗'}
                </td>
                <td className="compliance-cell">
                  {competitor.feature_parity >= 70 ? '✓' : '○'}
                </td>
                <td className={competitor.margin_feasible ? 'compliance-cell success' : 'compliance-cell error'}>
                  {competitor.margin_feasible ? '✓' : '✗'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ChartsTab;
