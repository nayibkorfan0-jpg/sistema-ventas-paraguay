// ERP Empresarial - Professional Sales Management System
const API_BASE = '';
let authToken = localStorage.getItem('authToken');
let currentUser = null;
let allProducts = [];
let allCustomers = [];
let allCategories = [];

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    if (authToken) {
        await checkAuth();
    } else {
        showLogin();
    }
    
    setupEventListeners();
}

function setupEventListeners() {
    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Navigation links
    document.querySelectorAll('.nav-link[data-section]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.dataset.section;
            showSection(section);
            updateActiveNav(this);
            updatePageHeader(section);
        });
    });
    
    // Form submissions
    setupFormHandlers();
}

function setupFormHandlers() {
    // Product forms
    const addProductForm = document.getElementById('addProductForm');
    if (addProductForm) {
        addProductForm.addEventListener('submit', handleAddProduct);
    }
    
    const editProductForm = document.getElementById('editProductForm');
    if (editProductForm) {
        editProductForm.addEventListener('submit', handleEditProduct);
    }
    
    // Customer forms
    const addCustomerForm = document.getElementById('addCustomerForm');
    if (addCustomerForm) {
        addCustomerForm.addEventListener('submit', handleAddCustomer);
    }
    
    // Quote forms
    const addQuoteForm = document.getElementById('addQuoteForm');
    if (addQuoteForm) {
        addQuoteForm.addEventListener('submit', handleAddQuote);
    }
    
    // Quote item management
    const addQuoteItemBtn = document.getElementById('addQuoteItem');
    if (addQuoteItemBtn) {
        addQuoteItemBtn.addEventListener('click', addQuoteItem);
    }
}

// ===== AUTHENTICATION FUNCTIONS =====
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    const submitBtn = e.target.querySelector('.btn-login');
    const originalText = submitBtn.innerHTML;
    
    submitBtn.innerHTML = '<div class="spinner"></div> Iniciando sesión...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            currentUser = data.user;
            
            localStorage.setItem('authToken', authToken);
            
            await showApp();
            await loadInitialData();
        } else {
            const error = await response.json();
            showNotification('Error de autenticación: ' + (error.detail || 'Credenciales inválidas'), 'error');
        }
    } catch (error) {
        showNotification('Error de conexión con el servidor', 'error');
        console.error('Login error:', error);
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

async function checkAuth() {
    try {
        const response = await apiCall('/api/customers/');
        if (response) {
            await showApp();
            await loadInitialData();
        } else {
            logout();
        }
    } catch (error) {
        logout();
    }
}

function showLogin() {
    const loginSection = document.getElementById('login-section');
    const appSection = document.getElementById('app-section');
    
    if (loginSection) {
        loginSection.classList.remove('d-none');
    }
    if (appSection) {
        appSection.classList.add('d-none');
    }
}

async function showApp() {
    const loginSection = document.getElementById('login-section');
    const appSection = document.getElementById('app-section');
    
    if (loginSection) {
        loginSection.classList.add('d-none');
    }
    if (appSection) {
        appSection.classList.remove('d-none');
    }
    
    if (currentUser) {
        const userNameEl = document.getElementById('user-name');
        const userAvatarEl = document.getElementById('user-avatar');
        
        if (userNameEl) {
            userNameEl.textContent = currentUser.full_name || currentUser.username;
        }
        if (userAvatarEl) {
            userAvatarEl.textContent = (currentUser.full_name || currentUser.username).charAt(0).toUpperCase();
        }
    }
}

function logout() {
    localStorage.removeItem('authToken');
    authToken = null;
    currentUser = null;
    showLogin();
}

// ===== API FUNCTIONS =====
async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    if (finalOptions.headers && options.headers) {
        finalOptions.headers = { ...defaultOptions.headers, ...options.headers };
    }
    
    try {
        const response = await fetch(url, finalOptions);
        
        if (response.status === 401) {
            logout();
            return null;
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// ===== NAVIGATION FUNCTIONS =====
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.add('d-none');
    });
    
    // Show selected section
    const targetSection = document.getElementById(`${sectionName}-section`);
    if (targetSection) {
        targetSection.classList.remove('d-none');
    }
    
    // Load section-specific data
    loadSectionData(sectionName);
}

function updateActiveNav(activeLink) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    activeLink.classList.add('active');
}

