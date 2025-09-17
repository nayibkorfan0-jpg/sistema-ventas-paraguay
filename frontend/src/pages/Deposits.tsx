import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Autocomplete,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Payment as PaymentIcon,
  Undo as UndoIcon,
  AccountBalance as AccountBalanceIcon,
  AttachMoney as MoneyIcon,
  TrendingUp as TrendingUpIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';

interface Customer {
  id: number;
  company_name: string;
}

interface Deposit {
  id: number;
  deposit_number: string;
  customer_id: number;
  customer_name: string;
  deposit_type: string;
  amount: number;
  currency: string;
  available_amount: number;
  status: string;
  deposit_date: string;
  expiry_date?: string;
  project_reference?: string;
  contract_reference?: string;
  notes?: string;
}

// Tipos de depósito específicos para Paraguay
const DEPOSIT_TYPES = [
  { value: 'ANTICIPO', label: 'Anticipo' },
  { value: 'SEÑA', label: 'Seña' },
  { value: 'GARANTIA', label: 'Garantía' },
  { value: 'CAUCION', label: 'Caución' },
  { value: 'PARCIAL', label: 'Pago Parcial' },
];

const CURRENCIES = [
  { value: 'PYG', label: 'Guaraníes (PYG)' },
  { value: 'USD', label: 'Dólares (USD)' },
];

