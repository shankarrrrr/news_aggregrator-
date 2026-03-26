import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Landing.css';

function Landing() {
  const navigate = useNavigate();

  return (
    <div className="landing-page">
      <header className="header">
        <div className="header-content">
          <div className="header-brand">NEWSNEXUS</div>
          <h1 className="header-title">UPSC Daily Intelligence</h1>
          <p className="header-subtitle">Curated by autonomous AI agents for serious aspirants</p>
        </div>
      </header>

      <div className="landing-content">
        <div className="landing-hero">
          <h2 className="hero-title">Your AI-Powered UPSC Preparation Platform</h2>
          <p className="hero-description">
            Daily curated news, intelligent MCQs, and personalized learning insights mapped to GS Papers
          </p>
        </div>

        <div className="landing-features">
          <div className="feature-card">
            <div className="feature-icon">📰</div>
            <h3 className="feature-title">Curated News</h3>
            <p className="feature-description">Daily selection of UPSC-relevant articles from PIB, The Hindu, and Indian Express</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3 className="feature-title">Smart MCQs</h3>
            <p className="feature-description">AI-generated questions mapped to GS Papers with detailed explanations</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📚</div>
            <h3 className="feature-title">Learning Insights</h3>
            <p className="feature-description">Key takeaways and concepts to remember for better retention</p>
          </div>
        </div>

        <div className="landing-actions">
          <button 
            className="btn-primary"
            onClick={() => navigate('/signup')}
          >
            Get Started
          </button>
          <button 
            className="btn-secondary"
            onClick={() => navigate('/login')}
          >
            Login
          </button>
        </div>
      </div>
    </div>
  );
}

export default Landing;
