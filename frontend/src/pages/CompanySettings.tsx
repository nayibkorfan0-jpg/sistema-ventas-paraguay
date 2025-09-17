import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  Divider,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Card,
  CardContent,
  CardHeader,
  Chip,
} from '@mui/material';
import {
  Save,
  Business,
  Receipt,
  ContactMail,
  Settings,
  CheckCircle,
  Warning,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';

interface CompanySettings {
  id?: number;
  razon_social: string;
  nombre_comercial?: string;
  ruc: string;
  timbrado: string;
  punto_expedicion: string;
  dv_ruc?: string;
  direccion: string;
  ciudad: string;
  departamento: string;
  codigo_postal?: string;
  telefono?: string;
  celular?: string;
  email?: string;
  sitio_web?: string;
  moneda_defecto: 'PYG' | 'USD';
  iva_10_porciento: number;
  iva_5_porciento: number;
  iva_exento: boolean;
  numeracion_facturas_inicio: number;
  numeracion_facturas_actual: number;
  numeracion_cotizaciones_inicio: number;
  numeracion_cotizaciones_actual: number;
  formato_impresion: 'A4' | 'ticket';
  logo_empresa?: string;
  firma_digital?: string;
  regimen_tributario: string;
  contribuyente_iva: boolean;
  actividad_economica?: string;
  sector_economico?: string;
  notas_adicionales?: string;
  is_active: boolean;
  configuracion_completa: boolean;
}

const defaultSettings: CompanySettings = {
  razon_social: '',
  nombre_comercial: '',
  ruc: '',
  timbrado: '',
  punto_expedicion: '001',
  dv_ruc: '',
  direccion: '',
  ciudad: 'Asunción',
  departamento: 'Central',
  codigo_postal: '',
  telefono: '',
  celular: '',
  email: '',
  sitio_web: '',
  moneda_defecto: 'PYG',
  iva_10_porciento: 10.00,
  iva_5_porciento: 5.00,
  iva_exento: false,
  numeracion_facturas_inicio: 1,
  numeracion_facturas_actual: 1,
  numeracion_cotizaciones_inicio: 1,
  numeracion_cotizaciones_actual: 1,
  formato_impresion: 'A4',
  logo_empresa: '',
  firma_digital: '',
  regimen_tributario: 'GENERAL',
  contribuyente_iva: true,
  actividad_economica: '',
  sector_economico: '',
  notas_adicionales: '',
  is_active: true,
  configuracion_completa: false,
};

export default function CompanySettings() {
  const { user } = useAuth();
  const [settings, setSettings] = useState<CompanySettings>(defaultSettings);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isNewConfiguration, setIsNewConfiguration] = useState(false);

  // Verificar permisos
  const canEdit = user?.role === 'admin' || user?.role === 'manager';

  useEffect(() => {
    loadCompanySettings();
  }, []);

  const loadCompanySettings = async () => {
    try {
      setLoading(true);
      setError('');
      
      const data = await apiService.getCompanySettings();
      setSettings(data);
      setIsNewConfiguration(false);
    } catch (err: any) {
      if (err.response?.status === 404) {
        // No existe configuración, usar valores por defecto
        setSettings(defaultSettings);
        setIsNewConfiguration(true);
      } else {
        setError('Error al cargar configuración de empresa');
        console.error('Error loading company settings:', err);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!canEdit) {
      setError('No tienes permisos para modificar la configuración');
      return;
    }

    try {
      setSaving(true);
      setError('');
      setSuccess('');

      let savedSettings;
      if (isNewConfiguration) {
        savedSettings = await apiService.createCompanySettings(settings);
        setIsNewConfiguration(false);
      } else {
        savedSettings = await apiService.updateCompanySettings(settings);
      }

      setSettings(savedSettings);
      setSuccess('Configuración guardada exitosamente');
      
      // Limpiar mensaje de éxito después de 3 segundos
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al guardar configuración');
      console.error('Error saving company settings:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: keyof CompanySettings, value: any) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const validateRUC = (ruc: string) => {
    const rucClean = ruc.replace(/[-\s]/g, '');
    if (rucClean.length < 6 || rucClean.length > 10) {
      return 'RUC debe tener entre 6 y 10 dígitos';
    }
    if (!/^\d+$/.test(rucClean)) {
      return 'RUC debe contener solo números';
    }
    return '';
  };

  const validateTimbrado = (timbrado: string) => {
    const timbradoClean = timbrado.replace(/[-\s]/g, '');
    if (timbradoClean.length < 8) {
      return 'Timbrado debe tener al menos 8 dígitos';
    }
    if (!/^\d+$/.test(timbradoClean)) {
      return 'Timbrado debe contener solo números';
    }
    return '';
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
      <Box mb={3}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          <Settings sx={{ mr: 1, verticalAlign: 'middle' }} />
          Configuración de Empresa
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Configure los datos fiscales y operativos de su empresa paraguaya
        </Typography>
        
        {!canEdit && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            Solo los administradores pueden modificar la configuración de empresa
          </Alert>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} icon={<CheckCircle />}>
          {success}
        </Alert>
      )}

      {/* Estado de configuración */}
      <Card sx={{ mb: 3, bgcolor: settings.configuracion_completa ? 'success.light' : 'warning.light' }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center">
              {settings.configuracion_completa ? (
                <CheckCircle sx={{ color: 'success.main', mr: 1 }} />
              ) : (
                <Warning sx={{ color: 'warning.main', mr: 1 }} />
              )}
              <Typography variant="h6">
                Estado de Configuración: {' '}
                <Chip 
                  label={settings.configuracion_completa ? 'Completa' : 'Pendiente'}
                  color={settings.configuracion_completa ? 'success' : 'warning'}
                  size="small"
                />
              </Typography>
            </Box>
            {isNewConfiguration && (
              <Chip label="Nueva Configuración" color="primary" />
            )}
          </Box>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* DATOS BÁSICOS DE LA EMPRESA */}
        <Grid {...({ item: true, xs: 12, md: 6 } as any)}>
          <Card>
            <CardHeader 
              title="Datos Básicos de la Empresa"
              avatar={<Business />}
            />
            <CardContent>
              <Grid container spacing={2}>
                <Grid {...({ item: true, xs: 12 } as any)}>
                  <TextField
                    fullWidth
                    label="Razón Social *"
                    value={settings.razon_social}
                    onChange={(e) => handleInputChange('razon_social', e.target.value)}
                    disabled={!canEdit}
                    error={!settings.razon_social}
                    helperText={!settings.razon_social ? 'Campo obligatorio' : ''}
                  />
                </Grid>
                <Grid {...({ item: true, xs: 12 } as any)}>
                  <TextField
                    fullWidth
                    label="Nombre Comercial"
                    value={settings.nombre_comercial}
                    onChange={(e) => handleInputChange('nombre_comercial', e.target.value)}
                    disabled={!canEdit}
                  />
                </Grid>
                <Grid {...({ item: true, xs: 12 } as any)}>
                  <TextField
                    fullWidth
                    multiline
                    rows={2}
                    label="Dirección *"
                    value={settings.direccion}
                    onChange={(e) => handleInputChange('direccion', e.target.value)}
                    disabled={!canEdit}
                    error={!settings.direccion}
                    helperText={!settings.direccion ? 'Campo obligatorio' : ''}
                  />
                </Grid>
                <Grid {...({ item: true, xs: 6 } as any)}>
                  <TextField
                    fullWidth
                    label="Ciudad"
                    value={settings.ciudad}
                    onChange={(e) => handleInputChange('ciudad', e.target.value)}
                    disabled={!canEdit}
                  />
                </Grid>
                <Grid {...({ item: true, xs: 6 } as any)}>
                  <TextField
                    fullWidth
                    label="Departamento"
                    value={settings.departamento}
                    onChange={(e) => handleInputChange('departamento', e.target.value)}
                    disabled={!canEdit}
                  />
                </Grid>
                <Grid {...({ item: true, xs: 12 } as any)}>
                  <TextField
                    fullWidth
                    label="Actividad Económica"
                    value={settings.actividad_economica}
                    onChange={(e) => handleInputChange('actividad_economica', e.target.value)}
                    disabled={!canEdit}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* DATOS FISCALES PARA PARAGUAY */}
        <Grid {...({ item: true, xs: 12, md: 6 } as any)}>
          <Card>
            <CardHeader 
              title="Datos Fiscales Paraguay"
              avatar={<Receipt />}
            />
            <CardContent>
              <Grid container spacing={2}>
                <Grid {...({ item: true, xs: 12 } as any)}>
                  <TextField
                    fullWidth
                    label="RUC *"
                    value={settings.ruc}
                    onChange={(e) => handleInputChange('ruc', e.target.value)}
                    disabled={!canEdit}
                    error={!settings.ruc || !!validateRUC(settings.ruc)}
                    helperText={
                      !settings.ruc 
                        ? 'Campo obligatorio' 
                        : validateRUC(settings.ruc) || 'Ej: 80012345-1'
                    }
                    placeholder="80012345-1"
                  />
                </Grid>
                <Grid {...({ item: true, xs: 12 } as any)}>
                  <TextField
                    fullWidth
                    label="Timbrado *"
                    value={settings.timbrado}
                    onChange={(e) => handleInputChange('timbrado', e.target.value)}
                    disabled={!canEdit}
                    error={!settings.timbrado || !!validateTimbrado(settings.timbrado)}
                    helperText={
                      !settings.timbrado 
                        ? 'Campo obligatorio' 
                        : validateTimbrado(settings.timbrado) || 'Número de timbrado fiscal'
                    }
                  />
                </Grid>
                <Grid {...({ item: true, xs: 6 } as any)}>
                  <TextField
                    fullWidth
                    label="Punto de Expedición"
                    value={settings.punto_expedicion}
                    onChange={(e) => handleInputChange('punto_expedicion', e.target.value.padStart(3, '0'))}
                    disabled={!canEdit}
                    inputProps={{ maxLength: 3 }}
                  />
                </Grid>
                <Grid {...({ item: true, xs: 6 } as any)}>
                  <TextField
                    fullWidth
                    label="DV RUC"
                    value={settings.dv_ruc}
                    onChange={(e) => handleInputChange('dv_ruc', e.target.value)}
                    disabled={!canEdit}
                    inputProps={{ maxLength: 2 }}
                  />
                </Grid>
                <Grid {...({ item: true, xs: 12 } as any)}>
                  <FormControl fullWidth>
                    <InputLabel>Régimen Tributario</InputLabel>
                    <Select
                      value={settings.regimen_tributario}
                      onChange={(e) => handleInputChange('regimen_tributario', e.target.value)}
                      disabled={!canEdit}
                      label="Régimen Tributario"
                    >
                      <MenuItem value="GENERAL">General</MenuItem>
                      <MenuItem value="SIMPLIFICADO">Simplificado</MenuItem>
                      <MenuItem value="PEQUENO_CONTRIBUYENTE">Pequeño Contribuyente</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid {...({ item: true, xs: 12 } as any)}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.contribuyente_iva}
                        onChange={(e) => handleInputChange('contribuyente_iva', e.target.checked)}
                        disabled={!canEdit}
                      />
                    }
                    label="Contribuyente de IVA"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* DATOS DE CONTACTO */}
        <Grid {...({ item: true, xs: 12, md: 6 } as any)}>
          <Card>
            <CardHeader 
              title="Información de Contacto"
              avatar={<ContactMail />}
            />
            <CardContent>
              <Grid container spacing={2}>
                <Grid {...({ item: true, xs: 6 } as any)}>
                  <TextField
                    fullWidth
                    label="Teléfono"
                    value={settings.telefono}
                    onChange={(e) => handleInputChange('telefono', e.target.value)}
                    disabled={!canEdit}
                  />
                </Grid>
                <Grid {...({ item: true, xs: 6 } as any)}>
                  <TextField
                    fullWidth
                    label="Celular"
                    value={settings.celular}
                    onChange={(e) => handleInputChange('celular', e.target.value)}
                    disabled={!canEdit}
                  />
                </Grid>
                <Grid {...({ item: true, xs: 12 } as any)}>
                  <TextField
                    fullWidth
                    type="email"
                    label="Email"
                    value={settings.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    disabled={!canEdit}
                  />
                </Grid>
                <Grid {...({ item: true, xs: 12 } as any)}>
                  <TextField
                    fullWidth
                    label="Sitio Web"
                    value={settings.sitio_web}
                    onChange={(e) => handleInputChange('sitio_web', e.target.value)}
                    disabled={!canEdit}
                    placeholder="https://www.miempresa.com.py"
                  />
                </Grid>
                <Grid {...({ item: true, xs: 12 } as any)}>
                  <TextField
                    fullWidth
                    label="Código Postal"
                    value={settings.codigo_postal}
                    onChange={(e) => handleInputChange('codigo_postal', e.target.value)}
                    disabled={!canEdit}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* CONFIGURACIÓN OPERATIVA */}
        <Grid {...({ item: true, xs: 12, md: 6 } as any)}>
          <Card>
            <CardHeader 
              title="Configuración Operativa"
              avatar={<Settings />}
            />
            <CardContent>
              <Grid container spacing={2}>
                <Grid {...({ item: true, xs: 12 } as any)}>
                  <FormControl fullWidth>
                    <InputLabel>Moneda por Defecto</InputLabel>
                    <Select
                      value={settings.moneda_defecto}
                      onChange={(e) => handleInputChange('moneda_defecto', e.target.value)}
                      disabled={!canEdit}
                      label="Moneda por Defecto"
                    >
                      <MenuItem value="PYG">Guaraníes (PYG)</MenuItem>
                      <MenuItem value="USD">Dólares (USD)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid {...({ item: true, xs: 6 } as any)}>
                  <TextField
                    fullWidth
                    type="number"
                    label="IVA 10%"
                    value={settings.iva_10_porciento}
                    onChange={(e) => handleInputChange('iva_10_porciento', parseFloat(e.target.value) || 0)}
                    disabled={!canEdit}
                    inputProps={{ step: 0.01, min: 0, max: 100 }}
                  />
                </Grid>
                <Grid {...({ item: true, xs: 6 } as any)}>
                  <TextField
                    fullWidth
                    type="number"
                    label="IVA 5%"
                    value={settings.iva_5_porciento}
                    onChange={(e) => handleInputChange('iva_5_porciento', parseFloat(e.target.value) || 0)}
                    disabled={!canEdit}
                    inputProps={{ step: 0.01, min: 0, max: 100 }}
                  />
                </Grid>
                <Grid {...({ item: true, xs: 12 } as any)}>
                  <FormControl fullWidth>
                    <InputLabel>Formato de Impresión</InputLabel>
                    <Select
                      value={settings.formato_impresion}
                      onChange={(e) => handleInputChange('formato_impresion', e.target.value)}
                      disabled={!canEdit}
                      label="Formato de Impresión"
                    >
                      <MenuItem value="A4">A4 (Carta)</MenuItem>
                      <MenuItem value="ticket">Ticket (80mm)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid {...({ item: true, xs: 6 } as any)}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Numeración Facturas - Inicio"
                    value={settings.numeracion_facturas_inicio}
                    onChange={(e) => handleInputChange('numeracion_facturas_inicio', parseInt(e.target.value) || 1)}
                    disabled={!canEdit}
                    inputProps={{ min: 1 }}
                  />
                </Grid>
                <Grid {...({ item: true, xs: 6 } as any)}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Numeración Facturas - Actual"
                    value={settings.numeracion_facturas_actual}
                    onChange={(e) => handleInputChange('numeracion_facturas_actual', parseInt(e.target.value) || 1)}
                    disabled={!canEdit}
                    inputProps={{ min: 1 }}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Notas adicionales */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Notas Adicionales
        </Typography>
        <TextField
          fullWidth
          multiline
          rows={3}
          label="Observaciones y notas"
          value={settings.notas_adicionales}
          onChange={(e) => handleInputChange('notas_adicionales', e.target.value)}
          disabled={!canEdit}
          placeholder="Ingrese cualquier información adicional sobre la empresa..."
        />
      </Paper>

      {/* Botones de acción */}
      {canEdit && (
        <Box display="flex" justifyContent="flex-end" gap={2} mt={3}>
          <Button
            variant="outlined"
            onClick={loadCompanySettings}
            disabled={saving}
          >
            Cancelar
          </Button>
          <Button
            variant="contained"
            startIcon={saving ? <CircularProgress size={20} /> : <Save />}
            onClick={handleSave}
            disabled={saving || !settings.razon_social || !settings.ruc || !settings.timbrado || !settings.direccion}
          >
            {saving ? 'Guardando...' : (isNewConfiguration ? 'Crear Configuración' : 'Guardar Cambios')}
          </Button>
        </Box>
      )}
    </Box>
  );
}