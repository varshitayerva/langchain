import React from 'react';
import './TabStyles.css';

interface ReportTabProps {
  data: any;
}

const ReportTab: React.FC<ReportTabProps> = ({ data }) => {
  if (!data?.data) {
    return <div className="tab-container">No report data available</div>;
  }

  const { product_query, research_results, rag_output } = data.data;
  const competitors = research_results || [];

  // Extract human decision and status from rag_output
  const humanDecision = rag_output?.human_decision;
  const reviewStatus = rag_output?.review_status;
  const humanNotes = rag_output?.human_notes;

  // Determine if this was approved or rejected
  const isApproved = humanDecision === 'override_approve' || reviewStatus === 'approved';
  const isRejected = humanDecision === 'override_reject' || reviewStatus === 'failed';

  const copyToClipboard = () => {
    const reportText = generateReportText();
    navigator.clipboard.writeText(reportText);
  };

  const downloadPDF = () => {
    // Simple text-based PDF download
    const element = document.createElement('a');
    const file = new Blob([generateReportText()], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `analysis-report-${product_query}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const generateReportText = () => {
    let text = `MARGINGUARD COMPETITIVE ANALYSIS REPORT\n`;
    text += `=====================================\n\n`;
    text += `Product: ${product_query}\n`;
    text += `Date: ${new Date().toLocaleDateString()}\n\n`;
    text += `EXECUTIVE SUMMARY\n`;
    text += `-----------------\n`;
    text += `This report analyzes the competitive landscape for ${product_query}. `;
    text += `We identified ${competitors.length} key competitors with varying price points `;
    text += `and feature parity levels.\n\n`;
    text += `COMPETITIVE LANDSCAPE\n`;
    text += `--------------------\n`;
    competitors.forEach((c: any, idx: number) => {
      text += `\n${idx + 1}. ${c.competitor_name}\n`;
      text += `   Price: $${c.price_normalized?.toFixed(2) || 'N/A'}\n`;
      text += `   Feature Parity: ${c.feature_parity}%\n`;
      text += `   Price Gap: ${c.price_gap < 0 ? '-' : '+'}$${Math.abs(c.price_gap || 0).toFixed(2)}\n`;
      text += `   Margin Feasible: ${c.margin_feasible ? 'Yes' : 'No'}\n`;
    });
    text += `\nRECOMMENDATIONS\n`;
    text += `---------------\n`;
    competitors.forEach((c: any, idx: number) => {
      text += `${idx + 1}. For ${c.competitor_name}: `;
      if (c.margin_feasible) {
        text += `Consider price matching strategy.\n`;
      } else {
        text += `Monitor closely for margin impact.\n`;
      }
    });
    return text;
  };

  const shareEmail = () => {
    const subject = `MarginGuard Analysis Report: ${product_query}`;
    const body = generateReportText();
    const mailtoLink = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.location.href = mailtoLink;
  };

  // CASE A: Human Approved the proposal
  if (isApproved) {
    return (
      <div className="tab-container">
        <div className="report-wrapper">
          <div className="approval-banner approved">
            <h2>✅ STRATEGIC PROPOSAL OVERRIDDEN & APPROVED</h2>
            <p>This analysis has been manually approved by a human reviewer after initial rejection.</p>
          </div>

          <div className="report-header">
            <h2>Competitive Analysis Report</h2>
            <p>Product: <strong>{product_query}</strong></p>
          </div>

          {humanNotes && (
            <section className="human-notes-section">
              <h3>🔏 Approval Justification</h3>
              <div className="notes-box">
                <p><strong>Manager Notes:</strong> {humanNotes}</p>
              </div>
            </section>
          )}

          <div className="report-content">
            <section className="report-section">
              <h3>Executive Summary</h3>
              <p>
                This report provides a comprehensive competitive analysis for <strong>{product_query}</strong>.
                We have identified {competitors.length} key competitors in the market with varying
                pricing strategies and feature offerings. The analysis considers margin feasibility
                and policy compliance for strategic positioning.
              </p>
            </section>

            <section className="report-section">
              <h3>Competitive Landscape</h3>
              {competitors.map((competitor: any, index: number) => (
                <div key={index} className="competitor-section">
                  <h4>{competitor.competitor_name}</h4>
                  <ul>
                    <li><strong>Price:</strong> ${competitor.price_normalized?.toFixed(2) || 'N/A'}</li>
                    <li>
                      <strong>Price Gap:</strong>{' '}
                      {competitor.price_gap < 0 ? '-' : '+'}
                      ${Math.abs(competitor.price_gap || 0).toFixed(2)}
                    </li>
                    <li><strong>Feature Parity:</strong> {competitor.feature_parity}%</li>
                    <li>
                      <strong>Policy Compliance:</strong>{' '}
                      <span className={competitor.margin_feasible ? 'text-success' : 'text-error'}>
                        {competitor.margin_feasible ? '✓ Compliant' : '✗ Non-Compliant'}
                      </span>
                    </li>
                    <li>
                      <strong>Recommendation:</strong>{' '}
                      {competitor.margin_feasible ? 'Price Match' : 'Hold Position'}
                    </li>
                  </ul>
                </div>
              ))}
            </section>

            <section className="report-section">
              <h3>Recommendations</h3>
              <ol>
                {competitors.filter((c: any) => c.margin_feasible).length > 0 && (
                  <li>Price match feasible competitors to maintain market position</li>
                )}
                {competitors.filter((c: any) => !c.margin_feasible).length > 0 && (
                  <li>Monitor non-feasible competitors for market trends</li>
                )}
                <li>Review feature parity gaps and prioritize improvements</li>
                <li>Regular policy compliance checks recommended</li>
              </ol>
            </section>

            <section className="report-section">
              <h3>Approval Status</h3>
              <div className="approval-badge success">
                ✓ APPROVED FOR ACTION (Manual Override)
              </div>
              <p>This analysis has been completed, reviewed, and manually approved. Recommendations are ready for implementation.</p>
            </section>
          </div>

          <div className="report-actions">
            <button className="btn-action" onClick={downloadPDF}>
              Download PDF
            </button>
            <button className="btn-action" onClick={copyToClipboard}>
              Copy to Clipboard
            </button>
            <button className="btn-action" onClick={shareEmail}>
              Share via Email
            </button>
          </div>
        </div>
      </div>
    );
  }

  // CASE B: Human Rejected the proposal
  if (isRejected) {
    return (
      <div className="tab-container">
        <div className="report-wrapper">
          <div className="rejection-banner">
            <h2>❌ POLICY VIOLATION: PROPOSAL REJECTED & LOCKED</h2>
            <p>This pricing proposal does not meet company policy requirements and has been locked.</p>
          </div>

          <div className="report-header">
            <h2>Analysis Result for {product_query}</h2>
          </div>

          {humanNotes && (
            <section className="rejection-summary">
              <h3>⛔ Manager Rejection Justification</h3>
              <div className="rejection-box">
                <p><strong>Reason for Rejection:</strong> {humanNotes}</p>
              </div>
            </section>
          )}

          <section className="rejection-notice">
            <h3>What This Means</h3>
            <div className="notice-content">
              <p>
                The proposed pricing strategy for <strong>{product_query}</strong> has been reviewed and rejected
                by a human manager. This analysis cannot be implemented as presented.
              </p>
              <h4>Next Steps:</h4>
              <ol>
                <li>Review the manager's rejection notes above</li>
                <li>Adjust pricing strategy to meet policy constraints</li>
                <li>Resubmit for analysis if changes are made</li>
              </ol>
            </div>
          </section>

          <section className="approval-status-rejected">
            <div className="approval-badge rejected">
              ✗ REJECTED - LOCKED
            </div>
            <p>This proposal is locked and cannot proceed to implementation without manager override.</p>
          </section>
        </div>
      </div>
    );
  }

  // Default fallback (no decision yet)
  return (
    <div className="tab-container">
      <div className="report-wrapper">
        <div className="report-header">
          <h2>Competitive Analysis Report</h2>
          <p>Product: <strong>{product_query}</strong></p>
        </div>

        <div className="report-content">
          <section className="report-section">
            <h3>Executive Summary</h3>
            <p>
              This report provides a comprehensive competitive analysis for <strong>{product_query}</strong>.
              We have identified {competitors.length} key competitors in the market with varying
              pricing strategies and feature offerings. The analysis considers margin feasibility
              and policy compliance for strategic positioning.
            </p>
          </section>

          <section className="report-section">
            <h3>Competitive Landscape</h3>
            {competitors.map((competitor: any, index: number) => (
              <div key={index} className="competitor-section">
                <h4>{competitor.competitor_name}</h4>
                <ul>
                  <li><strong>Price:</strong> ${competitor.price_normalized?.toFixed(2) || 'N/A'}</li>
                  <li>
                    <strong>Price Gap:</strong>{' '}
                    {competitor.price_gap < 0 ? '-' : '+'}
                    ${Math.abs(competitor.price_gap || 0).toFixed(2)}
                  </li>
                  <li><strong>Feature Parity:</strong> {competitor.feature_parity}%</li>
                  <li>
                    <strong>Policy Compliance:</strong>{' '}
                    <span className={competitor.margin_feasible ? 'text-success' : 'text-error'}>
                      {competitor.margin_feasible ? '✓ Compliant' : '✗ Non-Compliant'}
                    </span>
                  </li>
                  <li>
                    <strong>Recommendation:</strong>{' '}
                    {competitor.margin_feasible ? 'Price Match' : 'Hold Position'}
                  </li>
                </ul>
              </div>
            ))}
          </section>

          <section className="report-section">
            <h3>Recommendations</h3>
            <ol>
              {competitors.filter((c: any) => c.margin_feasible).length > 0 && (
                <li>Price match feasible competitors to maintain market position</li>
              )}
              {competitors.filter((c: any) => !c.margin_feasible).length > 0 && (
                <li>Monitor non-feasible competitors for market trends</li>
              )}
              <li>Review feature parity gaps and prioritize improvements</li>
              <li>Regular policy compliance checks recommended</li>
            </ol>
          </section>

          <section className="report-section">
            <h3>Approval Status</h3>
            <div className="approval-badge success">
              ✓ APPROVED FOR ACTION
            </div>
            <p>This analysis has been completed and reviewed. Recommendations are ready for implementation.</p>
          </section>
        </div>

        <div className="report-actions">
          <button className="btn-action" onClick={downloadPDF}>
            Download PDF
          </button>
          <button className="btn-action" onClick={copyToClipboard}>
            Copy to Clipboard
          </button>
          <button className="btn-action" onClick={shareEmail}>
            Share via Email
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReportTab;
