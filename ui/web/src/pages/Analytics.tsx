import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useQuery } from 'react-query';
import { equipmentAPI, operationsAPI, safetyAPI } from '../services/api';

const Analytics: React.FC = () => {
  const { data: equipmentAssets } = useQuery('equipment', equipmentAPI.getAllAssets);
  const { data: tasks } = useQuery('tasks', operationsAPI.getTasks);
  const { data: incidents } = useQuery('incidents', safetyAPI.getIncidents);

  // Mock data for charts (in a real app, this would come from analytics API)
  const inventoryTrendData = [
    { month: 'Jan', items: 120, lowStock: 5 },
    { month: 'Feb', items: 125, lowStock: 3 },
    { month: 'Mar', items: 130, lowStock: 8 },
    { month: 'Apr', items: 135, lowStock: 4 },
    { month: 'May', items: 140, lowStock: 6 },
    { month: 'Jun', items: 145, lowStock: 2 },
  ];

  const taskStatusData = [
    { status: 'Completed', count: tasks?.filter(t => t.status === 'completed').length || 0 },
    { status: 'In Progress', count: tasks?.filter(t => t.status === 'in_progress').length || 0 },
    { status: 'Pending', count: tasks?.filter(t => t.status === 'pending').length || 0 },
  ];

  const incidentSeverityData = [
    { severity: 'Low', count: incidents?.filter(i => i.severity === 'low').length || 0 },
    { severity: 'Medium', count: incidents?.filter(i => i.severity === 'medium').length || 0 },
    { severity: 'High', count: incidents?.filter(i => i.severity === 'high').length || 0 },
    { severity: 'Critical', count: incidents?.filter(i => i.severity === 'critical').length || 0 },
  ];

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Analytics Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Inventory Trend */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Inventory Trend
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={inventoryTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="items" stroke="#8884d8" name="Total Items" />
                <Line type="monotone" dataKey="lowStock" stroke="#82ca9d" name="Low Stock Items" />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Task Status Distribution */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Task Status
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={taskStatusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ status, percent }) => `${status} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {taskStatusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Incident Severity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Incident Severity Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={incidentSeverityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="severity" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Key Metrics */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Key Metrics
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Total Equipment Assets
                    </Typography>
                    <Typography variant="h4">
                      {equipmentAssets?.length || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Active Tasks
                    </Typography>
                    <Typography variant="h4">
                      {tasks?.filter(t => t.status !== 'completed').length || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Safety Incidents
                    </Typography>
                    <Typography variant="h4">
                      {incidents?.length || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Maintenance Needed
                    </Typography>
                    <Typography variant="h4">
                      {equipmentAssets?.filter(asset => 
                        asset.status === 'maintenance' || 
                        (asset.next_pm_due && new Date(asset.next_pm_due) <= new Date())
                      ).length || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Analytics;
