import React from 'react';
import './Footer.css';

const Footer: React.FC = () => {
  return (
    <footer className="vaak-footer" id="footer">
      <div className="footer-inner">
        <div className="footer-divider"></div>

        <div className="footer-content">
          <div className="footer-brand">
            <span className="footer-logo warm-text">VocalNote</span>
            <span className="v2-badge">v2</span>
          </div>

          <div className="footer-tech">
            <span className="tech-badge">Qwen3 1.7B</span>
            <span className="tech-badge">Qwen2.5 3B</span>
            <span className="tech-badge">Kokoro TTS</span>
            <span className="tech-badge">FastAPI</span>
          </div>

          <p className="footer-desc">
            Runs entirely on your machine. No data leaves your device.
          </p>
        </div>

        <p className="footer-copy">
          Made in India
        </p>
      </div>
    </footer>
  );
};

export default Footer;
