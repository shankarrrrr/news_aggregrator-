import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import LanguageSelector from './LanguageSelector';
import './Dashboard.css';

const API_BASE = 'http://localhost:8000';

const Dashboard = () => {
  const { token } = useParams();
  const { t, i18n } = useTranslation();
  const [session, setSession] = useState(null);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [currentMCQ, setCurrentMCQ] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);
  const [attemptResult, setAttemptResult] = useState(null);
  const [results, setResults] = useState(null);
  const [performance, setPerformance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showLearningInsights, setShowLearningInsights] = useState(false);

  // Fetch session on mount
  useEffect(() => {
    fetchSession();
  }, [token]);

  // Poll for session status if pending
  useEffect(() => {
    let pollInterval;
    
    if (error && error.includes('being prepared')) {
      console.log('[Dashboard] Session pending, starting polling...');
      pollInterval = setInterval(() => {
        console.log('[Dashboard] Polling for session status...');
        fetchSession();
      }, 5000); // Poll every 5 seconds
    }
    
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [error]);

  // Helper function to translate category names
  const translateCategory = (category) => {
    const categoryMap = {
      'Polity': 'categories.polity',
      'Economy': 'categories.economy',
      'International Relations': 'categories.international_relations',
      'Environment': 'categories.environment',
      'Science & Tech': 'categories.science_tech',
      'History & Culture': 'categories.history_culture',
      'Security & Defence': 'categories.security_defence',
      'Social Issues': 'categories.social_issues'
    };
    return t(categoryMap[category] || category);
  };

  const fetchSession = async (autoSelectNext = true) => {
    try {
      console.log('[Dashboard] Fetching session with token:', token);
      const response = await fetch(`${API_BASE}/session/${token}?lang=${i18n.language}`);
      if (!response.ok) throw new Error('Session not found');
      const data = await response.json();
      
      console.log('[Dashboard] Session data received:', data);
      console.log('[Dashboard] Session status:', data.status);
      console.log('[Dashboard] Articles count:', data.articles?.length);
      
      if (data.status === 'pending') {
        setError(t('session.preparing'));
        setLoading(false);
        return;
      }
      
      // Clear error if session is ready
      setError(null);
      
      // Log each article to check for title issues
      data.articles?.forEach((article, idx) => {
        console.log(`[Dashboard] Article ${idx}:`, {
          id: article.id,
          title: article.title,
          titleLength: article.title?.length,
          category: article.category,
          source: article.source
        });
      });
      
      setSession(data);
      
      // Check if all completed
      const allAttempted = data.articles.every(a => a.attempted);
      if (allAttempted) {
        fetchResults();
      } else if (autoSelectNext) {
        // Only auto-select first unattempted article if autoSelectNext is true
        const firstUnattempted = data.articles.find(a => !a.attempted);
        if (firstUnattempted) {
          console.log('[Dashboard] Selecting first unattempted article:', firstUnattempted.title);
          selectArticle(firstUnattempted);
        }
      }
      
      setLoading(false);
    } catch (err) {
      console.error('[Dashboard] Error fetching session:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const selectArticle = async (article) => {
    console.log('[Dashboard] Selecting article:', {
      id: article.id,
      title: article.title,
      category: article.category
    });
    
    setSelectedArticle(article);
    setSelectedOption(null);
    setAttemptResult(null);
    setCanSubmit(true); // Reset submit flag
    
    try {
      const response = await fetch(`${API_BASE}/session/${token}/mcq/${article.id}?lang=${i18n.language}`);
      const mcq = await response.json();
      console.log('[Dashboard] MCQ loaded:', {
        id: mcq.id,
        question: mcq.question?.substring(0, 50) + '...',
        gs_paper: mcq.gs_paper
      });
      setCurrentMCQ(mcq);
    } catch (err) {
      console.error('[Dashboard] Failed to fetch MCQ:', err);
    }
  };

  const [canSubmit, setCanSubmit] = useState(true);

  const handleOptionSelect = (option, event) => {
    console.log('[Dashboard] handleOptionSelect called with option:', option);
    
    if (event) {
      event.preventDefault();
      event.stopPropagation();
      console.log('[Dashboard] Event prevented and stopped');
    }
    
    if (attemptResult) {
      console.log('[Dashboard] Option select blocked - already answered');
      return;
    }
    
    console.log('[Dashboard] Setting selected option to:', option);
    setSelectedOption(option);
    
    // Prevent immediate submission with a very short delay
    setCanSubmit(false);
    setTimeout(() => {
      setCanSubmit(true);
      console.log('[Dashboard] Submit now enabled');
    }, 50); // Reduced to 50ms - just enough to prevent accidental double-click
    
    console.log('[Dashboard] Option selection complete - NOT submitting');
  };

  const submitAttempt = async () => {
    console.log('[Dashboard] submitAttempt called');
    console.log('[Dashboard] attemptResult:', attemptResult);
    console.log('[Dashboard] selectedOption:', selectedOption);
    console.log('[Dashboard] canSubmit:', canSubmit);
    
    if (!canSubmit) {
      console.log('[Dashboard] Submit blocked - too soon after selection');
      return;
    }
    
    if (attemptResult || !selectedOption) {
      console.log('[Dashboard] Submit blocked - already answered or no option selected');
      return;
    }
    
    console.log('[Dashboard] Submitting attempt for article:', selectedArticle.id, 'option:', selectedOption);
    
    try {
      const response = await fetch(`${API_BASE}/session/${token}/attempt?lang=${i18n.language}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          article_id: selectedArticle.id,
          mcq_id: currentMCQ.id,
          selected_option: selectedOption,
          time_taken_seconds: 0
        })
      });
      
      const result = await response.json();
      console.log('[Dashboard] Attempt result:', result);
      setAttemptResult(result);
      
      // Refresh session to update attempted status, but don't auto-select next
      setTimeout(() => {
        console.log('[Dashboard] Refreshing session after attempt');
        fetchSession(false); // Pass false to prevent auto-selecting next article
      }, 500);
    } catch (err) {
      console.error('[Dashboard] Failed to submit attempt:', err);
    }
  };

  const fetchResults = async () => {
    try {
      const [resultsRes, perfRes] = await Promise.all([
        fetch(`${API_BASE}/session/${token}/results`),
        fetch(`${API_BASE}/performance`)
      ]);
      
      if (!resultsRes.ok) {
        console.error('Failed to fetch results');
        return;
      }
      
      const resultsData = await resultsRes.json();
      const perfData = perfRes.ok ? await perfRes.json() : [];
      
      setResults(resultsData);
      setPerformance(perfData);
    } catch (err) {
      console.error('Failed to fetch results:', err);
    }
  };

  const goToNextQuestion = () => {
    console.log('[Dashboard] Going to next question');
    
    // Clear current state
    setAttemptResult(null);
    setSelectedOption(null);
    setCanSubmit(true); // Reset submit flag
    
    // Find next unattempted article
    const nextUnattempted = session.articles.find(a => !a.attempted && a.id !== selectedArticle.id);
    
    if (nextUnattempted) {
      console.log('[Dashboard] Found next unattempted article:', nextUnattempted.title);
      selectArticle(nextUnattempted);
    } else {
      console.log('[Dashboard] No more unattempted articles, staying on current');
      // Stay on current article, just clear the attempt result
      setCurrentMCQ(null);
      // Reload the current article's MCQ
      selectArticle(selectedArticle);
    }
  };

  // Format explanation text into structured format
  const formatExplanation = (text) => {
    if (!text) return null;
    
    // Split by sentences or common delimiters
    const sentences = text.split(/(?<=[.!?])\s+/);
    
    // If it's a single sentence or very short, return as is
    if (sentences.length <= 1 || text.length < 100) {
      return <p className="explanation-text">{text}</p>;
    }
    
    // Otherwise, format as bullet points
    return (
      <ul className="explanation-list">
        {sentences.map((sentence, idx) => (
          sentence.trim() && <li key={idx}>{sentence.trim()}</li>
        ))}
      </ul>
    );
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-dots">···</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <header className="header">
          <div className="header-content">
            <div className="header-brand">{t('app.name')}</div>
            <h1 className="header-title">{t('app.tagline')}</h1>
            <p className="header-subtitle">{t('app.subtitle')}</p>
          </div>
          <div className="header-actions" style={{ position: 'absolute', top: '20px', right: '20px' }}>
            <LanguageSelector />
          </div>
        </header>
        <div className="error-content">
          <div className="error-icon">⏳</div>
          <h1 className="error-title">{error}</h1>
          <p className="error-subtitle">
            {error.includes('prepared') || error.includes('preparing')
              ? 'The AI agents are analyzing articles and generating questions. This page will automatically refresh when ready.'
              : 'Please check your link and try again.'}
          </p>
          {(error.includes('prepared') || error.includes('preparing')) && (
            <div className="loading-dots" style={{ marginTop: '24px' }}>···</div>
          )}
        </div>
      </div>
    );
  }

  if (results) {
    return <ResultsScreen results={results} performance={performance} />;
  }

  const attemptedCount = session.articles.filter(a => a.attempted).length;
  const correctCount = session.articles.filter(a => a.is_correct).length;
  const scorePercent = attemptedCount > 0 ? Math.round((correctCount / attemptedCount) * 100) : 0;

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="header-brand">{t('app.name')}</div>
          <h1 className="header-title">{t('app.tagline')}</h1>
          <p className="header-subtitle">{t('app.subtitle')}</p>
          <div className="header-date">{new Date(session.session_date).toLocaleDateString('en-US', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).toUpperCase()}</div>
        </div>
        <div className="header-actions" style={{ position: 'absolute', top: '20px', right: '20px' }}>
          <LanguageSelector />
        </div>
      </header>
      <div className="header-coverage">
        <div className="coverage-content">
          <span className="coverage-label">{t('session.todays_coverage')}:</span>
          {Object.entries(session.coverage_summary).map(([cat, count], idx) => (
            <span key={cat}>
              {idx > 0 && ' | '}
              <strong>{count}</strong> {translateCategory(cat)}
            </span>
          ))}
        </div>
      </div>

      {/* Focus Note */}
      {session.focus_note && (
        <div className="focus-note">
          💡 {t('session.todays_focus')}: {session.focus_note}
        </div>
      )}

      {/* Main Content */}
      <div className="main-content">
        {/* Sidebar */}
        <aside className="sidebar">
          {session.articles.map((article, idx) => (
            <div
              key={article.id}
              className={`article-card ${selectedArticle?.id === article.id ? 'active' : ''} ${article.attempted ? 'attempted' : ''}`}
              onClick={() => selectArticle(article)}
            >
              <div className="article-header">
                <span className="article-category">{translateCategory(article.category)}</span>
                <span className="article-source">{article.source}</span>
              </div>
              <div className="article-title">
                {article.attempted && (
                  <span className={`status-icon ${article.is_correct ? 'correct' : 'wrong'}`}>
                    {article.is_correct ? '✓' : '✗'}
                  </span>
                )}
                {article.title || '[No Title]'}
              </div>
              <div className="article-relevance">
                <span className="relevance-item">
                  <span className="relevance-label">{t('session.prelims').toUpperCase()}</span>
                  <span className="relevance-value">{article.prelims_score}/10</span>
                </span>
                <span className="relevance-item">
                  <span className="relevance-label">{t('session.mains').toUpperCase()}</span>
                  <span className="relevance-value">{article.mains_score}/10</span>
                </span>
              </div>
            </div>
          ))}
        </aside>

        {/* MCQ Panel */}
        <main className="mcq-panel">
          {currentMCQ ? (
            <div className="mcq-card">
              <div className="mcq-header">
                <span className="mcq-source">{selectedArticle.source}</span>
                <span className="mcq-category">{translateCategory(selectedArticle.category)}</span>
              </div>
              <div className="mcq-divider"></div>
              
              {currentMCQ.gs_paper && (
                <div className="gs-paper-badge">
                  <span className="gs-paper-icon">📚</span>
                  <span className="gs-paper-text">{currentMCQ.gs_paper}</span>
                </div>
              )}
              
              <h2 className="mcq-question">{currentMCQ.question}</h2>
              
              <div className="mcq-options">
                {['A', 'B', 'C', 'D'].map(letter => (
                  <div
                    key={letter}
                    className={`option-button ${
                      selectedOption === letter ? 'selected' : ''
                    } ${
                      attemptResult && attemptResult.correct_option === letter ? 'correct-answer' : ''
                    } ${
                      attemptResult && selectedOption === letter && !attemptResult.is_correct ? 'wrong-answer' : ''
                    } ${
                      attemptResult ? 'disabled' : ''
                    }`}
                    onClick={(e) => {
                      console.log('[Dashboard] Option div clicked:', letter);
                      e.preventDefault();
                      e.stopPropagation();
                      if (!attemptResult) {
                        console.log('[Dashboard] Calling handleOptionSelect for:', letter);
                        handleOptionSelect(letter, e);
                      } else {
                        console.log('[Dashboard] Click ignored - already answered');
                      }
                    }}
                    role="button"
                    tabIndex={attemptResult ? -1 : 0}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !attemptResult) {
                        e.preventDefault();
                        handleOptionSelect(letter, e);
                      }
                    }}
                  >
                    <span className="option-letter" onClick={(e) => e.stopPropagation()}>{letter}</span>
                    <span className="option-text" onClick={(e) => e.stopPropagation()}>{currentMCQ[`option_${letter.toLowerCase()}`]}</span>
                  </div>
                ))}
              </div>
              
              {!attemptResult && selectedOption && (
                <div className="submit-button-container">
                  <button 
                    type="button"
                    className="submit-button" 
                    style={{ opacity: canSubmit ? 1 : 0.6, transition: 'opacity 0.05s' }}
                    disabled={!canSubmit}
                    onClick={(e) => {
                      console.log('[Dashboard] Submit button clicked');
                      e.preventDefault();
                      e.stopPropagation();
                      if (canSubmit) {
                        submitAttempt();
                      }
                    }}
                  >
                    {t('session.submit_answer')}
                  </button>
                </div>
              )}
              
              {attemptResult && (
                <div className="explanation-box">
                  <div className="explanation-label">{t('session.explanation').toUpperCase()}</div>
                  {formatExplanation(attemptResult.explanation)}
                  
                  {attemptResult.learning_insight && (
                    <div className="learning-insight">
                      <div className="insight-icon">💡</div>
                      <div className="insight-content">
                        <div className="insight-label">{t('session.learning_insight').toUpperCase()}</div>
                        <p className="insight-text">{attemptResult.learning_insight}</p>
                      </div>
                    </div>
                  )}
                  
                  <button 
                    type="button"
                    className="next-button" 
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      goToNextQuestion();
                    }}
                  >
                    {t('session.next_article')} →
                  </button>
                </div>
              )}
            </div>
          ) : selectedArticle ? (
            <div className="mcq-placeholder">
              <p>{t('common.loading')}</p>
            </div>
          ) : (
            <div className="mcq-placeholder">
              <p>{t('session.select_option')}</p>
            </div>
          )}
        </main>
      </div>

      {/* Stats Bar */}
      <div className="stats-bar">
        <span>Progress <strong>{attemptedCount}</strong>/{session.articles.length}</span>
        <span className="stat-separator">·</span>
        <span>Correct <strong className="stat-highlight">{correctCount}</strong></span>
        <span className="stat-separator">·</span>
        <span>Score <strong className="stat-highlight">{scorePercent}%</strong></span>
      </div>
    </div>
  );
};

const ResultsScreen = ({ results, performance }) => {
  const { t } = useTranslation();
  
  // Safety checks for undefined data
  if (!results || !results.per_question) {
    return (
      <div className="loading-container">
        <div className="loading-dots">{t('common.loading')}</div>
      </div>
    );
  }

  // Group questions by GS Paper
  const questionsByGS = {};
  results.per_question.forEach(q => {
    const gsPaper = q.gs_paper || 'General';
    if (!questionsByGS[gsPaper]) {
      questionsByGS[gsPaper] = [];
    }
    questionsByGS[gsPaper].push(q);
  });

  return (
    <div className="results-screen">
      <header className="header">
        <div className="header-content">
          <div className="header-brand">{t('app.name')}</div>
          <h1 className="header-title">{t('results.title')}</h1>
          <p className="header-subtitle">Your UPSC preparation insights</p>
        </div>
        <div className="header-actions" style={{ position: 'absolute', top: '20px', right: '20px' }}>
          <LanguageSelector />
        </div>
      </header>

      <div className="results-content">
        <div className="results-score">
          <div className="score-big">{results.total_correct}/{results.total_questions}</div>
          <div className="score-subtitle">{t('results.correct_answers', { correct: results.total_correct, total: results.total_questions })}</div>
          <div className="score-percent">{results.score_percent}%</div>
        </div>

        <div className="results-divider"></div>

        {/* GS Paper-wise Analysis */}
        <div className="gs-analysis-section">
          <h3 className="results-section-title">{t('results.performance_by_category')}</h3>
          {Object.entries(questionsByGS).map(([gsPaper, questions]) => {
            const correct = questions.filter(q => q.is_correct).length;
            const total = questions.length;
            const percentage = Math.round((correct / total) * 100);
            
            return (
              <div key={gsPaper} className="gs-paper-analysis">
                <div className="gs-paper-header">
                  <span className="gs-paper-name">{gsPaper}</span>
                  <span className="gs-paper-stats">{correct}/{total} understood ({percentage}%)</span>
                </div>
                <div className="gs-paper-bar-bg">
                  <div 
                    className="gs-paper-bar-fill" 
                    style={{ width: `${percentage}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="results-divider"></div>

        <div className="results-table-container">
          <h3 className="results-section-title">{t('results.review_answers')}</h3>
          <table className="results-table">
            <thead>
              <tr>
                <th>Article</th>
                <th>{t('results.category')}</th>
                <th>{t('session.gs_paper')}</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {results.per_question.map((q, idx) => (
                <tr key={idx}>
                  <td className="article-cell">{q.article_title}</td>
                  <td className="category-cell">{q.category}</td>
                  <td className="gs-paper-cell">{q.gs_paper || 'General'}</td>
                  <td className="correct-cell">
                    <span className={q.is_correct ? 'correct-icon' : 'wrong-icon'}>
                      {q.is_correct ? `✓ ${t('session.correct')}` : `✗ ${t('session.incorrect')}`}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {results.weak_topics && results.weak_topics.length > 0 && (
          <div className="weak-topics">
            <h3 className="weak-topics-title">AREAS TO FOCUS</h3>
            <ul className="weak-topics-list">
              {results.weak_topics.map(topic => (
                <li key={topic}>— {topic}</li>
              ))}
            </ul>
          </div>
        )}

        {performance && performance.length > 0 && (
          <div className="performance-section">
            <h3 className="results-section-title">{t('results.performance_by_category')}</h3>
            <div className="performance-bars">
              {performance.map(perf => (
                <div key={perf.category} className="performance-bar-item">
                  <div className="performance-label">
                    <span className="performance-category">{perf.category}</span>
                    <span className="performance-accuracy">{perf.accuracy_percent}%</span>
                  </div>
                  <div className="performance-bar-bg">
                    <div 
                      className="performance-bar-fill" 
                      style={{ width: `${perf.accuracy_percent}%` }}
                    ></div>
                  </div>
                  <div className="performance-stats">
                    {perf.total_correct}/{perf.total_attempted} {t('results.questions')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