export default function Deposits() {
  const { user } = useAuth();
  const [deposits, setDeposits] = useState<Deposit[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [actionDialogOpen, setActionDialogOpen] = useState(false);
  const [selectedDeposit, setSelectedDeposit] = useState<Deposit | null>(null);
  const [actionType, setActionType] = useState<'apply' | 'refund'>('apply');
  
  // Formulario para nuevo depósito
  const [formData, setFormData] = useState({
    customer_id: 0,
    deposit_type: 'ANTICIPO',
    amount: 0,
    currency: 'PYG',
    deposit_date: new Date().toISOString().split('T')[0],
    expiry_date: '',
    project_reference: '',
    contract_reference: '',
    notes: '',
  });

  // Formulario para aplicar/reembolsar
  const [actionData, setActionData] = useState({
    amount: 0,
    invoice_id: 0,
    reason: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [depositsData, customersData] = await Promise.all([
        apiService.getDeposits({ limit: 1000 }),
        apiService.getCustomers({ limit: 1000, is_active: true })
      ]);
      
      setDeposits(depositsData);
      setCustomers(customersData);
    } catch (err) {
      setError('Error al cargar depósitos');
      console.error('Error loading deposits:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = () => {
    setFormData({
      customer_id: 0,
      deposit_type: 'ANTICIPO',
      amount: 0,
      currency: 'PYG',
      deposit_date: new Date().toISOString().split('T')[0],
      expiry_date: '',
      project_reference: '',
      contract_reference: '',
      notes: '',
    });
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
  };

  const handleSubmit = async () => {
    try {
      await apiService.createDeposit(formData);
      await loadData();
      handleCloseDialog();
    } catch (err) {
      setError('Error al crear depósito');
      console.error('Error creating deposit:', err);
    }
  };

  const handleOpenActionDialog = (deposit: Deposit, action: 'apply' | 'refund') => {
    setSelectedDeposit(deposit);
    setActionType(action);
    setActionData({
      amount: action === 'apply' ? deposit.available_amount : 0,
      invoice_id: 0,
      reason: '',
    });
    setActionDialogOpen(true);
  };

  const handleCloseActionDialog = () => {
    setActionDialogOpen(false);
    setSelectedDeposit(null);
  };

  const handleApplyDeposit = async () => {
    if (!selectedDeposit) return;
    
    try {
      await apiService.applyDepositToInvoice(selectedDeposit.id, {
        invoice_id: actionData.invoice_id,
        amount: actionData.amount,
      });
      
      await loadData();
      handleCloseActionDialog();
    } catch (err) {
      setError('Error al aplicar depósito');
      console.error('Error applying deposit:', err);
    }
  };

  const handleRefundDeposit = async () => {
    if (!selectedDeposit) return;
    
    try {
      await apiService.refundDeposit(selectedDeposit.id, {
        amount: actionData.amount,
        reason: actionData.reason,
      });
      
      await loadData();
      handleCloseActionDialog();
    } catch (err) {
      setError('Error al reembolsar depósito');
      console.error('Error refunding deposit:', err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'success';
      case 'APPLIED': return 'info';
      case 'REFUNDED': return 'warning';
      case 'EXPIRED': return 'error';
      default: return 'default';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'ANTICIPO': return 'primary';
      case 'SEÑA': return 'secondary';
      case 'GARANTIA': return 'info';
      case 'CAUCION': return 'warning';
      case 'PARCIAL': return 'success';
      default: return 'default';
    }
  };

  const getTotalByType = (type: string) => {
    return deposits
      .filter(d => d.deposit_type === type && d.status === 'ACTIVE')
      .reduce((sum, d) => sum + d.available_amount, 0);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Encabezado */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Control de Depósitos
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenDialog}
          disabled={!user?.can_manage_deposits}
        >
          Nuevo Depósito
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Estadísticas por tipo de depósito (Paraguay) */}
      <Grid container spacing={2} mb={3}>
        {DEPOSIT_TYPES.map((type) => (
          <Grid item xs={12} sm={6} md={2.4} key={type.value}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <AccountBalanceIcon sx={{ fontSize: 40, color: `${getTypeColor(type.value)}.main`, mb: 1 }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Gs. {getTotalByType(type.value).toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {type.label}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {deposits.filter(d => d.deposit_type === type.value && d.status === 'ACTIVE').length} activos
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Resumen general */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <MoneyIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Gs. {deposits.filter(d => d.status === 'ACTIVE').reduce((sum, d) => sum + d.available_amount, 0).toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Disponible
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <TrendingUpIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Gs. {deposits.filter(d => d.status === 'APPLIED').reduce((sum, d) => sum + d.amount, 0).toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Aplicado
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <AssignmentIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {deposits.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Depósitos
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <AccountBalanceIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {deposits.filter(d => d.status === 'ACTIVE').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Depósitos Activos
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Información sobre el sistema de depósitos paraguayo */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          Sistema de Depósitos para Paraguay:
        </Typography>
        <Typography variant="body2">
          • <strong>ANTICIPO:</strong> Pago adelantado sobre servicios/productos futuros<br/>
          • <strong>SEÑA:</strong> Reserva de productos o servicios<br/>
          • <strong>GARANTÍA:</strong> Depósito de garantía por daños o incumplimiento<br/>
          • <strong>CAUCIÓN:</strong> Garantía monetaria por obligaciones contractuales<br/>
          • <strong>PARCIAL:</strong> Pago parcial de una factura mayor
        </Typography>
      </Alert>

      {/* Tabla de depósitos */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><strong>Número</strong></TableCell>
              <TableCell><strong>Cliente</strong></TableCell>
              <TableCell><strong>Tipo</strong></TableCell>
              <TableCell><strong>Monto Total</strong></TableCell>
              <TableCell><strong>Disponible</strong></TableCell>
              <TableCell><strong>Moneda</strong></TableCell>
              <TableCell><strong>Fecha</strong></TableCell>
              <TableCell><strong>Estado</strong></TableCell>
              <TableCell><strong>Acciones</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {deposits.map((deposit) => (
              <TableRow key={deposit.id}>
                <TableCell>{deposit.deposit_number}</TableCell>
                <TableCell>{deposit.customer_name}</TableCell>
                <TableCell>
                  <Chip 
                    label={DEPOSIT_TYPES.find(t => t.value === deposit.deposit_type)?.label || deposit.deposit_type}
                    color={getTypeColor(deposit.deposit_type)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{deposit.currency} {deposit.amount.toLocaleString()}</TableCell>
                <TableCell>
                  <Typography
                    color={deposit.available_amount > 0 ? 'success.main' : 'text.secondary'}
                    fontWeight={deposit.available_amount > 0 ? 600 : 400}
                  >
                    {deposit.currency} {deposit.available_amount.toLocaleString()}
                  </Typography>
                </TableCell>
                <TableCell>{deposit.currency}</TableCell>
                <TableCell>{new Date(deposit.deposit_date).toLocaleDateString()}</TableCell>
                <TableCell>
                  <Chip 
                    label={deposit.status} 
                    color={getStatusColor(deposit.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {deposit.status === 'ACTIVE' && deposit.available_amount > 0 && (
                    <>
                      <IconButton 
                        onClick={() => handleOpenActionDialog(deposit, 'apply')}
                        color="primary"
                        size="small"
                        title="Aplicar a Factura"
                      >
                        <PaymentIcon />
                      </IconButton>
                      <IconButton 
                        onClick={() => handleOpenActionDialog(deposit, 'refund')}
                        color="warning"
                        size="small"
                        title="Reembolsar"
                      >
                        <UndoIcon />
                      </IconButton>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog para crear depósito */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>Nuevo Depósito</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <Autocomplete
                options={customers}
                getOptionLabel={(option) => option.company_name}
                value={customers.find(c => c.id === formData.customer_id) || null}
                onChange={(_, value) => setFormData({...formData, customer_id: value?.id || 0})}
                renderInput={(params) => <TextField {...params} label="Cliente *" />}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Depósito</InputLabel>
                <Select
                  value={formData.deposit_type}
                  onChange={(e) => setFormData({...formData, deposit_type: e.target.value})}
                >
                  {DEPOSIT_TYPES.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Monto *"
                type="number"
                value={formData.amount}
                onChange={(e) => setFormData({...formData, amount: Number(e.target.value)})}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Moneda</InputLabel>
                <Select
                  value={formData.currency}
                  onChange={(e) => setFormData({...formData, currency: e.target.value})}
                >
                  {CURRENCIES.map((currency) => (
                    <MenuItem key={currency.value} value={currency.value}>
                      {currency.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Fecha del Depósito"
                type="date"
                value={formData.deposit_date}
                onChange={(e) => setFormData({...formData, deposit_date: e.target.value})}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Fecha de Vencimiento"
                type="date"
                value={formData.expiry_date}
                onChange={(e) => setFormData({...formData, expiry_date: e.target.value})}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Referencia de Proyecto"
                value={formData.project_reference}
                onChange={(e) => setFormData({...formData, project_reference: e.target.value})}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Referencia de Contrato"
                value={formData.contract_reference}
                onChange={(e) => setFormData({...formData, contract_reference: e.target.value})}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notas"
                multiline
                rows={3}
                value={formData.notes}
                onChange={(e) => setFormData({...formData, notes: e.target.value})}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>
            Cancelar
          </Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            disabled={!formData.customer_id || !formData.amount}
          >
            Crear Depósito
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog para aplicar/reembolsar depósito */}
      <Dialog open={actionDialogOpen} onClose={handleCloseActionDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {actionType === 'apply' ? 'Aplicar Depósito a Factura' : 'Reembolsar Depósito'}
        </DialogTitle>
        <DialogContent>
          {selectedDeposit && (
            <Box>
              <Typography variant="body1" gutterBottom>
                <strong>Depósito:</strong> {selectedDeposit.deposit_number}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Cliente:</strong> {selectedDeposit.customer_name}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Disponible:</strong> {selectedDeposit.currency} {selectedDeposit.available_amount.toLocaleString()}
              </Typography>
              
              <Grid container spacing={2} sx={{ mt: 2 }}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Monto"
                    type="number"
                    value={actionData.amount}
                    onChange={(e) => setActionData({...actionData, amount: Number(e.target.value)})}
                    inputProps={{
                      max: selectedDeposit.available_amount,
                      min: 0,
                    }}
                  />
                </Grid>
                
                {actionType === 'apply' && (
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="ID de Factura"
                      type="number"
                      value={actionData.invoice_id}
                      onChange={(e) => setActionData({...actionData, invoice_id: Number(e.target.value)})}
                    />
                  </Grid>
                )}
                
                {actionType === 'refund' && (
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Motivo del Reembolso *"
                      multiline
                      rows={3}
                      value={actionData.reason}
                      onChange={(e) => setActionData({...actionData, reason: e.target.value})}
                    />
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseActionDialog}>
            Cancelar
          </Button>
          <Button 
            onClick={actionType === 'apply' ? handleApplyDeposit : handleRefundDeposit}
            variant="contained"
            color={actionType === 'apply' ? 'primary' : 'warning'}
            disabled={
              !actionData.amount || 
              (actionType === 'apply' && !actionData.invoice_id) ||
              (actionType === 'refund' && !actionData.reason)
            }
          >
            {actionType === 'apply' ? 'Aplicar' : 'Reembolsar'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}