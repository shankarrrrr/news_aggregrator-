# NewsNexus Dashboard - Premium Editorial MCQ Interface

A premium, editorial-style React dashboard for UPSC intelligence testing.

## Design Philosophy

Premium editorial aesthetic inspired by Financial Times, The Economist, and high-end print digests. Clean, typographic, authoritative. No glassmorphism, no gradients, no glow effects. Every element earns its place.

## Setup

### Prerequisites
- Node.js 16+
- React 18+
- React Router v6

### Installation

```bash
# Create React app (if starting fresh)
npx create-react-app newsnexus-dashboard
cd newsnexus-dashboard

# Install dependencies
npm install react-router-dom

# Copy Dashboard files
# Copy Dashboard.jsx to src/components/
# Copy Dashboard.css to src/components/

# Update App.js to include routing
```

### App.js Setup

```jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/dashboard/:token" element={<Dashboard />} />
      </Routes>
    </Router>
  );
}

export default App;
```

### Environment Configuration

Update API base URL in Dashboard.jsx if needed:
```javascript
const API_BASE = 'http://localhost:8000';
```

Or use environment variables:
```javascript
const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
```

## Features

### Main Dashboard
- **Premium Header**: Dark navy with editorial typography
- **Article Sidebar**: Clean list with category tags, scores, and status indicators
- **MCQ Panel**: Full-width question with 4 options
- **Timer**: Simple progress bar (60 seconds per question)
- **Explanation**: Slides in after answer submission
- **Stats Bar**: Sticky bottom bar with attempt count and score

### Results Screen
- **Big Score Display**: Playfair Display, 72px, amber
- **Question Breakdown**: Clean table with per-question results
- **Weak Topics**: Areas needing focus
- **Performance Bars**: Category-wise accuracy visualization

## Typography

- **Display/Headers**: Playfair Display (Google Fonts)
- **Body Text**: Source Serif 4 (Google Fonts)
- **Labels/Meta**: DM Mono (Google Fonts)

All fonts are imported via Google Fonts CDN in the CSS file.

## Color System

```css
--bg-primary: #f5f0e8        /* Warm off-white */
--bg-secondary: #eee9df      /* Darker cream */
--bg-header: #1a2332         /* Deep navy */
--text-primary: #1a1a1a      /* Near black */
--text-secondary: #555550    /* Muted grey */
--accent-red: #c0392b        /* Crimson */
--accent-amber: #d4820a      /* Amber */
--correct: #2d6a2d           /* Dark green */
--wrong: #c0392b             /* Crimson */
```

## API Integration

### Endpoints Used

1. **GET /session/{token}**
   - Fetches session details and articles
   - Checks if session is pending/ready/completed

2. **GET /session/{token}/mcq/{article_id}**
   - Fetches MCQ for selected article
   - Returns question without correct answer

3. **POST /session/{token}/attempt**
   - Submits user's answer
   - Returns correctness, correct option, and explanation

4. **GET /session/{token}/results**
   - Fetches detailed results after completion
   - Returns per-question breakdown and weak topics

5. **GET /performance**
   - Fetches overall performance across all sessions
   - Returns category-wise statistics

## User Flow

1. User receives email with dashboard link
2. Clicks link → lands on `/dashboard/{token}`
3. Dashboard loads session and articles
4. User selects article from sidebar
5. MCQ loads with 60-second timer
6. User selects option → immediate feedback
7. Explanation slides in
8. User clicks "Next Question →"
9. Repeat until all articles attempted
10. Results screen displays with full breakdown

## Design Principles

### What We Do
✅ Clean typography hierarchy
✅ Generous white space
✅ Subtle borders and dividers
✅ Muted, sophisticated colors
✅ Left-aligned content
✅ Editorial restraint

### What We Don't Do
❌ Box shadows (except one subtle on MCQ card)
❌ Border radius > 3px
❌ Gradients or glow effects
❌ Hover scale/lift effects
❌ Pill-shaped tags
❌ Centered body text
❌ Bright, saturated colors

## Responsive Design

- Desktop: Two-column layout (sidebar + MCQ panel)
- Tablet/Mobile: Single column, sidebar stacks above MCQ panel
- All breakpoints maintain editorial aesthetic

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development

```bash
# Start development server
npm start

# Build for production
npm run build
```

## Production Deployment

1. Update API_BASE to production API URL
2. Build: `npm run build`
3. Deploy `build/` folder to hosting (Vercel, Netlify, etc.)
4. Ensure CORS is configured on backend API

## License

MIT
