import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import LanguageSelector from './LanguageSelector';
import './Landing.css';

function Landing() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div className="landing-page">
      <header className="header">
        <div className="header-content">
          <div className="header-brand">{t('app.name')}</div>
          <h1 className="header-title">{t('app.tagline')}</h1>
          <p className="header-subtitle">{t('app.subtitle')}</p>
        </div>
        <div className="header-actions">
          <LanguageSelector />
        </div>
      </header>

      <div className="landing-content">
        <div className="landing-hero">
          <h2 className="hero-title">{t('landing.hero_title')}</h2>
          <p className="hero-description">
            {t('landing.hero_description')}
          </p>
        </div>

        <div className="landing-features">
          <div className="feature-card">
            <div className="feature-icon">📰</div>
            <h3 className="feature-title">{t('landing.feature_news_title')}</h3>
            <p className="feature-description">{t('landing.feature_news_desc')}</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3 className="feature-title">{t('landing.feature_mcq_title')}</h3>
            <p className="feature-description">{t('landing.feature_mcq_desc')}</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📚</div>
            <h3 className="feature-title">{t('landing.feature_insights_title')}</h3>
            <p className="feature-description">{t('landing.feature_insights_desc')}</p>
          </div>
        </div>

        <div className="landing-actions">
          <button 
            className="btn-primary"
            onClick={() => navigate('/signup')}
          >
            {t('landing.get_started')}
          </button>
          <button 
            className="btn-secondary"
            onClick={() => navigate('/login')}
          >
            {t('landing.login')}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Landing;
