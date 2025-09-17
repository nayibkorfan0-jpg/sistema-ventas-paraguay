from datetime import datetime, timedelta
from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_
from decimal import Decimal

from app.core.database import get_database
from app.models.customer import Customer
from app.models.sales import Quote, SalesOrder
from app.models.invoice import Invoice, Payment
from app.models.product import Product
from app.core.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Obtener estadísticas consolidadas para el dashboard principal"""
    
    from datetime import datetime, timedelta
    from app.models.deposit import Deposit
    
    # Estadísticas básicas
    total_customers = db.query(Customer).count()
    active_customers = db.query(Customer).filter(Customer.is_active == True).count()
    total_quotes = db.query(Quote).count()
    total_invoices = db.query(Invoice).count()
    total_products = db.query(Product).count()
    
    # Estadísticas del mes actual
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1)
    
    monthly_quotes = db.query(Quote).filter(
        Quote.created_at >= start_of_month
    ).count()
    
    monthly_invoices = db.query(Invoice).filter(
        Invoice.invoice_date >= start_of_month.date()
    ).count()
    
    # Ventas del mes por moneda
    monthly_sales_pyg = db.query(func.sum(Invoice.total_amount)).filter(
        and_(
            Invoice.invoice_date >= start_of_month.date(),
            Invoice.currency == 'PYG'
        )
    ).scalar() or Decimal('0')
    
    monthly_sales_usd = db.query(func.sum(Invoice.total_amount)).filter(
        and_(
            Invoice.invoice_date >= start_of_month.date(),
            Invoice.currency == 'USD'
        )
    ).scalar() or Decimal('0')
    
    # Facturas pendientes
    pending_invoices_count = db.query(Invoice).filter(
        Invoice.status.in_(['PENDING', 'SENT'])
    ).count()
    
    pending_amount_pyg = db.query(func.sum(Invoice.balance_due)).filter(
        and_(
            Invoice.status.in_(['PENDING', 'SENT']),
            Invoice.currency == 'PYG'
        )
    ).scalar() or Decimal('0')
    
    pending_amount_usd = db.query(func.sum(Invoice.balance_due)).filter(
        and_(
            Invoice.status.in_(['PENDING', 'SENT']),
            Invoice.currency == 'USD'
        )
    ).scalar() or Decimal('0')
    
    # Depósitos activos
    active_deposits = db.query(Deposit).filter(
        Deposit.status == 'ACTIVO'
    ).count()
    
    deposits_total = db.query(func.sum(Deposit.available_amount)).filter(
        Deposit.status == 'ACTIVO'
    ).scalar() or Decimal('0')
    
    # Régimen de turismo - clientes próximos a vencer (próximos 30 días)
    expiry_threshold = (datetime.now() + timedelta(days=30)).date()
    tourism_regime_expiring = db.query(Customer).filter(
        and_(
            Customer.tourism_regime == True,
            Customer.tourism_regime_expiry.isnot(None),
            Customer.tourism_regime_expiry <= expiry_threshold,
            Customer.is_active == True
        )
    ).count()
    
    # Stock bajo (menos de 10 unidades)
    low_stock_count = db.query(Product).filter(
        and_(
            Product.is_trackable == True,
            Product.current_stock < 10,
            Product.is_active == True
        )
    ).count()
    
    # Productos sin stock
    out_of_stock_count = db.query(Product).filter(
        and_(
            Product.is_trackable == True,
            Product.current_stock <= 0,
            Product.is_active == True
        )
    ).count()
    
    return {
        "basic_stats": {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "total_quotes": total_quotes,
            "total_invoices": total_invoices,
            "total_products": total_products
        },
        "monthly_stats": {
            "quotes": monthly_quotes,
            "invoices": monthly_invoices,
            "sales_pyg": float(monthly_sales_pyg),
            "sales_usd": float(monthly_sales_usd)
        },
        "pending_invoices": {
            "count": pending_invoices_count,
            "amount_pyg": float(pending_amount_pyg),
            "amount_usd": float(pending_amount_usd)
        },
        "deposits": {
            "active_count": active_deposits,
            "total_amount": float(deposits_total)
        },
        "alerts": {
            "tourism_regime_expiring": tourism_regime_expiring,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count
        }
    }

@router.get("/metrics/overview")
async def get_overview_metrics(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Obtener métricas generales del dashboard"""
    
    # Métricas básicas
    total_customers = db.query(Customer).count()
    total_quotes = db.query(Quote).count()
    total_orders = db.query(SalesOrder).count()
    total_products = db.query(Product).count()
    total_invoices = db.query(Invoice).count()
    
    # Métricas financieras
    total_revenue = db.query(func.sum(Invoice.total_amount)).scalar() or Decimal('0')
    pending_amount = db.query(func.sum(Invoice.balance_due)).filter(
        Invoice.status.in_(['PENDING', 'SENT'])
    ).scalar() or Decimal('0')
    overdue_amount = db.query(func.sum(Invoice.balance_due)).filter(
        Invoice.status == 'OVERDUE'
    ).scalar() or Decimal('0')
    paid_amount = db.query(func.sum(Payment.amount)).scalar() or Decimal('0')
    
    # Métricas del mes actual
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_revenue = db.query(func.sum(Invoice.total_amount)).filter(
        and_(
            extract('month', Invoice.invoice_date) == current_month,
            extract('year', Invoice.invoice_date) == current_year
        )
    ).scalar() or Decimal('0')
    
    monthly_orders = db.query(SalesOrder).filter(
        and_(
            extract('month', SalesOrder.created_at) == current_month,
            extract('year', SalesOrder.created_at) == current_year
        )
    ).count()
    
    # Ratios de conversión
    quote_to_order_ratio = 0
    if total_quotes > 0:
        orders_from_quotes = db.query(SalesOrder).filter(SalesOrder.quote_id.isnot(None)).count()
        quote_to_order_ratio = round((orders_from_quotes / total_quotes) * 100, 2)
    
    order_to_invoice_ratio = 0
    if total_orders > 0:
        invoiced_orders = db.query(Invoice).filter(Invoice.sales_order_id.isnot(None)).count()
        order_to_invoice_ratio = round((invoiced_orders / total_orders) * 100, 2)
    
    # Ticket promedio
    average_order_value = Decimal('0')
    if total_orders > 0:
        avg_value = db.query(func.avg(SalesOrder.total_amount)).scalar()
        average_order_value = avg_value or Decimal('0')
    
    average_invoice_value = Decimal('0')
    if total_invoices > 0:
        avg_value = db.query(func.avg(Invoice.total_amount)).scalar()
        average_invoice_value = avg_value or Decimal('0')
    
    return {
        "basic_stats": {
            "total_customers": total_customers,
            "total_quotes": total_quotes,
            "total_orders": total_orders,
            "total_products": total_products,
            "total_invoices": total_invoices
        },
        "financial_stats": {
            "total_revenue": float(total_revenue),
            "pending_amount": float(pending_amount),
            "overdue_amount": float(overdue_amount),
            "paid_amount": float(paid_amount),
            "monthly_revenue": float(monthly_revenue),
            "monthly_orders": monthly_orders
        },
        "conversion_metrics": {
            "quote_to_order_ratio": quote_to_order_ratio,
            "order_to_invoice_ratio": order_to_invoice_ratio,
            "average_order_value": float(average_order_value),
            "average_invoice_value": float(average_invoice_value)
        }
    }

