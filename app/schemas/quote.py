from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field

# Enums
class QuoteStatus(str, Enum):
    draft = "DRAFT"
    sent = "SENT"
    accepted = "ACCEPTED"
    rejected = "REJECTED"
    expired = "EXPIRED"

def parse_quote_status(status_str: str) -> QuoteStatus:
    """
    Helper function to parse quote status case-insensitively.
    Handles legacy lowercase status values from database.
    """
    if not status_str:
        return QuoteStatus.draft
    
    # Convert to uppercase and try to match
    status_upper = status_str.upper()
    
    # Map to enum values
    for status in QuoteStatus:
        if status.value == status_upper:
            return status
    
    # Fallback for unknown values
    raise ValueError(f"Unknown quote status: {status_str}")

# Schemas para QuoteLine
class QuoteLineBase(BaseModel):
    product_id: int = Field(..., description="ID del producto")
    quantity: int = Field(..., gt=0, description="Cantidad")
    unit_price: Decimal = Field(..., ge=0, description="Precio unitario")
    discount_percent: Decimal = Field(Decimal("0.00"), ge=0, le=100, description="Descuento en porcentaje")
    description: Optional[str] = Field(None, description="Descripción del artículo")

class QuoteLineCreate(QuoteLineBase):
    pass

class QuoteLineUpdate(BaseModel):
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    discount_percent: Optional[Decimal] = None
    description: Optional[str] = None

class QuoteLine(QuoteLineBase):
    id: int
    quote_id: int
    line_total: Decimal = Field(..., description="Total de la línea")
    
    class Config:
        from_attributes = True

# Schemas para Quote
class QuoteBase(BaseModel):
    customer_id: int = Field(..., description="ID del cliente")
    quote_date: date = Field(..., description="Fecha de la cotización")
    valid_until: date = Field(..., description="Válida hasta")
    notes: Optional[str] = Field(None, description="Notas adicionales")
    terms_conditions: Optional[str] = Field(None, description="Términos y condiciones")

class QuoteCreate(QuoteBase):
    lines: List[QuoteLineCreate] = Field(..., min_length=1, description="Líneas de la cotización")

class QuoteUpdate(BaseModel):
    customer_id: Optional[int] = None
    quote_date: Optional[date] = None
    valid_until: Optional[date] = None
    status: Optional[QuoteStatus] = None
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    lines: Optional[List[QuoteLineCreate]] = None

class Quote(QuoteBase):
    id: int
    quote_number: str
    status: QuoteStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    lines: List[QuoteLine] = []
    
    # Información del cliente (para mostrar en listados)
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    
    class Config:
        from_attributes = True

class QuoteList(BaseModel):
    id: int
    quote_number: str
    customer_id: int
    customer_name: str
    quote_date: date
    valid_until: date
    status: QuoteStatus
    total_amount: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True

class QuotePDFResponse(BaseModel):
    quote_id: int
    pdf_filename: str
    download_url: str