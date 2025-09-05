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
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Add as AddIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { inventoryAPI, InventoryItem } from '../services/api';

const Inventory: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [formData, setFormData] = useState<Partial<InventoryItem>>({});
  const queryClient = useQueryClient();

  const { data: inventoryItems, isLoading, error } = useQuery(
    'inventory',
    inventoryAPI.getAllItems
  );

  const createMutation = useMutation(inventoryAPI.createItem, {
    onSuccess: () => {
      queryClient.invalidateQueries('inventory');
      setOpen(false);
      setFormData({});
    },
  });

  const updateMutation = useMutation(
    ({ sku, data }: { sku: string; data: Partial<InventoryItem> }) =>
      inventoryAPI.updateItem(sku, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('inventory');
        setOpen(false);
        setSelectedItem(null);
        setFormData({});
      },
    }
  );

  const handleOpen = (item?: InventoryItem) => {
    if (item) {
      setSelectedItem(item);
      setFormData(item);
    } else {
      setSelectedItem(null);
      setFormData({});
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setSelectedItem(null);
    setFormData({});
  };

  const handleSubmit = () => {
    if (selectedItem) {
      updateMutation.mutate({ sku: selectedItem.sku, data: formData });
    } else {
      createMutation.mutate(formData as Omit<InventoryItem, 'updated_at'>);
    }
  };

  const columns: GridColDef[] = [
    { field: 'sku', headerName: 'SKU', width: 150 },
    { field: 'name', headerName: 'Name', width: 200 },
    { field: 'quantity', headerName: 'Quantity', width: 120 },
    { field: 'location', headerName: 'Location', width: 150 },
    { field: 'reorder_point', headerName: 'Reorder Point', width: 130 },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => {
        const isLowStock = params.row.quantity <= params.row.reorder_point;
        return (
          <Chip
            label={isLowStock ? 'Low Stock' : 'In Stock'}
            color={isLowStock ? 'warning' : 'success'}
            size="small"
          />
        );
      },
    },
    {
      field: 'updated_at',
      headerName: 'Last Updated',
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
          Edit
        </Button>
      ),
    },
  ];

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Inventory Management
        </Typography>
        <Alert severity="error">
          Failed to load inventory data. Please try again.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Inventory Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpen()}
        >
          Add Item
        </Button>
      </Box>

      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={inventoryItems || []}
          columns={columns}
          loading={isLoading}
          pageSize={10}
          rowsPerPageOptions={[10, 25, 50]}
          disableSelectionOnClick
          getRowId={(row) => row.sku}
        />
      </Paper>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedItem ? 'Edit Inventory Item' : 'Add New Inventory Item'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="SKU"
                value={formData.sku || ''}
                onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                disabled={!!selectedItem}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Name"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Quantity"
                type="number"
                value={formData.quantity || ''}
                onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) })}
                required
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Reorder Point"
                type="number"
                value={formData.reorder_point || ''}
                onChange={(e) => setFormData({ ...formData, reorder_point: parseInt(e.target.value) })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Location"
                value={formData.location || ''}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                required
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={createMutation.isLoading || updateMutation.isLoading}
          >
            {selectedItem ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Inventory;