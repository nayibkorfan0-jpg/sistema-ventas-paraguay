import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Customers from './pages/Customers';
import Quotes from './pages/Quotes';
import Invoices from './pages/Invoices';
import Products from './pages/Products';
import Deposits from './pages/Deposits';
import Reports from './pages/Reports';
import CompanySettings from './pages/CompanySettings';
import './App.css';

// Tema profesional para empresas paraguayas
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Azul empresarial
      dark: '#115293',
      light: '#42a5f5',
    },
    secondary: {
      main: '#ff9800', // Naranja paraguayo
      dark: '#f57c00',
      light: '#ffb74d',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
    text: {
      primary: '#212121',
      secondary: '#757575',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
      fontSize: '2.125rem',
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.5rem',
    },
    h6: {
      fontWeight: 600,
      fontSize: '1.25rem',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          fontWeight: 500,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="clientes" element={<Customers />} />
              <Route path="cotizaciones" element={<Quotes />} />
              <Route path="facturas" element={<Invoices />} />
              <Route path="productos" element={<Products />} />
              <Route path="depositos" element={<Deposits />} />
              <Route path="reportes" element={<Reports />} />
              <Route path="configuracion" element={<CompanySettings />} />
            </Route>
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;