function updatePageHeader(section) {
    const pageTitle = document.getElementById('page-title');
    const pageSubtitle = document.getElementById('page-subtitle');
    
    const headers = {
        dashboard: {
            title: 'Dashboard Ejecutivo',
            subtitle: 'Vista general del sistema de ventas'
        },
        customers: {
            title: 'Gestión de Clientes',
            subtitle: 'Administración completa de clientes y prospectos'
        },
        quotes: {
            title: 'Cotizaciones',
            subtitle: 'Crear y gestionar cotizaciones de venta'
        },
        orders: {
            title: 'Órdenes de Venta',
            subtitle: 'Procesamiento y seguimiento de órdenes'
        },
        invoices: {
            title: 'Facturas',
            subtitle: 'Facturación y control de pagos'
        },
        products: {
            title: 'Productos',
            subtitle: 'Catálogo y gestión de inventario'
        },
        analytics: {
            title: 'Análisis Avanzado',
            subtitle: 'Métricas detalladas y reportes empresariales'
        }
    };
    
    const header = headers[section] || headers.dashboard;
    
    if (pageTitle) {
        pageTitle.textContent = header.title;
    }
    if (pageSubtitle) {
        pageSubtitle.textContent = header.subtitle;
    }
}

// ===== DATA LOADING FUNCTIONS =====
async function loadInitialData() {
    try {
        showLoadingState();
        
        // Load all necessary data
        await Promise.all([
            loadDashboardMetrics(),
            loadNavigationCounts(),
            loadCategories(),
            loadCustomers(),
            loadProducts()
        ]);
        
        hideLoadingState();
        
    } catch (error) {
        console.error('Error loading initial data:', error);
        showNotification('Error cargando datos del sistema', 'error');
        hideLoadingState();
    }
}

async function loadSectionData(section) {
    switch (section) {
        case 'products':
            await loadProducts();
            break;
        case 'customers':
            await loadCustomers();
            break;
        case 'quotes':
            await loadQuotes();
            break;
        case 'users':
            await loadUsersData();
            break;
        default:
            break;
    }
}

async function loadDashboardMetrics() {
    try {
        const [customers, quotes, orders, products] = await Promise.all([
            apiCall('/api/customers/'),
            apiCall('/api/quotes/'),
            apiCall('/api/sales-orders/'),
            apiCall('/api/products/')
        ]);
        
        const totalRevenue = orders ? orders.reduce((sum, order) => sum + parseFloat(order.total_amount || 0), 0) : 0;
        
        updateDashboardMetric('total-customers-metric', customers ? customers.length : '0');
        updateDashboardMetric('total-quotes-metric', quotes ? quotes.length : '0');
        updateDashboardMetric('total-orders-metric', orders ? orders.length : '0');
        updateDashboardMetric('total-revenue-metric', formatCurrency(totalRevenue));
        
    } catch (error) {
        console.error('Error loading dashboard metrics:', error);
    }
}

async function loadNavigationCounts() {
    try {
        const [customers, quotes, orders, products, invoices] = await Promise.all([
            apiCall('/api/customers/'),
            apiCall('/api/quotes/'),
            apiCall('/api/sales-orders/'),
            apiCall('/api/products/'),
            apiCall('/api/invoices/')
        ]);
        
        updateNavigationCount('customers-count', customers ? customers.length : '0');
        updateNavigationCount('quotes-count', quotes ? quotes.length : '0');
        updateNavigationCount('orders-count', orders ? orders.length : '0');
        updateNavigationCount('products-count', products ? products.length : '0');
        updateNavigationCount('invoices-count', invoices ? invoices.length : '0');
        
    } catch (error) {
        console.error('Error loading navigation counts:', error);
    }
}

async function loadCategories() {
    try {
        allCategories = await apiCall('/api/products/categories/') || [];
        updateCategorySelects();
    } catch (error) {
        console.error('Error loading categories:', error);
        allCategories = [];
    }
}

async function loadCustomers() {
    try {
        allCustomers = await apiCall('/api/customers/') || [];
        updateCustomerTable();
        updateCustomerSelects();
    } catch (error) {
        console.error('Error loading customers:', error);
        allCustomers = [];
    }
}

async function loadProducts() {
    try {
        allProducts = await apiCall('/api/products/') || [];
        updateProductTable();
    } catch (error) {
        console.error('Error loading products:', error);
        allProducts = [];
    }
}

