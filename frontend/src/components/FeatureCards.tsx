import React from 'react';
import './FeatureCards.css';

const features = [
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <rect x="3" y="3" width="14" height="18" rx="2" stroke="var(--terracotta)" strokeWidth="1.5"/>
        <line x1="7" y1="8" x2="13" y2="8" stroke="var(--text-muted)" strokeWidth="1"/>
        <line x1="7" y1="11" x2="12" y2="11" stroke="var(--text-muted)" strokeWidth="1"/>
        <line x1="7" y1="14" x2="11" y2="14" stroke="var(--text-muted)" strokeWidth="1"/>
        <path d="M17 7L21 7V19C21 20.1 20.1 21 19 21H7" stroke="var(--brass)" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    ),
    title: 'PDF extraction',
    description: 'Extracts and deduplicates up to 100K characters from any PDF document.',
  },
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="9" stroke="var(--terracotta)" strokeWidth="1.5"/>
        <circle cx="12" cy="12" r="4" stroke="var(--brass)" strokeWidth="1"/>
        <circle cx="12" cy="12" r="1.5" fill="var(--terracotta)"/>
        <path d="M12 3V6" stroke="var(--text-muted)" strokeWidth="1" strokeLinecap="round"/>
        <path d="M12 18V21" stroke="var(--text-muted)" strokeWidth="1" strokeLinecap="round"/>
        <path d="M3 12H6" stroke="var(--text-muted)" strokeWidth="1" strokeLinecap="round"/>
        <path d="M18 12H21" stroke="var(--text-muted)" strokeWidth="1" strokeLinecap="round"/>
      </svg>
    ),
    title: 'Local AI models',
    description: 'Runs Qwen3 1.7B and Qwen2.5 3B entirely on-device. No cloud, no API keys.',
  },
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <path d="M12 3C12 3 14 6.5 14 12C14 17.5 12 21 12 21" stroke="var(--terracotta)" strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M7 5.5C7 5.5 9 8 9 12C9 16 7 18.5 7 18.5" stroke="var(--brass)" strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M17 5.5C17 5.5 19 8 19 12C19 16 17 18.5 17 18.5" stroke="var(--brass)" strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M3 10C3 10 5 11 5 12C5 13 3 14 3 14" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M21 10C21 10 23 11 23 12C23 13 21 14 21 14" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    ),
    title: 'Natural voices',
    description: 'Kokoro TTS renders two distinct speakers with natural cadence and intonation.',
  },
];

const FeatureCards: React.FC = () => {
  return (
    <section className="features-section" id="features">
      <div className="features-inner">
        <h3 className="features-title">How it works</h3>
        <div className="features-steps">
          {features.map((feature, index) => (
            <article
              key={index}
              className="feature-step"
              style={{ animationDelay: `${0.1 + index * 0.12}s` }}
            >
              <div className="step-number" aria-hidden="true">{index + 1}</div>
              <div className="step-icon">{feature.icon}</div>
              <h4 className="step-title">{feature.title}</h4>
              <p className="step-desc">{feature.description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeatureCards;
