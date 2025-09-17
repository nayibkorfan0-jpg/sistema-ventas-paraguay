from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field

# Enums
class SalesOrderStatus(str, Enum):
    pending = "PENDING"
    confirmed = "CONFIRMED"
    shipped = "SHIPPED"
    delivered = "DELIVERED"
    cancelled = "CANCELLED"

# Schemas para SalesOrderLine
class SalesOrderLineBase(BaseModel):
    product_id: int = Field(..., description="ID del producto")
    quantity: int = Field(..., gt=0, description="Cantidad")
    unit_price: Decimal = Field(..., ge=0, description="Precio unitario")
    discount_percent: Decimal = Field(Decimal("0.00"), ge=0, le=100, description="Descuento en porcentaje")
    description: Optional[str] = Field(None, description="Descripción del artículo")

class SalesOrderLineCreate(SalesOrderLineBase):
    pass

class SalesOrderLineUpdate(BaseModel):
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    discount_percent: Optional[Decimal] = None
    description: Optional[str] = None

class SalesOrderLine(SalesOrderLineBase):
    id: int
    order_id: int
    line_total: Decimal = Field(..., description="Total de la línea")
    quantity_shipped: int = Field(0, description="Cantidad enviada")
    quantity_invoiced: int = Field(0, description="Cantidad facturada")
    
    class Config:
        from_attributes = True

# Schemas para SalesOrder
class SalesOrderBase(BaseModel):
    customer_id: int = Field(..., description="ID del cliente")
    order_date: date = Field(..., description="Fecha de la orden")
    delivery_date: Optional[date] = Field(None, description="Fecha de entrega esperada")
    shipping_cost: Decimal = Field(Decimal("0.00"), ge=0, description="Costo de envío")
    shipping_address: Optional[str] = Field(None, description="Dirección de envío")
    notes: Optional[str] = Field(None, description="Notas adicionales")

class SalesOrderCreate(SalesOrderBase):
    quote_id: Optional[int] = Field(None, description="ID de cotización origen")
    lines: List[SalesOrderLineCreate] = Field(..., min_length=1, description="Líneas de la orden")

class SalesOrderUpdate(BaseModel):
    customer_id: Optional[int] = None
    order_date: Optional[date] = None
    delivery_date: Optional[date] = None
    status: Optional[SalesOrderStatus] = None
    shipping_cost: Optional[Decimal] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    lines: Optional[List[SalesOrderLineCreate]] = None

class SalesOrder(SalesOrderBase):
    id: int
    order_number: str
    quote_id: Optional[int] = None
    status: SalesOrderStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    lines: List[SalesOrderLine] = []
    
    # Información del cliente
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    
    class Config:
        from_attributes = True

class SalesOrderList(BaseModel):
    id: int
    order_number: str
    customer_id: int
    customer_name: str
    order_date: date
    delivery_date: Optional[date] = None
    status: SalesOrderStatus
    total_amount: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True

# Helper function similar to quote status
def parse_sales_order_status(status_value) -> SalesOrderStatus:
    """Parse and normalize database status value to SalesOrderStatus enum"""
    if isinstance(status_value, SalesOrderStatus):
        return status_value
    if not status_value:
        return SalesOrderStatus.pending
    
    status_str = str(status_value).strip().upper()
    try:
        return SalesOrderStatus(status_str)
    except ValueError:
        # Handle legacy or unknown values
        if status_str in ["DRAFT", "NEW"]:
            return SalesOrderStatus.pending
        return SalesOrderStatus.pending