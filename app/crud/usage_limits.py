"""
CRUD operations for usage limits enforcement
Sistema de límites de uso para Paraguay ERP/CRM
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import Dict

from app.models.customer import Customer
from app.models.sales import Quote, SalesOrder
from app.models.invoice import Invoice


def get_user_usage(db: Session, user_id: int, limit_type: str) -> int:
    """
    Obtener el uso actual del usuario según el tipo de límite
    Para quotes, orders, invoices se cuenta por mes actual
    Para customers se cuenta total acumulado
    """
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    if limit_type == "customers":
        # Customers: Total acumulado
        count = db.query(Customer).filter(
            Customer.created_by_id == user_id
        ).count()
        
    elif limit_type == "quotes":
        # Quotes: Este mes
        count = db.query(Quote).filter(
            Quote.created_by_id == user_id,
            extract('month', Quote.created_at) == current_month,
            extract('year', Quote.created_at) == current_year
        ).count()
        
    elif limit_type == "orders":
        # Orders: Este mes
        count = db.query(SalesOrder).filter(
            SalesOrder.created_by_id == user_id,
            extract('month', SalesOrder.created_at) == current_month,
            extract('year', SalesOrder.created_at) == current_year
        ).count()
        
    elif limit_type == "invoices":
        # Invoices: Este mes
        count = db.query(Invoice).filter(
            Invoice.created_by_id == user_id,
            extract('month', Invoice.created_at) == current_month,
            extract('year', Invoice.created_at) == current_year
        ).count()
        
    else:
        count = 0
    
    return count


def get_user_usage_details(db: Session, user_id: int) -> Dict[str, int]:
    """
    Obtener detalles completos de uso del usuario
    """
    return {
        "customers": get_user_usage(db, user_id, "customers"),
        "quotes": get_user_usage(db, user_id, "quotes"), 
        "orders": get_user_usage(db, user_id, "orders"),
        "invoices": get_user_usage(db, user_id, "invoices")
    }


def check_user_can_create(db: Session, user_id: int, limit_type: str, user_limits: Dict[str, int]) -> tuple[bool, str]:
    """
    Verificar si el usuario puede crear un nuevo elemento
    Retorna (puede_crear, mensaje_error)
    """
    current_usage = get_user_usage(db, user_id, limit_type)
    max_allowed = user_limits.get(f"max_{limit_type}", 0)
    
    if current_usage >= max_allowed:
        period = "este mes" if limit_type in ["quotes", "orders", "invoices"] else "en total"
        return False, f"Límite excedido: {current_usage}/{max_allowed} {limit_type} {period}"
    
    return True, f"OK: {current_usage + 1}/{max_allowed} {limit_type}"


def get_user_limits_summary(db: Session, user_id: int, user_limits: Dict[str, int]) -> Dict:
    """
    Obtener resumen completo de límites y uso actual
    """
    usage = get_user_usage_details(db, user_id)
    
    return {
        "limits": user_limits,
        "current_usage": usage,
        "remaining": {
            "customers": max(0, user_limits.get("max_customers", 0) - usage["customers"]),
            "quotes": max(0, user_limits.get("max_quotes", 0) - usage["quotes"]),
            "orders": max(0, user_limits.get("max_orders", 0) - usage["orders"]),
            "invoices": max(0, user_limits.get("max_invoices", 0) - usage["invoices"])
        },
        "percentage_used": {
            "customers": round((usage["customers"] / max(1, user_limits.get("max_customers", 1))) * 100, 1),
            "quotes": round((usage["quotes"] / max(1, user_limits.get("max_quotes", 1))) * 100, 1),
            "orders": round((usage["orders"] / max(1, user_limits.get("max_orders", 1))) * 100, 1),
            "invoices": round((usage["invoices"] / max(1, user_limits.get("max_invoices", 1))) * 100, 1)
        }
    }