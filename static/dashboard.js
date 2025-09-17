// Dashboard JavaScript
const API_BASE = '';
let authToken = localStorage.getItem('authToken');
let charts = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    checkAuthAndInit();
    
    // Setup navigation
    document.querySelectorAll('[data-section]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.dataset.section;
            showSection(section);
            updateActiveNav(this);
        });
    });
});

async function checkAuthAndInit() {
    if (!authToken) {
        window.location.href = '/';
        return;
    }
    
    try {
        // Verificar token y cargar datos
        await loadOverviewData();
        await loadSalesTrend();
    } catch (error) {
        console.error('Error inicializando dashboard:', error);
        if (error.message === 'Authentication failed') {
            localStorage.removeItem('authToken');
            window.location.href = '/';
        }
    }
}

async function apiCall(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.status === 401 || response.status === 403) {
            throw new Error('Authentication failed');
        }
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

function showSection(sectionName) {
    // Ocultar todas las secciones
    document.querySelectorAll('.dashboard-section').forEach(section => {
        section.classList.add('d-none');
    });
    
    // Mostrar la sección seleccionada
    const targetSection = document.getElementById(`${sectionName}-section`);
    if (targetSection) {
        targetSection.classList.remove('d-none');
    }
    
    // Cargar datos específicos de la sección
    loadSectionData(sectionName);
}

function updateActiveNav(activeLink) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    activeLink.classList.add('active');
}

async function loadOverviewData() {
    try {
        const data = await apiCall('/api/dashboard/metrics/overview');
        renderMetricsCards(data);
        renderKPIs(data);
    } catch (error) {
        console.error('Error loading overview:', error);
        showErrorMessage('Error cargando métricas generales');
    }
}

function renderMetricsCards(data) {
    const metricsRow = document.getElementById('metrics-row');
    
    const metrics = [
        {
            icon: 'fas fa-users',
            value: data.basic_stats.total_customers,
            label: 'Clientes Totales',
            color: '#667eea'
        },
        {
            icon: 'fas fa-file-alt',
            value: data.basic_stats.total_quotes,
            label: 'Cotizaciones',
            color: '#764ba2'
        },
        {
            icon: 'fas fa-shopping-cart',
            value: data.basic_stats.total_orders,
            label: 'Órdenes',
            color: '#f093fb'
        },
        {
            icon: 'fas fa-file-invoice-dollar',
            value: data.basic_stats.total_invoices,
            label: 'Facturas',
            color: '#4facfe'
        },
        {
            icon: 'fas fa-dollar-sign',
            value: formatCurrency(data.financial_stats.total_revenue),
            label: 'Ingresos Totales',
            color: '#43e97b',
            isLarge: true
        },
        {
            icon: 'fas fa-chart-line',
            value: formatCurrency(data.financial_stats.monthly_revenue),
            label: 'Ingresos del Mes',
            color: '#38f9d7',
            isLarge: true
        }
    ];
    
    metricsRow.innerHTML = metrics.map(metric => `
        <div class="col-md-${metric.isLarge ? '6' : '3'} col-sm-6 mb-3">
            <div class="metric-card text-center">
                <div style="color: ${metric.color}">
                    <i class="${metric.icon} fa-2x mb-3"></i>
                </div>
                <div class="metric-value" style="color: ${metric.color}">${metric.value}</div>
                <div class="metric-label">${metric.label}</div>
            </div>
        </div>
    `).join('');
}

function renderKPIs(data) {
    const kpisContainer = document.getElementById('kpis-container');
    
    const kpis = [
        {
            label: 'Ratio Cotización → Orden',
            value: `${data.conversion_metrics.quote_to_order_ratio}%`,
            status: data.conversion_metrics.quote_to_order_ratio >= 50 ? 'excellent' : 
                   data.conversion_metrics.quote_to_order_ratio >= 30 ? 'good' : 'warning'
        },
        {
            label: 'Ratio Orden → Factura',
            value: `${data.conversion_metrics.order_to_invoice_ratio}%`,
            status: data.conversion_metrics.order_to_invoice_ratio >= 80 ? 'excellent' : 
                   data.conversion_metrics.order_to_invoice_ratio >= 60 ? 'good' : 'warning'
        },
        {
            label: 'Ticket Promedio Orden',
            value: formatCurrency(data.conversion_metrics.average_order_value),
            status: 'good'
        },
        {
            label: 'Ticket Promedio Factura',
            value: formatCurrency(data.conversion_metrics.average_invoice_value),
            status: 'good'
        }
    ];
    
    kpisContainer.innerHTML = kpis.map(kpi => `
        <div class="d-flex justify-content-between align-items-center mb-3 p-2 border rounded">
            <small class="text-muted">${kpi.label}</small>
            <span class="status-badge status-${kpi.status}">${kpi.value}</span>
        </div>
    `).join('');
}

