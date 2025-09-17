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
  FormControlLabel,
  Switch,
  Grid,
  Alert,
  CircularProgress,
  Tooltip,
  Card,
  CardContent,
  CardActions,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PictureAsPdf as PdfIcon,
  CloudUpload as UploadIcon,
  Download as DownloadIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  LocationOn as LocationIcon,
  MonetizationOn as MoneyIcon,
  Notes as NotesIcon,
  AttachFile as AttachFileIcon,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';

interface Customer {
  id: number;
  company_name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  country: string;
  tax_id?: string;
  credit_limit: number;
  payment_terms: number;
  is_active: boolean;
  tourism_regime: boolean;
  tourism_regime_pdf?: string;
  tourism_regime_expiry?: string;
  notes?: string;
}

export default function Customers() {
  const { user } = useAuth();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  // File upload is now integrated into the main form
  
  // Estados para manejo de archivos y validaciones
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [rucError, setRucError] = useState('');
  
  // Formulario
  const [formData, setFormData] = useState({
    company_name: '',
    contact_name: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    country: 'Paraguay',
    tax_id: '',
    credit_limit: 0,
    payment_terms: 30,
    is_active: true,
    tourism_regime: false,
    tourism_regime_expiry: '',
    notes: '',
  });

  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    try {
      setLoading(true);
      const data = await apiService.getCustomers({ limit: 1000 });
      setCustomers(data);
    } catch (err) {
      setError('Error al cargar clientes');
      console.error('Error loading customers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (customer?: Customer) => {
    if (customer) {
      setEditingCustomer(customer);
      setFormData({
        company_name: customer.company_name,
        contact_name: customer.contact_name || '',
        email: customer.email || '',
        phone: customer.phone || '',
        address: customer.address || '',
        city: customer.city || '',
        country: customer.country,
        tax_id: customer.tax_id || '',
        credit_limit: customer.credit_limit,
        payment_terms: customer.payment_terms,
        is_active: customer.is_active,
        tourism_regime: customer.tourism_regime,
        tourism_regime_expiry: customer.tourism_regime_expiry || '',
        notes: customer.notes || '',
      });
    } else {
      setEditingCustomer(null);
      setFormData({
        company_name: '',
        contact_name: '',
        email: '',
        phone: '',
        address: '',
        city: '',
        country: 'Paraguay',
        tax_id: '',
        credit_limit: 0,
        payment_terms: 30,
        is_active: true,
        tourism_regime: false,
        tourism_regime_expiry: '',
        notes: '',
      });
      setSelectedFile(null);
      setFileError('');
      setEmailError('');
      setRucError('');
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingCustomer(null);
    setSelectedFile(null);
    setFileError('');
    setEmailError('');
    setRucError('');
    setSubmitting(false);
  };

  // Función para validación de email en tiempo real
  const validateEmail = (email: string) => {
    if (!email) {
      setEmailError('');
      return true;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setEmailError('Formato de email inválido');
      return false;
    }
    setEmailError('');
    return true;
  };

  // Función para validación de RUC paraguayo en tiempo real
  const validateRuc = (ruc: string) => {
    if (!ruc) {
      setRucError('');
      return true;
    }
    // Formato básico del RUC paraguayo: 12345678-1
    const rucRegex = /^\d{8}-\d{1}$/;
    if (!rucRegex.test(ruc)) {
      setRucError('Formato RUC inválido. Use: 12345678-1');
      return false;
    }
    setRucError('');
    return true;
  };

  // Función para manejar la selección de archivos
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validar tipo de archivo - solo PDF
      if (file.type !== 'application/pdf') {
        setFileError('Solo se permiten archivos PDF');
        return;
      }
      
      // Validar tamaño (máximo 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setFileError('El archivo es demasiado grande. Máximo permitido: 10MB');
        return;
      }
      
      setSelectedFile(file);
      setFileError('');
    }
  };

  const handleSubmit = async () => {
    try {
      setSubmitting(true);
      setError('');
      
      // Validaciones frontend específicas para régimen turístico
      if (formData.tourism_regime) {
        if (!formData.tourism_regime_expiry) {
          setError('Debe proporcionar la fecha de vencimiento del régimen de turismo');
          return;
        }
        
        // Validar que la fecha de vencimiento sea futura
        const expiryDate = new Date(formData.tourism_regime_expiry);
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Reset time for accurate date comparison
        
        if (expiryDate <= today) {
          setError('La fecha de vencimiento del régimen de turismo debe ser futura');
          return;
        }
      }
      
      let customer;
      
      if (editingCustomer) {
        customer = await apiService.updateCustomer(editingCustomer.id, formData);
      } else {
        customer = await apiService.createCustomer(formData);
      }
      
      // Si hay un archivo seleccionado y régimen de turismo activo, subirlo
      if (selectedFile && formData.tourism_regime && customer) {
        const customerId = editingCustomer ? editingCustomer.id : customer.id;
        try {
          await apiService.uploadTourismPdf(customerId, selectedFile);
        } catch (fileErr) {
          setError('Cliente guardado, pero error al subir archivo. Puede subirlo después editando el cliente.');
          console.error('Error uploading file:', fileErr);
        }
      }
      
      await loadCustomers();
      handleCloseDialog();
    } catch (err) {
      setError('Error al guardar cliente');
      console.error('Error saving customer:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteCustomer = async (id: number) => {
    if (window.confirm('¿Está seguro que desea eliminar este cliente?')) {
      try {
        await apiService.deleteCustomer(id);
        await loadCustomers();
      } catch (err) {
        setError('Error al eliminar cliente');
        console.error('Error deleting customer:', err);
      }
    }
  };


  const handlePdfDownload = async (customer: Customer) => {
    try {
      const blob = await apiService.downloadTourismPdf(customer.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `regimen_turismo_${customer.company_name}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Error al descargar PDF');
      console.error('Error downloading PDF:', err);
    }
  };

  const handlePdfDelete = async (customer: Customer) => {
    if (window.confirm('¿Está seguro que desea eliminar el PDF del régimen de turismo?')) {
      try {
        await apiService.deleteTourismPdf(customer.id);
        await loadCustomers();
      } catch (err) {
        setError('Error al eliminar PDF');
        console.error('Error deleting PDF:', err);
      }
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return '-';
      return date.toLocaleDateString('es-PY', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
    } catch (error) {
      console.error('Error formatting date:', error);
      return '-';
    }
  };

  const isRegimeExpiringSoon = (expiryDate?: string) => {
    if (!expiryDate) return false;
    try {
      const expiry = new Date(expiryDate);
      if (isNaN(expiry.getTime())) return false;
      
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      expiry.setHours(0, 0, 0, 0);
      
      const daysUntilExpiry = Math.ceil((expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
      return daysUntilExpiry <= 5 && daysUntilExpiry >= 0;
    } catch (error) {
      console.error('Error checking expiry:', error);
      return false;
    }
  };

  const isRegimeExpired = (expiryDate?: string) => {
    if (!expiryDate) return false;
    try {
      const expiry = new Date(expiryDate);
      if (isNaN(expiry.getTime())) return false;
      
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      expiry.setHours(0, 0, 0, 0);
      
      return expiry < today;
    } catch (error) {
      console.error('Error checking expiry:', error);
      return false;
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
          Gestión de Clientes
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
          disabled={!user?.can_create_customers}
        >
          Nuevo Cliente
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Estadísticas rápidas del régimen de turismo */}
      <Box 
        display="flex" 
        flexWrap="wrap" 
        gap={2} 
        mb={3}
        sx={{
          '& > *': {
            flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)', md: '1 1 calc(25% - 12px)' },
            minWidth: { xs: '100%', sm: '250px', md: '200px' }
          }
        }}
      >
        <Box>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <BusinessIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {customers.filter(c => c.tourism_regime).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Con Régimen de Turismo
              </Typography>
            </CardContent>
          </Card>
        </Box>
        
        <Box>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <WarningIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {customers.filter(c => c.tourism_regime && isRegimeExpiringSoon(c.tourism_regime_expiry)).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Vencen Pronto (5 días)
              </Typography>
            </CardContent>
          </Card>
        </Box>
        
        <Box>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <CheckIcon sx={{ fontSize: 40, color: 'error.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {customers.filter(c => c.tourism_regime && isRegimeExpired(c.tourism_regime_expiry)).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Regímenes Vencidos
              </Typography>
            </CardContent>
          </Card>
        </Box>
        
        <Box>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <PdfIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {customers.filter(c => c.tourism_regime && c.tourism_regime_pdf).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Con PDF Subido
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Tabla de clientes */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><strong>Empresa</strong></TableCell>
              <TableCell><strong>Contacto</strong></TableCell>
              <TableCell><strong>Email</strong></TableCell>
              <TableCell><strong>RUC</strong></TableCell>
              <TableCell><strong>Régimen Turismo</strong></TableCell>
              <TableCell><strong>Estado</strong></TableCell>
              <TableCell><strong>Acciones</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {customers.map((customer) => (
              <TableRow key={customer.id}>
                <TableCell>{customer.company_name}</TableCell>
                <TableCell>{customer.contact_name || '-'}</TableCell>
                <TableCell>{customer.email || '-'}</TableCell>
                <TableCell>{customer.tax_id || '-'}</TableCell>
                <TableCell>
                  {customer.tourism_regime ? (
                    <Box>
                      <Chip 
                        label="Activo" 
                        color={
                          isRegimeExpired(customer.tourism_regime_expiry) ? 'error' :
                          isRegimeExpiringSoon(customer.tourism_regime_expiry) ? 'warning' : 'success'
                        }
                        size="small"
                        sx={{ mb: 0.5 }}
                      />
                      {customer.tourism_regime_expiry && (
                        <Typography variant="caption" display="block">
                          Vence: {formatDate(customer.tourism_regime_expiry)}
                        </Typography>
                      )}
                      <Box display="flex" gap={0.5} mt={0.5}>
                        {customer.tourism_regime_pdf ? (
                          <>
                            <Tooltip title="Descargar PDF del régimen">
                              <IconButton 
                                size="small" 
                                onClick={() => handlePdfDownload(customer)}
                                color="primary"
                                sx={{ 
                                  bgcolor: 'primary.light', 
                                  '&:hover': { bgcolor: 'primary.main', color: 'white' } 
                                }}
                              >
                                <DownloadIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Eliminar PDF">
                              <IconButton 
                                size="small" 
                                onClick={() => handlePdfDelete(customer)}
                                color="error"
                                sx={{ 
                                  bgcolor: 'error.light', 
                                  '&:hover': { bgcolor: 'error.main', color: 'white' } 
                                }}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </>
                        ) : (
                          <Tooltip title="Editar cliente para subir PDF">
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<EditIcon />}
                              onClick={() => handleOpenDialog(customer)}
                              sx={{ 
                                minWidth: 'auto', 
                                px: 1,
                                color: 'warning.main',
                                borderColor: 'warning.main',
                                '&:hover': { 
                                  bgcolor: 'warning.main', 
                                  color: 'white',
                                  borderColor: 'warning.main'
                                }
                              }}
                            >
                              Subir PDF
                            </Button>
                          </Tooltip>
                        )}
                      </Box>
                    </Box>
                  ) : (
                    <Chip label="No aplica" variant="outlined" size="small" />
                  )}
                </TableCell>
                <TableCell>
                  <Chip 
                    label={customer.is_active ? 'Activo' : 'Inactivo'} 
                    color={customer.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <IconButton 
                    onClick={() => handleOpenDialog(customer)}
                    color="primary"
                    size="small"
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton 
                    onClick={() => handleDeleteCustomer(customer.id)}
                    color="error"
                    size="small"
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog para crear/editar cliente - MEJORADO CON SECCIONES ORGANIZADAS */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ bgcolor: 'primary.main', color: 'white', display: 'flex', alignItems: 'center', gap: 2 }}>
          <BusinessIcon />
          {editingCustomer ? 'Editar Cliente' : 'Nuevo Cliente'}
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Box display="flex" flexDirection="column" gap={3}>
            
            {/* SECCIÓN 1: INFORMACIÓN DE LA EMPRESA */}
            <Box>
              <Paper elevation={2} sx={{ p: 3, bgcolor: 'info.light', borderRadius: 2 }}>
                <Box display="flex" alignItems="center" gap={2} mb={3}>
                  <PersonIcon sx={{ fontSize: 28, color: 'info.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600, color: 'info.dark' }}>
                    Información del Cliente
                  </Typography>
                </Box>
                <Box display="flex" flexWrap="wrap" gap={2}>
                  <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)' }, minWidth: '250px' }}>
                    <TextField
                      fullWidth
                      label="Razón Social / Nombre del Cliente *"
                      placeholder="Ej: Turismo Paraguay SA o Juan Pérez"
                      value={formData.company_name}
                      onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                      error={!formData.company_name}
                      helperText={!formData.company_name ? 'Campo obligatorio - puede ser empresa o persona individual' : 'Puede ser nombre de empresa o persona individual'}
                      variant="outlined"
                    />
                  </Box>
                  <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)' }, minWidth: '250px' }}>
                    <TextField
                      fullWidth
                      label="Contacto Principal"
                      placeholder="Ej: Juan Pérez"
                      value={formData.contact_name}
                      onChange={(e) => setFormData({...formData, contact_name: e.target.value})}
                      variant="outlined"
                    />
                  </Box>
                  <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)' }, minWidth: '250px' }}>
                    <TextField
                      fullWidth
                      label="Email"
                      type="email"
                      placeholder="contacto@empresa.com"
                      value={formData.email}
                      onChange={(e) => {
                        const email = e.target.value;
                        setFormData({...formData, email});
                        validateEmail(email);
                      }}
                      error={!!emailError}
                      helperText={emailError || 'Email de contacto principal'}
                      variant="outlined"
                    />
                  </Box>
                  <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)' }, minWidth: '250px' }}>
                    <TextField
                      fullWidth
                      label="Teléfono"
                      placeholder="Ej: +595 21 123-4567"
                      value={formData.phone}
                      onChange={(e) => setFormData({...formData, phone: e.target.value})}
                      variant="outlined"
                    />
                  </Box>
                </Box>
              </Paper>
            </Box>

            {/* SECCIÓN 2: DATOS FISCALES */}
            <Box>
              <Paper elevation={2} sx={{ p: 3, bgcolor: 'warning.light', borderRadius: 2 }}>
                <Box display="flex" alignItems="center" gap={2} mb={3}>
                  <LocationIcon sx={{ fontSize: 28, color: 'warning.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600, color: 'warning.dark' }}>
                    Datos Fiscales y Ubicación
                  </Typography>
                </Box>
                <Box display="flex" flexWrap="wrap" gap={2}>
                  <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)' }, minWidth: '250px' }}>
                    <TextField
                      fullWidth
                      label="RUC/Identificación Fiscal"
                      placeholder="Ej: 80012345-1"
                      value={formData.tax_id}
                      onChange={(e) => {
                        const ruc = e.target.value;
                        setFormData({...formData, tax_id: ruc});
                        validateRuc(ruc);
                      }}
                      error={!!rucError}
                      helperText={rucError || 'Formato: 12345678-1'}
                      variant="outlined"
                    />
                  </Box>
                  <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)' }, minWidth: '250px' }}>
                    <TextField
                      fullWidth
                      label="Ciudad"
                      placeholder="Ej: Asunción"
                      value={formData.city}
                      onChange={(e) => setFormData({...formData, city: e.target.value})}
                      variant="outlined"
                    />
                  </Box>
                  <Box sx={{ flex: '1 1 100%' }}>
                    <TextField
                      fullWidth
                      label="Dirección Completa"
                      placeholder="Ej: Av. España 1234 c/ Brasil"
                      value={formData.address}
                      onChange={(e) => setFormData({...formData, address: e.target.value})}
                      variant="outlined"
                    />
                  </Box>
                </Box>
              </Paper>
            </Box>

            {/* SECCIÓN 3: TÉRMINOS COMERCIALES */}
            <Box>
              <Paper elevation={2} sx={{ p: 3, bgcolor: 'success.light', borderRadius: 2 }}>
                <Box display="flex" alignItems="center" gap={2} mb={3}>
                  <MoneyIcon sx={{ fontSize: 28, color: 'success.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600, color: 'success.dark' }}>
                    Términos Comerciales
                  </Typography>
                </Box>
                <Box display="flex" flexWrap="wrap" gap={2}>
                  <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)' }, minWidth: '250px' }}>
                    <TextField
                      fullWidth
                      label="Límite de Crédito (Gs.)"
                      type="number"
                      placeholder="0"
                      value={formData.credit_limit}
                      onChange={(e) => setFormData({...formData, credit_limit: Number(e.target.value)})}
                      variant="outlined"
                      helperText="Monto máximo de crédito autorizado"
                      InputProps={{
                        inputProps: { min: 0 }
                      }}
                    />
                  </Box>
                  <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)' }, minWidth: '250px' }}>
                    <TextField
                      fullWidth
                      label="Términos de Pago (días)"
                      type="number"
                      placeholder="30"
                      value={formData.payment_terms}
                      onChange={(e) => setFormData({...formData, payment_terms: Number(e.target.value)})}
                      variant="outlined"
                      helperText="Días de plazo para el pago"
                      InputProps={{
                        inputProps: { min: 0, max: 365 }
                      }}
                    />
                  </Box>
                </Box>
              </Paper>
            </Box>

            {/* SECCIÓN 4: RÉGIMEN DE TURISMO - CON UPLOAD INTEGRADO */}
            <Box>
              <Paper 
                elevation={3} 
                sx={{ 
                  p: 3, 
                  bgcolor: formData.tourism_regime ? 'primary.light' : 'grey.50',
                  border: formData.tourism_regime ? '2px solid' : '1px solid',
                  borderColor: formData.tourism_regime ? 'primary.main' : 'grey.300',
                  borderRadius: 2,
                  transition: 'all 0.3s ease'
                }}
              >
                <Box display="flex" alignItems="center" gap={2} mb={3}>
                  <BusinessIcon 
                    sx={{ 
                      fontSize: 32, 
                      color: formData.tourism_regime ? 'primary.main' : 'grey.600' 
                    }} 
                  />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: formData.tourism_regime ? 'primary.main' : 'text.primary' }}>
                      Régimen de Turismo Paraguay
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Cliente exento de impuestos por régimen especial de turismo
                    </Typography>
                  </Box>
                </Box>
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.tourism_regime}
                      onChange={(e) => {
                        const isChecked = e.target.checked;
                        setFormData({
                          ...formData, 
                          tourism_regime: isChecked,
                          tourism_regime_expiry: isChecked ? formData.tourism_regime_expiry : ''
                        });
                        if (!isChecked) {
                          setSelectedFile(null);
                          setFileError('');
                        }
                      }}
                      size="medium"
                      color="primary"
                    />
                  }
                  label={
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      Este cliente tiene Régimen de Turismo activo
                    </Typography>
                  }
                />
                
                {formData.tourism_regime && (
                  <Box sx={{ mt: 3 }}>
                    <Alert severity="info" sx={{ mb: 3 }}>
                      <Typography variant="body2">
                        <strong>Información requerida:</strong> Complete la fecha de vencimiento y suba el documento oficial del régimen de turismo.
                      </Typography>
                    </Alert>
                    
                    <Box display="flex" flexWrap="wrap" gap={3}>
                      <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 12px)' }, minWidth: '300px' }}>
                        <TextField
                          fullWidth
                          label="Fecha de Vencimiento del Régimen *"
                          type="date"
                          value={formData.tourism_regime_expiry || ''}
                          onChange={(e) => setFormData({...formData, tourism_regime_expiry: e.target.value})}
                          InputLabelProps={{ shrink: true }}
                          required={formData.tourism_regime}
                          error={formData.tourism_regime && !formData.tourism_regime_expiry}
                          helperText={formData.tourism_regime && !formData.tourism_regime_expiry ? 'Campo obligatorio para régimen de turismo' : 'Fecha hasta la cual el régimen está vigente'}
                          inputProps={{
                            min: new Date().toISOString().split('T')[0]
                          }}
                          variant="outlined"
                        />
                      </Box>
                      
                      <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 12px)' }, minWidth: '300px' }}>
                        <Box>
                          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                            Documento del Régimen de Turismo
                          </Typography>
                          
                          <Paper 
                            variant="outlined" 
                            sx={{ 
                              p: 2, 
                              border: selectedFile ? '2px solid' : '2px dashed',
                              borderColor: selectedFile ? 'success.main' : 'grey.400',
                              bgcolor: selectedFile ? 'success.light' : 'grey.50',
                              transition: 'all 0.3s ease',
                              '&:hover': {
                                bgcolor: selectedFile ? 'success.light' : 'grey.100',
                                borderColor: selectedFile ? 'success.main' : 'primary.main'
                              }
                            }}
                          >
                            <input
                              accept=".pdf,application/pdf"
                              style={{ display: 'none' }}
                              id="tourism-file-upload"
                              type="file"
                              onChange={handleFileSelect}
                            />
                            <label htmlFor="tourism-file-upload">
                              <Box display="flex" flexDirection="column" alignItems="center" sx={{ cursor: 'pointer' }}>
                                {selectedFile ? (
                                  <>
                                    <CheckIcon sx={{ fontSize: 32, color: 'success.main', mb: 1 }} />
                                    <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.dark' }}>
                                      Archivo seleccionado:
                                    </Typography>
                                    <Typography variant="body2" sx={{ color: 'success.dark', textAlign: 'center' }}>
                                      {selectedFile.name}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                    </Typography>
                                    <Button 
                                      size="small" 
                                      variant="outlined" 
                                      sx={{ mt: 1 }}
                                      startIcon={<AttachFileIcon />}
                                    >
                                      Cambiar archivo
                                    </Button>
                                  </>
                                ) : (
                                  <>
                                    <UploadIcon sx={{ fontSize: 32, color: 'grey.600', mb: 1 }} />
                                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                      Explorar Archivo
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center' }}>
                                      PDF o Excel (máx. 10MB)
                                    </Typography>
                                    <Button 
                                      size="small" 
                                      variant="contained" 
                                      sx={{ mt: 1 }}
                                      startIcon={<AttachFileIcon />}
                                    >
                                      Seleccionar Archivo
                                    </Button>
                                  </>
                                )}
                              </Box>
                            </label>
                          </Paper>
                          
                          {fileError && (
                            <Alert severity="error" sx={{ mt: 1 }}>
                              {fileError}
                            </Alert>
                          )}
                          
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                            Formatos permitidos: PDF únicamente. Tamaño máximo: 10MB
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                    
                    {/* Mostrar información del archivo existente si estamos editando */}
                    {editingCustomer && editingCustomer.tourism_regime_pdf && (
                      <Alert severity="warning" sx={{ mt: 2 }}>
                        <Typography variant="body2">
                          <strong>Archivo actual:</strong> {editingCustomer.tourism_regime_pdf}
                          {selectedFile && (
                            <>
                              <br />
                              <strong>Será reemplazado por:</strong> {selectedFile.name}
                            </>
                          )}
                        </Typography>
                      </Alert>
                    )}
                  </Box>
                )}
              </Paper>
            </Box>

            {/* SECCIÓN 5: NOTAS Y ESTADO */}
            <Box>
              <Paper elevation={2} sx={{ p: 3, bgcolor: 'grey.50', borderRadius: 2 }}>
                <Box display="flex" alignItems="center" gap={2} mb={3}>
                  <NotesIcon sx={{ fontSize: 28, color: 'grey.700' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600, color: 'grey.800' }}>
                    Notas y Estado del Cliente
                  </Typography>
                </Box>
                <Box display="flex" flexDirection="column" gap={2}>
                  <Box>
                    <TextField
                      fullWidth
                      label="Notas Adicionales"
                      multiline
                      rows={3}
                      placeholder="Información adicional sobre el cliente..."
                      value={formData.notes}
                      onChange={(e) => setFormData({...formData, notes: e.target.value})}
                      variant="outlined"
                    />
                  </Box>
                  <Box>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={formData.is_active}
                          onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                          size="medium"
                          color="success"
                        />
                      }
                      label={
                        <Typography variant="body1" sx={{ fontWeight: 500 }}>
                          Cliente Activo - Puede realizar transacciones
                        </Typography>
                      }
                    />
                  </Box>
                </Box>
              </Paper>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3, bgcolor: 'grey.50', gap: 2 }}>
          <Button 
            onClick={handleCloseDialog} 
            variant="outlined" 
            size="medium"
            disabled={submitting}
          >
            Cancelar
          </Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            size="medium"
            disabled={Boolean(
              submitting || 
              !formData.company_name || 
              (formData.tourism_regime && !formData.tourism_regime_expiry) ||
              (formData.tourism_regime && selectedFile && fileError)
            )}
            startIcon={submitting ? <CircularProgress size={20} /> : null}
            sx={{ px: 4 }}
          >
            {submitting ? 'Guardando...' : (editingCustomer ? 'Actualizar Cliente' : 'Crear Cliente')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}