import React, { useState } from 'react';
import './Admin.css';

const API_BASE = 'http://localhost:8000';

const Admin = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [error, setError] = useState(null);

  const triggerPipeline = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/admin/trigger-pipeline`, {
        method: 'POST'
      });
      
      const data = await response.json();
      setResult(data);
      
      // Refresh sessions list
      fetchSessions();
    } catch (err) {
      setError('Failed to trigger pipeline: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessions = async () => {
    try {
      const response = await fetch(`${API_BASE}/admin/sessions`);
      const data = await response.json();
      setSessions(data.sessions);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
    }
  };

  React.useEffect(() => {
    fetchSessions();
  }, []);

  return (
    <div className="admin-container">
      <header className="admin-header">
        <div className="admin-brand">NEWSNEXUS</div>
        <h1 className="admin-title">Admin Dashboard</h1>
        <p className="admin-subtitle">Manage UPSC Intelligence Sessions</p>
      </header>

      <div className="admin-content">
        <div className="admin-section">
          <h2 className="section-title">Create New Session</h2>
          <p className="section-description">
            Trigger the pipeline to fetch articles, analyze with AI, generate MCQs, and send email digest.
          </p>
          
          <button 
            className="trigger-button" 
            onClick={triggerPipeline}
            disabled={loading}
          >
            {loading ? 'Starting Pipeline...' : 'Trigger Pipeline'}
          </button>

          {result && (
            <div className="result-box">
              <div className="result-label">Pipeline Started</div>
              <div className="result-item">
                <span className="result-key">Session ID:</span>
                <span className="result-value">{result.session_id}</span>
              </div>
              <div className="result-item">
                <span className="result-key">Dashboard Token:</span>
                <span className="result-value token">{result.dashboard_token}</span>
              </div>
              <div className="result-item">
                <span className="result-key">Status:</span>
                <span className="result-value">{result.status}</span>
              </div>
              <div className="result-item">
                <span className="result-key">Dashboard URL:</span>
                <a 
                  href={`/dashboard/${result.dashboard_token}`}
                  className="dashboard-link"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open Dashboard →
                </a>
              </div>
              <p className="result-note">
                The pipeline is running in the background. Articles will be analyzed and MCQs generated. 
                Check the session status below.
              </p>
            </div>
          )}

          {error && (
            <div className="error-box">
              {error}
            </div>
          )}
        </div>

        <div className="admin-section">
          <div className="section-header">
            <h2 className="section-title">Recent Sessions</h2>
            <button className="refresh-button" onClick={fetchSessions}>
              Refresh
            </button>
          </div>

          <div className="sessions-table">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Date</th>
                  <th>Status</th>
                  <th>Token</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map(session => (
                  <tr key={session.id}>
                    <td>{session.id}</td>
                    <td>{new Date(session.session_date).toLocaleDateString()}</td>
                    <td>
                      <span className={`status-badge status-${session.status}`}>
                        {session.status}
                      </span>
                    </td>
                    <td className="token-cell">{session.dashboard_token.substring(0, 20)}...</td>
                    <td>
                      {session.status !== 'pending' && (
                        <>
                          <a 
                            href={`/dashboard/${session.dashboard_token}`}
                            className="view-link"
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            View Dashboard
                          </a>
                          <a 
                            href={`/trace/${session.id}`}
                            className="view-link"
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ marginLeft: '8px' }}
                          >
                            Agent Trace
                          </a>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="admin-section">
          <h2 className="section-title">API Documentation</h2>
          <p className="section-description">
            View the complete API documentation and test endpoints.
          </p>
          <a 
            href="http://localhost:8000/docs" 
            target="_blank" 
            rel="noopener noreferrer"
            className="docs-link"
          >
            Open API Docs →
          </a>
        </div>
      </div>
    </div>
  );
};

export default Admin;
