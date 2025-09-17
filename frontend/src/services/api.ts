import axios, { type AxiosInstance } from 'axios';

// Configuración del cliente Axios
// En Replit, usar URL relativa para que funcione correctamente
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

class ApiService {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Interceptor para agregar el token a las peticiones
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Interceptor para manejar errores de autenticación
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expirado o inválido
          this.setToken(null);
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string | null) {
    this.token = token;
  }

  // ===== AUTENTICACIÓN =====
  async login(username: string, password: string) {
    // Enviar como JSON, no FormData
    const response = await this.client.post('/auth/login', {
      username,
      password
    });
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // ===== CLIENTES =====
  async getCustomers(params?: { skip?: number; limit?: number; search?: string; is_active?: boolean }) {
    const response = await this.client.get('/customers/', { params });
    return response.data;
  }

  async getCustomer(id: number) {
    const response = await this.client.get(`/customers/${id}`);
    return response.data;
  }

  async createCustomer(customerData: any) {
    const response = await this.client.post('/customers/', customerData);
    return response.data;
  }

  async updateCustomer(id: number, customerData: any) {
    const response = await this.client.put(`/customers/${id}`, customerData);
    return response.data;
  }

  async deleteCustomer(id: number) {
    const response = await this.client.delete(`/customers/${id}`);
    return response.data;
  }

  // Funciones específicas para régimen de turismo
  async uploadTourismPdf(customerId: number, file: File) {
    const formData = new FormData();
    formData.append('pdf_file', file);
    
    const response = await this.client.post(`/customers/${customerId}/upload-tourism-pdf`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async downloadTourismPdf(customerId: number) {
    const response = await this.client.get(`/customers/${customerId}/tourism-pdf`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async deleteTourismPdf(customerId: number) {
    const response = await this.client.delete(`/customers/${customerId}/tourism-pdf`);
    return response.data;
  }

  // ===== PRODUCTOS =====
  async getProducts(params?: { skip?: number; limit?: number; search?: string; category_id?: number }) {
    const response = await this.client.get('/products/', { params });
    return response.data;
  }

  async getProduct(id: number) {
    const response = await this.client.get(`/products/${id}`);
    return response.data;
  }

  async createProduct(productData: any) {
    const response = await this.client.post('/products/', productData);
    return response.data;
  }

  async updateProduct(id: number, productData: any) {
    const response = await this.client.put(`/products/${id}`, productData);
    return response.data;
  }

  async getProductCategories() {
    const response = await this.client.get('/products/categories/');
    return response.data;
  }

  // ===== COTIZACIONES =====
  async getQuotes(params?: { skip?: number; limit?: number; customer_id?: number; status?: string }) {
    const response = await this.client.get('/quotes/', { params });
    return response.data;
  }

  async getQuote(id: number) {
    const response = await this.client.get(`/quotes/${id}`);
    return response.data;
  }

  async createQuote(quoteData: any) {
    const response = await this.client.post('/quotes/', quoteData);
    return response.data;
  }

  async updateQuote(id: number, quoteData: any) {
    const response = await this.client.put(`/quotes/${id}`, quoteData);
    return response.data;
  }

  async generateQuotePdf(id: number) {
    const response = await this.client.get(`/quotes/${id}/pdf`);
    return response.data;
  }

  async downloadQuotePdf(id: number) {
    const response = await this.client.get(`/quotes/${id}/pdf/download`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // ===== FACTURAS =====
  async getInvoices(params?: { skip?: number; limit?: number; customer_id?: number; status?: string }) {
    const response = await this.client.get('/invoices/', { params });
    return response.data;
  }

  async getInvoice(id: number) {
    const response = await this.client.get(`/invoices/${id}`);
    return response.data;
  }

  async createInvoice(invoiceData: any) {
    const response = await this.client.post('/invoices/', invoiceData);
    return response.data;
  }

  async updateInvoice(id: number, invoiceData: any) {
    const response = await this.client.put(`/invoices/${id}`, invoiceData);
    return response.data;
  }

  // ===== DEPÓSITOS =====
  async getDeposits(params?: { skip?: number; limit?: number; customer_id?: number; deposit_type?: string }) {
    const response = await this.client.get('/deposits/', { params });
    return response.data;
  }

  async getDeposit(id: number) {
    const response = await this.client.get(`/deposits/${id}`);
    return response.data;
  }

  async createDeposit(depositData: any) {
    const response = await this.client.post('/deposits/', depositData);
    return response.data;
  }

  async applyDepositToInvoice(depositId: number, data: { invoice_id: number; amount: number }) {
    const response = await this.client.post(`/deposits/${depositId}/apply-to-invoice`, data);
    return response.data;
  }

  async refundDeposit(depositId: number, data: { amount: number; reason: string }) {
    const response = await this.client.post(`/deposits/${depositId}/refund`, data);
    return response.data;
  }

  async getDepositSummary() {
    const response = await this.client.get('/deposits/summary');
    return response.data;
  }

  // ===== CONFIGURACIÓN DE EMPRESA =====
  async getCompanySettings() {
    const response = await this.client.get('/company/settings');
    return response.data;
  }

  async createCompanySettings(settingsData: any) {
    const response = await this.client.post('/company/settings', settingsData);
    return response.data;
  }

  async updateCompanySettings(settingsData: any) {
    const response = await this.client.put('/company/settings', settingsData);
    return response.data;
  }

  async getCompanySettingsPublic() {
    const response = await this.client.get('/company/settings/public');
    return response.data;
  }

  async markConfigurationComplete() {
    const response = await this.client.post('/company/settings/complete');
    return response.data;
  }

  async getNextInvoiceNumber() {
    const response = await this.client.get('/company/numbering/next-invoice');
    return response.data;
  }

  async getNextQuoteNumber() {
    const response = await this.client.get('/company/numbering/next-quote');
    return response.data;
  }

  // ===== DASHBOARD =====
  async getDashboardStats() {
    const response = await this.client.get('/dashboard/stats');
    return response.data;
  }

  async getDashboardOverview() {
    const response = await this.client.get('/dashboard/metrics/overview');
    return response.data;
  }

  async getSalesTrend(days: number = 30) {
    const response = await this.client.get(`/dashboard/metrics/sales-trend?days=${days}`);
    return response.data;
  }

  async getTopProducts(limit: number = 10) {
    const response = await this.client.get(`/dashboard/metrics/top-products?limit=${limit}`);
    return response.data;
  }

  async getCustomerAnalysis() {
    const response = await this.client.get('/dashboard/metrics/customer-analysis');
    return response.data;
  }

  async getInventoryStatus() {
    const response = await this.client.get('/dashboard/metrics/inventory-status');
    return response.data;
  }
}

export const apiService = new ApiService();