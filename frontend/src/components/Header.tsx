import React from 'react';
import './Header.css';

const Header: React.FC = () => {
  return (
    <header className="vaak-header" id="header">
      <div className="header-inner">
        <div className="header-brand">
          <div className="brand-icon" aria-hidden="true">
            {/* Diya-inspired icon */}
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <ellipse cx="16" cy="24" rx="10" ry="5" stroke="var(--gold-foil)" strokeWidth="1.5" fill="none"/>
              <path d="M10 24 C10 18 8 14 16 6 C24 14 22 18 22 24" stroke="var(--saffron)" strokeWidth="1.5" fill="var(--saffron-glow)"/>
              <ellipse cx="16" cy="10" rx="2" ry="3" fill="var(--diya-amber)"/>
              <circle cx="16" cy="8" r="1.5" fill="var(--gold-light)" opacity="0.9"/>
            </svg>
          </div>
          <div className="brand-text">
            <h1 className="brand-name" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className="gold-text">VaakPod</span>
              <span className="v2-badge">v2</span>
            </h1>
            <span className="brand-tagline devanagari-accent">वाक्पॉड</span>
          </div>
        </div>
        <nav className="header-nav" aria-label="Main navigation">
          <span className="nav-status" id="server-status">
            <span className="status-diya" aria-hidden="true"></span>
            <span className="status-text">AI Ready</span>
          </span>
        </nav>
      </div>
    </header>
  );
};

export default Header;
