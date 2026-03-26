import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
      setError('Please select at least one category');
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
          <div className="header-brand">NEWSNEXUS</div>
          <h1 className="header-title">Choose Your Interests</h1>
          <p className="header-subtitle">Select topics to personalize your daily intelligence brief</p>
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
            {selectedCategories.length} {selectedCategories.length === 1 ? 'category' : 'categories'} selected
          </div>

          <div className="interests-actions">
            <button 
              className="btn-submit"
              onClick={handleSubmit}
              disabled={loading || selectedCategories.length === 0}
            >
              {loading ? 'Saving...' : 'Continue'}
            </button>
            <button 
              className="btn-skip"
              onClick={() => navigate('/user-dashboard')}
            >
              Skip for now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Interests;
