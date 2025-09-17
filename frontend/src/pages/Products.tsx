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
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Inventory as InventoryIcon,
  Category as CategoryIcon,
  AttachMoney as MoneyIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';

interface Product {
  id: number;
  name: string;
  description?: string;
  sku: string;
  category_id?: number;
  category_name?: string;
  unit_price: number;
  cost_price: number;
  stock_quantity: number;
  min_stock_level: number;
  max_stock_level: number;
  is_active: boolean;
  expiry_date?: string;
}

interface Category {
  id: number;
  name: string;
}

export default function Products() {
  const { user } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  
  // Formulario
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    sku: '',
    category_id: 0,
    unit_price: 0,
    cost_price: 0,
    stock_quantity: 0,
    min_stock_level: 0,
    max_stock_level: 100,
    is_active: true,
    expiry_date: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [productsData, categoriesData] = await Promise.all([
        apiService.getProducts({ limit: 1000 }),
        apiService.getProductCategories()
      ]);
      
      setProducts(productsData);
      setCategories(categoriesData);
    } catch (err) {
      setError('Error al cargar productos');
      console.error('Error loading products:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (product?: Product) => {
    if (product) {
      setEditingProduct(product);
      setFormData({
        name: product.name,
        description: product.description || '',
        sku: product.sku,
        category_id: product.category_id || 0,
        unit_price: product.unit_price,
        cost_price: product.cost_price,
        stock_quantity: product.stock_quantity,
        min_stock_level: product.min_stock_level,
        max_stock_level: product.max_stock_level,
        is_active: product.is_active,
        expiry_date: product.expiry_date || '',
      });
    } else {
      setEditingProduct(null);
      setFormData({
        name: '',
        description: '',
        sku: '',
        category_id: 0,
        unit_price: 0,
        cost_price: 0,
        stock_quantity: 0,
        min_stock_level: 0,
        max_stock_level: 100,
        is_active: true,
        expiry_date: '',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingProduct(null);
  };

  const handleSubmit = async () => {
    try {
      if (editingProduct) {
        await apiService.updateProduct(editingProduct.id, formData);
      } else {
        await apiService.createProduct(formData);
      }
      
      await loadData();
      handleCloseDialog();
    } catch (err) {
      setError('Error al guardar producto');
      console.error('Error saving product:', err);
    }
  };

  const isLowStock = (product: Product) => {
    return product.stock_quantity <= product.min_stock_level;
  };

  const isExpiringSoon = (expiryDate?: string) => {
    if (!expiryDate) return false;
    const expiry = new Date(expiryDate);
    const today = new Date();
    const daysUntilExpiry = Math.ceil((expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    return daysUntilExpiry <= 30 && daysUntilExpiry >= 0;
  };

  const isExpired = (expiryDate?: string) => {
    if (!expiryDate) return false;
    const expiry = new Date(expiryDate);
    const today = new Date();
    return expiry < today;
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
          Gestión de Productos
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Nuevo Producto
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
              <InventoryIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {products.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Productos
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <WarningIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {products.filter(p => isLowStock(p)).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Stock Bajo
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <CategoryIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {categories.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Categorías
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <MoneyIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Gs. {products.reduce((sum, p) => sum + (p.unit_price * p.stock_quantity), 0).toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Valor Inventario
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alertas de productos */}
      {products.filter(p => isLowStock(p) || isExpiringSoon(p.expiry_date) || isExpired(p.expiry_date)).length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Productos que requieren atención:
          </Typography>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {products.filter(p => isLowStock(p)).map(p => (
              <li key={p.id}>
                <strong>{p.name}</strong> - Stock bajo ({p.stock_quantity} unidades)
              </li>
            ))}
            {products.filter(p => isExpired(p.expiry_date)).map(p => (
              <li key={p.id}>
                <strong>{p.name}</strong> - Producto vencido
              </li>
            ))}
            {products.filter(p => isExpiringSoon(p.expiry_date) && !isExpired(p.expiry_date)).map(p => (
              <li key={p.id}>
                <strong>{p.name}</strong> - Vence pronto
              </li>
            ))}
          </ul>
        </Alert>
      )}

      {/* Tabla de productos */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><strong>Producto</strong></TableCell>
              <TableCell><strong>SKU</strong></TableCell>
              <TableCell><strong>Categoría</strong></TableCell>
              <TableCell><strong>Precio</strong></TableCell>
              <TableCell><strong>Stock</strong></TableCell>
              <TableCell><strong>Vencimiento</strong></TableCell>
              <TableCell><strong>Estado</strong></TableCell>
              <TableCell><strong>Acciones</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {products.map((product) => (
              <TableRow key={product.id}>
                <TableCell>
                  <Box>
                    <Typography variant="subtitle2" fontWeight={600}>
                      {product.name}
                    </Typography>
                    {product.description && (
                      <Typography variant="caption" color="text.secondary">
                        {product.description}
                      </Typography>
                    )}
                  </Box>
                </TableCell>
                <TableCell>{product.sku}</TableCell>
                <TableCell>{product.category_name || '-'}</TableCell>
                <TableCell>Gs. {product.unit_price.toLocaleString()}</TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography
                      variant="body2"
                      color={isLowStock(product) ? 'error' : 'text.primary'}
                      fontWeight={isLowStock(product) ? 600 : 400}
                    >
                      {product.stock_quantity}
                    </Typography>
                    {isLowStock(product) && (
                      <Chip 
                        label="Bajo" 
                        color="warning" 
                        size="small"
                      />
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  {product.expiry_date ? (
                    <Box>
                      <Typography 
                        variant="body2"
                        color={
                          isExpired(product.expiry_date) ? 'error' :
                          isExpiringSoon(product.expiry_date) ? 'warning.main' : 'text.primary'
                        }
                      >
                        {new Date(product.expiry_date).toLocaleDateString()}
                      </Typography>
                      {isExpired(product.expiry_date) && (
                        <Chip label="Vencido" color="error" size="small" />
                      )}
                      {isExpiringSoon(product.expiry_date) && !isExpired(product.expiry_date) && (
                        <Chip label="Vence pronto" color="warning" size="small" />
                      )}
                    </Box>
                  ) : '-'}
                </TableCell>
                <TableCell>
                  <Chip 
                    label={product.is_active ? 'Activo' : 'Inactivo'} 
                    color={product.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <IconButton 
                    onClick={() => handleOpenDialog(product)}
                    color="primary"
                    size="small"
                  >
                    <EditIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog para crear/editar producto */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingProduct ? 'Editar Producto' : 'Nuevo Producto'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Nombre del Producto *"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="SKU/Código"
                value={formData.sku}
                onChange={(e) => setFormData({...formData, sku: e.target.value})}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Descripción"
                multiline
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                select
                label="Categoría"
                value={formData.category_id}
                onChange={(e) => setFormData({...formData, category_id: Number(e.target.value)})}
              >
                <MenuItem value={0}>Sin categoría</MenuItem>
                {categories.map((category) => (
                  <MenuItem key={category.id} value={category.id}>
                    {category.name}
                  </MenuItem>
                ))}
              </TextField>
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
                label="Precio de Venta"
                type="number"
                value={formData.unit_price}
                onChange={(e) => setFormData({...formData, unit_price: Number(e.target.value)})}
                InputProps={{
                  startAdornment: <Typography sx={{ mr: 1 }}>Gs.</Typography>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Precio de Costo"
                type="number"
                value={formData.cost_price}
                onChange={(e) => setFormData({...formData, cost_price: Number(e.target.value)})}
                InputProps={{
                  startAdornment: <Typography sx={{ mr: 1 }}>Gs.</Typography>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Stock Actual"
                type="number"
                value={formData.stock_quantity}
                onChange={(e) => setFormData({...formData, stock_quantity: Number(e.target.value)})}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Stock Mínimo"
                type="number"
                value={formData.min_stock_level}
                onChange={(e) => setFormData({...formData, min_stock_level: Number(e.target.value)})}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Stock Máximo"
                type="number"
                value={formData.max_stock_level}
                onChange={(e) => setFormData({...formData, max_stock_level: Number(e.target.value)})}
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
            disabled={!formData.name}
          >
            {editingProduct ? 'Actualizar' : 'Crear'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}