import React from 'react';
import './FeatureCards.css';

const features = [
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
        <rect x="3" y="4" width="16" height="20" rx="2" stroke="var(--saffron)" strokeWidth="1.5"/>
        <path d="M9 4V1" stroke="var(--saffron)" strokeWidth="1.5" strokeLinecap="round"/>
        <line x1="7" y1="10" x2="15" y2="10" stroke="var(--text-muted)" strokeWidth="1"/>
        <line x1="7" y1="13" x2="13" y2="13" stroke="var(--text-muted)" strokeWidth="1"/>
        <line x1="7" y1="16" x2="14" y2="16" stroke="var(--text-muted)" strokeWidth="1"/>
        <path d="M19 8L25 8V24C25 25.1 24.1 26 23 26H9" stroke="var(--gold-foil)" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    ),
    title: 'PDF Extraction',
    titleHi: 'पाठ निष्कर्षण',
    description: 'Extracts and cleans up to 100K characters from any PDF document using smart deduplication.',
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
        <circle cx="14" cy="14" r="10" stroke="var(--saffron)" strokeWidth="1.5"/>
        <circle cx="14" cy="14" r="5" stroke="var(--gold-foil)" strokeWidth="1"/>
        <circle cx="14" cy="14" r="1.5" fill="var(--saffron)"/>
        <path d="M14 4V7" stroke="var(--text-muted)" strokeWidth="1" strokeLinecap="round"/>
        <path d="M14 21V24" stroke="var(--text-muted)" strokeWidth="1" strokeLinecap="round"/>
        <path d="M4 14H7" stroke="var(--text-muted)" strokeWidth="1" strokeLinecap="round"/>
        <path d="M21 14H24" stroke="var(--text-muted)" strokeWidth="1" strokeLinecap="round"/>
      </svg>
    ),
    title: 'Local AI Models',
    titleHi: 'स्थानीय AI',
    description: 'Runs Qwen3 1.7B and Qwen2.5 3B models entirely on your CPU — no cloud, no API keys needed.',
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
        <path d="M14 3C14 3 17 8 17 14C17 20 14 25 14 25" stroke="var(--saffron)" strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M8 6C8 6 11 10 11 14C11 18 8 22 8 22" stroke="var(--gold-foil)" strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M20 6C20 6 23 10 23 14C23 18 20 22 20 22" stroke="var(--gold-foil)" strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M3 11C3 11 6 12.5 6 14C6 15.5 3 17 3 17" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M25 11C25 11 28 12.5 28 14C28 15.5 25 17 25 17" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    ),
    title: 'Natural Voices',
    titleHi: 'प्राकृतिक स्वर',
    description: 'Kokoro TTS renders two distinct speaker voices with natural cadence and intonation.',
  },
];

const FeatureCards: React.FC = () => {
  return (
    <section className="features-section" id="features">
      <div className="features-inner">
        <div className="features-header">
          <span className="features-kicker devanagari-accent">कैसे काम करता है</span>
          <h3 className="features-title">How it works</h3>
        </div>
        <div className="features-grid">
          {features.map((feature, index) => (
            <article
              key={index}
              className="feature-card"
              style={{ animationDelay: `${index * 0.15}s` }}
            >
              <div className="feature-icon">{feature.icon}</div>
              <h4 className="feature-title">{feature.title}</h4>
              <span className="feature-title-hi devanagari-accent">{feature.titleHi}</span>
              <p className="feature-desc">{feature.description}</p>
              <div className="feature-step-badge" aria-hidden="true">
                {index + 1}
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeatureCards;
