import React, { useState } from 'react';
import './TabStyles.css';

interface CompetitorsTabProps {
  data: any;
}

const CompetitorsTab: React.FC<CompetitorsTabProps> = ({ data }) => {
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'asc' | 'desc';
  } | null>(null);

  if (!data?.data?.research_results) {
    return <div className="tab-container">No competitor data available</div>;
  }

  const competitors = data.data.research_results;

  const handleSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (
      sortConfig?.key === key &&
      sortConfig.direction === 'asc'
    ) {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const getSortedCompetitors = () => {
    const sorted = [...competitors];
    if (sortConfig) {
      sorted.sort((a: any, b: any) => {
        let aVal = a[sortConfig.key];
        let bVal = b[sortConfig.key];

        if (typeof aVal === 'string') {
          aVal = aVal.toLowerCase();
        }
        if (typeof bVal === 'string') {
          bVal = bVal.toLowerCase();
        }

        if (aVal < bVal) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aVal > bVal) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    return sorted;
  };

  const toggleRow = (index: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRows(newExpanded);
  };

  const sortedCompetitors = getSortedCompetitors();

  return (
    <div className="tab-container">
      <div className="table-wrapper">
        <table className="competitors-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('competitor_name')}>
                Product {sortConfig?.key === 'competitor_name' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
              </th>
              <th onClick={() => handleSort('price_normalized')}>
                Price {sortConfig?.key === 'price_normalized' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
              </th>
              <th onClick={() => handleSort('feature_parity')}>
                Parity {sortConfig?.key === 'feature_parity' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
              </th>
              <th onClick={() => handleSort('price_gap')}>
                Gap {sortConfig?.key === 'price_gap' && (sortConfig.direction === 'asc' ? '▲' : '▼')}
              </th>
              <th>Feasible</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {sortedCompetitors.map((competitor: any, index: number) => (
              <React.Fragment key={index}>
                <tr
                  className={`competitor-row ${expandedRows.has(index) ? 'expanded' : ''}`}
                  onClick={() => toggleRow(index)}
                >
                  <td>{competitor.competitor_name}</td>
                  <td>${competitor.price_normalized?.toFixed(2) || 'N/A'}</td>
                  <td>{competitor.feature_parity}%</td>
                  <td
                    className={
                      competitor.price_gap < 0 ? 'text-error' : 'text-success'
                    }
                  >
                    {competitor.price_gap < 0 ? '-' : '+'}${Math.abs(competitor.price_gap || 0).toFixed(2)}
                  </td>
                  <td>
                    <span
                      className={
                        competitor.margin_feasible ? 'text-success' : 'text-error'
                      }
                    >
                      {competitor.margin_feasible ? '✓ Yes' : '✗ No'}
                    </span>
                  </td>
                  <td>
                    <span className="status-badge">Active</span>
                  </td>
                </tr>
                {expandedRows.has(index) && (
                  <tr className="expanded-content">
                    <td colSpan={6}>
                      <div className="expansion-details">
                        <div className="detail-group">
                          <h5>Source</h5>
                          <a href={competitor.source} target="_blank" rel="noreferrer">
                            {competitor.source}
                          </a>
                        </div>
                        <div className="detail-group">
                          <h5>Margin</h5>
                          <p>{competitor.margin_feasible ? 'Feasible' : 'Not Feasible'}</p>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CompetitorsTab;
