import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, BarChart3, Activity, Wrench, LineChart, DollarSign } from 'lucide-react';

const Navbar = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/risk-heatmap', icon: Activity, label: 'Risk Heatmap' },
    { path: '/cost-analysis', icon: DollarSign, label: 'Cost Analysis' },
    { path: '/explainability', icon: BarChart3, label: 'Explainability' },
    { path: '/defect-intelligence', icon: Wrench, label: 'Defect Intelligence' },
    { path: '/defect-analytics', icon: LineChart, label: 'Defect Analytics' }
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
