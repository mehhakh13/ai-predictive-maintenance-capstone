import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Card,
  CardContent,
  CircularProgress,
  Alert as MuiAlert,
  Divider,
  Badge,
  Stack
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  Cell
} from 'recharts';
import {
  TrendingUp,
  Warning,
  Cloud,
  Psychology,
  CheckCircle,
  Error,
  WatchLater,
  Speed,
  Assessment,
  EmojiObjects
} from '@mui/icons-material';
import Alert from '../components/Alert';
import '../styles/theme.css';

// Faculty Manager UX Color System
// 🔴 Red → Immediate action required
// 🟠 Amber → Urgent, plan this week
// 🔵 Blue → Monitor, schedule proactively
// 🟢 Green → OK / no action needed
const COLORS = {
  critical: '#DC2626',     // Red
  urgent: '#F59E0B',       // Amber
  monitor: '#3B82F6',      // Blue
  ok: '#10B981',           // Green

  // Chart gradients using severity system
  gradient: ['#EF4444', '#F59E0B', '#3B82F6', '#10B981', '#60A5FA', '#34D399'],

  // Severity scale (red to amber to blue to green)
  severity: ['#DC2626', '#EF4444', '#F59E0B', '#FBBF24', '#3B82F6', '#60A5FA', '#10B981'],

  // Legacy support
  primary: '#3B82F6',
  secondary: '#60A5FA',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#DC2626',
  info: '#3B82F6',
  neutral: '#64748B',

  // Backgrounds
  bgDeepNavy: '#060b18',
  bgNavyLighter: '#0f1729',
  bgNavyCard: '#1a2332'
};

