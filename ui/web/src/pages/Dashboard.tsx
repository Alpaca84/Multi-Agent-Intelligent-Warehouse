import React from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Build as EquipmentIcon,
  Work as OperationsIcon,
  Security as SafetyIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { healthAPI, equipmentAPI, operationsAPI, safetyAPI } from '../services/api';

const Dashboard: React.FC = () => {
  const { data: healthStatus } = useQuery('health', healthAPI.check);
  const { data: equipmentItems } = useQuery('equipment', equipmentAPI.getAllItems);
  const { data: tasks } = useQuery('tasks', operationsAPI.getTasks);
  const { data: incidents } = useQuery('incidents', safetyAPI.getIncidents);

  const lowStockItems = equipmentItems?.filter(item => item.quantity <= item.reorder_point) || [];
  const pendingTasks = tasks?.filter(task => task.status === 'pending') || [];
  const recentIncidents = incidents?.slice(0, 5) || [];

  const stats = [
    {
      title: 'Total Equipment Items',
      value: equipmentItems?.length || 0,
      icon: <EquipmentIcon />,
      color: 'primary',
    },
    {
      title: 'Low Stock Equipment',
      value: lowStockItems.length,
      icon: <EquipmentIcon />,
      color: 'warning',
    },
    {
      title: 'Pending Tasks',
      value: pendingTasks.length,
      icon: <OperationsIcon />,
      color: 'info',
    },
    {
      title: 'Recent Incidents',
      value: recentIncidents.length,
      icon: <SafetyIcon />,
      color: 'error',
    },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      {/* System Status */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6">System Status</Typography>
          <Chip
            label={healthStatus?.ok ? 'Online' : 'Offline'}
            color={healthStatus?.ok ? 'success' : 'error'}
            variant="outlined"
          />
        </Box>
      </Paper>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{ color: `${stat.color}.main` }}>
                    {stat.icon}
                  </Box>
                  <Box>
                    <Typography variant="h4" component="div">
                      {stat.value}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {stat.title}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Low Stock Items */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Low Stock Items
            </Typography>
            {lowStockItems.length > 0 ? (
              <Box>
                {lowStockItems.map((item) => (
                  <Box key={item.sku} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body1">{item.name}</Typography>
                      <Chip label={`${item.quantity} left`} color="warning" size="small" />
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      SKU: {item.sku} | Location: {item.location}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={(item.quantity / item.reorder_point) * 100}
                      color="warning"
                      sx={{ mt: 1 }}
                    />
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography color="text.secondary">No low stock items</Typography>
            )}
          </Paper>
        </Grid>

        {/* Recent Tasks */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Tasks
            </Typography>
            {pendingTasks.length > 0 ? (
              <Box>
                {pendingTasks.slice(0, 5).map((task) => (
                  <Box key={task.id} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body1">{task.kind}</Typography>
                      <Chip label={task.status} color="info" size="small" />
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Assignee: {task.assignee || 'Unassigned'}
                    </Typography>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography color="text.secondary">No pending tasks</Typography>
            )}
          </Paper>
        </Grid>

        {/* Recent Incidents */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Safety Incidents
            </Typography>
            {recentIncidents.length > 0 ? (
              <Box>
                {recentIncidents.map((incident) => (
                  <Box key={incident.id} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body1">{incident.description}</Typography>
                      <Chip label={incident.severity} color="error" size="small" />
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Reported by: {incident.reported_by} | {new Date(incident.occurred_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography color="text.secondary">No recent incidents</Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