@router.get("/metrics/sales-trend")
async def get_sales_trend(
    days: int = 30,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Obtener tendencia de ventas por día"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Generar lista de fechas
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    
    # Obtener datos de ventas agrupados por día
    sales_data = db.query(
        func.date(Invoice.invoice_date).label('date'),
        func.sum(Invoice.total_amount).label('total'),
        func.count(Invoice.id).label('count')
    ).filter(
        Invoice.invoice_date >= start_date,
        Invoice.invoice_date <= end_date
    ).group_by(
        func.date(Invoice.invoice_date)
    ).all()
    
    # Crear diccionario para lookup rápido
    sales_dict = {str(row.date): {"total": float(row.total), "count": row.count} for row in sales_data}
    
    # Generar series de datos completando días faltantes
    revenue_series = []
    count_series = []
    labels = []
    
    for date_str in date_range:
        labels.append(date_str)
        if date_str in sales_dict:
            revenue_series.append(sales_dict[date_str]["total"])
            count_series.append(sales_dict[date_str]["count"])
        else:
            revenue_series.append(0)
            count_series.append(0)
    
    return {
        "labels": labels,
        "revenue_series": revenue_series,
        "count_series": count_series,
        "period_days": days
    }

@router.get("/metrics/top-products")
async def get_top_products(
    limit: int = 10,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """Obtener productos más vendidos"""
    
    # Obtener productos más vendidos de órdenes de venta
    from app.models.sales import SalesOrderLine
    
    top_products = db.query(
        Product.id,
        Product.name,
        Product.product_code,
        func.sum(SalesOrderLine.quantity).label('total_quantity'),
        func.sum(SalesOrderLine.line_total).label('total_revenue'),
        func.count(SalesOrderLine.id).label('order_count')
    ).join(
        SalesOrderLine, Product.id == SalesOrderLine.product_id
    ).join(
        SalesOrder, SalesOrderLine.order_id == SalesOrder.id
    ).filter(
        SalesOrder.status.in_(['CONFIRMED', 'SHIPPED', 'DELIVERED'])
    ).group_by(
        Product.id, Product.name, Product.product_code
    ).order_by(
        func.sum(SalesOrderLine.line_total).desc()
    ).limit(limit).all()
    
    return [
        {
            "product_id": product.id,
            "name": product.name,
            "code": product.product_code,
            "total_quantity": float(product.total_quantity or 0),
            "total_revenue": float(product.total_revenue or 0),
            "order_count": product.order_count
        }
        for product in top_products
    ]

@router.get("/metrics/customer-analysis")
async def get_customer_analysis(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Análisis de clientes por valor"""
    
    # Clientes con más órdenes
    top_customers_by_orders = db.query(
        Customer.id,
        Customer.company_name,
        Customer.email,
        func.count(SalesOrder.id).label('order_count'),
        func.sum(SalesOrder.total_amount).label('total_value')
    ).join(
        SalesOrder, Customer.id == SalesOrder.customer_id
    ).group_by(
        Customer.id, Customer.company_name, Customer.email
    ).order_by(
        func.sum(SalesOrder.total_amount).desc()
    ).limit(10).all()
    
    # Clientes con más facturas pendientes
    customers_with_pending = db.query(
        Customer.id,
        Customer.company_name,
        Customer.email,
        func.sum(Invoice.balance_due).label('pending_balance'),
        func.count(Invoice.id).label('pending_invoices')
    ).join(
        Invoice, Customer.id == Invoice.customer_id
    ).filter(
        Invoice.status.in_(['PENDING', 'SENT', 'OVERDUE']),
        Invoice.balance_due > 0
    ).group_by(
        Customer.id, Customer.company_name, Customer.email
    ).order_by(
        func.sum(Invoice.balance_due).desc()
    ).limit(10).all()
    
    return {
        "top_customers_by_value": [
            {
                "customer_id": customer.id,
                "company_name": customer.company_name,
                "email": customer.email,
                "order_count": customer.order_count,
                "total_value": float(customer.total_value or 0)
            }
            for customer in top_customers_by_orders
        ],
        "customers_with_pending": [
            {
                "customer_id": customer.id,
                "company_name": customer.company_name,
                "email": customer.email,
                "pending_balance": float(customer.pending_balance or 0),
                "pending_invoices": customer.pending_invoices
            }
            for customer in customers_with_pending
        ]
    }

@router.get("/metrics/inventory-status")
async def get_inventory_status(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Estado del inventario y productos con stock bajo"""
    
    # Productos con stock bajo (menos de 10 unidades para trackeable)
    low_stock_products = db.query(Product).filter(
        and_(
            Product.is_trackable == True,
            Product.current_stock < 10
        )
    ).order_by(Product.current_stock.asc()).limit(20).all()
    
    # Productos sin stock
    out_of_stock = db.query(Product).filter(
        and_(
            Product.is_trackable == True,
            Product.current_stock <= 0
        )
    ).count()
    
    # Valor total del inventario
    inventory_value = db.query(
        func.sum(Product.current_stock * Product.selling_price)
    ).filter(
        Product.is_trackable == True
    ).scalar() or Decimal('0')
    
    # Productos más movidos (necesitaríamos una tabla de movimientos de inventario)
    # Por ahora usar datos de órdenes como proxy
    from app.models.sales import SalesOrderLine
    
    most_moved_products = db.query(
        Product.id,
        Product.name,
        Product.product_code,
        Product.current_stock,
        func.sum(SalesOrderLine.quantity).label('total_moved')
    ).join(
        SalesOrderLine, Product.id == SalesOrderLine.product_id
    ).filter(
        Product.is_trackable == True
    ).group_by(
        Product.id, Product.name, Product.product_code, Product.current_stock
    ).order_by(
        func.sum(SalesOrderLine.quantity).desc()
    ).limit(10).all()
    
    return {
        "inventory_summary": {
            "total_products": db.query(Product).count(),
            "trackable_products": db.query(Product).filter(Product.is_trackable == True).count(),
            "out_of_stock_count": out_of_stock,
            "low_stock_count": len(low_stock_products),
            "total_inventory_value": float(inventory_value)
        },
        "low_stock_products": [
            {
                "id": product.id,
                "name": product.name,
                "code": product.product_code,
                "current_stock": product.current_stock,
                "price": float(getattr(product, 'selling_price', 0) or 0)
            }
            for product in low_stock_products
        ],
        "most_moved_products": [
            {
                "id": product.id,
                "name": product.name,
                "code": product.product_code,
                "current_stock": product.current_stock,
                "total_moved": float(product.total_moved or 0)
            }
            for product in most_moved_products
        ]
    }