import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import LanguageSelector from './LanguageSelector';
import './Interests.css';

const CATEGORIES = [
  'Polity',
  'Economy',
  'International Relations',
  'Environment',
  'Science & Tech',
  'History & Culture',
  'Security & Defence',
  'Social Issues'
];

function Interests() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const toggleCategory = (category) => {
    if (selectedCategories.includes(category)) {
      setSelectedCategories(selectedCategories.filter(c => c !== category));
    } else {
      setSelectedCategories([...selectedCategories, category]);
    }
  };

  const handleSubmit = async () => {
    if (selectedCategories.length === 0) {
      setError(t('interests.save_error'));
      return;
    }

    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/user/interests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ categories: selectedCategories }),
      });

      if (!response.ok) {
        throw new Error('Failed to save interests');
      }

      navigate('/user-dashboard');

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="interests-page">
      <header className="header">
        <div className="header-content">
          <div className="header-brand">{t('app.name')}</div>
          <h1 className="header-title">{t('interests.title')}</h1>
          <p className="header-subtitle">{t('interests.subtitle')}</p>
        </div>
        <div className="header-actions" style={{ position: 'absolute', top: '20px', right: '20px' }}>
          <LanguageSelector />
        </div>
      </header>

      <div className="interests-content">
        <div className="interests-card">
          <div className="categories-grid">
            {CATEGORIES.map((category) => (
              <div
                key={category}
                className={`category-chip ${selectedCategories.includes(category) ? 'selected' : ''}`}
                onClick={() => toggleCategory(category)}
              >
                {category}
              </div>
            ))}
          </div>

          {error && <div className="error-message">{error}</div>}

          <div className="selected-count">
            {t(selectedCategories.length === 1 ? 'interests.category_selected' : 'interests.categories_selected', { count: selectedCategories.length })}
          </div>

          <div className="interests-actions">
            <button 
              className="btn-submit"
              onClick={handleSubmit}
              disabled={loading || selectedCategories.length === 0}
            >
              {loading ? t('interests.saving') : t('interests.continue')}
            </button>
            <button 
              className="btn-skip"
              onClick={() => navigate('/user-dashboard')}
            >
              {t('interests.skip')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Interests;
