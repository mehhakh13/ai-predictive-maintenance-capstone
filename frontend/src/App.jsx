import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { CircularProgress, Box } from '@mui/material';
import Navbar from './components/Navbar';
import './App.css';

// Lazy load all page components for better initial load performance
const HomePage = lazy(() => import('./pages/HomePage'));
const RiskHeatmapPage = lazy(() => import('./pages/RiskHeatmapPage'));
const CostAnalysisPage = lazy(() => import('./pages/CostAnalysisPage'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Prediction = lazy(() => import('./pages/Prediction'));
const RiskRanking = lazy(() => import('./pages/RiskRanking'));
const Explainability = lazy(() => import('./pages/Explainability'));
const DefectIntelligence = lazy(() => import('./pages/DefectIntelligence'));
const DefectAnalytics = lazy(() => import('./pages/DefectAnalytics'));
const ChatAssistant = lazy(() => import('./pages/ChatAssistant'));

// Loading fallback component
const PageLoader = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
    <CircularProgress size={60} />
  </Box>
);

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <main className="main-content">
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/risk-heatmap" element={<RiskHeatmapPage />} />
              <Route path="/cost-analysis" element={<CostAnalysisPage />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/prediction" element={<Prediction />} />
              <Route path="/risk-ranking" element={<RiskRanking />} />
              <Route path="/explainability" element={<Explainability />} />
              <Route path="/defect-intelligence" element={<DefectIntelligence />} />
              <Route path="/defect-analytics" element={<DefectAnalytics />} />
              <Route path="/chat" element={<ChatAssistant />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </Router>
  );
}

export default App;
