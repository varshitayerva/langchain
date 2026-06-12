import React from 'react';
import './PipelineConsole.css';

interface PipelineConsoleProps {
  logs: string[];
  logsEndRef: React.RefObject<HTMLDivElement | null>;
}

const PipelineConsole: React.FC<PipelineConsoleProps> = ({ logs, logsEndRef }) => {
  const copyLogs = () => {
    const logText = logs.join('\n');
    navigator.clipboard.writeText(logText);
  };

  return (
    <div className="pipeline-console">
      <h3 className="console-header">Pipeline Execution (Real-time)</h3>
      <div className="console-log">
        {logs.length === 0 ? (
          <p className="empty-state">Logs will appear here during analysis...</p>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="log-entry">
              <code>{log}</code>
            </div>
          ))
        )}
        <div ref={logsEndRef} />
      </div>
      <button className="btn-copy-log" onClick={copyLogs}>
        Copy Log
      </button>
    </div>
  );
};

export default PipelineConsole;