async function loadSalesTrend() {
    try {
        const data = await apiCall('/api/dashboard/metrics/sales-trend?days=30');
        renderSalesTrendChart(data);
    } catch (error) {
        console.error('Error loading sales trend:', error);
        document.getElementById('salesTrendChart').parentElement.innerHTML = 
            '<p class="text-danger">Error cargando tendencia de ventas</p>';
    }
}

function renderSalesTrendChart(data) {
    const ctx = document.getElementById('salesTrendChart').getContext('2d');
    
    if (charts.salesTrend) {
        charts.salesTrend.destroy();
    }
    
    charts.salesTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels.map(date => new Date(date).toLocaleDateString('es-MX', {
                month: 'short', day: 'numeric'
            })),
            datasets: [{
                label: 'Ingresos Diarios',
                data: data.revenue_series,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            },
            elements: {
                point: {
                    radius: 4,
                    hoverRadius: 6
                }
            }
        }
    });
}

async function loadSectionData(sectionName) {
    switch(sectionName) {
        case 'overview':
            // Ya cargado
            break;
            
        case 'products':
            await loadTopProducts();
            break;
            
        case 'customers':
            await loadCustomerAnalysis();
            break;
            
        case 'inventory':
            await loadInventoryStatus();
            break;
            
        case 'sales':
            await loadSalesAnalysis();
            break;
            
        case 'financial':
            await loadFinancialDetails();
            break;
    }
}

