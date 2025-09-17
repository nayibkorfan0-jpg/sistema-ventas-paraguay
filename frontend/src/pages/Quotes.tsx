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
  Alert,
  CircularProgress,
  Autocomplete,
  Card,
  CardContent,
  Divider,
  Fab,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Print as PrintIcon,
  Download as DownloadIcon,
  Save as SaveIcon,
  Remove as RemoveIcon,
  Business as BusinessIcon,
  Description as DescriptionIcon,
  PictureAsPdf as PdfIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';

interface Customer {
  id: number;
  company_name: string;
}

interface Product {
  id: number;
  name: string;
  description?: string;
  unit_price: number;
  category_name?: string;
  stock_quantity: number;
}

interface QuoteLine {
  product_id: number;
  product_name?: string;
  quantity: number;
  unit_price: number;
  discount: number;
  subtotal: number;
}

interface Quote {
  id: number;
  quote_number: string;
  customer_id: number;
  customer_name: string;
  quote_date: string;
  valid_until: string;
  status: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  notes?: string;
  terms_conditions?: string;
  lines: QuoteLine[];
}

// Robust number formatter to prevent toLocaleString crashes
const formatNumber = (n?: number | null): string => {
  const num = Number(n) || 0;
  return isNaN(num) ? '0' : num.toLocaleString();
};

