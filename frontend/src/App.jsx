import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import RiskHeatmapPage from './pages/RiskHeatmapPage';
import CostAnalysisPage from './pages/CostAnalysisPage';
import Dashboard from './pages/Dashboard';
import Prediction from './pages/Prediction';
import RiskRanking from './pages/RiskRanking';
import Explainability from './pages/Explainability';
import DefectIntelligence from './pages/DefectIntelligence';
import DefectAnalytics from './pages/DefectAnalytics';
import ChatPage from './pages/ChatPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <main className="main-content">
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
            <Route path="/chat" element={<ChatPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
