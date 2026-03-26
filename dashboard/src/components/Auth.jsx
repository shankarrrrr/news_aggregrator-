import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Auth.css';

function Auth({ mode = 'login' }) {
  const navigate = useNavigate();
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
          <div className="header-brand">NEWSNEXUS</div>
          <h1 className="header-title">{isSignup ? 'Create Account' : 'Welcome Back'}</h1>
          <p className="header-subtitle">
            {isSignup ? 'Sign up to start your UPSC journey' : 'Curated by autonomous AI agents for serious aspirants'}
          </p>
        </div>
      </header>

      <div className="auth-content">
        <div className="auth-card">
          <form onSubmit={handleSubmit} className="auth-form">
            {isSignup && (
              <div className="form-group">
                <label htmlFor="name">Name (Optional)</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Your name"
                />
              </div>
            )}

            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="your@email.com"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                required
                minLength={6}
              />
              {isSignup && (
                <small className="form-hint">At least 6 characters</small>
              )}
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="auth-submit" disabled={loading}>
              {loading ? 'Please wait...' : (isSignup ? 'Sign Up' : 'Login')}
            </button>
          </form>

          <div className="auth-footer">
            {isSignup ? (
              <p>
                Already have an account?{' '}
                <span className="auth-link" onClick={() => navigate('/login')}>
                  Login
                </span>
              </p>
            ) : (
              <p>
                Don't have an account?{' '}
                <span className="auth-link" onClick={() => navigate('/signup')}>
                  Sign up
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
