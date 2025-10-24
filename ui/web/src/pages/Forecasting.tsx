import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  CircularProgress,
  IconButton,
  Button,
  Tabs,
  Tab,
  LinearProgress,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Analytics as AnalyticsIcon,
  Inventory as InventoryIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { forecastingAPI } from '../services/forecastingAPI';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`forecast-tabpanel-${index}`}
      aria-labelledby={`forecast-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const ForecastingPage: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState(0);

  // Fetch forecasting data - use dashboard endpoint only for faster loading
  const { data: dashboardData, isLoading: dashboardLoading, refetch: refetchDashboard, error: dashboardError } = useQuery(
    'forecasting-dashboard',
    forecastingAPI.getDashboardSummary,
    { 
      refetchInterval: 300000, // Refetch every 5 minutes
      retry: 1,
      retryDelay: 200,
      staleTime: 30000, // Consider data fresh for 30 seconds
      cacheTime: 300000, // Keep in cache for 5 minutes
      refetchOnWindowFocus: false // Don't refetch when window gains focus
    }
  );

  // Use dashboard data for forecast summary as well (no separate call)
  const forecastSummary = dashboardData ? {
    total_skus: dashboardData.business_intelligence?.total_skus || 0,
    forecast_summary: {} // We'll use dashboard data instead
  } : null;

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return <TrendingUpIcon color="success" />;
      case 'decreasing':
        return <TrendingDownIcon color="error" />;
      default:
        return <TrendingFlatIcon color="info" />;
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      default:
        return 'success';
    }
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 0.9) return 'success';
    if (accuracy >= 0.8) return 'info';
    if (accuracy >= 0.7) return 'warning';
    return 'error';
  };

  // Show error if there are issues
  if (dashboardError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Error loading forecasting data: {dashboardError instanceof Error ? dashboardError.message : 'Unknown error'}
        </Alert>
        <Button onClick={() => {
          refetchDashboard();
        }} variant="contained">
          Retry
        </Button>
      </Box>
    );
  }

  if (dashboardLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Demand Forecasting Dashboard
          </Typography>
          <CircularProgress size={24} />
        </Box>
        
        {/* Show skeleton loading for cards */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {[1, 2, 3, 4].map((i) => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    <Typography variant="h6">Loading...</Typography>
                  </Box>
                  <Typography variant="h4" sx={{ mt: 1 }}>
                    --
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
        
        <Typography variant="body1" sx={{ textAlign: 'center', color: 'text.secondary' }}>
          Loading forecasting data... This may take a few seconds.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Demand Forecasting Dashboard
        </Typography>
        <IconButton onClick={() => {
          refetchDashboard();
        }} color="primary">
          <RefreshIcon />
        </IconButton>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <AnalyticsIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" component="div">
                  Products Forecasted
                </Typography>
              </Box>
              <Typography variant="h4" component="div" sx={{ mt: 1 }}>
                {forecastSummary?.total_skus || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <WarningIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6" component="div">
                  Reorder Alerts
                </Typography>
              </Box>
              <Typography variant="h4" component="div" sx={{ mt: 1 }}>
                {dashboardData?.reorder_recommendations?.filter((r: any) => 
                  r.urgency_level === 'HIGH' || r.urgency_level === 'CRITICAL'
                ).length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SpeedIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="h6" component="div">
                  Avg Accuracy
                </Typography>
              </Box>
              <Typography variant="h4" component="div" sx={{ mt: 1 }}>
                {dashboardData?.model_performance ? 
                  `${(dashboardData.model_performance.reduce((acc: number, m: any) => acc + m.accuracy_score, 0) / dashboardData.model_performance.length * 100).toFixed(1)}%` 
                  : 'N/A'
                }
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <InventoryIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="h6" component="div">
                  Models Active
                </Typography>
              </Box>
              <Typography variant="h4" component="div" sx={{ mt: 1 }}>
                {dashboardData?.model_performance?.length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={selectedTab} onChange={handleTabChange} aria-label="forecasting tabs">
          <Tab label="Forecast Summary" />
          <Tab label="Reorder Recommendations" />
          <Tab label="Model Performance" />
          <Tab label="Business Intelligence" />
        </Tabs>
      </Box>

      {/* Forecast Summary Tab */}
      <TabPanel value={selectedTab} index={0}>
        <Typography variant="h5" gutterBottom>
          Product Demand Forecasts
        </Typography>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>SKU</TableCell>
                <TableCell>Avg Daily Demand</TableCell>
                <TableCell>Min Demand</TableCell>
                <TableCell>Max Demand</TableCell>
                <TableCell>Trend</TableCell>
                <TableCell>Forecast Date</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {forecastSummary?.forecast_summary && Object.entries(forecastSummary.forecast_summary).map(([sku, data]: [string, any]) => (
                <TableRow key={sku}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="bold">
                      {sku}
                    </Typography>
                  </TableCell>
                  <TableCell>{data.average_daily_demand.toFixed(1)}</TableCell>
                  <TableCell>{data.min_demand.toFixed(1)}</TableCell>
                  <TableCell>{data.max_demand.toFixed(1)}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {getTrendIcon(data.trend)}
                      <Typography variant="body2" sx={{ ml: 1, textTransform: 'capitalize' }}>
                        {data.trend}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    {new Date(data.forecast_date).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Reorder Recommendations Tab */}
      <TabPanel value={selectedTab} index={1}>
        <Typography variant="h5" gutterBottom>
          Reorder Recommendations
        </Typography>
        {dashboardData?.reorder_recommendations && dashboardData.reorder_recommendations.length > 0 ? (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>SKU</TableCell>
                  <TableCell>Current Stock</TableCell>
                  <TableCell>Recommended Order</TableCell>
                  <TableCell>Urgency</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell>Confidence</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {dashboardData.reorder_recommendations.map((rec: any, index: number) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Typography variant="body2" fontWeight="bold">
                        {rec.sku}
                      </Typography>
                    </TableCell>
                    <TableCell>{rec.current_stock}</TableCell>
                    <TableCell>{rec.recommended_order_quantity}</TableCell>
                    <TableCell>
                      <Chip 
                        label={rec.urgency_level} 
                        color={getUrgencyColor(rec.urgency_level.toLowerCase()) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{rec.reason}</TableCell>
                    <TableCell>{(rec.confidence_score * 100).toFixed(1)}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Alert severity="info">
            No reorder recommendations available at this time.
          </Alert>
        )}
      </TabPanel>

      {/* Model Performance Tab */}
      <TabPanel value={selectedTab} index={2}>
        <Typography variant="h5" gutterBottom>
          Model Performance Metrics
        </Typography>
        {dashboardData?.model_performance && dashboardData.model_performance.length > 0 ? (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Model Name</TableCell>
                  <TableCell>Accuracy</TableCell>
                  <TableCell>MAPE</TableCell>
                  <TableCell>Drift Score</TableCell>
                  <TableCell>Last Trained</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {dashboardData.model_performance.map((model: any, index: number) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Typography variant="body2" fontWeight="bold">
                        {model.model_name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={model.accuracy_score * 100} 
                          color={getAccuracyColor(model.accuracy_score) as any}
                          sx={{ width: 100, mr: 1 }}
                        />
                        <Typography variant="body2">
                          {(model.accuracy_score * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>{model.mape.toFixed(2)}%</TableCell>
                    <TableCell>{model.drift_score.toFixed(2)}</TableCell>
                    <TableCell>
                      {new Date(model.last_training_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Chip 
                        icon={model.status === 'HEALTHY' ? <CheckCircleIcon /> : <WarningIcon />}
                        label={model.status} 
                        color={model.status === 'HEALTHY' ? 'success' : model.status === 'WARNING' ? 'warning' : 'error'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Alert severity="info">
            No model performance data available.
          </Alert>
        )}
      </TabPanel>

      {/* Business Intelligence Tab */}
      <TabPanel value={selectedTab} index={3}>
        <Typography variant="h5" gutterBottom>
          Business Intelligence Summary
        </Typography>
        {dashboardData?.business_intelligence ? (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Overall Performance
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Forecast Accuracy: {(dashboardData.business_intelligence.forecast_accuracy * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total SKUs: {dashboardData.business_intelligence.total_skus}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Low Stock Items: {dashboardData.business_intelligence.low_stock_items}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Key Insights
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    High Demand Items: {dashboardData.business_intelligence.high_demand_items}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Reorder Recommendations: {dashboardData.business_intelligence.reorder_recommendations}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        ) : (
          <Alert severity="info">
            Business intelligence data is being generated...
          </Alert>
        )}
      </TabPanel>
    </Box>
  );
};

export default ForecastingPage;