const DefectAnalytics = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [selectedUniversity, setSelectedUniversity] = useState('');
  const [selectedBuilding, setSelectedBuilding] = useState('');
  const [selectedSubsystem, setSelectedSubsystem] = useState('');

  // Data states
  const [globalData, setGlobalData] = useState([]);
  const [universityData, setUniversityData] = useState([]);
  const [buildingData, setBuildingData] = useState([]);
  const [universities, setUniversities] = useState([]);
  const [allBuildings, setAllBuildings] = useState([]);

  // ML Model states
  const [recurrenceModels, setRecurrenceModels] = useState([]);
  const [environmentalModels, setEnvironmentalModels] = useState([]);
  const [survivalResults, setSurvivalResults] = useState(null);

  useEffect(() => {
    loadInitialData();
    loadMLResults();
  }, []);

  useEffect(() => {
    if (selectedUniversity && buildingData.length === 0) {
      loadBuildingData();
    }
  }, [selectedUniversity]);

  const loadInitialData = async () => {
    try {
      console.log('[DefectAnalytics] Starting loadInitialData...');
      setLoading(true);
      const cacheKey = 'defect_analytics_cache_v2';
      const cached = sessionStorage.getItem(cacheKey);

      if (cached) {
        console.log('[DefectAnalytics] Using cached data');
        try {
          const { globalData: cachedGlobal, universityData: cachedUni, timestamp } = JSON.parse(cached);
          const age = Date.now() - timestamp;

          if (age < 5 * 60 * 1000) {
            setGlobalData(cachedGlobal);
            setUniversityData(cachedUni);
            const uniqueUnis = [...new Set(cachedUni.map(row => row.UniversityID))].sort();
            setUniversities(uniqueUnis);
            setLoading(false);
            console.log('[DefectAnalytics] Loaded from cache successfully');
            return;
          }
        } catch (cacheError) {
          console.warn('[DefectAnalytics] Cache parse error, fetching fresh data', cacheError);
          sessionStorage.removeItem(cacheKey);
        }
      }

      console.log('[DefectAnalytics] Fetching fresh data...');
      const [globalResponse, uniResponse] = await Promise.all([
        fetch('/data/defect_analytics/global_rankings.csv'),
        fetch('/data/defect_analytics/university_rankings.csv')
      ]);

      if (!globalResponse.ok || !uniResponse.ok) {
        throw new Error(`HTTP error: ${globalResponse.status} / ${uniResponse.status}`);
      }

      const [globalText, uniText] = await Promise.all([
        globalResponse.text(),
        uniResponse.text()
      ]);

      console.log('[DefectAnalytics] Parsing CSV data...');
      const global = parseCSV(globalText);
      const uni = parseCSV(uniText);

      setGlobalData(global);
      setUniversityData(uni);

      const uniqueUnis = [...new Set(uni.map(row => row.UniversityID))].sort();
      setUniversities(uniqueUnis);

      try {
        sessionStorage.setItem(cacheKey, JSON.stringify({
          globalData: global,
          universityData: uni,
          timestamp: Date.now()
        }));
      } catch (storageError) {
        console.warn('[DefectAnalytics] Failed to cache data', storageError);
      }

      console.log('[DefectAnalytics] Data loaded successfully');
      setLoading(false);
    } catch (err) {
      console.error('[DefectAnalytics] Error loading data:', err);
      setError(`Failed to load analytics data: ${err.message}`);
      setLoading(false);
    }
  };

  const loadBuildingData = async () => {
    try {
      const cacheKey = 'building_data_cache_v2';
      const cached = sessionStorage.getItem(cacheKey);

      if (cached) {
        const { buildingData: cachedBldg, allBuildings: cachedAll, timestamp } = JSON.parse(cached);
        const age = Date.now() - timestamp;

        if (age < 5 * 60 * 1000) {
          setBuildingData(cachedBldg);
          setAllBuildings(cachedAll);
          return;
        }
      }

      const bldgResponse = await fetch('/data/defect_analytics/building_rankings.csv');
      const bldgText = await bldgResponse.text();
      const bldg = parseCSV(bldgText);
      setBuildingData(bldg);

      const buildingMap = new Map();
      bldg.forEach(row => {
        const key = `${row.UniversityID}_${row.BuildingName}`;
        if (!buildingMap.has(key)) {
          buildingMap.set(key, {
            name: row.BuildingName,
            universityId: row.UniversityID
          });
        }
      });

      const uniqueBldgs = Array.from(buildingMap.values());
      setAllBuildings(uniqueBldgs);

      sessionStorage.setItem(cacheKey, JSON.stringify({
        buildingData: bldg,
        allBuildings: uniqueBldgs,
        timestamp: Date.now()
      }));
    } catch (e) {
      console.log('Building data not available');
    }
  };

  const loadMLResults = async () => {
    try {
      const cacheKey = 'ml_results_cache_v2';
      const cached = sessionStorage.getItem(cacheKey);

      if (cached) {
        const { recurrence, environmental, survival, timestamp } = JSON.parse(cached);
        const age = Date.now() - timestamp;

        if (age < 5 * 60 * 1000) {
          setRecurrenceModels(recurrence);
          setEnvironmentalModels(environmental);
          setSurvivalResults(survival);
          return;
        }
      }

      const [recResponse, envResponse, survResponse] = await Promise.all([
        fetch('/data/ml_defect_analytics/recurrence_forecast_comparison.csv'),
        fetch('/data/ml_defect_analytics/environmental_model_comparison.csv'),
        fetch('/data/ml_defect_analytics/survival_cox_model.json')
      ]);

      const [recText, envText, surv] = await Promise.all([
        recResponse.text(),
        envResponse.text(),
        survResponse.json()
      ]);

      const rec = parseCSV(recText);
      const env = parseCSV(envText);

      setRecurrenceModels(rec);
      setEnvironmentalModels(env);
      setSurvivalResults(surv);

      sessionStorage.setItem(cacheKey, JSON.stringify({
        recurrence: rec,
        environmental: env,
        survival: surv,
        timestamp: Date.now()
      }));
    } catch (err) {
      console.log('ML results not available:', err);
    }
  };

  const parseCSV = (text) => {
    const lines = text.trim().split('\n');
    if (lines.length === 0) return [];

    const headers = lines[0].split(',');
    const result = new Array(lines.length - 1);

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',');
      const row = {};

      for (let j = 0; j < headers.length; j++) {
        const value = values[j];
        if (value && /^-?\d+\.?\d*$/.test(value)) {
          row[headers[j]] = parseFloat(value);
        } else {
          row[headers[j]] = value;
        }
      }
      result[i - 1] = row;
    }

    return result;
  };

  const getAvailableBuildings = () => {
    if (!selectedUniversity) return [];
    const buildings = allBuildings
      .filter(b => b.universityId == selectedUniversity)
      .map(b => b.name);
    return [...new Set(buildings)].sort();
  };

  const getAvailableSubsystems = () => {
    const data = getFilteredData();
    const subsystems = data.map(row => row.SubsystemDescription).filter(Boolean);
    return [...new Set(subsystems)].sort();
  };

  const handleUniversityChange = (universityId) => {
    setSelectedUniversity(universityId);
    setSelectedBuilding('');
    setSelectedSubsystem('');
  };

  const handleBuildingChange = (building) => {
    setSelectedBuilding(building);
    setSelectedSubsystem('');
  };

  const getFilteredData = () => {
    let data = [];

    if (selectedUniversity && selectedBuilding) {
      data = buildingData.filter(row =>
        row.UniversityID == selectedUniversity &&
        row.BuildingName === selectedBuilding
      );
    } else if (selectedUniversity) {
      data = universityData.filter(row => row.UniversityID == selectedUniversity);
    } else {
      data = globalData;
    }

    if (selectedSubsystem) {
      data = data.filter(row => row.SubsystemDescription === selectedSubsystem);
    }

    return data;
  };

  const getContextLabel = () => {
    if (selectedBuilding) return `${selectedBuilding}, University ${selectedUniversity}`;
    if (selectedUniversity) return `University ${selectedUniversity}`;
    return 'All Universities';
  };

  // Helper function to calculate KPIs
  const calculateKPIs = () => {
    const data = getFilteredData();
    if (data.length === 0) return null;

    const totalDefects = data.reduce((sum, row) => sum + (row.total_count || 0), 0);
    const avgFrequency = data.reduce((sum, row) => sum + (row.frequency_per_month || 0), 0) / data.length;
    const totalCost = data.reduce((sum, row) => sum + (row.total_cost || 0), 0);
    const avgSeverity = data.reduce((sum, row) => sum + (row.severity_score || 0), 0) / data.length;
    const highSeverityCount = data.filter(row => (row.severity_score || 0) > 10).length;
    const environmentalSensitive = data.filter(row => Math.abs(row.strongest_correlation || 0) > 0.3).length;

    const topRecurrent = data.sort((a, b) => (b.frequency_per_month || 0) - (a.frequency_per_month || 0))[0];
    const topSevere = data.sort((a, b) => (b.severity_score || 0) - (a.severity_score || 0))[0];

    return {
      totalDefects,
      avgFrequency,
      totalCost,
      avgSeverity,
      highSeverityCount,
      environmentalSensitive,
      topRecurrent,
      topSevere,
      subsystemCount: data.length
    };
  };

  // ==================== TAB COMPONENTS ====================

  // OVERVIEW TAB
  const OverviewTab = () => {
    const data = getFilteredData();
    const kpis = calculateKPIs();

    if (!kpis) {
      return (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            Please select a university to view analytics
          </Typography>
        </Box>
      );
    }

    const topRecurrent = data
      .sort((a, b) => (b.frequency_per_month || 0) - (a.frequency_per_month || 0))
      .slice(0, 8);

    const topSevere = data
      .sort((a, b) => (b.severity_score || 0) - (a.severity_score || 0))
      .slice(0, 5);

    const envSensitive = data
      .filter(row => Math.abs(row.strongest_correlation || 0) > 0.25)
      .sort((a, b) => Math.abs(b.strongest_correlation || 0) - Math.abs(a.strongest_correlation || 0))
      .slice(0, 5);

    return (
      <Box>
        {/* Executive Summary Header */}
        <Paper sx={{ p: 3, mb: 3, bgcolor: COLORS.bgNavyCard, borderTop: `3px solid ${COLORS.monitor}`, borderRadius: 2 }}>
          <Typography variant="h5" fontWeight={600} gutterBottom sx={{ color: 'white' }}>
            📊 Executive Analytics Dashboard
          </Typography>
          <Typography variant="body2" sx={{ color: '#94A3B8' }}>
            {getContextLabel()} • Comprehensive Maintenance Intelligence
          </Typography>
        </Paper>

        {/* KPI Cards */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', borderTop: `4px solid ${COLORS.monitor}`, bgcolor: COLORS.bgNavyCard }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box>
                    <Typography color="text.secondary" variant="caption" fontWeight={500}>
                      TOTAL DEFECTS
                    </Typography>
                    <Typography variant="h4" fontWeight={700} className="numeric-value" sx={{ mt: 1, color: 'white' }}>
                      {kpis.totalDefects.toLocaleString()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {kpis.subsystemCount} subsystems tracked
                    </Typography>
                  </Box>
                  <Assessment sx={{ fontSize: 40, color: COLORS.monitor, opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', borderTop: `4px solid ${COLORS.urgent}`, bgcolor: COLORS.bgNavyCard }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box>
                    <Typography color="text.secondary" variant="caption" fontWeight={500}>
                      AVG FREQUENCY
                    </Typography>
                    <Typography variant="h4" fontWeight={700} className="numeric-value" sx={{ mt: 1, color: COLORS.urgent }}>
                      {kpis.avgFrequency.toFixed(1)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      defects per month
                    </Typography>
                  </Box>
                  <TrendingUp sx={{ fontSize: 40, color: COLORS.urgent, opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', borderTop: `4px solid ${COLORS.critical}`, bgcolor: COLORS.bgNavyCard }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box>
                    <Typography color="text.secondary" variant="caption" fontWeight={500}>
                      TOTAL COST
                    </Typography>
                    <Typography variant="h4" fontWeight={700} className="numeric-value" sx={{ mt: 1, color: COLORS.critical }}>
                      ${(kpis.totalCost / 1000000).toFixed(1)}M
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      maintenance expenditure
                    </Typography>
                  </Box>
                  <Warning sx={{ fontSize: 40, color: COLORS.critical, opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', borderTop: `4px solid ${COLORS.critical}`, bgcolor: COLORS.bgNavyCard }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box>
                    <Typography color="text.secondary" variant="caption" fontWeight={500}>
                      HIGH SEVERITY
                    </Typography>
                    <Typography variant="h4" fontWeight={700} className="numeric-value" sx={{ mt: 1, color: COLORS.critical }}>
                      {kpis.highSeverityCount}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      critical subsystems
                    </Typography>
                  </Box>
                  <Error sx={{ fontSize: 40, color: COLORS.critical, opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Main Analytics Section */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {/* Top Recurrent Defects */}
          <Grid item xs={12} lg={8}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" fontWeight={600} gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <TrendingUp sx={{ mr: 1, color: COLORS.primary }} />
                Top Recurrent Defects
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={topRecurrent} layout="horizontal" margin={{ left: 20, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis type="number" stroke="#666" />
                  <YAxis
                    type="category"
                    dataKey="SubsystemDescription"
                    width={150}
                    tick={{ fontSize: 11 }}
                    stroke="#666"
                  />
                  <Tooltip
                    contentStyle={{ borderRadius: 8, border: '1px solid #e0e0e0' }}
                    formatter={(value) => [value.toFixed(1), 'Frequency/Month']}
                  />
                  <Bar dataKey="frequency_per_month" radius={[0, 8, 8, 0]}>
                    {topRecurrent.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS.gradient[index % COLORS.gradient.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <Alert severity="info" sx={{ mt: 2 }} variant="outlined">
                <strong>Insight:</strong> {topRecurrent[0]?.SubsystemDescription} has the highest recurrence rate at{' '}
                {topRecurrent[0]?.frequency_per_month?.toFixed(1)} defects/month
              </Alert>
            </Paper>
          </Grid>

          {/* Severity Hotspot */}
          <Grid item xs={12} lg={4}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" fontWeight={600} gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <Warning sx={{ mr: 1, color: COLORS.error }} />
                Severity Ranking
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Stack spacing={1.5}>
                {topSevere.slice(0, 6).map((item, idx) => (
                  <Box
                    key={idx}
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      border: '1px solid #e0e0e0',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: idx === 0 ? '#FFF3E0' : 'white'
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                      <Chip
                        label={idx + 1}
                        size="small"
                        sx={{
                          minWidth: 28,
                          height: 28,
                          fontWeight: 700,
                          mr: 1.5,
                          bgcolor: COLORS.severity[idx] || COLORS.neutral,
                          color: 'white'
                        }}
                      />
                      <Typography variant="body2" sx={{ fontSize: '0.85rem', fontWeight: 500 }}>
                        {item.SubsystemDescription?.substring(0, 30)}
                        {item.SubsystemDescription?.length > 30 ? '...' : ''}
                      </Typography>
                    </Box>
                    <Chip
                      label={item.severity_score?.toFixed(1)}
                      size="small"
                      color={item.severity_score > 15 ? 'error' : item.severity_score > 10 ? 'warning' : 'default'}
                      sx={{ fontWeight: 600 }}
                    />
                  </Box>
                ))}
              </Stack>
              <Alert severity="warning" sx={{ mt: 2 }} variant="outlined">
                <strong>Priority:</strong> {kpis.highSeverityCount} subsystems require immediate attention
              </Alert>
            </Paper>
          </Grid>
        </Grid>

        {/* Environmental & Model Performance Row */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {/* Environmental Risk */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" fontWeight={600} gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <Cloud sx={{ mr: 1, color: COLORS.success }} />
                Environmental Sensitivity
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Subsystem</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Factor</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600 }}>Correlation</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {envSensitive.slice(0, 5).map((row, idx) => (
                      <TableRow key={idx}>
                        <TableCell sx={{ fontSize: '0.85rem' }}>
                          {row.SubsystemDescription?.substring(0, 25)}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={row.strongest_weather_factor || 'N/A'}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.75rem' }}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Chip
                            label={Math.abs(row.strongest_correlation || 0).toFixed(3)}
                            size="small"
                            color={Math.abs(row.strongest_correlation) > 0.4 ? 'error' : 'warning'}
                            sx={{ fontWeight: 600 }}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <Alert severity="success" sx={{ mt: 2 }} variant="outlined">
                {kpis.environmentalSensitive} subsystems show strong environmental correlation (&gt;0.3)
              </Alert>
            </Paper>
          </Grid>

          {/* AI Model Summary */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" fontWeight={600} gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <Psychology sx={{ mr: 1, color: COLORS.info }} />
                AI Model Performance
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Stack spacing={2}>
                <Card variant="outlined" sx={{ bgcolor: '#E3F2FD' }}>
                  <CardContent sx={{ py: 2 }}>
                    <Typography variant="caption" color="text.secondary" fontWeight={600}>
                      Recurrence Forecasting
                    </Typography>
                    <Typography variant="h5" fontWeight={700} color="primary">
                      XGBoost
                    </Typography>
                    <Typography variant="caption">
                      MAE: 127-248 defects/month • Best for short-term prediction
                    </Typography>
                  </CardContent>
                </Card>

                <Card variant="outlined" sx={{ bgcolor: '#E8F5E9' }}>
                  <CardContent sx={{ py: 2 }}>
                    <Typography variant="caption" color="text.secondary" fontWeight={600}>
                      Environmental Impact
                    </Typography>
                    <Typography variant="h5" fontWeight={700} color="success.main">
                      R² = 0.8134
                    </Typography>
                    <Typography variant="caption">
                      XGBoost • 81.3% variance explained • Production-ready
                    </Typography>
                  </CardContent>
                </Card>

                <Card variant="outlined" sx={{ bgcolor: '#FFF3E0' }}>
                  <CardContent sx={{ py: 2 }}>
                    <Typography variant="caption" color="text.secondary" fontWeight={600}>
                      Time-to-Failure (Cox Model)
                    </Typography>
                    <Typography variant="h5" fontWeight={700} color="warning.main">
                      C-index: 0.52
                    </Typography>
                    <Typography variant="caption">
                      Requires additional features for production deployment
                    </Typography>
                  </CardContent>
                </Card>
              </Stack>
            </Paper>
          </Grid>
        </Grid>

        {/* Recommendations */}
        <Paper sx={{ p: 3, background: 'linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%)' }}>
          <Typography variant="h6" fontWeight={600} gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <EmojiObjects sx={{ mr: 1, color: COLORS.warning }} />
            Key Recommendations
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 2, bgcolor: 'white', borderRadius: 2, border: '2px solid #D32F2F' }}>
                <Chip label="IMMEDIATE" color="error" size="small" sx={{ mb: 1, fontWeight: 700 }} />
                <Typography variant="body2" fontWeight={600} gutterBottom>
                  Address Top 3 Recurrent Defects
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Focus on {topRecurrent[0]?.SubsystemDescription}, {topRecurrent[1]?.SubsystemDescription}, and{' '}
                  {topRecurrent[2]?.SubsystemDescription} to reduce maintenance frequency
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 2, bgcolor: 'white', borderRadius: 2, border: '2px solid #F57C00' }}>
                <Chip label="PREVENTIVE" color="warning" size="small" sx={{ mb: 1, fontWeight: 700 }} />
                <Typography variant="body2" fontWeight={600} gutterBottom>
                  Monitor Environmental Conditions
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {envSensitive[0]?.strongest_weather_factor} shows strongest correlation. Implement predictive
                  maintenance during high-risk weather periods
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 2, bgcolor: 'white', borderRadius: 2, border: '2px solid #1976D2' }}>
                <Chip label="MONITORING" color="info" size="small" sx={{ mb: 1, fontWeight: 700 }} />
                <Typography variant="body2" fontWeight={600} gutterBottom>
                  Deploy XGBoost Models
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Use environmental impact model (R²=0.81) for resource allocation. Enhance survival model with
                  additional predictors
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      </Box>
    );
  };

  // RECURRENCE ANALYSIS TAB
  const RecurrenceTab = () => {
    const data = getFilteredData();

    if (data.length === 0) {
      return (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            No recurrence data available for this selection
          </Typography>
        </Box>
      );
    }

    const topRecurrent = data
      .sort((a, b) => (b.frequency_per_month || 0) - (a.frequency_per_month || 0))
      .slice(0, 15);

    const forecastData = recurrenceModels.map(row => ({
      subsystem: row.subsystem?.substring(0, 20) || 'Unknown',
      ARIMA: row.arima_mae,
      Prophet: row.prophet_mae,
      XGBoost: row.xgb_mae,
      best: row.best_model
    }));

    return (
      <Box>
        <Paper className="tab-header recurrence">
          <Typography variant="h5" fontWeight={600} gutterBottom sx={{ color: 'white' }}>
            🔄 Recurrence Analysis
          </Typography>
          <Typography variant="body2" sx={{ color: '#94A3B8' }}>
            Identifying patterns in defect frequency and predicting future occurrences
          </Typography>
        </Paper>

        {/* Top Recurrent Subsystems */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Top Recurrent Subsystems
          </Typography>
          <Divider sx={{ mb: 3 }} />
          <ResponsiveContainer width="100%" height={450}>
            <BarChart data={topRecurrent} layout="horizontal" margin={{ left: 120, right: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" stroke="#666" />
              <YAxis
                type="category"
                dataKey="SubsystemDescription"
                width={110}
                tick={{ fontSize: 11 }}
                stroke="#666"
              />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: '1px solid #e0e0e0' }}
                formatter={(value) => [value.toFixed(2), 'Defects/Month']}
              />
              <Bar dataKey="frequency_per_month" radius={[0, 8, 8, 0]}>
                {topRecurrent.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS.gradient[index % COLORS.gradient.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Paper>

        {/* Recurrence Forecast Comparison */}
        {forecastData.length > 0 && (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              AI Model Forecast Comparison (MAE)
            </Typography>
            <Divider sx={{ mb: 3 }} />
            <Alert severity="info" sx={{ mb: 2 }} variant="outlined">
              Lower MAE indicates better prediction accuracy. XGBoost performs best for short-term forecasts.
            </Alert>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={forecastData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="subsystem" tick={{ fontSize: 11 }} />
                <YAxis stroke="#666" />
                <Tooltip contentStyle={{ borderRadius: 8 }} />
                <Legend />
                <Bar dataKey="ARIMA" fill={COLORS.gradient[0]} />
                <Bar dataKey="Prophet" fill={COLORS.gradient[2]} />
                <Bar dataKey="XGBoost" fill={COLORS.gradient[4]} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        )}

        {/* Recurrence Summary Table */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Detailed Recurrence Metrics
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                  <TableCell sx={{ fontWeight: 700 }}>Rank</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Subsystem</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 700 }}>Frequency/Month</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 700 }}>Total Count</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 700 }}>Months Observed</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Risk Level</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {topRecurrent.map((row, idx) => (
                  <TableRow key={idx} hover>
                    <TableCell>{idx + 1}</TableCell>
                    <TableCell>{row.SubsystemDescription}</TableCell>
                    <TableCell align="right">
                      <strong>{row.frequency_per_month?.toFixed(2)}</strong>
                    </TableCell>
                    <TableCell align="right">{row.total_count?.toLocaleString()}</TableCell>
                    <TableCell align="right">{row.months_observed?.toFixed(0)}</TableCell>
                    <TableCell>
                      <Chip
                        label={
                          row.frequency_per_month > 300
                            ? 'Critical'
                            : row.frequency_per_month > 150
                            ? 'High'
                            : row.frequency_per_month > 50
                            ? 'Medium'
                            : 'Low'
                        }
                        size="small"
                        color={
                          row.frequency_per_month > 300
                            ? 'error'
                            : row.frequency_per_month > 150
                            ? 'warning'
                            : row.frequency_per_month > 50
                            ? 'info'
                            : 'success'
                        }
                        sx={{ fontWeight: 600 }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Box>
    );
  };

  // SEVERITY ANALYSIS TAB
  const SeverityTab = () => {
    const data = getFilteredData();

    if (data.length === 0) {
      return (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            No severity data available for this selection
          </Typography>
        </Box>
      );
    }

    const topSevere = data
      .sort((a, b) => (b.severity_score || 0) - (a.severity_score || 0))
      .slice(0, 15);

    const scatterData = data
      .filter(row => row.avg_cost && row.avg_duration)
      .map(row => ({
        name: row.SubsystemDescription?.substring(0, 20),
        cost: row.avg_cost,
        duration: row.avg_duration,
        severity: row.severity_score || 0
      }));

    return (
      <Box>
        <Paper className="tab-header severity">
          <Typography variant="h5" fontWeight={600} gutterBottom sx={{ color: 'white' }}>
            ⚠️ Severity Analysis
          </Typography>
          <Typography variant="body2" sx={{ color: '#94A3B8' }}>
            Composite scoring based on cost, duration, and frequency to prioritize maintenance efforts
          </Typography>
        </Paper>

        {/* Severity Ranking */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Severity Score Ranking
          </Typography>
          <Divider sx={{ mb: 3 }} />
          <ResponsiveContainer width="100%" height={450}>
            <BarChart data={topSevere} layout="horizontal" margin={{ left: 120, right: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" stroke="#666" />
              <YAxis
                type="category"
                dataKey="SubsystemDescription"
                width={110}
                tick={{ fontSize: 11 }}
                stroke="#666"
              />
              <Tooltip
                contentStyle={{ borderRadius: 8 }}
                formatter={(value) => [value.toFixed(2), 'Severity Score']}
              />
              <Bar dataKey="severity_score" radius={[0, 8, 8, 0]}>
                {topSevere.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS.severity[Math.min(index, 4)]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Paper>

        {/* Cost vs Duration Scatter */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Cost vs Duration Analysis
          </Typography>
          <Divider sx={{ mb: 3 }} />
          <Alert severity="warning" sx={{ mb: 2 }} variant="outlined">
            Subsystems in the top-right quadrant require both high cost and long repair times
          </Alert>
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                type="number"
                dataKey="duration"
                name="Duration"
                label={{ value: 'Avg Duration (hours)', position: 'insideBottom', offset: -10 }}
                stroke="#666"
              />
              <YAxis
                type="number"
                dataKey="cost"
                name="Cost"
                label={{ value: 'Avg Cost ($)', angle: -90, position: 'insideLeft' }}
                stroke="#666"
              />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                formatter={(value, name) =>
                  name === 'cost' ? [`$${value.toFixed(2)}`, 'Cost'] : [`${value.toFixed(1)} hrs`, 'Duration']
                }
              />
              <Scatter data={scatterData.slice(0, 30)} fill={COLORS.error}>
                {scatterData.slice(0, 30).map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.severity > 15 ? COLORS.error : entry.severity > 10 ? COLORS.warning : COLORS.info}
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </Paper>

        {/* Enhanced Priority Action List */}
        <Paper sx={{ p: 3, bgcolor: COLORS.bgNavyCard }}>
          <Typography variant="h6" fontWeight={600} gutterBottom sx={{ color: 'white' }}>
            🎯 Priority Action List
          </Typography>
          <Typography variant="body2" sx={{ color: '#94A3B8', mb: 2 }}>
            Items ranked by severity — Red: Immediate, Amber: Urgent, Blue: Monitor
          </Typography>
          <Divider sx={{ mb: 3, borderColor: '#334155' }} />

          <Stack spacing={2}>
            {topSevere.slice(0, 10).map((row, idx) => {
              const isImmediate = idx < 3;
              const isUrgent = idx >= 3 && idx < 5;
              const statusLabel = isImmediate ? 'Immediate' : isUrgent ? 'Urgent' : 'Monitor';
              const statusColor = isImmediate ? COLORS.critical : isUrgent ? COLORS.urgent : COLORS.monitor;
              const borderColor = isImmediate ? COLORS.critical : isUrgent ? COLORS.urgent : COLORS.monitor;

              return (
                <Card
                  key={idx}
                  sx={{
                    bgcolor: COLORS.bgNavyLighter,
                    borderLeft: `4px solid ${borderColor}`,
                    transition: 'all 0.2s',
                    '&:hover': {
                      transform: 'translateX(4px)',
                      bgcolor: COLORS.bgNavyCard
                    }
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={`#${idx + 1}`}
                          size="small"
                          sx={{
                            bgcolor: statusColor,
                            color: 'white',
                            fontWeight: 700,
                            minWidth: 40
                          }}
                        />
                        <Typography variant="body1" fontWeight={600} sx={{ color: 'white' }}>
                          {row.SubsystemDescription}
                        </Typography>
                      </Box>
                      <Chip
                        label={statusLabel}
                        size="small"
                        className="status-pill"
                        sx={{
                          bgcolor: statusColor,
                          color: 'white',
                          fontWeight: 600,
                          textTransform: 'uppercase'
                        }}
                      />
                    </Box>

                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="caption" sx={{ color: '#94A3B8' }}>Severity Score</Typography>
                        <Typography variant="h6" className="numeric-value" sx={{ color: 'white' }}>
                          {row.severity_score?.toFixed(2)}
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="caption" sx={{ color: '#94A3B8' }}>Avg Cost</Typography>
                        <Typography variant="h6" className="numeric-value" sx={{ color: COLORS.urgent }}>
                          ${row.avg_cost?.toFixed(2)}
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="caption" sx={{ color: '#94A3B8' }}>Repair Time</Typography>
                        <Typography variant="h6" className="numeric-value" sx={{ color: 'white' }}>
                          {row.avg_duration?.toFixed(1)} hrs
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="caption" sx={{ color: '#94A3B8' }}>Frequency</Typography>
                        <Typography variant="h6" className="numeric-value" sx={{ color: 'white' }}>
                          {row.frequency_per_month?.toFixed(1)}/mo
                        </Typography>
                      </Grid>
                    </Grid>

                    <Alert type={isImmediate ? 'danger' : isUrgent ? 'warn' : 'info'}>
                      <strong>Action: </strong>
                      {isImmediate &&
                        'Schedule comprehensive inspection immediately. Allocate emergency maintenance budget. Consider equipment replacement if repair costs exceed 60% of replacement value.'
                      }
                      {isUrgent &&
                        'Plan inspection within this week. Increase monitoring frequency. Prepare maintenance resources and parts inventory.'
                      }
                      {!isImmediate && !isUrgent &&
                        'Monitor closely and schedule preventive maintenance. Track trends and implement predictive maintenance strategies.'
                      }
                    </Alert>
                  </CardContent>
                </Card>
              );
            })}
          </Stack>
        </Paper>
      </Box>
    );
  };

  // ENVIRONMENTAL SENSITIVITY TAB
  const EnvironmentalTab = () => {
    const data = getFilteredData();

    if (data.length === 0) {
      return (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            No environmental data available for this selection
          </Typography>
        </Box>
      );
    }

    const topSensitive = data
      .filter(row => Math.abs(row.strongest_correlation || 0) > 0.1)
      .sort((a, b) => Math.abs(b.strongest_correlation || 0) - Math.abs(a.strongest_correlation || 0))
      .slice(0, 15);

    // Group by weather factor
    const weatherFactorGroups = topSensitive.reduce((acc, row) => {
      const factor = row.strongest_weather_factor || 'Unknown';
      if (!acc[factor]) acc[factor] = [];
      acc[factor].push(row);
      return acc;
    }, {});

    const weatherFactorSummary = Object.entries(weatherFactorGroups).map(([factor, items]) => ({
      factor,
      count: items.length,
      avgCorrelation: items.reduce((sum, item) => sum + Math.abs(item.strongest_correlation || 0), 0) / items.length
    }));

    return (
      <Box>
        <Paper className="tab-header environmental">
          <Typography variant="h5" fontWeight={600} gutterBottom sx={{ color: 'white' }}>
            🌤️ Environmental Sensitivity Analysis
          </Typography>
          <Typography variant="body2" sx={{ color: '#94A3B8' }}>
            Analyzing the impact of weather and environmental conditions on defect occurrence
          </Typography>
        </Paper>

        {/* Environmental Impact Chart */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Top Weather-Sensitive Subsystems
          </Typography>
          <Divider sx={{ mb: 3 }} />
          <ResponsiveContainer width="100%" height={450}>
            <BarChart data={topSensitive} layout="horizontal" margin={{ left: 120, right: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" domain={[0, 1]} stroke="#666" />
              <YAxis
                type="category"
                dataKey="SubsystemDescription"
                width={110}
                tick={{ fontSize: 11 }}
                stroke="#666"
              />
              <Tooltip
                contentStyle={{ borderRadius: 8 }}
                formatter={(value) => [Math.abs(value).toFixed(3), 'Correlation']}
              />
              <Bar dataKey="strongest_correlation" radius={[0, 8, 8, 0]}>
                {topSensitive.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={
                      Math.abs(entry.strongest_correlation) > 0.4
                        ? COLORS.error
                        : Math.abs(entry.strongest_correlation) > 0.3
                        ? COLORS.warning
                        : COLORS.success
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Paper>

        {/* Weather Factor Distribution */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Weather Factor Impact
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={weatherFactorSummary}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="factor" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#666" />
                  <Tooltip contentStyle={{ borderRadius: 8 }} />
                  <Bar dataKey="count" fill={COLORS.success} radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                ML Model Performance
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {environmentalModels.length > 0 && (
                <Stack spacing={2}>
                  {environmentalModels.map((model, idx) => (
                    <Card
                      key={idx}
                      variant="outlined"
                      sx={{
                        bgcolor:
                          model.test_r2 === Math.max(...environmentalModels.map(m => m.test_r2))
                            ? '#E8F5E9'
                            : 'white',
                        border:
                          model.test_r2 === Math.max(...environmentalModels.map(m => m.test_r2))
                            ? `2px solid ${COLORS.success}`
                            : '1px solid #e0e0e0'
                      }}
                    >
                      <CardContent sx={{ py: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Box>
                            <Typography variant="body2" fontWeight={600}>
                              {model.model}
                              {model.test_r2 === Math.max(...environmentalModels.map(m => m.test_r2)) && ' 🏆'}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              MAE: {model.test_mae?.toFixed(2)} • R²: {model.test_r2?.toFixed(4)}
                            </Typography>
                          </Box>
                          <Chip
                            label={model.test_r2 > 0.8 ? 'Excellent' : model.test_r2 > 0.7 ? 'Good' : 'Fair'}
                            size="small"
                            color={model.test_r2 > 0.8 ? 'success' : model.test_r2 > 0.7 ? 'primary' : 'default'}
                            sx={{ fontWeight: 600 }}
                          />
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </Stack>
              )}
              <Alert severity="success" sx={{ mt: 2 }} variant="outlined">
                <strong>Best Model:</strong> XGBoost with R² = 0.8134 (81.3% variance explained)
              </Alert>
            </Paper>
          </Grid>
        </Grid>

        {/* Detailed Environmental Table */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Environmental Correlation Details
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                  <TableCell sx={{ fontWeight: 700 }}>Rank</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Subsystem</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Weather Factor</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 700 }}>Correlation</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 700 }}>Sensitivity Score</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Risk Level</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {topSensitive.map((row, idx) => (
                  <TableRow key={idx} hover>
                    <TableCell>{idx + 1}</TableCell>
                    <TableCell sx={{ fontWeight: 500 }}>{row.SubsystemDescription}</TableCell>
                    <TableCell>
                      <Chip label={row.strongest_weather_factor || 'N/A'} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell align="right">
                      <strong>{Math.abs(row.strongest_correlation || 0).toFixed(3)}</strong>
                    </TableCell>
                    <TableCell align="right">{row.sensitivity_score?.toFixed(2)}</TableCell>
                    <TableCell>
                      <Chip
                        label={
                          Math.abs(row.strongest_correlation) > 0.4
                            ? 'High'
                            : Math.abs(row.strongest_correlation) > 0.3
                            ? 'Medium'
                            : 'Low'
                        }
                        size="small"
                        color={
                          Math.abs(row.strongest_correlation) > 0.4
                            ? 'error'
                            : Math.abs(row.strongest_correlation) > 0.3
                            ? 'warning'
                            : 'success'
                        }
                        sx={{ fontWeight: 600 }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Box>
    );
  };

  // AI/ML PERFORMANCE TAB
  const AIMLPerformanceTab = () => {
    const bestEnvModel =
      environmentalModels.length > 0
        ? environmentalModels.reduce((prev, curr) => (curr.test_r2 > prev.test_r2 ? curr : prev))
        : null;

    return (
      <Box>
        <Paper className="tab-header ai-ml">
          <Typography variant="h5" fontWeight={600} gutterBottom sx={{ color: 'white' }}>
            🧠 AI/ML Model Performance Analysis
          </Typography>
          <Typography variant="body2" sx={{ color: '#94A3B8' }}>
            Comprehensive evaluation of predictive models for maintenance optimization
          </Typography>
        </Paper>

        {/* Enhanced Model Performance Scorecards */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {/* Recurrence Forecasting - Needs Work (Amber) */}
          <Grid item xs={12} md={4}>
            <Card className="model-tile needs-work" sx={{ height: '100%', bgcolor: COLORS.bgNavyCard }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      bgcolor: COLORS.urgent,
                      animation: 'pulse 2s ease-in-out infinite',
                      '@keyframes pulse': {
                        '0%, 100%': { opacity: 1 },
                        '50%': { opacity: 0.5 }
                      }
                    }}
                  />
                  <Typography variant="overline" sx={{ color: '#94A3B8', fontWeight: 600, letterSpacing: '0.1em' }}>
                    Model 1: Recurrence Forecasting
                  </Typography>
                </Box>
                <Typography variant="h5" fontWeight={700} sx={{ color: 'white', mb: 1 }}>
                  XGBoost Recurrence
                </Typography>
                <Divider sx={{ my: 2, borderColor: '#334155' }} />
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                      Best Performer
                    </Typography>
                    <Typography variant="h6" fontWeight={700} sx={{ color: 'white' }}>
                      XGBoost
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                      MAE Range (defects/month)
                    </Typography>
                    <Typography variant="h6" fontWeight={700} className="numeric-value" sx={{ color: COLORS.urgent }}>
                      127–248
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                      Performance Grade
                    </Typography>
                    <Chip
                      label="B+"
                      sx={{
                        bgcolor: COLORS.urgent,
                        color: 'white',
                        fontWeight: 700,
                        fontSize: '1rem'
                      }}
                    />
                  </Box>
                </Stack>
                <Alert type="warn">
                  <strong>Status:</strong> Needs refinement. Suitable for short to medium-term forecasting. Consider ensemble methods for improved accuracy.
                </Alert>
              </CardContent>
            </Card>
          </Grid>

          {/* Environmental Impact - Production Ready (Green) */}
          <Grid item xs={12} md={4}>
            <Card className="model-tile production-ready" sx={{ height: '100%', bgcolor: COLORS.bgNavyCard }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <CheckCircle sx={{ color: COLORS.ok, fontSize: 20 }} />
                  <Typography variant="overline" sx={{ color: '#94A3B8', fontWeight: 600, letterSpacing: '0.1em' }}>
                    Model 2: Environmental Impact
                  </Typography>
                </Box>
                <Typography variant="h5" fontWeight={700} sx={{ color: 'white', mb: 1 }}>
                  Environmental ML
                </Typography>
                <Divider sx={{ my: 2, borderColor: '#334155' }} />
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                      Best Performer
                    </Typography>
                    <Typography variant="h6" fontWeight={700} sx={{ color: 'white' }}>
                      {bestEnvModel?.model || 'XGBoost'}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                      R² Score (Variance Explained)
                    </Typography>
                    <Typography variant="h6" fontWeight={700} className="numeric-value" sx={{ color: COLORS.ok }}>
                      {bestEnvModel?.test_r2?.toFixed(4) || '0.8134'} (81.3%)
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                      Performance Grade
                    </Typography>
                    <Chip
                      label="A"
                      sx={{
                        bgcolor: COLORS.ok,
                        color: 'white',
                        fontWeight: 700,
                        fontSize: '1rem'
                      }}
                    />
                  </Box>
                </Stack>
                <Alert type="success">
                  <strong>Status:</strong> Production-ready ✓ Deploy immediately for weather-based predictive maintenance scheduling.
                </Alert>
              </CardContent>
            </Card>
          </Grid>

          {/* Survival Analysis - Not Ready (Red/Amber) */}
          <Grid item xs={12} md={4}>
            <Card className="model-tile needs-work" sx={{ height: '100%', bgcolor: COLORS.bgNavyCard }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Warning sx={{ color: COLORS.urgent, fontSize: 20 }} />
                  <Typography variant="overline" sx={{ color: '#94A3B8', fontWeight: 600, letterSpacing: '0.1em' }}>
                    Model 3: Time-to-Failure
                  </Typography>
                </Box>
                <Typography variant="h5" fontWeight={700} sx={{ color: 'white', mb: 1 }}>
                  Cox Survival Model
                </Typography>
                <Divider sx={{ my: 2, borderColor: '#334155' }} />
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                      Model Type
                    </Typography>
                    <Typography variant="h6" fontWeight={700} sx={{ color: 'white' }}>
                      Cox Proportional Hazards
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                      C-index (Concordance)
                    </Typography>
                    <Typography variant="h6" fontWeight={700} className="numeric-value" sx={{ color: COLORS.urgent }}>
                      {survivalResults?.c_index?.toFixed(4) || '0.5232'}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                      Performance Grade
                    </Typography>
                    <Chip
                      label="C"
                      sx={{
                        bgcolor: COLORS.urgent,
                        color: 'white',
                        fontWeight: 700,
                        fontSize: '1rem'
                      }}
                    />
                  </Box>
                </Stack>
                <Alert type="warn">
                  <strong>Status:</strong> Requires improvement. Add equipment age, building type, and maintenance history features before deployment.
                </Alert>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Recurrence Model Comparison */}
        {recurrenceModels.length > 0 && (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Recurrence Forecast Model Leaderboard
            </Typography>
            <Divider sx={{ mb: 3 }} />
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                    <TableCell sx={{ fontWeight: 700 }}>Subsystem</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>ARIMA MAE</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>Prophet MAE</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>XGBoost MAE</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Best Model</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {recurrenceModels.map((row, idx) => (
                    <TableRow key={idx} hover>
                      <TableCell sx={{ fontWeight: 500 }}>{row.subsystem}</TableCell>
                      <TableCell align="right">{row.arima_mae?.toFixed(2) || 'N/A'}</TableCell>
                      <TableCell align="right">{row.prophet_mae?.toFixed(2) || 'N/A'}</TableCell>
                      <TableCell align="right">{row.xgb_mae?.toFixed(2) || 'N/A'}</TableCell>
                      <TableCell>
                        <Chip
                          label={row.best_model || 'N/A'}
                          size="small"
                          color={
                            row.best_model === 'xgb'
                              ? 'success'
                              : row.best_model === 'arima'
                              ? 'primary'
                              : 'default'
                          }
                          sx={{ fontWeight: 600 }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <Box sx={{ mt: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 2 }}>
              <Typography variant="caption" display="block" gutterBottom>
                <strong>MAE (Mean Absolute Error):</strong> Average prediction error in defect count. Lower values
                indicate better accuracy.
              </Typography>
              <Typography variant="caption" display="block">
                <strong>Interpretation:</strong> XGBoost shows superior performance for short-term predictions. ARIMA
                performs well for stable patterns, while Prophet handles seasonality effectively.
              </Typography>
            </Box>
          </Paper>
        )}

        {/* Environmental Model Comparison */}
        {environmentalModels.length > 0 && (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Environmental Impact Model Comparison
            </Typography>
            <Divider sx={{ mb: 3 }} />
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={environmentalModels}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="model" tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 1]} stroke="#666" />
                    <Tooltip contentStyle={{ borderRadius: 8 }} />
                    <Legend />
                    <Bar dataKey="train_r2" name="Train R²" fill={COLORS.gradient[1]} radius={[8, 8, 0, 0]} />
                    <Bar dataKey="test_r2" name="Test R²" fill={COLORS.gradient[3]} radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Grid>
              <Grid item xs={12} md={6}>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                        <TableCell sx={{ fontWeight: 700 }}>Model</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700 }}>Test R²</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700 }}>Test MAE</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Performance</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {environmentalModels.map((row, idx) => {
                        const isBest = row.test_r2 === Math.max(...environmentalModels.map(m => m.test_r2));
                        return (
                          <TableRow key={idx} sx={{ bgcolor: isBest ? '#E8F5E9' : 'white' }}>
                            <TableCell sx={{ fontWeight: 500 }}>
                              {row.model} {isBest && '🏆'}
                            </TableCell>
                            <TableCell align="right">
                              <strong>{row.test_r2?.toFixed(4)}</strong>
                            </TableCell>
                            <TableCell align="right">{row.test_mae?.toFixed(2)}</TableCell>
                            <TableCell>
                              <Chip
                                label={row.test_r2 > 0.8 ? 'Excellent' : row.test_r2 > 0.7 ? 'Good' : 'Fair'}
                                size="small"
                                color={row.test_r2 > 0.8 ? 'success' : row.test_r2 > 0.7 ? 'primary' : 'default'}
                                sx={{ fontWeight: 600 }}
                              />
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
            </Grid>
            <Box sx={{ mt: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 2 }}>
              <Typography variant="caption" display="block" gutterBottom>
                <strong>R² (Coefficient of Determination):</strong> Proportion of variance in defect counts explained
                by environmental factors. Range: 0-1, higher is better.
              </Typography>
              <Typography variant="caption" display="block">
                <strong>Academic Interpretation:</strong> XGBoost achieves R²=0.8134, indicating that 81.34% of the
                variance in defect occurrence can be explained by environmental variables (temperature, humidity,
                precipitation, pressure). This strong correlation supports the deployment of weather-based predictive
                maintenance strategies.
              </Typography>
            </Box>
          </Paper>
        )}

        {/* Survival Analysis Details */}
        {survivalResults && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Survival Analysis: Cox Proportional Hazards Model
            </Typography>
            <Divider sx={{ mb: 3 }} />
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="caption" color="text.secondary">
                      Concordance Index
                    </Typography>
                    <Typography variant="h4" fontWeight={700} color="warning.main">
                      {survivalResults.c_index?.toFixed(4)}
                    </Typography>
                    <Typography variant="caption">Range: 0.5 (random) to 1.0 (perfect)</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="caption" color="text.secondary">
                      Sample Size
                    </Typography>
                    <Typography variant="h4" fontWeight={700}>
                      {survivalResults.n_samples?.toLocaleString()}
                    </Typography>
                    <Typography variant="caption">Work orders analyzed</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="caption" color="text.secondary">
                      Top Risk Factor
                    </Typography>
                    <Typography variant="h4" fontWeight={700} color="error.main">
                      Humidity
                    </Typography>
                    <Typography variant="caption">HR: 1.004, p &lt; 0.001</Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
            <Alert severity="info" sx={{ mt: 3 }}>
              <Typography variant="body2" gutterBottom>
                <strong>Model Limitations:</strong> C-index of 0.52 indicates weak discriminative ability. The model
                barely outperforms random chance (0.50).
              </Typography>
              <Typography variant="body2">
                <strong>Recommendations for Improvement:</strong> Incorporate additional covariates such as equipment
                age, building type, subsystem complexity, historical failure patterns, and maintenance schedules to
                enhance predictive power.
              </Typography>
            </Alert>
          </Paper>
        )}
      </Box>
    );
  };

  // RECOMMENDATIONS TAB
  const RecommendationsTab = () => {
    const data = getFilteredData();
    const kpis = calculateKPIs();

    if (!kpis) {
      return (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            Please select a university to view recommendations
          </Typography>
        </Box>
      );
    }

    const topRecurrent = data.sort((a, b) => (b.frequency_per_month || 0) - (a.frequency_per_month || 0)).slice(0, 3);
    const topSevere = data.sort((a, b) => (b.severity_score || 0) - (a.severity_score || 0)).slice(0, 3);
    const envSensitive = data
      .filter(row => Math.abs(row.strongest_correlation || 0) > 0.3)
      .sort((a, b) => Math.abs(b.strongest_correlation || 0) - Math.abs(a.strongest_correlation || 0))
      .slice(0, 3);

    return (
      <Box>
        <Paper className="tab-header recommendations">
          <Typography variant="h5" fontWeight={600} gutterBottom sx={{ color: 'white' }}>
            💡 Strategic Recommendations
          </Typography>
          <Typography variant="body2" sx={{ color: '#94A3B8' }}>
            Data-driven action items for {getContextLabel()}
          </Typography>
        </Paper>

        {/* Immediate Attention */}
        <Paper sx={{ p: 3, mb: 3, borderLeft: `6px solid ${COLORS.error}` }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Error sx={{ fontSize: 32, color: COLORS.error, mr: 1 }} />
            <Box>
              <Typography variant="h6" fontWeight={700} color="error.main">
                IMMEDIATE ATTENTION REQUIRED
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Critical issues requiring urgent intervention
              </Typography>
            </Box>
          </Box>
          <Divider sx={{ mb: 2 }} />
          <Stack spacing={2}>
            {topSevere.map((item, idx) => (
              <Card key={idx} variant="outlined" sx={{ bgcolor: '#FFEBEE' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="body1" fontWeight={600} gutterBottom>
                        {idx + 1}. {item.SubsystemDescription}
                      </Typography>
                      <Grid container spacing={1}>
                        <Grid item xs={12} sm={4}>
                          <Typography variant="caption" color="text.secondary">
                            Severity Score
                          </Typography>
                          <Typography variant="body2" fontWeight={700}>
                            {item.severity_score?.toFixed(2)}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={4}>
                          <Typography variant="caption" color="text.secondary">
                            Avg Cost
                          </Typography>
                          <Typography variant="body2" fontWeight={700}>
                            ${item.avg_cost?.toFixed(2)}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={4}>
                          <Typography variant="caption" color="text.secondary">
                            Avg Duration
                          </Typography>
                          <Typography variant="body2" fontWeight={700}>
                            {item.avg_duration?.toFixed(1)} hrs
                          </Typography>
                        </Grid>
                      </Grid>
                      <Alert severity="error" sx={{ mt: 1 }} variant="outlined">
                        <strong>Action:</strong> Schedule comprehensive inspection and allocate emergency maintenance
                        budget. Consider equipment replacement if repair costs exceed 60% of replacement value.
                      </Alert>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Paper>

        {/* Preventive Planning */}
        <Paper sx={{ p: 3, mb: 3, borderLeft: `6px solid ${COLORS.warning}` }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <WatchLater sx={{ fontSize: 32, color: COLORS.warning, mr: 1 }} />
            <Box>
              <Typography variant="h6" fontWeight={700} color="warning.main">
                PREVENTIVE PLANNING
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Reduce future failures through proactive maintenance
              </Typography>
            </Box>
          </Box>
          <Divider sx={{ mb: 2 }} />
          <Stack spacing={2}>
            {topRecurrent.map((item, idx) => (
              <Card key={idx} variant="outlined" sx={{ bgcolor: '#FFF3E0' }}>
                <CardContent>
                  <Typography variant="body1" fontWeight={600} gutterBottom>
                    {idx + 1}. {item.SubsystemDescription}
                  </Typography>
                  <Grid container spacing={1}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="caption" color="text.secondary">
                        Frequency
                      </Typography>
                      <Typography variant="body2" fontWeight={700}>
                        {item.frequency_per_month?.toFixed(1)} defects/month
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="caption" color="text.secondary">
                        Total Count
                      </Typography>
                      <Typography variant="body2" fontWeight={700}>
                        {item.total_count?.toLocaleString()} defects
                      </Typography>
                    </Grid>
                  </Grid>
                  <Alert severity="warning" sx={{ mt: 1 }} variant="outlined">
                    <strong>Action:</strong> Implement predictive maintenance schedule using XGBoost forecast model.
                    Increase inspection frequency by 30%. Consider root cause analysis to identify systemic issues.
                  </Alert>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Paper>

        {/* Monitoring and Optimization */}
        <Paper sx={{ p: 3, mb: 3, borderLeft: `6px solid ${COLORS.info}` }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Cloud sx={{ fontSize: 32, color: COLORS.info, mr: 1 }} />
            <Box>
              <Typography variant="h6" fontWeight={700} color="info.main">
                ENVIRONMENTAL MONITORING
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Weather-based predictive maintenance strategies
              </Typography>
            </Box>
          </Box>
          <Divider sx={{ mb: 2 }} />
          <Stack spacing={2}>
            {envSensitive.map((item, idx) => (
              <Card key={idx} variant="outlined" sx={{ bgcolor: '#E3F2FD' }}>
                <CardContent>
                  <Typography variant="body1" fontWeight={600} gutterBottom>
                    {idx + 1}. {item.SubsystemDescription}
                  </Typography>
                  <Grid container spacing={1}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="caption" color="text.secondary">
                        Weather Factor
                      </Typography>
                      <Typography variant="body2" fontWeight={700}>
                        {item.strongest_weather_factor}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="caption" color="text.secondary">
                        Correlation
                      </Typography>
                      <Typography variant="body2" fontWeight={700}>
                        {Math.abs(item.strongest_correlation || 0).toFixed(3)}
                      </Typography>
                    </Grid>
                  </Grid>
                  <Alert severity="info" sx={{ mt: 1 }} variant="outlined">
                    <strong>Action:</strong> Deploy environmental impact ML model (R²=0.81) to predict failure risk
                    based on weather forecasts. Implement automated alerts when risk thresholds are exceeded.
                  </Alert>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Paper>

        {/* Strategic Summary */}
        <Paper sx={{ p: 3, background: 'linear-gradient(135deg, #E8EAF6 0%, #C5CAE9 100%)' }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Executive Summary
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Box sx={{ textAlign: 'center', p: 2 }}>
                <Typography variant="h3" fontWeight={700} color="error.main">
                  {topSevere.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Critical subsystems
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ textAlign: 'center', p: 2 }}>
                <Typography variant="h3" fontWeight={700} color="warning.main">
                  {topRecurrent.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  High-frequency subsystems
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ textAlign: 'center', p: 2 }}>
                <Typography variant="h3" fontWeight={700} color="info.main">
                  {envSensitive.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Weather-sensitive subsystems
                </Typography>
              </Box>
            </Grid>
          </Grid>
          <Alert severity="success" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Overall Recommendation:</strong> Prioritize immediate repairs for high-severity subsystems,
              implement XGBoost-based forecasting for recurrent defects, and deploy environmental monitoring for
              weather-sensitive systems. Expected cost reduction: 15-25% within 12 months.
            </Typography>
          </Alert>
        </Paper>
      </Box>
    );
  };

  // ==================== MAIN RENDER ====================

  if (loading) {
    return (
      <Container>
        <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '80vh', gap: 3 }}>
          <CircularProgress size={60} thickness={4} />
          <Typography variant="h6" color="text.secondary">
            Loading analytics data...
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Open browser console (F12) to see detailed loading progress
          </Typography>
          <button
            onClick={() => {
              sessionStorage.clear();
              window.location.reload();
            }}
            style={{
              padding: '10px 20px',
              marginTop: '20px',
              cursor: 'pointer',
              backgroundColor: '#1976d2',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '14px'
            }}
          >
            Clear Cache & Reload
          </button>
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Alert severity="error" sx={{ mt: 4 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Box sx={{ bgcolor: COLORS.bgDeepNavy, minHeight: '100vh', py: 4 }}>
      <Container maxWidth="xl">
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h3" fontWeight={700} gutterBottom sx={{ color: 'white' }}>
            🎯 Defect Analytics Intelligence
          </Typography>
          <Typography variant="body1" sx={{ color: '#94A3B8' }}>
            Master's-Level Predictive Maintenance Analytics Platform for Faculty Managers
          </Typography>
        </Box>

        {/* Filters */}
        <Paper sx={{ p: 3, mb: 3, bgcolor: COLORS.bgNavyCard, boxShadow: 3 }}>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom sx={{ mb: 2, color: 'white' }}>
            🔍 Drill-Down Filters
          </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>University</InputLabel>
              <Select
                value={selectedUniversity}
                label="University"
                onChange={(e) => handleUniversityChange(e.target.value)}
              >
                <MenuItem value="">
                  <em>All Universities</em>
                </MenuItem>
                {universities.map(uni => (
                  <MenuItem key={uni} value={uni}>
                    University {uni}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small" disabled={!selectedUniversity}>
              <InputLabel>Building</InputLabel>
              <Select
                value={selectedBuilding}
                label="Building"
                onChange={(e) => handleBuildingChange(e.target.value)}
              >
                <MenuItem value="">
                  <em>{selectedUniversity ? 'All Buildings' : 'Select University First'}</em>
                </MenuItem>
                {getAvailableBuildings().map(bldg => (
                  <MenuItem key={bldg} value={bldg}>
                    {bldg}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small" disabled={!selectedUniversity}>
              <InputLabel>Subsystem</InputLabel>
              <Select
                value={selectedSubsystem}
                label="Subsystem"
                onChange={(e) => setSelectedSubsystem(e.target.value)}
              >
                <MenuItem value="">
                  <em>All Subsystems</em>
                </MenuItem>
                {getAvailableSubsystems().map(sub => (
                  <MenuItem key={sub} value={sub}>
                    {sub}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Box
              sx={{
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                bgcolor: COLORS.bgNavyLighter,
                borderRadius: 1,
                px: 2,
                border: `1px solid ${COLORS.monitor}`
              }}
            >
              <Typography variant="body2" fontWeight={600} color="primary" textAlign="center">
                {getContextLabel()}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

        {/* Tabs */}
        <Paper sx={{ boxShadow: 3, bgcolor: COLORS.bgNavyCard }}>
          <Tabs
            value={activeTab}
            onChange={(e, newValue) => setActiveTab(newValue)}
            variant="scrollable"
            scrollButtons="auto"
            sx={{
              borderBottom: 1,
              borderColor: '#334155',
              '& .MuiTab-root': {
                fontWeight: 600,
                fontSize: '0.9rem',
                textTransform: 'none',
                color: '#94A3B8',
                '&.Mui-selected': {
                  color: COLORS.monitor
                }
              }
            }}
          >
            <Tab label="Overview" icon={<Assessment />} iconPosition="start" />
            <Tab label="Recurrence Analysis" icon={<TrendingUp />} iconPosition="start" />
            <Tab label="Severity Analysis" icon={<Warning />} iconPosition="start" />
            <Tab label="Environmental" icon={<Cloud />} iconPosition="start" />
            <Tab label="AI/ML Performance" icon={<Psychology />} iconPosition="start" />
            <Tab label="Recommendations" icon={<EmojiObjects />} iconPosition="start" />
          </Tabs>

          <Box sx={{ p: 4, bgcolor: COLORS.bgDeepNavy }}>
            {activeTab === 0 && <OverviewTab />}
            {activeTab === 1 && <RecurrenceTab />}
            {activeTab === 2 && <SeverityTab />}
            {activeTab === 3 && <EnvironmentalTab />}
            {activeTab === 4 && <AIMLPerformanceTab />}
            {activeTab === 5 && <RecommendationsTab />}
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default DefectAnalytics;
