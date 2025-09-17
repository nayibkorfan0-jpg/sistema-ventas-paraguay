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
  ButtonGroup,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Print as PrintIcon,
  Save as SaveIcon,
  PrintOutlined as PrintOutlinedIcon,
  Receipt as ReceiptIcon,
  Payment as PaymentIcon,
  PictureAsPdf as PdfIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';

interface Customer {
  id: number;
  company_name: string;
}

interface Invoice {
  id: number;
  invoice_number: string;
  customer_id: number;
  customer_name: string;
  invoice_date: string;
  due_date: string;
  status: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  paid_amount: number;
  balance_due: number;
  currency: string;
  notes?: string;
}

export default function Invoices() {
  const { user } = useAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingInvoice, setEditingInvoice] = useState<Invoice | null>(null);
  const [processingAction, setProcessingAction] = useState<string>('');
  
  // Formulario
  const [formData, setFormData] = useState({
    customer_id: 0,
    invoice_date: new Date().toISOString().split('T')[0],
    due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 días
    currency: 'PYG',
    notes: '',
    lines: [] as any[],
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [invoicesData, customersData] = await Promise.all([
        apiService.getInvoices({ limit: 1000 }),
        apiService.getCustomers({ limit: 1000, is_active: true })
      ]);
      
      setInvoices(invoicesData);
      setCustomers(customersData);
    } catch (err) {
      setError('Error al cargar facturas');
      console.error('Error loading invoices:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (invoice?: Invoice) => {
    if (invoice) {
      setEditingInvoice(invoice);
      setFormData({
        customer_id: invoice.customer_id,
        invoice_date: invoice.invoice_date,
        due_date: invoice.due_date,
        currency: invoice.currency,
        notes: invoice.notes || '',
        lines: [],
      });
    } else {
      setEditingInvoice(null);
      setFormData({
        customer_id: 0,
        invoice_date: new Date().toISOString().split('T')[0],
        due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        currency: 'PYG',
        notes: '',
        lines: [],
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingInvoice(null);
  };

  // Opciones de guardado que pidió el usuario
  const handleSave = async () => {
    try {
      setProcessingAction('save');
      
      if (editingInvoice) {
        await apiService.updateInvoice(editingInvoice.id, formData);
      } else {
        await apiService.createInvoice(formData);
      }
      
      await loadData();
      handleCloseDialog();
    } catch (err) {
      setError('Error al guardar factura');
      console.error('Error saving invoice:', err);
    } finally {
      setProcessingAction('');
    }
  };

  const handleSaveAndPrint = async () => {
    try {
      setProcessingAction('save_print');
      
      let invoiceId;
      if (editingInvoice) {
        await apiService.updateInvoice(editingInvoice.id, formData);
        invoiceId = editingInvoice.id;
      } else {
        const newInvoice = await apiService.createInvoice(formData);
        invoiceId = newInvoice.id;
      }
      
      // Imprimir directamente después de guardar
      await handlePrint({ id: invoiceId } as Invoice);
      
      await loadData();
      handleCloseDialog();
    } catch (err) {
      setError('Error al guardar e imprimir factura');
      console.error('Error saving and printing invoice:', err);
    } finally {
      setProcessingAction('');
    }
  };

  const handlePrint = async (invoice: Invoice) => {
    try {
      setProcessingAction('print');
      
      // Generar PDF desde el backend y abrir en nueva ventana para imprimir
      const response = await fetch(`/api/invoices/${invoice.id}/pdf`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Error al generar PDF');
      }
      
      // Convertir respuesta a blob y crear URL
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      
      // Abrir PDF en nueva ventana para impresión
      const printWindow = window.open(url, '_blank');
      if (printWindow) {
        printWindow.onload = () => {
          printWindow.print();
        };
      }
      
      // Limpiar URL después de un tiempo
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
      }, 1000);
      
    } catch (err) {
      setError('Error al imprimir factura');
      console.error('Error printing invoice:', err);
    } finally {
      setProcessingAction('');
    }
  };

  const handleGeneratePdf = async (invoice: Invoice) => {
    try {
      setProcessingAction('pdf');
      
      // Descargar PDF desde el backend
      const response = await fetch(`/api/invoices/${invoice.id}/pdf`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Error al generar PDF');
      }
      
      // Convertir respuesta a blob y crear descarga
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `factura_${invoice.invoice_number}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
    } catch (err) {
      setError('Error al generar PDF');
      console.error('Error generating PDF:', err);
    } finally {
      setProcessingAction('');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'DRAFT': return 'default';
      case 'SENT': return 'info';
      case 'PAID': return 'success';
      case 'OVERDUE': return 'error';
      case 'PARTIALLY_PAID': return 'warning';
      default: return 'default';
    }
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
          Gestión de Facturas
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Nueva Factura
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Estadísticas rápidas */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <ReceiptIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {invoices.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Facturas
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <CheckIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {invoices.filter(i => i.status === 'PAID').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Pagadas
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <PaymentIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {invoices.filter(i => i.status === 'OVERDUE').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Vencidas
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <PdfIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Gs. {invoices.reduce((sum, i) => sum + (i.balance_due || 0), 0).toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Por Cobrar
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabla de facturas */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><strong>Número</strong></TableCell>
              <TableCell><strong>Cliente</strong></TableCell>
              <TableCell><strong>Fecha</strong></TableCell>
              <TableCell><strong>Vencimiento</strong></TableCell>
              <TableCell><strong>Total</strong></TableCell>
              <TableCell><strong>Pagado</strong></TableCell>
              <TableCell><strong>Saldo</strong></TableCell>
              <TableCell><strong>Estado</strong></TableCell>
              <TableCell><strong>Acciones</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {invoices.map((invoice) => (
              <TableRow key={invoice.id}>
                <TableCell>{invoice.invoice_number}</TableCell>
                <TableCell>{invoice.customer_name}</TableCell>
                <TableCell>{new Date(invoice.invoice_date).toLocaleDateString()}</TableCell>
                <TableCell>{new Date(invoice.due_date).toLocaleDateString()}</TableCell>
                <TableCell>{invoice.currency} {invoice.total_amount.toLocaleString()}</TableCell>
                <TableCell>{invoice.currency} {invoice.paid_amount.toLocaleString()}</TableCell>
                <TableCell>
                  <Typography 
                    color={invoice.balance_due > 0 ? 'error' : 'success.main'}
                    fontWeight={invoice.balance_due > 0 ? 600 : 400}
                  >
                    {invoice.currency} {invoice.balance_due.toLocaleString()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip 
                    label={invoice.status} 
                    color={getStatusColor(invoice.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <ButtonGroup size="small" variant="outlined">
                    <Tooltip title="Editar">
                      <IconButton 
                        onClick={() => handleOpenDialog(invoice)}
                        color="primary"
                        size="small"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="Imprimir">
                      <IconButton 
                        onClick={() => handlePrint(invoice)}
                        color="info"
                        size="small"
                        disabled={processingAction === 'print'}
                      >
                        {processingAction === 'print' ? 
                          <CircularProgress size={16} /> : 
                          <PrintIcon fontSize="small" />
                        }
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="Descargar PDF">
                      <IconButton 
                        onClick={() => handleGeneratePdf(invoice)}
                        color="secondary"
                        size="small"
                        disabled={processingAction === 'pdf'}
                      >
                        {processingAction === 'pdf' ? 
                          <CircularProgress size={16} /> : 
                          <PdfIcon fontSize="small" />
                        }
                      </IconButton>
                    </Tooltip>
                  </ButtonGroup>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog para crear/editar factura */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingInvoice ? 'Editar Factura' : 'Nueva Factura'}
        </DialogTitle>
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
              <TextField
                fullWidth
                select
                label="Moneda"
                value={formData.currency}
                onChange={(e) => setFormData({...formData, currency: e.target.value})}
              >
                <MenuItem value="PYG">Guaraníes (PYG)</MenuItem>
                <MenuItem value="USD">Dólares (USD)</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Fecha de Factura"
                type="date"
                value={formData.invoice_date}
                onChange={(e) => setFormData({...formData, invoice_date: e.target.value})}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Fecha de Vencimiento"
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData({...formData, due_date: e.target.value})}
                InputLabelProps={{ shrink: true }}
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
            
            {/* Información sobre productos */}
            <Grid item xs={12}>
              <Alert severity="info">
                <Typography variant="subtitle2" gutterBottom>
                  Agregar productos a la factura:
                </Typography>
                <Typography variant="body2">
                  Para agregar productos/servicios a esta factura, use el sistema de cotizaciones 
                  y conviértalas a facturas, o implemente la funcionalidad de líneas de productos aquí.
                </Typography>
              </Alert>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>
            Cancelar
          </Button>
          
          <ButtonGroup variant="contained">
            <Button 
              onClick={handleSave} 
              disabled={!formData.customer_id || processingAction !== ''}
              startIcon={processingAction === 'save' ? <CircularProgress size={16} /> : <SaveIcon />}
            >
              Guardar
            </Button>
            
            <Button 
              onClick={handleSaveAndPrint} 
              disabled={!formData.customer_id || processingAction !== ''}
              startIcon={processingAction === 'save_print' ? <CircularProgress size={16} /> : <PrintOutlinedIcon />}
            >
              Guardar e Imprimir
            </Button>
          </ButtonGroup>
        </DialogActions>
      </Dialog>
    </Box>
  );
}