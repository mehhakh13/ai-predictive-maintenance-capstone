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
  TableSortLabel,
  Button,
  Chip,
  CircularProgress,
  Alert
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
  Cell
} from 'recharts';
import { Download, TrendingUp, Warning, Cloud } from '@mui/icons-material';

const DefectAnalytics = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [viewLevel, setViewLevel] = useState('global'); // global, university, building
  const [selectedUniversity, setSelectedUniversity] = useState('all');
  const [selectedBuilding, setSelectedBuilding] = useState('all');

  // Data states
  const [globalData, setGlobalData] = useState([]);
  const [universityData, setUniversityData] = useState([]);
  const [buildingData, setBuildingData] = useState([]);
  const [universities, setUniversities] = useState([]);
  const [buildings, setBuildings] = useState([]);

  // Table sorting
  const [orderBy, setOrderBy] = useState('');
  const [order, setOrder] = useState('desc');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);

      // Load global rankings
      const globalResponse = await fetch('/data/defect_analytics/global_rankings.csv');
      const globalText = await globalResponse.text();
      const global = parseCSV(globalText);
      setGlobalData(global);

      // Load university rankings
      const uniResponse = await fetch('/data/defect_analytics/university_rankings.csv');
      const uniText = await uniResponse.text();
      const uni = parseCSV(uniText);
      setUniversityData(uni);

      // Extract unique universities
      const uniqueUnis = [...new Set(uni.map(row => row.UniversityID))].sort();
      setUniversities(uniqueUnis);

      // Load building rankings
      try {
        const bldgResponse = await fetch('/data/defect_analytics/building_rankings.csv');
        const bldgText = await bldgResponse.text();
        const bldg = parseCSV(bldgText);
        setBuildingData(bldg);

        // Extract unique buildings
        const uniqueBldgs = [...new Set(bldg.map(row => row.BuildingName))].sort();
        setBuildings(uniqueBldgs);
      } catch (e) {
        console.log('Building data not available');
      }

      setLoading(false);
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load analytics data');
      setLoading(false);
    }
  };

  const parseCSV = (text) => {
    const lines = text.trim().split('\n');
    const headers = lines[0].split(',');

    return lines.slice(1).map(line => {
      const values = line.split(',');
      const row = {};
      headers.forEach((header, i) => {
        const value = values[i];
        // Try to convert to number
        const numValue = parseFloat(value);
        row[header] = isNaN(numValue) ? value : numValue;
      });
      return row;
    });
  };

  const getFilteredData = () => {
    if (viewLevel === 'global') {
      return globalData;
    } else if (viewLevel === 'university') {
      if (selectedUniversity === 'all') return universityData;
      return universityData.filter(row => row.UniversityID == selectedUniversity);
    } else if (viewLevel === 'building') {
      if (selectedBuilding === 'all') return buildingData;
      return buildingData.filter(row => row.BuildingName === selectedBuilding);
    }
    return [];
  };

  const handleSort = (property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const sortData = (data, orderBy, order) => {
    if (!orderBy) return data;

    return [...data].sort((a, b) => {
      if (order === 'asc') {
        return a[orderBy] > b[orderBy] ? 1 : -1;
      } else {
        return a[orderBy] < b[orderBy] ? 1 : -1;
      }
    });
  };

  const exportToCSV = (data, filename) => {
    if (!data || data.length === 0) return;

    const headers = Object.keys(data[0]);
    const csv = [
      headers.join(','),
      ...data.map(row => headers.map(h => row[h]).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
  };

  const getBarColor = (index) => {
    const colors = ['#1976d2', '#2196f3', '#42a5f5', '#64b5f6', '#90caf9'];
    return colors[index % colors.length];
  };

  const RecurrenceTab = () => {
    const data = getFilteredData();
    const sorted = sortData(data, 'recurrence_rank', 'asc').slice(0, 20);

    const chartData = sorted.map(row => ({
      name: row.SubsystemDescription?.substring(0, 20) || 'Unknown',
      frequency: parseFloat(row.frequency_per_month) || 0,
      count: parseInt(row.total_count) || 0
    }));

    return (
      <Box>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
            <TrendingUp sx={{ mr: 1 }} />
            Most Recurrent Defects
          </Typography>
          <Button
            startIcon={<Download />}
            onClick={() => exportToCSV(sorted, 'recurrence_rankings.csv')}
          >
            Export
          </Button>
        </Box>

        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Frequency per Month (Top 20)
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={150} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload[0]) {
                    return (
                      <Paper sx={{ p: 1 }}>
                        <Typography variant="caption" display="block">
                          <strong>{payload[0].payload.name}</strong>
                        </Typography>
                        <Typography variant="caption" display="block">
                          Frequency: {payload[0].value.toFixed(2)}/month
                        </Typography>
                        <Typography variant="caption" display="block">
                          Total: {payload[0].payload.count} occurrences
                        </Typography>
                      </Paper>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="frequency" fill="#1976d2">
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(index)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Paper>

        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>
                  <TableSortLabel
                    active={orderBy === 'recurrence_rank'}
                    direction={order}
                    onClick={() => handleSort('recurrence_rank')}
                  >
                    Rank
                  </TableSortLabel>
                </TableCell>
                <TableCell>Subsystem</TableCell>
                <TableCell align="right">
                  <TableSortLabel
                    active={orderBy === 'total_count'}
                    direction={order}
                    onClick={() => handleSort('total_count')}
                  >
                    Total Count
                  </TableSortLabel>
                </TableCell>
                <TableCell align="right">
                  <TableSortLabel
                    active={orderBy === 'frequency_per_month'}
                    direction={order}
                    onClick={() => handleSort('frequency_per_month')}
                  >
                    Frequency/Month
                  </TableSortLabel>
                </TableCell>
                <TableCell align="right">Months Observed</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortData(sorted, orderBy, order).map((row) => (
                <TableRow key={row.recurrence_rank} hover>
                  <TableCell>
                    <Chip
                      label={row.recurrence_rank}
                      size="small"
                      color={row.recurrence_rank <= 3 ? 'error' : 'default'}
                    />
                  </TableCell>
                  <TableCell>{row.SubsystemDescription}</TableCell>
                  <TableCell align="right">{row.total_count?.toLocaleString()}</TableCell>
                  <TableCell align="right">{row.frequency_per_month?.toFixed(2)}</TableCell>
                  <TableCell align="right">{Math.round(row.months_observed)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    );
  };

  const SeverityTab = () => {
    const data = getFilteredData();
    const sorted = sortData(data, 'severity_rank', 'asc').slice(0, 20);

    const chartData = sorted.map(row => ({
      name: row.SubsystemDescription?.substring(0, 20) || 'Unknown',
      score: parseFloat(row.severity_score) || 0,
      cost: parseFloat(row.avg_cost) || 0,
      duration: parseFloat(row.avg_duration) || 0
    }));

    return (
      <Box>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
            <Warning sx={{ mr: 1 }} />
            Highest Severity Defects
          </Typography>
          <Button
            startIcon={<Download />}
            onClick={() => exportToCSV(sorted, 'severity_rankings.csv')}
          >
            Export
          </Button>
        </Box>

        <Alert severity="info" sx={{ mb: 2 }}>
          Severity Score = Cost (50%) + Duration (30%) + Priority (20%)
        </Alert>

        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Severity Score (Top 20)
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} />
              <YAxis dataKey="name" type="category" width={150} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload[0]) {
                    return (
                      <Paper sx={{ p: 1 }}>
                        <Typography variant="caption" display="block">
                          <strong>{payload[0].payload.name}</strong>
                        </Typography>
                        <Typography variant="caption" display="block">
                          Severity Score: {payload[0].value.toFixed(1)}
                        </Typography>
                        <Typography variant="caption" display="block">
                          Avg Cost: ${payload[0].payload.cost.toFixed(0)}
                        </Typography>
                        <Typography variant="caption" display="block">
                          Avg Duration: {payload[0].payload.duration.toFixed(1)}h
                        </Typography>
                      </Paper>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="score" fill="#d32f2f">
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.score > 80 ? '#d32f2f' : entry.score > 50 ? '#ff9800' : '#fbc02d'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Paper>

        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>
                  <TableSortLabel
                    active={orderBy === 'severity_rank'}
                    direction={order}
                    onClick={() => handleSort('severity_rank')}
                  >
                    Rank
                  </TableSortLabel>
                </TableCell>
                <TableCell>Subsystem</TableCell>
                <TableCell align="right">
                  <TableSortLabel
                    active={orderBy === 'severity_score'}
                    direction={order}
                    onClick={() => handleSort('severity_score')}
                  >
                    Severity Score
                  </TableSortLabel>
                </TableCell>
                <TableCell align="right">Avg Cost</TableCell>
                <TableCell align="right">Avg Duration (hrs)</TableCell>
                <TableCell align="right">Avg Priority</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortData(sorted, orderBy, order).map((row) => (
                <TableRow key={row.severity_rank} hover>
                  <TableCell>
                    <Chip
                      label={row.severity_rank}
                      size="small"
                      color={row.severity_rank <= 3 ? 'error' : 'default'}
                    />
                  </TableCell>
                  <TableCell>{row.SubsystemDescription}</TableCell>
                  <TableCell align="right">
                    <Chip
                      label={row.severity_score?.toFixed(1)}
                      size="small"
                      color={
                        row.severity_score > 80 ? 'error' :
                        row.severity_score > 50 ? 'warning' : 'default'
                      }
                    />
                  </TableCell>
                  <TableCell align="right">${row.avg_cost?.toFixed(0)}</TableCell>
                  <TableCell align="right">{row.avg_duration?.toFixed(1)}</TableCell>
                  <TableCell align="right">{row.avg_priority?.toFixed(1)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    );
  };

  const EnvironmentalTab = () => {
    const data = getFilteredData();
    const sorted = sortData(data.filter(row => row.env_sensitivity_rank), 'env_sensitivity_rank', 'asc').slice(0, 20);

    const chartData = sorted.map(row => ({
      name: row.SubsystemDescription?.substring(0, 20) || 'Unknown',
      score: parseFloat(row.sensitivity_score) || 0,
      factor: row.strongest_weather_factor || 'N/A',
      correlation: parseFloat(row.strongest_correlation) || 0
    }));

    return (
      <Box>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
            <Cloud sx={{ mr: 1 }} />
            Most Environmentally Sensitive Defects
          </Typography>
          <Button
            startIcon={<Download />}
            onClick={() => exportToCSV(sorted, 'environmental_rankings.csv')}
          >
            Export
          </Button>
        </Box>

        <Alert severity="info" sx={{ mb: 2 }}>
          Environmental Sensitivity shows which defects are most affected by weather conditions (temperature, humidity, precipitation, etc.)
        </Alert>

        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Environmental Sensitivity Score (Top 20)
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} />
              <YAxis dataKey="name" type="category" width={150} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload[0]) {
                    return (
                      <Paper sx={{ p: 1 }}>
                        <Typography variant="caption" display="block">
                          <strong>{payload[0].payload.name}</strong>
                        </Typography>
                        <Typography variant="caption" display="block">
                          Sensitivity: {payload[0].value.toFixed(1)}
                        </Typography>
                        <Typography variant="caption" display="block">
                          Factor: {payload[0].payload.factor}
                        </Typography>
                        <Typography variant="caption" display="block">
                          Correlation: {payload[0].payload.correlation.toFixed(3)}
                        </Typography>
                      </Paper>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="score" fill="#388e3c">
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(index)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Paper>

        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>
                  <TableSortLabel
                    active={orderBy === 'env_sensitivity_rank'}
                    direction={order}
                    onClick={() => handleSort('env_sensitivity_rank')}
                  >
                    Rank
                  </TableSortLabel>
                </TableCell>
                <TableCell>Subsystem</TableCell>
                <TableCell align="right">
                  <TableSortLabel
                    active={orderBy === 'sensitivity_score'}
                    direction={order}
                    onClick={() => handleSort('sensitivity_score')}
                  >
                    Sensitivity Score
                  </TableSortLabel>
                </TableCell>
                <TableCell>Strongest Weather Factor</TableCell>
                <TableCell align="right">Correlation</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortData(sorted, orderBy, order).map((row) => (
                <TableRow key={row.env_sensitivity_rank} hover>
                  <TableCell>
                    <Chip
                      label={row.env_sensitivity_rank}
                      size="small"
                      color={row.env_sensitivity_rank <= 3 ? 'success' : 'default'}
                    />
                  </TableCell>
                  <TableCell>{row.SubsystemDescription}</TableCell>
                  <TableCell align="right">
                    {row.sensitivity_score?.toFixed(1)}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={row.strongest_weather_factor}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell align="right">
                    {row.strongest_correlation?.toFixed(3)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    );
  };

  if (loading) {
    return (
      <Container>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
          <CircularProgress />
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
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Defect Intelligence Analytics
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Strategic analysis of maintenance defects by recurrence, severity, and environmental sensitivity
      </Typography>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>View Level</InputLabel>
              <Select
                value={viewLevel}
                label="View Level"
                onChange={(e) => setViewLevel(e.target.value)}
              >
                <MenuItem value="global">Global (All Data)</MenuItem>
                <MenuItem value="university">By University</MenuItem>
                <MenuItem value="building">By Building</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {viewLevel === 'university' && (
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>University</InputLabel>
                <Select
                  value={selectedUniversity}
                  label="University"
                  onChange={(e) => setSelectedUniversity(e.target.value)}
                >
                  <MenuItem value="all">All Universities</MenuItem>
                  {universities.map(uni => (
                    <MenuItem key={uni} value={uni}>University {uni}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          )}

          {viewLevel === 'building' && (
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Building</InputLabel>
                <Select
                  value={selectedBuilding}
                  label="Building"
                  onChange={(e) => setSelectedBuilding(e.target.value)}
                >
                  <MenuItem value="all">All Buildings</MenuItem>
                  {buildings.map(bldg => (
                    <MenuItem key={bldg} value={bldg}>{bldg}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          )}
        </Grid>
      </Paper>

      {/* Tabs */}
      <Paper>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Recurrence Analysis" />
          <Tab label="Severity Analysis" />
          <Tab label="Environmental Sensitivity" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {activeTab === 0 && <RecurrenceTab />}
          {activeTab === 1 && <SeverityTab />}
          {activeTab === 2 && <EnvironmentalTab />}
        </Box>
      </Paper>
    </Container>
  );
};

export default DefectAnalytics;
