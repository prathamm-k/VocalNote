import React from 'react';
import './StatusBar.css';

interface StatusBarProps {
  status: string;
  error: string;
  isProcessing: boolean;
}

const StatusBar: React.FC<StatusBarProps> = ({ status, error, isProcessing }) => {
  if (!status && !error) return null;

  return (
    <div className="status-bar-wrapper" id="status-bar">
      {/* Processing status */}
      {status && !error && (
        <div className={`status-card ${isProcessing ? 'status-card--processing' : 'status-card--success'}`}>
          <div className="status-card-icon" aria-hidden="true">
            {isProcessing ? (
              <div className="status-diya-container">
                <div className="diya-flame"></div>
                <div className="diya-body"></div>
              </div>
            ) : (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="var(--indian-green)" strokeWidth="2"/>
                <path d="M8 12L11 15L16 9" stroke="var(--indian-green)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            )}
          </div>
          <div className="status-card-content">
            <p className="status-message">{status}</p>
            {isProcessing && (
              <div className="status-progress">
                <div className="progress-track">
                  <div className="progress-fill"></div>
                </div>
                <p className="progress-hint">This may take several minutes depending on your PDF size and hardware…</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error status */}
      {error && (
        <div className="status-card status-card--error">
          <div className="status-card-icon" aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="var(--pomegranate)" strokeWidth="2"/>
              <line x1="8" y1="8" x2="16" y2="16" stroke="var(--pomegranate)" strokeWidth="2" strokeLinecap="round"/>
              <line x1="16" y1="8" x2="8" y2="16" stroke="var(--pomegranate)" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <div className="status-card-content">
            <p className="status-message status-message--error">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default StatusBar;
