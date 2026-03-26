import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './UserDashboard.css';

function UserDashboard() {
  const navigate = useNavigate();
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
          <div className="header-brand">NEWSNEXUS</div>
          <h1 className="header-title">Your Dashboard</h1>
          <p className="header-subtitle">
            {user ? `Welcome, ${user.name || user.email}` : 'Curated by autonomous AI agents for serious aspirants'}
          </p>
        </div>
        <div className="header-actions">
          <button className="btn-logout" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>

      <div className="user-dashboard-content">
        <div className="dashboard-main">
          <div className="dashboard-card">
            <h2 className="card-title">Daily Intelligence Brief</h2>
            <p className="card-description">
              Generate a personalized news digest with AI-curated articles and MCQs mapped to GS Papers
            </p>

            {error && <div className="error-message">{error}</div>}

            {sessionStatus?.status === 'ready' ? (
              <div className="session-ready">
                <div className="ready-icon">✓</div>
                <p className="ready-text">Your latest session is ready!</p>
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
                  View Session
                </button>
              </div>
            ) : (
              <div className="no-session">
                <div className="no-session-icon">📰</div>
                <p className="no-session-text">No active session yet</p>
                <button 
                  className="btn-trigger"
                  onClick={handleTriggerPipeline}
                  disabled={triggering}
                >
                  {triggering ? 'Generating...' : 'Generate New Session'}
                </button>
                {triggering && (
                  <p className="trigger-note">
                    This may take a few minutes. You'll be redirected when ready.
                  </p>
                )}
              </div>
            )}
          </div>

          <div className="dashboard-info">
            <div className="info-card">
              <h3 className="info-title">How it works</h3>
              <ol className="info-list">
                <li>Click "Generate New Session" to start</li>
                <li>AI curates relevant news articles</li>
                <li>Practice with GS Paper-mapped MCQs</li>
                <li>Learn with detailed insights and explanations</li>
              </ol>
            </div>

            <div className="info-card">
              <h3 className="info-title">Quick Actions</h3>
              <div className="action-buttons">
                <button 
                  className="action-button"
                  onClick={handleTriggerPipeline}
                  disabled={triggering}
                >
                  {triggering ? 'Running Pipeline...' : 'Run Pipeline'}
                </button>
                <button 
                  className="action-button"
                  onClick={() => navigate('/interests')}
                >
                  Update Interests
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
