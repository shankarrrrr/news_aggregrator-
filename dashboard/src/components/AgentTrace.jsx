import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import './AgentTrace.css';

const API_BASE = 'http://localhost:8000';

const AgentTrace = () => {
  const { sessionId } = useParams();
  const [trace, setTrace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTrace();
    // Poll every 2 seconds for updates
    const interval = setInterval(fetchTrace, 2000);
    return () => clearInterval(interval);
  }, [sessionId]);

  const fetchTrace = async () => {
    try {
      const response = await fetch(`${API_BASE}/admin/trace/${sessionId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch trace');
      }
      const data = await response.json();
      setTrace(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  if (loading && !trace) {
    return (
      <div className="trace-container">
        <div className="loading">Loading agent trace...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="trace-container">
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  const getStepStatus = (step) => {
    if (step.status === 'completed') return 'completed';
    if (step.status === 'in_progress') return 'in-progress';
    if (step.status === 'failed') return 'failed';
    return 'pending';
  };

  const getStepIcon = (step) => {
    if (step.status === 'completed') return '✓';
    if (step.status === 'in_progress') return '⟳';
    if (step.status === 'failed') return '✗';
    return '○';
  };

  return (
    <div className="trace-container">
      <header className="trace-header">
        <div className="trace-brand">NEWSNEXUS</div>
        <h1 className="trace-title">Agent Reasoning Trace</h1>
        <p className="trace-subtitle">Session {sessionId}</p>
      </header>

      <div className="trace-content">
        {/* Pipeline Status */}
        <div className="trace-section">
          <div className="section-header">
            <h2 className="section-title">Pipeline Status</h2>
            <span className={`status-badge status-${trace.status}`}>
              {trace.status}
            </span>
          </div>
          <div className="pipeline-stats">
            <div className="stat-item">
              <span className="stat-label">Started</span>
              <span className="stat-value">{new Date(trace.started_at).toLocaleString()}</span>
            </div>
            {trace.completed_at && (
              <div className="stat-item">
                <span className="stat-label">Completed</span>
                <span className="stat-value">{new Date(trace.completed_at).toLocaleString()}</span>
              </div>
            )}
            <div className="stat-item">
              <span className="stat-label">Duration</span>
              <span className="stat-value">{trace.duration || 'In progress...'}</span>
            </div>
          </div>
        </div>

        {/* Agent Steps */}
        <div className="trace-section">
          <h2 className="section-title">Agent Reasoning Steps</h2>
          <div className="steps-timeline">
            {trace.steps.map((step, idx) => (
              <div key={idx} className={`step-item ${getStepStatus(step)}`}>
                <div className="step-icon">{getStepIcon(step)}</div>
                <div className="step-content">
                  <div className="step-header">
                    <h3 className="step-name">{step.name}</h3>
                    <span className="step-time">{step.duration || '...'}</span>
                  </div>
                  <p className="step-description">{step.description}</p>
                  
                  {step.details && (
                    <div className="step-details">
                      {step.details.articles_fetched && (
                        <div className="detail-item">
                          <span className="detail-label">Articles Fetched:</span>
                          <span className="detail-value">{step.details.articles_fetched}</span>
                        </div>
                      )}
                      {step.details.articles_analyzed && (
                        <div className="detail-item">
                          <span className="detail-label">Articles Analyzed:</span>
                          <span className="detail-value">{step.details.articles_analyzed}</span>
                        </div>
                      )}
                      {step.details.articles_filtered && (
                        <div className="detail-item">
                          <span className="detail-label">High-Quality Articles:</span>
                          <span className="detail-value">{step.details.articles_filtered}</span>
                        </div>
                      )}
                      {step.details.mcqs_generated && (
                        <div className="detail-item">
                          <span className="detail-label">MCQs Generated:</span>
                          <span className="detail-value">{step.details.mcqs_generated}</span>
                        </div>
                      )}
                      {step.details.email_sent !== undefined && (
                        <div className="detail-item">
                          <span className="detail-label">Email Sent:</span>
                          <span className="detail-value">{step.details.email_sent ? 'Yes' : 'No'}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {step.reasoning && (
                    <div className="step-reasoning">
                      <div className="reasoning-label">Agent Reasoning:</div>
                      <p className="reasoning-text">{step.reasoning}</p>
                    </div>
                  )}

                  {step.articles && step.articles.length > 0 && (
                    <div className="step-articles">
                      <div className="articles-label">Articles Processed:</div>
                      <div className="articles-list">
                        {step.articles.map((article, aIdx) => (
                          <div key={aIdx} className="article-item">
                            <div className="article-title">{article.title}</div>
                            <div className="article-meta">
                              <span className="article-source">{article.source}</span>
                              <span className="article-category">{article.category}</span>
                              {article.prelims_score && (
                                <span className="article-score">
                                  P: {article.prelims_score}/10 | M: {article.mains_score}/10
                                </span>
                              )}
                            </div>
                            {article.reasoning && (
                              <div className="article-reasoning">
                                <strong>Why this article?</strong> {article.reasoning}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {step.error && (
                    <div className="step-error">
                      <strong>Error:</strong> {step.error}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Summary */}
        {trace.status === 'completed' && trace.summary && (
          <div className="trace-section">
            <h2 className="section-title">Summary</h2>
            <div className="summary-grid">
              <div className="summary-item">
                <div className="summary-number">{trace.summary.total_articles}</div>
                <div className="summary-label">Articles Fetched</div>
              </div>
              <div className="summary-item">
                <div className="summary-number">{trace.summary.high_quality_articles}</div>
                <div className="summary-label">High-Quality (≥5)</div>
              </div>
              <div className="summary-item">
                <div className="summary-number">{trace.summary.total_mcqs}</div>
                <div className="summary-label">MCQs Generated</div>
              </div>
              <div className="summary-item">
                <div className="summary-number">{trace.summary.categories}</div>
                <div className="summary-label">Categories Covered</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentTrace;
