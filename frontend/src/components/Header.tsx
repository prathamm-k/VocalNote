import React from 'react';
import './Header.css';

const Header: React.FC = () => {
  return (
    <header className="vaak-header" id="header">
      <div className="header-island">
        <div className="header-brand">
          <h1 className="brand-name">
            <span className="warm-text">VocalNote</span>
            <span className="v2-badge">v2</span>
          </h1>
          <span className="brand-tagline devanagari-accent">वोकलनोट</span>
        </div>
        <nav className="header-nav" aria-label="Main navigation">
          <span className="nav-status" id="server-status">
            <span className="status-dot" aria-hidden="true"></span>
            <span className="status-text">Ready</span>
          </span>
        </nav>
      </div>
    </header>
  );
};

export default Header;
