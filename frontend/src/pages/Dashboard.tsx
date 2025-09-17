import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  People,
  Description,
  Receipt,
  AccountBalance,
  TrendingUp,
  Warning,
  CheckCircle,
  Schedule,
  AttachMoney,
  Inventory,
  Assessment,
  MonetizationOn,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';

interface DashboardStats {
  basic_stats: {
    total_customers: number;
    active_customers: number;
    total_quotes: number;
    total_invoices: number;
    total_products: number;
  };
  monthly_stats: {
    quotes: number;
    invoices: number;
    sales_pyg: number;
    sales_usd: number;
  };
  pending_invoices: {
    count: number;
    amount_pyg: number;
    amount_usd: number;
  };
  deposits: {
    active_count: number;
    total_amount: number;
  };
  alerts: {
    tourism_regime_expiring: number;
    low_stock_count: number;
    out_of_stock_count: number;
  };
}

export default function Dashboard() {
  const { user, isLoading: authLoading } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    // Solo cargar datos cuando el usuario esté autenticado
    if (user && !authLoading) {
      loadDashboardData();
    }
  }, [user, authLoading]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Cargar estadísticas consolidadas del endpoint
      const dashboardStats = await apiService.getDashboardStats();
      
      setStats(dashboardStats);
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || 'Error al cargar datos del dashboard';
      setError(errorMessage);
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Función helper para formatear números como moneda paraguaya
  const formatCurrency = (amount: number, currency: string = 'PYG'): string => {
    if (amount === null || amount === undefined || isNaN(amount)) return '-';
    
    try {
      if (currency === 'USD') {
        return `USD ${amount.toLocaleString('en-US', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2
        })}`;
      } else {
        return `Gs. ${Math.round(amount).toLocaleString('es-PY')}`;
      }
    } catch (error) {
      console.error('Error formatting currency:', error);
      return `${currency} ${amount || 0}`;
    }
  };

  // Función helper para formatear fechas de manera segura
  const formatDate = (dateString?: string | null): string => {
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

  // Función helper para formatear números de manera segura
  const formatNumber = (num: number): string => {
    if (num === null || num === undefined || isNaN(num)) return '0';
    
    try {
      return num.toLocaleString('es-PY');
    } catch (error) {
      console.error('Error formatting number:', error);
      return String(num || 0);
    }
  };

  // Si aún está cargando la autenticación, mostrar loading
  if (authLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Cargando...</Typography>
      </Box>
    );
  }

  // Si no hay usuario autenticado, mostrar mensaje
  if (!user) {
    return (
      <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" minHeight="400px">
        <Alert severity="info" sx={{ mb: 2 }}>
          Debe iniciar sesión para acceder al dashboard
        </Alert>
        <Button variant="contained" href="/login">
          Iniciar Sesión
        </Button>
      </Box>
    );
  }

  // Si está cargando los datos del dashboard
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Cargando estadísticas...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Encabezado de bienvenida */}
      <Box mb={4}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          ¡Bienvenido, {user?.full_name || user?.username}!
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Sistema de Gestión de Ventas - Paraguay
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Tarjetas de estadísticas básicas */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', bgcolor: 'primary.main', color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {formatNumber(stats?.basic_stats?.total_customers || 0)}
                  </Typography>
                  <Typography variant="body1">
                    Clientes
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    {formatNumber(stats?.basic_stats?.active_customers || 0)} activos
                  </Typography>
                </Box>
                <People sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', bgcolor: 'secondary.main', color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {formatNumber(stats?.monthly_stats?.quotes || 0)}
                  </Typography>
                  <Typography variant="body1">
                    Cotizaciones
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    Este mes
                  </Typography>
                </Box>
                <Description sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', bgcolor: 'success.main', color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {formatNumber(stats?.monthly_stats?.invoices || 0)}
                  </Typography>
                  <Typography variant="body1">
                    Facturas
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    Este mes
                  </Typography>
                </Box>
                <Receipt sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', bgcolor: 'info.main', color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {formatNumber(stats?.deposits?.active_count || 0)}
                  </Typography>
                  <Typography variant="body1">
                    Depósitos
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    Activos
                  </Typography>
                </Box>
                <AccountBalance sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tarjetas de ventas por moneda */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <MonetizationOn sx={{ color: 'success.main', mr: 1 }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Ventas del Mes - Guaraníes
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main' }}>
                {formatCurrency(stats?.monthly_stats?.sales_pyg || 0, 'PYG')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Facturación en guaraníes del mes actual
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <AttachMoney sx={{ color: 'primary.main', mr: 1 }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Ventas del Mes - Dólares
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
                {formatCurrency(stats?.monthly_stats?.sales_usd || 0, 'USD')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Facturación en dólares del mes actual
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alertas y información importante */}
      <Grid container spacing={3} mb={4}>
        {/* Facturas Pendientes */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Box display="flex" alignItems="center" mb={2}>
              <Schedule sx={{ color: 'warning.main', mr: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Facturas Pendientes
              </Typography>
            </Box>
            
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
              {formatNumber(stats?.pending_invoices?.count || 0)}
            </Typography>
            
            <Box mb={2}>
              <Typography variant="body2" color="text.secondary">
                PYG: {formatCurrency(stats?.pending_invoices?.amount_pyg || 0, 'PYG')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                USD: {formatCurrency(stats?.pending_invoices?.amount_usd || 0, 'USD')}
              </Typography>
            </Box>
            
            <Button variant="outlined" size="small" href="/facturas">
              Ver Facturas
            </Button>
          </Paper>
        </Grid>

        {/* Régimen de Turismo */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Box display="flex" alignItems="center" mb={2}>
              <Warning sx={{ color: 'warning.main', mr: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Régimen de Turismo
              </Typography>
            </Box>
            
            {stats?.alerts?.tourism_regime_expiring === 0 ? (
              <Box display="flex" alignItems="center" mb={2}>
                <CheckCircle sx={{ color: 'success.main', mr: 1 }} />
                <Typography variant="body1">
                  Todos los regímenes vigentes
                </Typography>
              </Box>
            ) : (
              <Alert severity="warning" sx={{ mb: 2 }}>
                {formatNumber(stats?.alerts?.tourism_regime_expiring || 0)} régimen(es) vencen pronto
              </Alert>
            )}
            
            <Typography variant="body2" color="text.secondary" mb={2}>
              Documentos PDF del régimen de turismo. Alertas automáticas 30 días antes del vencimiento.
            </Typography>
            
            <Button variant="outlined" size="small" href="/clientes">
              Gestionar Clientes
            </Button>
          </Paper>
        </Grid>

        {/* Inventario */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Box display="flex" alignItems="center" mb={2}>
              <Inventory sx={{ color: 'info.main', mr: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Estado del Inventario
              </Typography>
            </Box>
            
            <Box mb={2}>
              <Typography variant="body1">
                Total productos: {formatNumber(stats?.basic_stats?.total_products || 0)}
              </Typography>
              
              {(stats?.alerts?.low_stock_count || 0) > 0 && (
                <Alert severity="warning" sx={{ mt: 1, mb: 1 }}>
                  {formatNumber(stats?.alerts?.low_stock_count || 0)} productos con stock bajo
                </Alert>
              )}
              
              {(stats?.alerts?.out_of_stock_count || 0) > 0 && (
                <Alert severity="error" sx={{ mt: 1, mb: 1 }}>
                  {formatNumber(stats?.alerts?.out_of_stock_count || 0)} productos sin stock
                </Alert>
              )}
              
              {(stats?.alerts?.low_stock_count || 0) === 0 && (stats?.alerts?.out_of_stock_count || 0) === 0 && (
                <Typography variant="body2" color="text.secondary">
                  Inventario sin alertas
                </Typography>
              )}
            </Box>
            
            <Button variant="outlined" size="small" href="/productos">
              Ver Productos
            </Button>
          </Paper>
        </Grid>
      </Grid>

      {/* Acciones Rápidas */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" mb={2}>
              <TrendingUp sx={{ color: 'primary.main', mr: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Acciones Rápidas
              </Typography>
            </Box>
            
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Button 
                  variant="contained" 
                  fullWidth 
                  href="/clientes"
                  sx={{ mb: 1, justifyContent: 'flex-start' }}
                >
                  <People sx={{ mr: 1 }} />
                  Nuevo Cliente
                </Button>
              </Grid>
              
              <Grid item xs={12}>
                <Button 
                  variant="outlined" 
                  fullWidth 
                  href="/cotizaciones"
                  sx={{ mb: 1, justifyContent: 'flex-start' }}
                >
                  <Description sx={{ mr: 1 }} />
                  Nueva Cotización
                </Button>
              </Grid>
              
              <Grid item xs={12}>
                <Button 
                  variant="outlined" 
                  fullWidth 
                  href="/depositos"
                  sx={{ mb: 1, justifyContent: 'flex-start' }}
                >
                  <AccountBalance sx={{ mr: 1 }} />
                  Gestionar Depósitos
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Información de Depósitos */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" mb={2}>
              <Assessment sx={{ color: 'secondary.main', mr: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Resumen de Depósitos
              </Typography>
            </Box>
            
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
              {formatCurrency(stats?.deposits?.total_amount || 0, 'PYG')}
            </Typography>
            
            <Typography variant="body2" color="text.secondary" mb={2}>
              Total disponible en {formatNumber(stats?.deposits?.active_count || 0)} depósitos activos
            </Typography>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="body2" color="text.secondary" mb={2}>
              Tipos: ANTICIPO, SEÑA, GARANTÍA, RETENCIÓN
            </Typography>
            
            <Button variant="outlined" size="small" href="/depositos">
              Ver Todos los Depósitos
            </Button>
          </Paper>
        </Grid>
      </Grid>

      {/* Información del Sistema */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3, bgcolor: 'background.paper' }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            Funcionalidades del Sistema
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center" p={2}>
                <Chip 
                  label="Régimen de Turismo" 
                  color="primary" 
                  sx={{ mb: 1, width: '100%' }} 
                />
                <Typography variant="body2" color="text.secondary">
                  Gestión de exención fiscal para turismo
                </Typography>
              </Box>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center" p={2}>
                <Chip 
                  label="Multi-Moneda" 
                  color="secondary" 
                  sx={{ mb: 1, width: '100%' }} 
                />
                <Typography variant="body2" color="text.secondary">
                  Guaraníes (PYG) y Dólares (USD)
                </Typography>
              </Box>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center" p={2}>
                <Chip 
                  label="Depósitos Paraguay" 
                  color="success" 
                  sx={{ mb: 1, width: '100%' }} 
                />
                <Typography variant="body2" color="text.secondary">
                  ANTICIPO, SEÑA, GARANTÍA, etc.
                </Typography>
              </Box>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center" p={2}>
                <Chip 
                  label="Notificaciones" 
                  color="info" 
                  sx={{ mb: 1, width: '100%' }} 
                />
                <Typography variant="body2" color="text.secondary">
                  Alertas automáticas de vencimientos
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      </Grid>
    </Box>
  );
}