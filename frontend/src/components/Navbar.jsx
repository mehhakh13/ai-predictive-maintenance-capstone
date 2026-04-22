import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, LayoutDashboard, TrendingUp, AlertCircle, BarChart3, Activity, Bug, Target } from 'lucide-react';

const Navbar = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/risk-heatmap', icon: Activity, label: 'Risk Heatmap' },
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/prediction', icon: TrendingUp, label: 'Prediction' },
    { path: '/risk-ranking', icon: AlertCircle, label: 'Risk Ranking' },
    { path: '/explainability', icon: BarChart3, label: 'Explainability' },
    { path: '/defect-intelligence', icon: Bug, label: 'Defect Intelligence' },
    { path: '/defect-analytics', icon: Target, label: 'Defect Analytics' }
  ];

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Activity size={24} />
        <span className="brand-name">Predictive Maintenance</span>
      </div>

      <div className="navbar-menu">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};

export default Navbar;