async function loadQuotes() {
    try {
        const quotes = await apiCall('/api/quotes/') || [];
        updateQuoteTable(quotes);
    } catch (error) {
        console.error('Error loading quotes:', error);
    }
}

// ===== PRODUCT FUNCTIONS =====
function openAddProductModal() {
    const modal = new bootstrap.Modal(document.getElementById('addProductModal'));
    // Reset form
    document.getElementById('addProductForm').reset();
    // Set default values
    document.getElementById('productIsActive').checked = true;
    document.getElementById('productIsTrackable').checked = true;
    modal.show();
}

function openEditProductModal(productId) {
    const product = allProducts.find(p => p.id === productId);
    if (!product) {
        showNotification('Producto no encontrado', 'error');
        return;
    }
    
    // Fill form with product data
    document.getElementById('editProductId').value = product.id;
    document.getElementById('editProductName').value = product.name;
    document.getElementById('editProductDescription').value = product.description || '';
    document.getElementById('editProductCategory').value = product.category_id || '';
    document.getElementById('editProductUnit').value = product.unit_of_measure;
    document.getElementById('editProductCurrency').value = product.currency;
    document.getElementById('editProductCostPrice').value = product.cost_price;
    document.getElementById('editProductSellingPrice').value = product.selling_price;
    document.getElementById('editProductMinStock').value = product.min_stock_level;
    document.getElementById('editProductMaxStock').value = product.max_stock_level;
    document.getElementById('editProductWeight').value = product.weight || '';
    document.getElementById('editProductBarcode').value = product.barcode || '';
    document.getElementById('editProductExpiryDate').value = product.expiry_date || '';
    document.getElementById('editProductImageUrl').value = product.image_url || '';
    document.getElementById('editProductIsActive').checked = product.is_active;
    document.getElementById('editProductIsTrackable').checked = product.is_trackable;
    
    const modal = new bootstrap.Modal(document.getElementById('editProductModal'));
    modal.show();
}

