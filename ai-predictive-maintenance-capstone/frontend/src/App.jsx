import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import RiskHeatmapPage from './pages/RiskHeatmapPage';
import Dashboard from './pages/Dashboard';
import Prediction from './pages/Prediction';
import RiskRanking from './pages/RiskRanking';
import Explainability from './pages/Explainability';
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
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/prediction" element={<Prediction />} />
            <Route path="/risk-ranking" element={<RiskRanking />} />
            <Route path="/explainability" element={<Explainability />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
