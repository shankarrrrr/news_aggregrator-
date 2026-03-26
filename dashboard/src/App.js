import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Admin from './components/Admin';
import AgentTrace from './components/AgentTrace';
import Landing from './components/Landing';
import Auth from './components/Auth';
import Interests from './components/Interests';
import UserDashboard from './components/UserDashboard';

// Protected Route Component
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Auth mode="login" />} />
        <Route path="/signup" element={<Auth mode="signup" />} />
        
        {/* Protected Routes */}
        <Route path="/interests" element={
          <ProtectedRoute>
            <Interests />
          </ProtectedRoute>
        } />
        <Route path="/user-dashboard" element={
          <ProtectedRoute>
            <UserDashboard />
          </ProtectedRoute>
        } />
        
        {/* Session Routes (can be accessed with token in URL) */}
        <Route path="/session/:token" element={<Dashboard />} />
        <Route path="/dashboard/:token" element={<Dashboard />} />
        
        {/* Admin Routes */}
        <Route path="/admin" element={<Admin />} />
        <Route path="/trace/:sessionId" element={<AgentTrace />} />
      </Routes>
    </Router>
  );
}

export default App;