export default function Quotes() {
  const { user } = useAuth();
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingQuote, setEditingQuote] = useState<Quote | null>(null);
  const [generatingPdf, setGeneratingPdf] = useState(false);
  
  // Formulario de cotización
  const [formData, setFormData] = useState({
    customer_id: 0,
    quote_date: new Date().toISOString().split('T')[0],
    valid_until: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 días
    notes: '',
    terms_conditions: 'Precios válidos por 30 días. No incluye IVA. Tiempo de entrega: 7 días hábiles.',
  });

  // Líneas de productos en la cotización
  const [quoteLines, setQuoteLines] = useState<QuoteLine[]>([]);
  
  // Producto seleccionado para agregar
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [productQuantity, setProductQuantity] = useState(1);
  const [productDiscount, setProductDiscount] = useState(0);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [quotesData, customersData, productsData] = await Promise.all([
        apiService.getQuotes({ limit: 1000 }),
        apiService.getCustomers({ limit: 1000, is_active: true }),
        apiService.getProducts({ limit: 1000 })
      ]);
      
      setQuotes(quotesData);
      setCustomers(customersData);
      setProducts(productsData);
    } catch (err) {
      setError('Error al cargar datos');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (quote?: Quote) => {
    if (quote) {
      setEditingQuote(quote);
      setFormData({
        customer_id: quote.customer_id,
        quote_date: quote.quote_date,
        valid_until: quote.valid_until,
        notes: quote.notes || '',
        terms_conditions: quote.terms_conditions || '',
      });
      setQuoteLines(quote.lines || []);
    } else {
      setEditingQuote(null);
      setFormData({
        customer_id: 0,
        quote_date: new Date().toISOString().split('T')[0],
        valid_until: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        notes: '',
        terms_conditions: 'Precios válidos por 30 días. No incluye IVA. Tiempo de entrega: 7 días hábiles.',
      });
      setQuoteLines([]);
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingQuote(null);
    setQuoteLines([]);
    // Limpiar campos de producto
    setSelectedProduct(null);
    setProductQuantity(1);
    setProductDiscount(0);
  };

  const handleAddProduct = () => {
    if (!selectedProduct) return;
    
    const existingLineIndex = quoteLines.findIndex(line => line.product_id === selectedProduct.id);
    
    if (existingLineIndex >= 0) {
      // Actualizar línea existente
      const updatedLines = [...quoteLines];
      updatedLines[existingLineIndex].quantity += productQuantity;
      updatedLines[existingLineIndex].discount = productDiscount;
      updatedLines[existingLineIndex].subtotal = 
        (updatedLines[existingLineIndex].quantity || 0) * (updatedLines[existingLineIndex].unit_price || 0) * 
        (1 - (productDiscount || 0) / 100);
      setQuoteLines(updatedLines);
    } else {
      // Agregar nueva línea - NO AFECTA STOCK
      const newLine: QuoteLine = {
        product_id: selectedProduct.id,
        product_name: selectedProduct.name,
        quantity: productQuantity || 1,
        unit_price: selectedProduct.unit_price || 0,
        discount: productDiscount || 0,
        subtotal: (productQuantity || 1) * (selectedProduct.unit_price || 0) * (1 - (productDiscount || 0) / 100),
      };
      setQuoteLines([...quoteLines, newLine]);
    }
    
    setSelectedProduct(null);
    setProductQuantity(1);
    setProductDiscount(0);
  };

  const handleRemoveProduct = (productId: number) => {
    setQuoteLines(quoteLines.filter(line => line.product_id !== productId));
  };

  const handleUpdateLine = (index: number, field: keyof QuoteLine, value: any) => {
    const updatedLines = [...quoteLines];
    updatedLines[index] = { ...updatedLines[index], [field]: value };
    
    // Recalcular subtotal
    if (field === 'quantity' || field === 'unit_price' || field === 'discount') {
      updatedLines[index].subtotal = 
        (updatedLines[index].quantity || 0) * 
        (updatedLines[index].unit_price || 0) * 
        (1 - (updatedLines[index].discount || 0) / 100);
    }
    
    setQuoteLines(updatedLines);
  };

  const calculateTotals = () => {
    const subtotal = quoteLines.reduce((sum, line) => sum + (line.subtotal || 0), 0);
    const taxAmount = subtotal * 0.1; // 10% IVA
    const total = subtotal + taxAmount;
    
    return { subtotal, taxAmount, total };
  };

  const handleSubmit = async () => {
    try {
      const totals = calculateTotals();
      const quoteData = {
        ...formData,
        lines: quoteLines.map(line => ({
          product_id: line.product_id,
          quantity: line.quantity,
          unit_price: line.unit_price,
          discount: line.discount,
        })),
        subtotal: totals.subtotal,
        tax_amount: totals.taxAmount,
        total_amount: totals.total,
      };

      if (editingQuote) {
        await apiService.updateQuote(editingQuote.id, quoteData);
      } else {
        await apiService.createQuote(quoteData);
      }
      
      await loadData();
      handleCloseDialog();
    } catch (err) {
      setError('Error al guardar cotización');
      console.error('Error saving quote:', err);
    }
  };

  const handleGeneratePdf = async (quote: Quote) => {
    try {
      setGeneratingPdf(true);
      await apiService.generateQuotePdf(quote.id);
      
      // Descargar automáticamente
      const blob = await apiService.downloadQuotePdf(quote.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cotizacion_${quote.quote_number}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Error al generar PDF');
      console.error('Error generating PDF:', err);
    } finally {
      setGeneratingPdf(false);
    }
  };

  const handlePrint = async (quote: Quote) => {
    try {
      setGeneratingPdf(true);
      const blob = await apiService.downloadQuotePdf(quote.id);
      const url = window.URL.createObjectURL(blob);
      
      // Abrir en nueva ventana para imprimir
      const printWindow = window.open(url, '_blank');
      if (printWindow) {
        printWindow.onload = () => {
          printWindow.print();
        };
      }
      
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Error al imprimir cotización');
      console.error('Error printing quote:', err);
    } finally {
      setGeneratingPdf(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'DRAFT': return 'default';
      case 'SENT': return 'info';
      case 'ACCEPTED': return 'success';
      case 'REJECTED': return 'error';
      case 'EXPIRED': return 'warning';
      default: return 'default';
    }
  };

  const totals = calculateTotals();

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
          Gestión de Cotizaciones
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
          disabled={!user?.can_create_quotes}
        >
          Nueva Cotización
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Estadísticas rápidas */}
      <Grid container spacing={2} mb={3}>
        <Grid {...({ item: true, xs: 12, sm: 6, md: 3 } as any)}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <DescriptionIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {quotes.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Cotizaciones
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid {...({ item: true, xs: 12, sm: 6, md: 3 } as any)}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <BusinessIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {quotes.filter(q => q.status === 'ACCEPTED').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Aceptadas
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid {...({ item: true, xs: 12, sm: 6, md: 3 } as any)}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <SaveIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {quotes.filter(q => q.status === 'DRAFT').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Borradores
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid {...({ item: true, xs: 12, sm: 6, md: 3 } as any)}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <PdfIcon sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Gs. {formatNumber(quotes.reduce((sum, q) => sum + (q.total_amount || 0), 0))}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Valor Total
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabla de cotizaciones */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><strong>Número</strong></TableCell>
              <TableCell><strong>Cliente</strong></TableCell>
              <TableCell><strong>Fecha</strong></TableCell>
              <TableCell><strong>Válida Hasta</strong></TableCell>
              <TableCell><strong>Total</strong></TableCell>
              <TableCell><strong>Estado</strong></TableCell>
              <TableCell><strong>Acciones</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {quotes.map((quote) => (
              <TableRow key={quote.id}>
                <TableCell>{quote.quote_number}</TableCell>
                <TableCell>{quote.customer_name}</TableCell>
                <TableCell>{new Date(quote.quote_date).toLocaleDateString()}</TableCell>
                <TableCell>{new Date(quote.valid_until).toLocaleDateString()}</TableCell>
                <TableCell>Gs. {formatNumber(quote.total_amount)}</TableCell>
                <TableCell>
                  <Chip 
                    label={quote.status} 
                    color={getStatusColor(quote.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <IconButton 
                    onClick={() => handleOpenDialog(quote)}
                    color="primary"
                    size="small"
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton 
                    onClick={() => handleGeneratePdf(quote)}
                    color="secondary"
                    size="small"
                    disabled={generatingPdf}
                  >
                    <DownloadIcon />
                  </IconButton>
                  <IconButton 
                    onClick={() => handlePrint(quote)}
                    color="info"
                    size="small"
                    disabled={generatingPdf}
                  >
                    <PrintIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog para crear/editar cotización */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="lg" fullWidth>
        <DialogTitle>
          {editingQuote ? 'Editar Cotización' : 'Nueva Cotización'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            {/* Información básica */}
            {/* Cliente - línea completa */}
            <Grid {...({ item: true, xs: 12, sm: 12 } as any)}>
              <Autocomplete<Customer, false, false, false>
                options={customers}
                getOptionLabel={(option) => option?.company_name || ''}
                value={customers.find(c => c.id === formData.customer_id) || null}
                onChange={(_, value) => setFormData({...formData, customer_id: value?.id || 0})}
                isOptionEqualToValue={(option, value) => option.id === value.id}
                renderInput={(params) => (
                  <TextField 
                    {...params} 
                    label="Cliente *" 
                    placeholder="Escriba para buscar clientes..." 
                    sx={{
                      '& .MuiInputBase-root': {
                        minHeight: '56px',
                        fontSize: '1.1rem'
                      }
                    }}
                  />
                )}
                filterOptions={(options, { inputValue }) => {
                  const filtered = options.filter(option =>
                    option?.company_name?.toLowerCase().includes(inputValue.toLowerCase())
                  );
                  return filtered.slice(0, 50); // Limitar resultados para mejor rendimiento
                }}
                renderOption={(props, option) => (
                  <Box component="li" {...props} key={option.id}>
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', py: 1, '&:hover': { bgcolor: 'action.hover' } }}>
                      <PersonIcon sx={{ mr: 2, color: 'primary.main', fontSize: 20 }} />
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body1" sx={{ fontWeight: 500 }}>
                          {option?.company_name || 'Sin nombre'}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                )}
                noOptionsText="No se encontraron clientes"
                loadingText="Cargando clientes..."
                loading={loading}
              />
            </Grid>
            {/* Fechas - línea separada */}
            <Grid {...({ item: true, xs: 12, sm: 6 } as any)}>
              <TextField
                fullWidth
                label="Fecha de Cotización"
                type="date"
                value={formData.quote_date}
                onChange={(e) => setFormData({...formData, quote_date: e.target.value})}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid {...({ item: true, xs: 12, sm: 6 } as any)}>
              <TextField
                fullWidth
                label="Válida Hasta"
                type="date"
                value={formData.valid_until}
                onChange={(e) => setFormData({...formData, valid_until: e.target.value})}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>

            {/* Productos */}
            <Grid {...({ item: true, xs: 12 } as any)}>
              <Paper sx={{ p: 2, mt: 2 }}>
                <Typography variant="h6" mb={2}>Productos/Servicios</Typography>
                
                {/* Selección de productos - REORGANIZACIÓN COMPLETA */}
                <Grid container spacing={3} mb={3}>
                  {/* LÍNEA 1: Campo Producto - ANCHO COMPLETO */}
                  <Grid {...({ item: true, xs: 12, sm: 12 } as any)}>
                    <Autocomplete<Product, false, false, false>
                      options={products}
                      getOptionLabel={(option) => option ? `${option.name || 'Sin nombre'} - Gs. ${formatNumber(option.unit_price)} (Stock: ${option.stock_quantity || 0})` : ''}
                      value={selectedProduct}
                      onChange={(_, value) => setSelectedProduct(value)}
                      isOptionEqualToValue={(option, value) => option.id === value.id}
                      renderInput={(params) => (
                        <TextField 
                          {...params} 
                          label="Buscar Producto" 
                          placeholder="Escriba el nombre del producto, descripción o categoría para buscar..." 
                          sx={{
                            '& .MuiInputBase-root': {
                              minHeight: '56px',
                              fontSize: '1.1rem'
                            },
                            '& .MuiInputLabel-root': {
                              fontSize: '1.1rem'
                            }
                          }}
                        />
                      )}
                      filterOptions={(options, { inputValue }) => {
                        const filtered = options.filter(option =>
                          option?.name?.toLowerCase().includes(inputValue.toLowerCase()) ||
                          (option?.description && option.description.toLowerCase().includes(inputValue.toLowerCase())) ||
                          (option?.category_name && option.category_name.toLowerCase().includes(inputValue.toLowerCase()))
                        );
                        return filtered.slice(0, 100);
                      }}
                      renderOption={(props, option) => (
                        <Box component="li" {...props} key={option.id}>
                          <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%', py: 1.5 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                              <Box sx={{ flex: 1 }}>
                                <Typography variant="body1" sx={{ fontWeight: 500, mb: 0.5, fontSize: '1.1rem' }}>
                                  {option.name}
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.95rem' }}>
                                  {option.description || 'Sin descripción'}
                                </Typography>
                                {option.category_name && (
                                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontSize: '0.85rem' }}>
                                    Categoría: {option.category_name}
                                  </Typography>
                                )}
                              </Box>
                              <Box sx={{ textAlign: 'right', ml: 2 }}>
                                <Typography variant="body1" color="primary.main" sx={{ fontWeight: 600, fontSize: '1.1rem' }}>
                                  Gs. {formatNumber(option.unit_price)}
                                </Typography>
                                <Typography 
                                  variant="body2" 
                                  color={(option.stock_quantity || 0) > 0 ? 'success.main' : 'error.main'}
                                  sx={{ fontWeight: 500, mt: 0.5, fontSize: '0.9rem' }}
                                >
                                  Stock: {option.stock_quantity || 0}
                                </Typography>
                                {(option.stock_quantity || 0) === 0 && (
                                  <Typography variant="caption" color="error.main" sx={{ fontSize: '0.8rem' }}>
                                    Sin stock
                                  </Typography>
                                )}
                              </Box>
                            </Box>
                          </Box>
                        </Box>
                      )}
                      noOptionsText="No se encontraron productos"
                      loadingText="Cargando productos..."
                      loading={loading}
                      size="medium"
                    />
                  </Grid>
                  
                  {/* LÍNEA 2: Cantidad, Descuento y Botón - MUCHO MÁS ESPACIOSO */}
                  <Grid {...({ item: true, xs: 12, sm: 4 } as any)}>
                    <TextField
                      fullWidth
                      label="Cantidad"
                      type="number"
                      value={productQuantity}
                      onChange={(e) => setProductQuantity(Number(e.target.value))}
                      inputProps={{ min: 1 }}
                      sx={{
                        '& .MuiInputBase-root': {
                          minHeight: '56px',
                          fontSize: '1.1rem'
                        },
                        '& .MuiInputLabel-root': {
                          fontSize: '1.1rem'
                        }
                      }}
                    />
                  </Grid>
                  <Grid {...({ item: true, xs: 12, sm: 4 } as any)}>
                    <TextField
                      fullWidth
                      label="Descuento %"
                      type="number"
                      value={productDiscount}
                      onChange={(e) => setProductDiscount(Number(e.target.value))}
                      inputProps={{ min: 0, max: 100 }}
                      sx={{
                        '& .MuiInputBase-root': {
                          minHeight: '56px',
                          fontSize: '1.1rem'
                        },
                        '& .MuiInputLabel-root': {
                          fontSize: '1.1rem'
                        }
                      }}
                    />
                  </Grid>
                  <Grid {...({ item: true, xs: 12, sm: 4 } as any)}>
                    <Button
                      fullWidth
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={handleAddProduct}
                      disabled={!selectedProduct || productQuantity <= 0}
                      sx={{ 
                        py: 2, 
                        fontSize: '1.1rem',
                        minHeight: '56px',
                        fontWeight: 600
                      }}
                    >
                      Agregar Producto
                    </Button>
                  </Grid>
                </Grid>

                {selectedProduct && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <strong>Nota:</strong> Los productos en cotizaciones NO afectan el stock del inventario. 
                    El stock solo se reduce cuando se convierte en venta o factura.
                  </Alert>
                )}

                {/* Lista de productos agregados */}
                {quoteLines.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" textAlign="center" py={3}>
                    No hay productos agregados. Seleccione un producto y haga clic en "Agregar".
                  </Typography>
                ) : (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Producto</TableCell>
                          <TableCell align="right">Cant.</TableCell>
                          <TableCell align="right">Precio Unit.</TableCell>
                          <TableCell align="right">Desc. %</TableCell>
                          <TableCell align="right">Subtotal</TableCell>
                          <TableCell align="center">Acción</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {quoteLines.map((line, index) => (
                          <TableRow key={line.product_id}>
                            <TableCell>{line.product_name}</TableCell>
                            <TableCell align="right">
                              <TextField
                                size="small"
                                type="number"
                                value={line.quantity}
                                onChange={(e) => handleUpdateLine(index, 'quantity', Number(e.target.value))}
                                sx={{ width: 80 }}
                              />
                            </TableCell>
                            <TableCell align="right">
                              <TextField
                                size="small"
                                type="number"
                                value={line.unit_price}
                                onChange={(e) => handleUpdateLine(index, 'unit_price', Number(e.target.value))}
                                sx={{ width: 100 }}
                              />
                            </TableCell>
                            <TableCell align="right">
                              <TextField
                                size="small"
                                type="number"
                                value={line.discount}
                                onChange={(e) => handleUpdateLine(index, 'discount', Number(e.target.value))}
                                sx={{ width: 70 }}
                              />
                            </TableCell>
                            <TableCell align="right">
                              Gs. {formatNumber(line.subtotal)}
                            </TableCell>
                            <TableCell align="center">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleRemoveProduct(line.product_id)}
                              >
                                <RemoveIcon />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}

                {/* Totales */}
                {quoteLines.length > 0 && (
                  <Box mt={2}>
                    <Divider sx={{ mb: 2 }} />
                    <Grid container spacing={2}>
                      <Grid {...({ item: true, xs: 12, sm: 6 } as any)}>
                        {/* Espacio vacío */}
                      </Grid>
                      <Grid {...({ item: true, xs: 12, sm: 6 } as any)}>
                        <Box textAlign="right">
                          <Typography variant="body1">
                            Subtotal: <strong>Gs. {formatNumber(totals.subtotal)}</strong>
                          </Typography>
                          <Typography variant="body1">
                            IVA (10%): <strong>Gs. {formatNumber(totals.taxAmount)}</strong>
                          </Typography>
                          <Typography variant="h6" color="primary">
                            Total: <strong>Gs. {formatNumber(totals.total)}</strong>
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </Box>
                )}
              </Paper>
            </Grid>

            {/* Notas y términos */}
            <Grid {...({ item: true, xs: 12, sm: 6 } as any)}>
              <TextField
                fullWidth
                label="Notas"
                multiline
                rows={3}
                value={formData.notes}
                onChange={(e) => setFormData({...formData, notes: e.target.value})}
              />
            </Grid>
            <Grid {...({ item: true, xs: 12, sm: 6 } as any)}>
              <TextField
                fullWidth
                label="Términos y Condiciones"
                multiline
                rows={3}
                value={formData.terms_conditions}
                onChange={(e) => setFormData({...formData, terms_conditions: e.target.value})}
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
            disabled={!formData.customer_id || quoteLines.length === 0}
          >
            {editingQuote ? 'Actualizar' : 'Crear'}
          </Button>
        </DialogActions>
      </Dialog>


      {/* FAB para acciones rápidas */}
      {generatingPdf && (
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          disabled
        >
          <CircularProgress size={24} color="inherit" />
        </Fab>
      )}
    </Box>
  );
}