async function loadTopProducts() {
    const container = document.getElementById('top-products-container');
    
    try {
        const data = await apiCall('/api/dashboard/metrics/top-products');
        
        if (data.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No hay datos de productos vendidos</p>';
            return;
        }
        
        container.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Producto</th>
                            <th>Código</th>
                            <th>Cantidad Vendida</th>
                            <th>Ingresos Totales</th>
                            <th>Número de Órdenes</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map((product, index) => `
                            <tr>
                                <td>
                                    <div class="d-flex align-items-center">
                                        <span class="badge bg-primary me-2">#${index + 1}</span>
                                        <strong>${product.name}</strong>
                                    </div>
                                </td>
                                <td><code>${product.product_code}</code></td>
                                <td><strong>${product.total_quantity}</strong></td>
                                <td><strong>${formatCurrency(product.total_revenue)}</strong></td>
                                <td>${product.order_count}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading top products:', error);
        container.innerHTML = '<p class="text-danger">Error cargando productos más vendidos</p>';
    }
}

async function loadInventoryStatus() {
    const container = document.getElementById('inventory-summary-container');
    
    try {
        const data = await apiCall('/api/dashboard/metrics/inventory-status');
        
        container.innerHTML = `
            <div class="row mb-4">
                <div class="col-md-3 text-center">
                    <h4 class="text-primary">${data.inventory_summary.total_products}</h4>
                    <small class="text-muted">Productos Totales</small>
                </div>
                <div class="col-md-3 text-center">
                    <h4 class="text-success">${data.inventory_summary.trackable_products}</h4>
                    <small class="text-muted">Productos con Inventario</small>
                </div>
                <div class="col-md-3 text-center">
                    <h4 class="text-warning">${data.inventory_summary.low_stock_count}</h4>
                    <small class="text-muted">Stock Bajo</small>
                </div>
                <div class="col-md-3 text-center">
                    <h4 class="text-danger">${data.inventory_summary.out_of_stock_count}</h4>
                    <small class="text-muted">Sin Stock</small>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <h6>Productos con Stock Bajo</h6>
                    ${data.low_stock_products.length === 0 ? 
                        '<p class="text-muted">No hay productos con stock bajo</p>' :
                        `<div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Producto</th>
                                        <th>Stock Actual</th>
                                        <th>Precio</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.low_stock_products.map(product => `
                                        <tr>
                                            <td>${product.name}</td>
                                            <td><span class="badge bg-warning">${product.current_stock}</span></td>
                                            <td>${formatCurrency(product.price)}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>`
                    }
                </div>
                <div class="col-md-6">
                    <h6>Productos Más Movidos</h6>
                    ${data.most_moved_products.length === 0 ? 
                        '<p class="text-muted">No hay datos de movimiento</p>' :
                        `<div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Producto</th>
                                        <th>Stock Actual</th>
                                        <th>Total Vendido</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.most_moved_products.map(product => `
                                        <tr>
                                            <td>${product.name}</td>
                                            <td>${product.current_stock || 'N/A'}</td>
                                            <td><strong>${product.total_moved}</strong></td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>`
                    }
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading inventory:', error);
        container.innerHTML = '<p class="text-danger">Error cargando estado del inventario</p>';
    }
}

async function loadCustomerAnalysis() {
    const topCustomersContainer = document.getElementById('top-customers-container');
    const pendingCustomersContainer = document.getElementById('pending-customers-container');
    
    try {
        const data = await apiCall('/api/dashboard/metrics/customer-analysis');
        
        // Top customers by value
        if (data.top_customers_by_value.length === 0) {
            topCustomersContainer.innerHTML = '<p class="text-muted text-center">No hay datos de clientes</p>';
        } else {
            topCustomersContainer.innerHTML = `
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Cliente</th>
                                <th>Órdenes</th>
                                <th>Valor Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.top_customers_by_value.map((customer, index) => `
                                <tr>
                                    <td>
                                        <div class="d-flex align-items-center">
                                            <span class="badge bg-success me-2">#${index + 1}</span>
                                            <div>
                                                <strong>${customer.company_name}</strong>
                                                <br><small class="text-muted">${customer.email}</small>
                                            </div>
                                        </div>
                                    </td>
                                    <td><strong>${customer.order_count}</strong></td>
                                    <td><strong>${formatCurrency(customer.total_value)}</strong></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }
        
        // Customers with pending payments
        if (data.customers_with_pending.length === 0) {
            pendingCustomersContainer.innerHTML = '<p class="text-muted text-center">No hay clientes con saldos pendientes</p>';
        } else {
            pendingCustomersContainer.innerHTML = `
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Cliente</th>
                                <th>Facturas</th>
                                <th>Saldo Pendiente</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.customers_with_pending.map(customer => `
                                <tr>
                                    <td>
                                        <div>
                                            <strong>${customer.company_name}</strong>
                                            <br><small class="text-muted">${customer.email}</small>
                                        </div>
                                    </td>
                                    <td><span class="badge bg-warning">${customer.pending_invoices}</span></td>
                                    <td><strong class="text-danger">${formatCurrency(customer.pending_balance)}</strong></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error loading customer analysis:', error);
        topCustomersContainer.innerHTML = '<p class="text-danger">Error cargando análisis de clientes</p>';
        pendingCustomersContainer.innerHTML = '<p class="text-danger">Error cargando saldos pendientes</p>';
    }
}

async function loadSalesAnalysis() {
    // Placeholder for sales analysis charts
    console.log('Loading sales analysis...');
}

async function loadFinancialDetails() {
    const container = document.getElementById('financial-details-container');
    
    try {
        const data = await apiCall('/api/dashboard/metrics/overview');
        
        container.innerHTML = `
            <div class="row">
                <div class="col-md-3">
                    <div class="text-center p-3 border rounded">
                        <h4 class="text-success">${formatCurrency(data.financial_stats.total_revenue)}</h4>
                        <small class="text-muted">Ingresos Totales</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center p-3 border rounded">
                        <h4 class="text-info">${formatCurrency(data.financial_stats.paid_amount)}</h4>
                        <small class="text-muted">Pagos Recibidos</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center p-3 border rounded">
                        <h4 class="text-warning">${formatCurrency(data.financial_stats.pending_amount)}</h4>
                        <small class="text-muted">Saldos Pendientes</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center p-3 border rounded">
                        <h4 class="text-danger">${formatCurrency(data.financial_stats.overdue_amount)}</h4>
                        <small class="text-muted">Facturas Vencidas</small>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-6">
                    <h6>Métricas del Mes Actual</h6>
                    <ul class="list-group">
                        <li class="list-group-item d-flex justify-content-between">
                            <span>Ingresos del Mes</span>
                            <strong>${formatCurrency(data.financial_stats.monthly_revenue)}</strong>
                        </li>
                        <li class="list-group-item d-flex justify-content-between">
                            <span>Órdenes del Mes</span>
                            <strong>${data.financial_stats.monthly_orders}</strong>
                        </li>
                    </ul>
                </div>
                <div class="col-md-6">
                    <h6>Ratios de Conversión</h6>
                    <ul class="list-group">
                        <li class="list-group-item d-flex justify-content-between">
                            <span>Cotización → Orden</span>
                            <strong>${data.conversion_metrics.quote_to_order_ratio}%</strong>
                        </li>
                        <li class="list-group-item d-flex justify-content-between">
                            <span>Orden → Factura</span>
                            <strong>${data.conversion_metrics.order_to_invoice_ratio}%</strong>
                        </li>
                    </ul>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading financial details:', error);
        container.innerHTML = '<p class="text-danger">Error cargando detalles financieros</p>';
    }
}

function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '$0.00';
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN',
        minimumFractionDigits: 2
    }).format(amount);
}

function showErrorMessage(message) {
    console.error(message);
    // Could show a toast notification here
}

async function refreshDashboard() {
    const button = event.target;
    const originalHtml = button.innerHTML;
    
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Actualizando...';
    button.disabled = true;
    
    try {
        await loadOverviewData();
        await loadSalesTrend();
        
        // Reload current section data
        const activeSection = document.querySelector('.nav-link.active')?.dataset.section;
        if (activeSection && activeSection !== 'overview') {
            await loadSectionData(activeSection);
        }
        
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
        showErrorMessage('Error actualizando el dashboard');
    } finally {
        button.innerHTML = originalHtml;
        button.disabled = false;
    }
}