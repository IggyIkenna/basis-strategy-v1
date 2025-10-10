
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { LoginPage } from './components/auth/LoginPage';
import { Layout } from './components/layout/Layout';
import { WizardContainer } from './components/wizard/WizardContainer';
import { ResultsPage } from './components/results/ResultsPage';
import { LiveTradingDashboard } from './components/live/LiveTradingDashboard';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<Navigate to="/wizard" replace />} />
            <Route path="wizard" element={<WizardContainer />} />
            <Route path="results/:backtestId" element={<ResultsPage />} />
            <Route path="live" element={<LiveTradingDashboard />} />
          </Route>
          <Route path="*" element={<Navigate to="/wizard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}


export default App;
