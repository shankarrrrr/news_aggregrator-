import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import LanguageSelector from './LanguageSelector';
import './UserDashboard.css';

function UserDashboard() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [user, setUser] = useState(null);
  const [sessionStatus, setSessionStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchUserData();
    fetchSessionStatus();
  }, []);

  const fetchUserData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch user data');
      }

      const data = await response.json();
      setUser(data);
    } catch (err) {
      console.error('Error fetching user:', err);
      if (err.message.includes('401')) {
        localStorage.removeItem('token');
        navigate('/login');
      }
    }
  };

  const fetchSessionStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/user/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch session status');
      }

      const data = await response.json();
      setSessionStatus(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerPipeline = async () => {
    setTriggering(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/user/trigger-pipeline', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to trigger pipeline');
      }

      const data = await response.json();
      navigate(`/session/${data.dashboard_token}`);

    } catch (err) {
      setError(err.message);
    } finally {
      setTriggering(false);
    }
  };

  const handleViewSession = () => {
    if (sessionStatus && sessionStatus.session_token) {
      navigate(`/session/${sessionStatus.session_token}`);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  if (loading) {
    return (
      <div className="user-dashboard-page">
        <div className="loading-container">
          <div className="loading-dots">···</div>
        </div>
      </div>
    );
  }

  return (
    <div className="user-dashboard-page">
      <header className="header">
        <div className="header-content">
          <div className="header-brand">{t('app.name')}</div>
          <h1 className="header-title">{t('dashboard.your_dashboard')}</h1>
          <p className="header-subtitle">
            {user ? t('dashboard.welcome', { name: user.name || user.email }) : t('app.subtitle')}
          </p>
        </div>
        <div className="header-actions">
          <LanguageSelector />
          <button className="btn-logout" onClick={handleLogout} style={{ marginLeft: '10px' }}>
            {t('dashboard.logout')}
          </button>
        </div>
      </header>

      <div className="user-dashboard-content">
        <div className="dashboard-main">
          <div className="dashboard-card">
            <h2 className="card-title">{t('dashboard.daily_brief_title')}</h2>
            <p className="card-description">
              {t('dashboard.daily_brief_desc')}
            </p>

            {error && <div className="error-message">{error}</div>}

            {sessionStatus?.status === 'ready' ? (
              <div className="session-ready">
                <div className="ready-icon">✓</div>
                <p className="ready-text">{t('dashboard.session_ready')}</p>
                <p className="ready-date">
                  {new Date(sessionStatus.session_date).toLocaleDateString('en-US', { 
                    weekday: 'long', 
                    day: 'numeric', 
                    month: 'long', 
                    year: 'numeric' 
                  }).toUpperCase()}
                </p>
                <button 
                  className="btn-view-session"
                  onClick={handleViewSession}
                >
                  {t('dashboard.view_session')}
                </button>
              </div>
            ) : (
              <div className="no-session">
                <div className="no-session-icon">📰</div>
                <p className="no-session-text">{t('dashboard.no_session')}</p>
                <button 
                  className="btn-trigger"
                  onClick={handleTriggerPipeline}
                  disabled={triggering}
                >
                  {triggering ? t('dashboard.generating') : t('dashboard.generate_session')}
                </button>
                {triggering && (
                  <p className="trigger-note">
                    {t('dashboard.trigger_note')}
                  </p>
                )}
              </div>
            )}
          </div>

          <div className="dashboard-info">
            <div className="info-card">
              <h3 className="info-title">{t('dashboard.how_it_works')}</h3>
              <ol className="info-list">
                <li>{t('dashboard.step1')}</li>
                <li>{t('dashboard.step2')}</li>
                <li>{t('dashboard.step3')}</li>
                <li>{t('dashboard.step4')}</li>
              </ol>
            </div>

            <div className="info-card">
              <h3 className="info-title">{t('dashboard.quick_actions')}</h3>
              <div className="action-buttons">
                <button 
                  className="action-button"
                  onClick={handleTriggerPipeline}
                  disabled={triggering}
                >
                  {triggering ? t('dashboard.running_pipeline') : t('dashboard.run_pipeline')}
                </button>
                <button 
                  className="action-button"
                  onClick={() => navigate('/interests')}
                >
                  {t('dashboard.update_interests')}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UserDashboard;
