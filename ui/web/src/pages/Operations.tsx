import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Chip,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Add as AddIcon, Assignment as AssignmentIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { operationsAPI, Task } from '../services/api';

const Operations: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [formData, setFormData] = useState<Partial<Task>>({});
  const queryClient = useQueryClient();

  const { data: tasks, isLoading, error } = useQuery(
    'tasks',
    operationsAPI.getTasks
  );

  const { data: workforceStatus } = useQuery(
    'workforce',
    operationsAPI.getWorkforceStatus
  );

  const assignMutation = useMutation(
    ({ taskId, assignee }: { taskId: number; assignee: string }) =>
      operationsAPI.assignTask(taskId, assignee),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('tasks');
        setOpen(false);
        setSelectedTask(null);
        setFormData({});
      },
    }
  );

  const handleOpen = (task?: Task) => {
    if (task) {
      setSelectedTask(task);
      setFormData(task);
    } else {
      setSelectedTask(null);
      setFormData({});
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setSelectedTask(null);
    setFormData({});
  };

  const handleSubmit = () => {
    if (selectedTask && formData.assignee) {
      assignMutation.mutate({ taskId: selectedTask.id, assignee: formData.assignee });
    }
  };

  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 80 },
    { field: 'kind', headerName: 'Task Type', width: 150 },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => {
        const status = params.value;
        const color = status === 'completed' ? 'success' : 
                     status === 'in_progress' ? 'info' : 'warning';
        return <Chip label={status} color={color} size="small" />;
      },
    },
    { field: 'assignee', headerName: 'Assignee', width: 150 },
    {
      field: 'created_at',
      headerName: 'Created',
      width: 150,
      renderCell: (params) => new Date(params.value).toLocaleDateString(),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      renderCell: (params) => (
        <Button
          size="small"
          onClick={() => handleOpen(params.row)}
        >
          Assign
        </Button>
      ),
    },
  ];

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Operations Management
        </Typography>
        <Alert severity="error">
          Failed to load operations data. Please try again.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Operations Management
      </Typography>

      {/* Workforce Status */}
      {workforceStatus && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Workforce Status
          </Typography>
          <Grid container spacing={2}>
            {workforceStatus.shifts && Object.entries(workforceStatus.shifts).map(([shift, data]: [string, any]) => (
              <Grid item xs={12} md={6} key={shift}>
                <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                  <Typography variant="subtitle1" sx={{ textTransform: 'capitalize' }}>
                    {shift} Shift
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {data.start_time} - {data.end_time}
                  </Typography>
                  <Typography variant="body2">
                    Employees: {data.total_count} | Active Tasks: {data.active_tasks}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Tasks Management */}
      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={tasks || []}
          columns={columns}
          loading={isLoading}
          pageSize={10}
          rowsPerPageOptions={[10, 25, 50]}
          disableSelectionOnClick
        />
      </Paper>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedTask ? 'Assign Task' : 'Create New Task'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Task Type"
                value={formData.kind || ''}
                onChange={(e) => setFormData({ ...formData, kind: e.target.value })}
                disabled={!!selectedTask}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Assignee</InputLabel>
                <Select
                  value={formData.assignee || ''}
                  onChange={(e) => setFormData({ ...formData, assignee: e.target.value })}
                  label="Assignee"
                >
                  <MenuItem value="John Smith">John Smith</MenuItem>
                  <MenuItem value="Sarah Johnson">Sarah Johnson</MenuItem>
                  <MenuItem value="Mike Wilson">Mike Wilson</MenuItem>
                  <MenuItem value="Lisa Brown">Lisa Brown</MenuItem>
                  <MenuItem value="David Lee">David Lee</MenuItem>
                  <MenuItem value="Amy Chen">Amy Chen</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.status || ''}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  label="Status"
                >
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="in_progress">In Progress</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={assignMutation.isLoading}
          >
            {selectedTask ? 'Assign' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Operations;
