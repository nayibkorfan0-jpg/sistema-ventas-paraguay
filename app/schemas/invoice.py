from pydantic import BaseModel, validator, Field
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from enum import Enum

class InvoiceStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"

class PaymentMethod(str, Enum):
    CASH = "CASH"
    TRANSFER = "TRANSFER"
    CHECK = "CHECK"
    CARD = "CARD"

class CondicionVenta(str, Enum):
    CONTADO = "CONTADO"
    CREDITO = "CREDITO"

class IVACategory(str, Enum):
    IVA_10 = "10"
    IVA_5 = "5"
    EXENTO = "EXENTO"

# Payment schemas
class PaymentBase(BaseModel):
    amount: Decimal = Field(..., ge=0, description="Monto del pago")
    payment_method: PaymentMethod
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    invoice_id: int
    payment_date: date

class Payment(PaymentBase):
    id: int
    invoice_id: int
    payment_date: date
    created_at: datetime
    
    class Config:
        from_attributes = True

# Invoice Line schemas
class InvoiceLineBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0, description="Cantidad debe ser mayor a 0")
    unit_price: Decimal = Field(..., ge=0, description="Precio unitario")
    discount_percent: Decimal = Field(Decimal('0'), ge=0, le=100, description="Descuento entre 0 y 100%")
    description: Optional[str] = None
    
    # CAMPOS FISCALES PARA IVA PARAGUAYO
    iva_category: IVACategory = IVACategory.IVA_10

class InvoiceLineCreate(InvoiceLineBase):
    pass

class InvoiceLine(InvoiceLineBase):
    id: int
    invoice_id: int
    line_total: Decimal
    
    # CAMPOS FISCALES PARA IVA PARAGUAYO
    iva_amount: Decimal = Decimal('0')
    
    # Información del producto para mostrar
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    
    class Config:
        from_attributes = True

# Invoice schemas
class InvoiceBase(BaseModel):
    customer_id: int
    invoice_date: date
    due_date: date
    payment_terms: Optional[str] = "Net 30"
    notes: Optional[str] = None
    
    # CAMPOS FISCALES ESPECÍFICOS PARA PARAGUAY
    condicion_venta: CondicionVenta = CondicionVenta.CREDITO
    lugar_emision: Optional[str] = "Asunción"

class InvoiceCreate(InvoiceBase):
    sales_order_id: Optional[int] = None
    lines: List[InvoiceLineCreate] = []

class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatus] = None
    due_date: Optional[date] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None

class Invoice(InvoiceBase):
    id: int
    invoice_number: str
    sales_order_id: Optional[int] = None
    status: InvoiceStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    balance_due: Decimal
    currency: str = "PYG"
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # CAMPOS FISCALES ESPECÍFICOS PARA PARAGUAY
    punto_expedicion: Optional[str] = None
    
    # DESGLOSE DE IVA PARAGUAYO
    subtotal_gravado_10: Decimal = Decimal('0')
    subtotal_gravado_5: Decimal = Decimal('0')
    subtotal_exento: Decimal = Decimal('0')
    iva_10: Decimal = Decimal('0')
    iva_5: Decimal = Decimal('0')
    
    # RÉGIMEN DE TURISMO PARAGUAY
    tourism_regime_applied: bool = False
    tourism_regime_percentage: Decimal = Decimal('0')
    
    # Información del cliente para mostrar
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_ruc: Optional[str] = None
    
    # Información de la orden de venta
    sales_order_number: Optional[str] = None
    
    class Config:
        from_attributes = True

class InvoiceWithDetails(Invoice):
    lines: List[InvoiceLine] = []
    payments: List[Payment] = []

# Schemas para listas
class InvoiceList(BaseModel):
    id: int
    invoice_number: str
    customer_id: int
    customer_name: str
    invoice_date: date
    due_date: date
    status: InvoiceStatus
    total_amount: Decimal
    balance_due: Decimal
    created_at: datetime

class InvoiceSummary(BaseModel):
    total_invoices: int
    total_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal
    overdue_amount: Decimal

# Schema para crear factura desde orden de venta
class InvoiceFromOrder(BaseModel):
    sales_order_id: int
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_terms: Optional[str] = "Net 30"
    notes: Optional[str] = None
    
    @validator('invoice_date', pre=True, always=True)
    def set_invoice_date(cls, v):
        return v or date.today()
    
    @validator('due_date', pre=True, always=True)
    def set_due_date(cls, v, values):
        if v:
            return v
        # Si no se especifica, usar 30 días desde la fecha de factura
        from datetime import timedelta
        invoice_date = values.get('invoice_date', date.today())
        return invoice_date + timedelta(days=30) if invoice_date else None

def parse_invoice_status(status_str: str) -> InvoiceStatus:
    """Convertir string a enum de estado de factura, manejando case insensitive"""
    if not status_str:
        return InvoiceStatus.PENDING
    
    status_upper = status_str.upper().strip()
    
    try:
        return InvoiceStatus(status_upper)
    except ValueError:
        # Si no es un estado válido, devolver PENDING por defecto
        return InvoiceStatus.PENDING

def parse_payment_method(method_str: str) -> PaymentMethod:
    """Convertir string a enum de método de pago, manejando case insensitive"""
    if not method_str:
        return PaymentMethod.CASH
    
    method_upper = method_str.upper().strip()
    
    try:
        return PaymentMethod(method_upper)
    except ValueError:
        # Si no es un método válido, devolver CASH por defecto
        return PaymentMethod.CASH