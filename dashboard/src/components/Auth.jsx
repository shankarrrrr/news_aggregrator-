import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import LanguageSelector from './LanguageSelector';
import './Auth.css';

function Auth({ mode = 'login' }) {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const isSignup = mode === 'signup';

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isSignup ? '/auth/signup' : '/auth/login';
      const body = isSignup 
        ? { email: formData.email, password: formData.password, name: formData.name }
        : { email: formData.email, password: formData.password };

      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      localStorage.setItem('token', data.access_token);

      if (isSignup) {
        navigate('/interests');
      } else {
        navigate('/user-dashboard');
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <header className="header">
        <div className="header-content">
          <div className="header-brand">{t('app.name')}</div>
          <h1 className="header-title">{isSignup ? t('auth.create_account') : t('auth.welcome_back')}</h1>
          <p className="header-subtitle">
            {isSignup ? t('auth.signup_subtitle') : t('app.subtitle')}
          </p>
        </div>
        <div className="header-actions" style={{ position: 'absolute', top: '20px', right: '20px' }}>
          <LanguageSelector />
        </div>
      </header>

      <div className="auth-content">
        <div className="auth-card">
          <form onSubmit={handleSubmit} className="auth-form">
            {isSignup && (
              <div className="form-group">
                <label htmlFor="name">{t('auth.name')}</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder={t('auth.name_placeholder')}
                />
              </div>
            )}

            <div className="form-group">
              <label htmlFor="email">{t('auth.email')}</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder={t('auth.email_placeholder')}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">{t('auth.password')}</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder={t('auth.password_placeholder')}
                required
                minLength={6}
              />
              {isSignup && (
                <small className="form-hint">{t('auth.password_hint')}</small>
              )}
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="auth-submit" disabled={loading}>
              {loading ? t('auth.please_wait') : (isSignup ? t('auth.signup') : t('auth.login'))}
            </button>
          </form>

          <div className="auth-footer">
            {isSignup ? (
              <p>
                {t('auth.already_have_account')}{' '}
                <span className="auth-link" onClick={() => navigate('/login')}>
                  {t('auth.login')}
                </span>
              </p>
            ) : (
              <p>
                {t('auth.dont_have_account')}{' '}
                <span className="auth-link" onClick={() => navigate('/signup')}>
                  {t('auth.sign_up')}
                </span>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Auth;
