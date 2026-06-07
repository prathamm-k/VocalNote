import React from 'react';
import './Footer.css';

const Footer: React.FC = () => {
  return (
    <footer className="vaak-footer" id="footer">
      <div className="footer-inner">
        {/* Rangoli Divider */}
        <div className="rangoli-divider">
          <span className="rangoli-dot"></span>
        </div>

        <div className="footer-content">
          <div className="footer-brand" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className="footer-logo gold-text">VaakPod</span>
            <span className="v2-badge">v2</span>
            <span className="footer-logo-hi devanagari-accent">वाक्पॉड</span>
          </div>

          <p className="footer-desc">
            Powered by Qwen LLMs & Kokoro TTS · Runs entirely on your machine
          </p>

          <div className="footer-tech">
            <span className="tech-badge">Qwen3 1.7B</span>
            <span className="tech-badge">Qwen2.5 3B</span>
            <span className="tech-badge">Kokoro TTS</span>
            <span className="tech-badge">FastAPI</span>
          </div>
        </div>

        <p className="footer-copy">
          Built with <span className="footer-heart" aria-label="love">🪔</span> in India
        </p>
      </div>
    </footer>
  );
};

export default Footer;