async function handleAddProduct(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    // Show loading state
    submitBtn.innerHTML = '<div class="spinner"></div> Guardando...';
    submitBtn.disabled = true;
    
    try {
        const formData = new FormData(form);
        const productData = {
            name: formData.get('name'),
            description: formData.get('description') || null,
            category_id: formData.get('category_id') ? parseInt(formData.get('category_id')) : null,
            unit_of_measure: formData.get('unit_of_measure'),
            cost_price: parseFloat(formData.get('cost_price')) || 0,
            selling_price: parseFloat(formData.get('selling_price')),
            min_stock_level: parseInt(formData.get('min_stock_level')) || 0,
            max_stock_level: parseInt(formData.get('max_stock_level')) || 0,
            is_active: formData.get('is_active') === 'on',
            is_trackable: formData.get('is_trackable') === 'on',
            image_url: formData.get('image_url') || null,
            barcode: formData.get('barcode') || null,
            weight: formData.get('weight') ? parseFloat(formData.get('weight')) : null,
            expiry_date: formData.get('expiry_date') || null,
            currency: formData.get('currency')
        };
        
        const newProduct = await apiCall('/api/products/', {
            method: 'POST',
            body: JSON.stringify(productData)
        });
        
        // Close modal and reload data
        bootstrap.Modal.getInstance(document.getElementById('addProductModal')).hide();
        await loadProducts();
        await loadDashboardMetrics();
        
        showNotification('Producto agregado exitosamente', 'success');
        
    } catch (error) {
        console.error('Error creating product:', error);
        showNotification('Error al crear producto: ' + error.message, 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

async function handleEditProduct(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    const productId = document.getElementById('editProductId').value;
    
    // Show loading state
    submitBtn.innerHTML = '<div class="spinner"></div> Actualizando...';
    submitBtn.disabled = true;
    
    try {
        const formData = new FormData(form);
        const productData = {
            name: formData.get('name'),
            description: formData.get('description') || null,
            category_id: formData.get('category_id') ? parseInt(formData.get('category_id')) : null,
            unit_of_measure: formData.get('unit_of_measure'),
            cost_price: parseFloat(formData.get('cost_price')) || 0,
            selling_price: parseFloat(formData.get('selling_price')),
            min_stock_level: parseInt(formData.get('min_stock_level')) || 0,
            max_stock_level: parseInt(formData.get('max_stock_level')) || 0,
            is_active: formData.get('is_active') === 'on',
            is_trackable: formData.get('is_trackable') === 'on',
            image_url: formData.get('image_url') || null,
            barcode: formData.get('barcode') || null,
            weight: formData.get('weight') ? parseFloat(formData.get('weight')) : null,
            expiry_date: formData.get('expiry_date') || null,
            currency: formData.get('currency')
        };
        
        await apiCall(`/api/products/${productId}`, {
            method: 'PUT',
            body: JSON.stringify(productData)
        });
        
        // Close modal and reload data
        bootstrap.Modal.getInstance(document.getElementById('editProductModal')).hide();
        await loadProducts();
        
        showNotification('Producto actualizado exitosamente', 'success');
        
    } catch (error) {
        console.error('Error updating product:', error);
        showNotification('Error al actualizar producto: ' + error.message, 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

function updateProductTable() {
    const tbody = document.getElementById('products-table-body');
    if (!tbody) return;
    
    if (allProducts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">No hay productos registrados</td></tr>';
        return;
    }
    
    tbody.innerHTML = allProducts.map(product => `
        <tr>
            <td><strong>${product.product_code}</strong></td>
            <td>${product.name}</td>
            <td>${product.category_name || '-'}</td>
            <td>${formatCurrency(product.selling_price, product.currency)}</td>
            <td>
                <span class="badge ${product.current_stock <= 0 ? 'bg-danger' : 'bg-success'}">
                    ${product.current_stock}
                </span>
            </td>
            <td>
                <span class="status-badge ${product.is_active ? 'status-confirmed' : 'status-draft'}">
                    ${product.is_active ? 'Activo' : 'Inactivo'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="openEditProductModal(${product.id})">
                    <i class="fas fa-edit"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// ===== CUSTOMER FUNCTIONS =====
function openAddCustomerModal() {
    const modal = new bootstrap.Modal(document.getElementById('addCustomerModal'));
    // Reset form
    document.getElementById('addCustomerForm').reset();
    // Set default values
    document.getElementById('customerIsActive').checked = true;
    document.getElementById('customerCountry').value = 'Paraguay';
    document.getElementById('customerPaymentTerms').value = 30;
    modal.show();
}

async function handleAddCustomer(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    // Show loading state
    submitBtn.innerHTML = '<div class="spinner"></div> Guardando...';
    submitBtn.disabled = true;
    
    try {
        const formData = new FormData(form);
        const customerData = {
            company_name: formData.get('company_name'),
            contact_name: formData.get('contact_name') || null,
            email: formData.get('email') || null,
            phone: formData.get('phone') || null,
            address: formData.get('address') || null,
            city: formData.get('city') || null,
            state: formData.get('state') || null,
            postal_code: formData.get('postal_code') || null,
            country: formData.get('country'),
            tax_id: formData.get('tax_id') || null,
            credit_limit: parseFloat(formData.get('credit_limit')) || 0,
            payment_terms: parseInt(formData.get('payment_terms')) || 30,
            is_active: formData.get('is_active') === 'on',
            notes: formData.get('notes') || null
        };
        
        const newCustomer = await apiCall('/api/customers/', {
            method: 'POST',
            body: JSON.stringify(customerData)
        });
        
        // Close modal and reload data
        bootstrap.Modal.getInstance(document.getElementById('addCustomerModal')).hide();
        await loadCustomers();
        await loadDashboardMetrics();
        
        showNotification('Cliente agregado exitosamente', 'success');
        
    } catch (error) {
        console.error('Error creating customer:', error);
        showNotification('Error al crear cliente: ' + error.message, 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

function updateCustomerTable() {
    const tbody = document.getElementById('customers-table-body');
    if (!tbody) return;
    
    if (allCustomers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">No hay clientes registrados</td></tr>';
        return;
    }
    
    tbody.innerHTML = allCustomers.map(customer => `
        <tr>
            <td><strong>${customer.customer_code}</strong></td>
            <td>${customer.company_name}</td>
            <td>${customer.contact_name || '-'}</td>
            <td>${customer.email || '-'}</td>
            <td>${customer.phone || '-'}</td>
            <td>${customer.city || '-'}</td>
            <td>
                <span class="status-badge ${customer.is_active ? 'status-confirmed' : 'status-draft'}">
                    ${customer.is_active ? 'Activo' : 'Inactivo'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="openEditCustomerModal(${customer.id})">
                    <i class="fas fa-edit"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// ===== QUOTE FUNCTIONS =====
function openAddQuoteModal() {
    const modal = new bootstrap.Modal(document.getElementById('addQuoteModal'));
    // Reset form
    document.getElementById('addQuoteForm').reset();
    document.getElementById('quoteItemsBody').innerHTML = '';
    
    // Set default valid until date (30 days from now)
    const validUntil = new Date();
    validUntil.setDate(validUntil.getDate() + 30);
    document.getElementById('quoteValidUntil').value = validUntil.toISOString().split('T')[0];
    
    updateQuoteTotal();
    modal.show();
}

function addQuoteItem() {
    const tbody = document.getElementById('quoteItemsBody');
    const rowCount = tbody.children.length;
    
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>
            <select class="form-select form-select-sm" name="product_id_${rowCount}" onchange="updateItemPrice(this, ${rowCount})">
                <option value="">Seleccionar producto...</option>
                ${allProducts.map(product => 
                    `<option value="${product.id}" data-price="${product.selling_price}" data-currency="${product.currency}">
                        ${product.name} - ${formatCurrency(product.selling_price, product.currency)}
                    </option>`
                ).join('')}
            </select>
        </td>
        <td>
            <input type="number" class="form-control form-control-sm" name="quantity_${rowCount}" 
                   min="1" value="1" onchange="updateItemTotal(${rowCount})">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm" name="unit_price_${rowCount}" 
                   min="0" step="0.01" onchange="updateItemTotal(${rowCount})">
        </td>
        <td>
            <input type="number" class="form-control form-control-sm" name="discount_${rowCount}" 
                   min="0" max="100" value="0" onchange="updateItemTotal(${rowCount})">
        </td>
        <td>
            <span id="itemTotal_${rowCount}">0</span>
        </td>
        <td>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeQuoteItem(this)">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    
    tbody.appendChild(row);
}

function removeQuoteItem(button) {
    button.closest('tr').remove();
    updateQuoteTotal();
}

function updateItemPrice(select, rowIndex) {
    const option = select.options[select.selectedIndex];
    if (option.value) {
        const price = option.dataset.price;
        document.querySelector(`input[name="unit_price_${rowIndex}"]`).value = price;
        updateItemTotal(rowIndex);
    }
}

function updateItemTotal(rowIndex) {
    const quantity = parseFloat(document.querySelector(`input[name="quantity_${rowIndex}"]`).value) || 0;
    const unitPrice = parseFloat(document.querySelector(`input[name="unit_price_${rowIndex}"]`).value) || 0;
    const discount = parseFloat(document.querySelector(`input[name="discount_${rowIndex}"]`).value) || 0;
    
    const subtotal = quantity * unitPrice;
    const discountAmount = subtotal * (discount / 100);
    const total = subtotal - discountAmount;
    
    document.getElementById(`itemTotal_${rowIndex}`).textContent = formatNumber(total);
    updateQuoteTotal();
}

function updateQuoteTotal() {
    const tbody = document.getElementById('quoteItemsBody');
    let subtotal = 0;
    
    for (let i = 0; i < tbody.children.length; i++) {
        const itemTotalEl = document.getElementById(`itemTotal_${i}`);
        if (itemTotalEl) {
            subtotal += parseFloat(itemTotalEl.textContent.replace(/[^\d.-]/g, '')) || 0;
        }
    }
    
    const tax = subtotal * 0.10; // 10% IVA
    const total = subtotal + tax;
    
    document.getElementById('quoteSubtotal').textContent = formatNumber(subtotal);
    document.getElementById('quoteTax').textContent = formatNumber(tax);
    document.getElementById('quoteTotal').textContent = formatNumber(total);
}

async function handleAddQuote(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    // Show loading state
    submitBtn.innerHTML = '<div class="spinner"></div> Creando...';
    submitBtn.disabled = true;
    
    try {
        const formData = new FormData(form);
        const tbody = document.getElementById('quoteItemsBody');
        
        // Collect quote items
        const items = [];
        for (let i = 0; i < tbody.children.length; i++) {
            const productId = document.querySelector(`select[name="product_id_${i}"]`)?.value;
            const quantity = document.querySelector(`input[name="quantity_${i}"]`)?.value;
            const unitPrice = document.querySelector(`input[name="unit_price_${i}"]`)?.value;
            const discount = document.querySelector(`input[name="discount_${i}"]`)?.value;
            
            if (productId && quantity && unitPrice) {
                items.push({
                    product_id: parseInt(productId),
                    quantity: parseInt(quantity),
                    unit_price: parseFloat(unitPrice),
                    discount_percentage: parseFloat(discount) || 0
                });
            }
        }
        
        if (items.length === 0) {
            showNotification('Debe agregar al menos un producto a la cotización', 'warning');
            return;
        }
        
        const quoteData = {
            customer_id: parseInt(formData.get('customer_id')),
            currency: formData.get('currency'),
            valid_until: formData.get('valid_until'),
            notes: formData.get('notes') || null,
            items: items
        };
        
        const newQuote = await apiCall('/api/quotes/', {
            method: 'POST',
            body: JSON.stringify(quoteData)
        });
        
        // Close modal and reload data
        bootstrap.Modal.getInstance(document.getElementById('addQuoteModal')).hide();
        await loadQuotes();
        await loadDashboardMetrics();
        
        showNotification('Cotización creada exitosamente', 'success');
        
    } catch (error) {
        console.error('Error creating quote:', error);
        showNotification('Error al crear cotización: ' + error.message, 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

function updateQuoteTable(quotes) {
    const tbody = document.getElementById('quotes-table-body');
    if (!tbody) return;
    
    if (!quotes || quotes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">No hay cotizaciones registradas</td></tr>';
        return;
    }
    
    tbody.innerHTML = quotes.map(quote => `
        <tr>
            <td><strong>${quote.quote_number}</strong></td>
            <td>${quote.customer_name || 'Cliente'}</td>
            <td>${formatDate(quote.created_at)}</td>
            <td>${formatCurrency(quote.total_amount, quote.currency)}</td>
            <td>
                <span class="status-badge status-${quote.status.toLowerCase()}">
                    ${quote.status}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="viewQuote(${quote.id})">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// ===== UTILITY FUNCTIONS =====
function updateCategorySelects() {
    const selects = ['productCategory', 'editProductCategory'];
    
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            // Keep the first option (Seleccionar categoría...)
            const firstOption = select.firstElementChild;
            select.innerHTML = firstOption.outerHTML;
            
            allCategories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                select.appendChild(option);
            });
        }
    });
}

function updateCustomerSelects() {
    const selects = ['quoteCustomer'];
    
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            // Keep the first option
            const firstOption = select.firstElementChild;
            select.innerHTML = firstOption.outerHTML;
            
            allCustomers.forEach(customer => {
                const option = document.createElement('option');
                option.value = customer.id;
                option.textContent = customer.company_name;
                select.appendChild(option);
            });
        }
    });
}

function updateDashboardMetric(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function updateNavigationCount(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function formatCurrency(amount, currency = 'PYG') {
    const numAmount = parseFloat(amount) || 0;
    
    if (currency === 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(numAmount);
    } else {
        return new Intl.NumberFormat('es-PY', {
            style: 'currency',
            currency: 'PYG',
            minimumFractionDigits: 0
        }).format(numAmount);
    }
}

function formatNumber(amount) {
    return new Intl.NumberFormat('es-PY').format(parseFloat(amount) || 0);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('es-PY');
}

function showLoadingState() {
    // Could implement a global loading overlay here
}

function hideLoadingState() {
    // Could hide the global loading overlay here
}

function showNotification(message, type = 'info') {
    // Create or update a notification system
    console.log(`${type.toUpperCase()}: ${message}`);
    
    // For now, use simple alerts - could be enhanced with toast notifications
    if (type === 'error') {
        alert(`Error: ${message}`);
    } else if (type === 'success') {
        alert(`Éxito: ${message}`);
    } else if (type === 'warning') {
        alert(`Advertencia: ${message}`);
    } else {
        alert(message);
    }
}

// ===== USER MANAGEMENT FUNCTIONS =====

// Show/Hide User Modal
function showCreateUserModal() {
    const modal = document.getElementById('create-user-modal');
    if (modal) {
        modal.classList.remove('d-none');
        document.body.style.overflow = 'hidden';
    }
}

function hideCreateUserModal() {
    const modal = document.getElementById('create-user-modal');
    if (modal) {
        modal.classList.add('d-none');
        document.body.style.overflow = 'auto';
        // Reset form
        const form = document.getElementById('create-user-form');
        if (form) form.reset();
    }
}

// Update user limitations based on role
function updateUserLimitations() {
    const roleSelect = document.querySelector('[name="role"]');
    const maxCustomers = document.querySelector('[name="max_customers"]');
    const maxQuotes = document.querySelector('[name="max_quotes"]');
    const maxOrders = document.querySelector('[name="max_orders"]');
    const maxInvoices = document.querySelector('[name="max_invoices"]');
    
    // Permission checkboxes
    const canManageInventory = document.querySelector('[name="can_manage_inventory"]');
    const canViewReports = document.querySelector('[name="can_view_reports"]');
    const canManageTourismRegime = document.querySelector('[name="can_manage_tourism_regime"]');
    const canManageDeposits = document.querySelector('[name="can_manage_deposits"]');
    const canExportData = document.querySelector('[name="can_export_data"]');
    
    if (!roleSelect || !maxCustomers) return;
    
    const role = roleSelect.value;
    
    // Preset limitations based on role
    switch(role) {
        case 'admin':
            maxCustomers.value = 999;
            maxQuotes.value = 999;
            maxOrders.value = 999;
            maxInvoices.value = 999;
            // Admin gets all permissions
            canManageInventory.checked = true;
            canViewReports.checked = true;
            canManageTourismRegime.checked = true;
            canManageDeposits.checked = true;
            canExportData.checked = true;
            break;
            
        case 'manager':
            maxCustomers.value = 100;
            maxQuotes.value = 100;
            maxOrders.value = 80;
            maxInvoices.value = 50;
            // Manager gets most permissions
            canManageInventory.checked = true;
            canViewReports.checked = true;
            canManageTourismRegime.checked = true;
            canManageDeposits.checked = true;
            canExportData.checked = true;
            break;
            
        case 'accountant':
            maxCustomers.value = 50;
            maxQuotes.value = 30;
            maxOrders.value = 30;
            maxInvoices.value = 40;
            // Accountant gets financial permissions
            canManageInventory.checked = false;
            canViewReports.checked = true;
            canManageTourismRegime.checked = true; // For tax regime
            canManageDeposits.checked = true;
            canExportData.checked = true;
            break;
            
        case 'seller':
            maxCustomers.value = 20;
            maxQuotes.value = 30;
            maxOrders.value = 25;
            maxInvoices.value = 15;
            // Seller gets basic permissions
            canManageInventory.checked = false;
            canViewReports.checked = true;
            canManageTourismRegime.checked = false;
            canManageDeposits.checked = false;
            canExportData.checked = false;
            break;
            
        case 'viewer':
            maxCustomers.value = 0;
            maxQuotes.value = 0;
            maxOrders.value = 0;
            maxInvoices.value = 0;
            // Viewer gets minimal permissions
            canManageInventory.checked = false;
            canViewReports.checked = true;
            canManageTourismRegime.checked = false;
            canManageDeposits.checked = false;
            canExportData.checked = false;
            break;
            
        default:
            // Default seller settings
            maxCustomers.value = 10;
            maxQuotes.value = 20;
            maxOrders.value = 15;
            maxInvoices.value = 10;
            canManageInventory.checked = false;
            canViewReports.checked = true;
            canManageTourismRegime.checked = false;
            canManageDeposits.checked = false;
            canExportData.checked = false;
    }
}

// Load users data
async function loadUsersData() {
    try {
        const response = await apiCall('/users/');
        if (response) {
            displayUsersTable(response);
            updateUserMetrics(response);
        }
    } catch (error) {
        console.error('Error loading users:', error);
        showNotification('Error al cargar usuarios: ' + error.message, 'error');
    }
}

// Display users in table
function displayUsersTable(users) {
    const tbody = document.getElementById('users-table-body');
    if (!tbody) return;
    
    if (!users || users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center">
                    <i class="fas fa-users"></i> No hay usuarios registrados
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <div class="user-avatar" style="width: 32px; height: 32px; font-size: 0.8rem;">
                        ${user.full_name.charAt(0).toUpperCase()}
                    </div>
                    <strong>${user.username}</strong>
                </div>
            </td>
            <td>${user.full_name}</td>
            <td>${user.email}</td>
            <td>
                <span class="badge role-${user.role}">${getRoleDisplayName(user.role)}</span>
            </td>
            <td>${user.department || '-'}</td>
            <td>
                <span class="badge ${user.is_active ? 'positive' : 'negative'}">
                    ${user.is_active ? 'Activo' : 'Inactivo'}
                </span>
            </td>
            <td>
                <small>
                    C: ${user.max_customers} | Q: ${user.max_quotes}<br>
                    O: ${user.max_orders} | F: ${user.max_invoices}
                </small>
            </td>
            <td>
                <div style="display: flex; gap: 0.25rem;">
                    <button class="btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;" 
                            onclick="editUser(${user.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-logout" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;" 
                            onclick="toggleUserStatus(${user.id}, ${user.is_active})">
                        <i class="fas fa-${user.is_active ? 'ban' : 'check'}"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Get role display name in Spanish
function getRoleDisplayName(role) {
    const roleNames = {
        'admin': 'Administrador',
        'manager': 'Gerente', 
        'seller': 'Vendedor',
        'viewer': 'Visualizador',
        'accountant': 'Contador'
    };
    return roleNames[role] || role;
}

// Update user metrics
function updateUserMetrics(users) {
    const totalUsers = users ? users.length : 0;
    const activeUsers = users ? users.filter(user => user.is_active).length : 0;
    
    // Update metric cards
    const totalUsersMetric = document.getElementById('total-users-metric');
    const activeUsersMetric = document.getElementById('active-users-metric');
    
    if (totalUsersMetric) totalUsersMetric.textContent = totalUsers;
    if (activeUsersMetric) activeUsersMetric.textContent = activeUsers;
}

// Create new user
async function createUser(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    // Convert form data to object
    const userData = {
        username: formData.get('username'),
        full_name: formData.get('full_name'),
        email: formData.get('email'),
        password: formData.get('password'),
        role: formData.get('role'),
        department: formData.get('department'),
        max_customers: parseInt(formData.get('max_customers')) || 10,
        max_quotes: parseInt(formData.get('max_quotes')) || 20,
        max_orders: parseInt(formData.get('max_orders')) || 15,
        max_invoices: parseInt(formData.get('max_invoices')) || 10,
        can_manage_inventory: formData.has('can_manage_inventory'),
        can_view_reports: formData.has('can_view_reports'),
        can_manage_tourism_regime: formData.has('can_manage_tourism_regime'),
        can_manage_deposits: formData.has('can_manage_deposits'),
        can_export_data: formData.has('can_export_data'),
        notes: formData.get('notes')
    };
    
    try {
        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.innerHTML = '<div class="loading-spinner"></div> Creando...';
        
        const response = await apiCall('/users/', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        
        if (response) {
            showNotification('Usuario creado exitosamente', 'success');
            hideCreateUserModal();
            loadUsersData(); // Refresh users table
        }
    } catch (error) {
        console.error('Error creating user:', error);
        showNotification('Error al crear usuario: ' + error.message, 'error');
    } finally {
        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fas fa-save"></i> Crear Usuario';
    }
}

// Edit user (placeholder)
function editUser(userId) {
    showNotification('Funcionalidad de edición de usuario estará disponible pronto', 'info');
}

// Toggle user status
async function toggleUserStatus(userId, currentStatus) {
    const action = currentStatus ? 'desactivar' : 'activar';
    if (!confirm(`¿Está seguro que desea ${action} este usuario?`)) {
        return;
    }
    
    try {
        const response = await apiCall(`/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify({ is_active: !currentStatus })
        });
        
        if (response) {
            showNotification(`Usuario ${action}do exitosamente`, 'success');
            loadUsersData(); // Refresh users table
        }
    } catch (error) {
        console.error('Error updating user status:', error);
        showNotification('Error al actualizar usuario: ' + error.message, 'error');
    }
}

// Make functions globally available
window.openAddProductModal = openAddProductModal;
window.openEditProductModal = openEditProductModal;
window.openAddCustomerModal = openAddCustomerModal;
window.openAddQuoteModal = openAddQuoteModal;
window.addQuoteItem = addQuoteItem;
window.removeQuoteItem = removeQuoteItem;
window.updateItemPrice = updateItemPrice;
window.updateItemTotal = updateItemTotal;

// User management functions
window.showCreateUserModal = showCreateUserModal;
window.hideCreateUserModal = hideCreateUserModal;
window.updateUserLimitations = updateUserLimitations;
window.loadUsersData = loadUsersData;
window.createUser = createUser;
window.editUser = editUser;
window.toggleUserStatus = toggleUserStatus;