import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Button,
  ButtonGroup,
  TextField,
  MenuItem,
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  Receipt as ReceiptIcon,
  AccountBalance as AccountBalanceIcon,
  AttachMoney as MoneyIcon,
  Download as DownloadIcon,
  Print as PrintIcon,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';

interface ReportData {
  customers: {
    total: number;
    with_tourism_regime: number;
    active: number;
  };
  quotes: {
    total: number;
    by_status: Record<string, number>;
    total_value: number;
  };
  invoices: {
    total: number;
    paid: number;
    overdue: number;
    total_value: number;
    pending_amount: number;
  };
  deposits: {
    total: number;
    active: number;
    total_value: number;
    by_type: Record<string, number>;
  };
}

export default function Reports() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [dateRange, setDateRange] = useState({
    from: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    to: new Date().toISOString().split('T')[0],
  });
  const [reportType, setReportType] = useState('general');

  useEffect(() => {
    loadReportData();
  }, [dateRange]);

  const loadReportData = async () => {
    try {
      setLoading(true);
      
      // Cargar datos desde múltiples endpoints
      const [customers, quotes, invoices, deposits] = await Promise.all([
        apiService.getCustomers({ limit: 10000 }),
        apiService.getQuotes({ limit: 10000 }),
        apiService.getInvoices({ limit: 10000 }),
        apiService.getDeposits({ limit: 10000 })
      ]);

      // Procesar datos para el reporte
      const processedData: ReportData = {
        customers: {
          total: customers.length,
          with_tourism_regime: customers.filter((c: any) => c.tourism_regime).length,
          active: customers.filter((c: any) => c.is_active).length,
        },
        quotes: {
          total: quotes.length,
          by_status: quotes.reduce((acc: any, quote: any) => {
            acc[quote.status] = (acc[quote.status] || 0) + 1;
            return acc;
          }, {}),
          total_value: quotes.reduce((sum: number, quote: any) => sum + (quote.total_amount || 0), 0),
        },
        invoices: {
          total: invoices.length,
          paid: invoices.filter((i: any) => i.status === 'PAID').length,
          overdue: invoices.filter((i: any) => i.status === 'OVERDUE').length,
          total_value: invoices.reduce((sum: number, invoice: any) => sum + (invoice.total_amount || 0), 0),
          pending_amount: invoices.reduce((sum: number, invoice: any) => sum + (invoice.balance_due || 0), 0),
        },
        deposits: {
          total: deposits.length,
          active: deposits.filter((d: any) => d.status === 'ACTIVE').length,
          total_value: deposits.reduce((sum: number, deposit: any) => sum + (deposit.available_amount || 0), 0),
          by_type: deposits.reduce((acc: any, deposit: any) => {
            acc[deposit.deposit_type] = (acc[deposit.deposit_type] || 0) + 1;
            return acc;
          }, {}),
        },
      };

      setReportData(processedData);
    } catch (err) {
      setError('Error al cargar datos del reporte');
      console.error('Error loading report data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportReport = (format: 'pdf' | 'excel') => {
    // Simular exportación de reporte
    if (format === 'pdf') {
      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write(`
          <html>
            <head>
              <title>Reporte de Gestión de Ventas</title>
              <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { text-align: center; margin-bottom: 30px; }
                .section { margin-bottom: 20px; }
                .metric { display: inline-block; margin: 10px; padding: 15px; border: 1px solid #ddd; }
              </style>
            </head>
            <body>
              <div class="header">
                <h1>Reporte de Gestión de Ventas</h1>
                <p>Sistema ERP Paraguay</p>
                <p>Período: ${dateRange.from} a ${dateRange.to}</p>
              </div>
              ${reportData ? `
                <div class="section">
                  <h2>Resumen de Clientes</h2>
                  <div class="metric">
                    <strong>Total:</strong> ${reportData.customers.total}
                  </div>
                  <div class="metric">
                    <strong>Con Régimen Turismo:</strong> ${reportData.customers.with_tourism_regime}
                  </div>
                  <div class="metric">
                    <strong>Activos:</strong> ${reportData.customers.active}
                  </div>
                </div>
                <div class="section">
                  <h2>Resumen de Cotizaciones</h2>
                  <div class="metric">
                    <strong>Total:</strong> ${reportData.quotes.total}
                  </div>
                  <div class="metric">
                    <strong>Valor Total:</strong> Gs. ${reportData.quotes.total_value.toLocaleString()}
                  </div>
                </div>
                <div class="section">
                  <h2>Resumen de Facturas</h2>
                  <div class="metric">
                    <strong>Total:</strong> ${reportData.invoices.total}
                  </div>
                  <div class="metric">
                    <strong>Pagadas:</strong> ${reportData.invoices.paid}
                  </div>
                  <div class="metric">
                    <strong>Vencidas:</strong> ${reportData.invoices.overdue}
                  </div>
                  <div class="metric">
                    <strong>Por Cobrar:</strong> Gs. ${reportData.invoices.pending_amount.toLocaleString()}
                  </div>
                </div>
                <div class="section">
                  <h2>Resumen de Depósitos</h2>
                  <div class="metric">
                    <strong>Total:</strong> ${reportData.deposits.total}
                  </div>
                  <div class="metric">
                    <strong>Activos:</strong> ${reportData.deposits.active}
                  </div>
                  <div class="metric">
                    <strong>Disponible:</strong> Gs. ${reportData.deposits.total_value.toLocaleString()}
                  </div>
                </div>
              ` : ''}
            </body>
          </html>
        `);
        printWindow.document.close();
        printWindow.print();
      }
    } else {
      // Simular exportación Excel
      alert('Funcionalidad de exportación Excel próximamente disponible');
    }
  };

  if (!user?.can_view_reports) {
    return (
      <Alert severity="warning">
        No tiene permisos para ver reportes. Contacte al administrador.
      </Alert>
    );
  }

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
          Reportes y Análisis
        </Typography>
        <ButtonGroup variant="outlined">
          <Button
            startIcon={<PrintIcon />}
            onClick={() => handleExportReport('pdf')}
          >
            Imprimir
          </Button>
          <Button
            startIcon={<DownloadIcon />}
            onClick={() => handleExportReport('excel')}
          >
            Exportar Excel
          </Button>
        </ButtonGroup>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Filtros */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Filtros de Reporte
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              select
              label="Tipo de Reporte"
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
            >
              <MenuItem value="general">Reporte General</MenuItem>
              <MenuItem value="customers">Clientes</MenuItem>
              <MenuItem value="sales">Ventas</MenuItem>
              <MenuItem value="deposits">Depósitos</MenuItem>
              <MenuItem value="tourism">Régimen de Turismo</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Fecha Desde"
              type="date"
              value={dateRange.from}
              onChange={(e) => setDateRange({...dateRange, from: e.target.value})}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Fecha Hasta"
              type="date"
              value={dateRange.to}
              onChange={(e) => setDateRange({...dateRange, to: e.target.value})}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
        </Grid>
      </Paper>

      {reportData && (
        <>
          {/* Métricas principales */}
          <Grid container spacing={3} mb={4}>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ bgcolor: 'primary.main', color: 'white' }}>
                <CardContent sx={{ textAlign: 'center' }}>
                  <PeopleIcon sx={{ fontSize: 48, mb: 2 }} />
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {reportData.customers.total}
                  </Typography>
                  <Typography variant="h6">
                    Clientes Totales
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    {reportData.customers.with_tourism_regime} con régimen turismo
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ bgcolor: 'secondary.main', color: 'white' }}>
                <CardContent sx={{ textAlign: 'center' }}>
                  <ReceiptIcon sx={{ fontSize: 48, mb: 2 }} />
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {reportData.invoices.total}
                  </Typography>
                  <Typography variant="h6">
                    Facturas Emitidas
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    {reportData.invoices.paid} pagadas
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ bgcolor: 'success.main', color: 'white' }}>
                <CardContent sx={{ textAlign: 'center' }}>
                  <MoneyIcon sx={{ fontSize: 48, mb: 2 }} />
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    Gs. {reportData.invoices.total_value.toLocaleString()}
                  </Typography>
                  <Typography variant="h6">
                    Facturación Total
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    Período actual
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ bgcolor: 'info.main', color: 'white' }}>
                <CardContent sx={{ textAlign: 'center' }}>
                  <AccountBalanceIcon sx={{ fontSize: 48, mb: 2 }} />
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    Gs. {reportData.deposits.total_value.toLocaleString()}
                  </Typography>
                  <Typography variant="h6">
                    Depósitos Activos
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    {reportData.deposits.active} depósitos
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Detalles por sección */}
          <Grid container spacing={3}>
            {/* Resumen de Clientes */}
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Box display="flex" alignItems="center" mb={2}>
                  <PeopleIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Análisis de Clientes
                  </Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Total Clientes
                    </Typography>
                    <Typography variant="h5" color="primary">
                      {reportData.customers.total}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Clientes Activos
                    </Typography>
                    <Typography variant="h5" color="success.main">
                      {reportData.customers.active}
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      Con Régimen de Turismo
                    </Typography>
                    <Typography variant="h5" color="secondary.main">
                      {reportData.customers.with_tourism_regime}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      ({((reportData.customers.with_tourism_regime / reportData.customers.total) * 100).toFixed(1)}% del total)
                    </Typography>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>

            {/* Resumen de Ventas */}
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Box display="flex" alignItems="center" mb={2}>
                  <TrendingUpIcon sx={{ mr: 1, color: 'success.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Análisis de Ventas
                  </Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Cotizaciones
                    </Typography>
                    <Typography variant="h5" color="primary">
                      {reportData.quotes.total}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Facturas
                    </Typography>
                    <Typography variant="h5" color="secondary.main">
                      {reportData.invoices.total}
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      Por Cobrar
                    </Typography>
                    <Typography variant="h5" color="error.main">
                      Gs. {reportData.invoices.pending_amount.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      ({reportData.invoices.overdue} facturas vencidas)
                    </Typography>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>

            {/* Resumen de Depósitos */}
            <Grid item xs={12}>
              <Paper sx={{ p: 3 }}>
                <Box display="flex" alignItems="center" mb={2}>
                  <AccountBalanceIcon sx={{ mr: 1, color: 'info.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Análisis de Depósitos (Sistema Paraguay)
                  </Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={2.4}>
                    <Typography variant="body2" color="text.secondary">
                      Total Depósitos
                    </Typography>
                    <Typography variant="h5" color="primary">
                      {reportData.deposits.total}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={2.4}>
                    <Typography variant="body2" color="text.secondary">
                      Depósitos Activos
                    </Typography>
                    <Typography variant="h5" color="success.main">
                      {reportData.deposits.active}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={2.4}>
                    <Typography variant="body2" color="text.secondary">
                      Monto Disponible
                    </Typography>
                    <Typography variant="h5" color="info.main">
                      Gs. {reportData.deposits.total_value.toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={2.4}>
                    <Typography variant="body2" color="text.secondary">
                      Anticipos
                    </Typography>
                    <Typography variant="h5" color="secondary.main">
                      {reportData.deposits.by_type.ANTICIPO || 0}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={2.4}>
                    <Typography variant="body2" color="text.secondary">
                      Garantías
                    </Typography>
                    <Typography variant="h5" color="warning.main">
                      {reportData.deposits.by_type.GARANTIA || 0}
                    </Typography>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          </Grid>

          {/* Información adicional */}
          <Box mt={4}>
            <Alert severity="success">
              <Typography variant="subtitle2" gutterBottom>
                Resumen del Período ({dateRange.from} a {dateRange.to}):
              </Typography>
              <Typography variant="body2">
                • Sistema funcionando correctamente con {reportData.customers.total} clientes registrados<br/>
                • {reportData.customers.with_tourism_regime} clientes aprovechando el régimen de turismo paraguayo<br/>
                • Gs. {reportData.invoices.total_value.toLocaleString()} en facturación total del período<br/>
                • Gs. {reportData.deposits.total_value.toLocaleString()} en depósitos activos gestionados<br/>
                • {((reportData.invoices.paid / reportData.invoices.total) * 100).toFixed(1)}% de facturas pagadas
              </Typography>
            </Alert>
          </Box>
        </>
      )}
    </Box>
  );
}