from pydantic import BaseModel, Field, validator
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List
from enum import Enum

class DepositType(str, Enum):
    """Tipos de depósito específicos para Paraguay"""
    ADVANCE = "ANTICIPO"        # Anticipo sobre trabajo futuro
    EARNEST = "SEÑA"           # Seña para reservar producto/servicio
    GUARANTEE = "GARANTIA"      # Garantía de cumplimiento
    SECURITY = "CAUCION"        # Caución para contratos
    PARTIAL = "PARCIAL"         # Pago parcial a cuenta

class DepositStatus(str, Enum):
    """Estados de depósito"""
    ACTIVE = "ACTIVO"           # Depósito disponible para aplicar
    APPLIED = "APLICADO"        # Depósito aplicado a facturas
    REFUNDED = "DEVUELTO"       # Depósito devuelto al cliente
    EXPIRED = "VENCIDO"         # Depósito vencido (si aplica)

class Currency(str, Enum):
    """Monedas soportadas en Paraguay"""
    PYG = "PYG"  # Guaraníes
    USD = "USD"  # Dólares

class PaymentMethod(str, Enum):
    """Métodos de pago para depósitos"""
    CASH = "CASH"
    TRANSFER = "TRANSFER"
    CHECK = "CHECK"
    CARD = "CARD"

# Schemas para Deposit
class DepositBase(BaseModel):
    customer_id: int
    deposit_type: DepositType
    amount: Decimal = Field(..., gt=0, description="Monto debe ser mayor a 0")
    currency: Currency = Currency.PYG
    deposit_date: date
    expiry_date: Optional[date] = None
    payment_method: PaymentMethod
    reference_number: Optional[str] = None
    bank_name: Optional[str] = None
    notes: Optional[str] = None
    project_reference: Optional[str] = None
    contract_number: Optional[str] = None

    @validator('expiry_date')
    def validate_expiry_date(cls, v, values):
        if v and 'deposit_date' in values and v <= values['deposit_date']:
            raise ValueError('Fecha de vencimiento debe ser posterior a la fecha del depósito')
        return v

class DepositCreate(DepositBase):
    pass

class DepositUpdate(BaseModel):
    deposit_type: Optional[DepositType] = None
    expiry_date: Optional[date] = None
    payment_method: Optional[PaymentMethod] = None
    reference_number: Optional[str] = None
    bank_name: Optional[str] = None
    notes: Optional[str] = None
    project_reference: Optional[str] = None
    contract_number: Optional[str] = None

class Deposit(DepositBase):
    id: int
    deposit_number: str
    status: DepositStatus
    applied_amount: Decimal
    available_amount: Decimal
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Información del cliente para mostrar
    customer_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class DepositList(BaseModel):
    """Schema para lista de depósitos"""
    id: int
    deposit_number: str
    customer_id: int
    customer_name: str
    deposit_type: DepositType
    amount: Decimal
    currency: Currency
    deposit_date: date
    status: DepositStatus
    available_amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True

# Schemas para DepositApplication
class DepositApplicationBase(BaseModel):
    deposit_id: int
    invoice_id: int
    amount_applied: Decimal = Field(..., gt=0, description="Monto a aplicar debe ser mayor a 0")
    application_date: date
    notes: Optional[str] = None

class DepositApplicationCreate(DepositApplicationBase):
    pass

class DepositApplication(DepositApplicationBase):
    id: int
    applied_by_id: int
    created_at: datetime
    
    # Información adicional para mostrar
    deposit_number: Optional[str] = None
    invoice_number: Optional[str] = None
    
    class Config:
        from_attributes = True

# Schemas para CustomerDepositSummary
class CustomerDepositSummary(BaseModel):
    customer_id: int
    customer_name: Optional[str] = None
    
    # Saldos en Guaraníes
    total_deposits_pyg: Decimal
    available_deposits_pyg: Decimal
    applied_deposits_pyg: Decimal
    
    # Saldos en Dólares
    total_deposits_usd: Decimal
    available_deposits_usd: Decimal
    applied_deposits_usd: Decimal
    
    # Contadores
    active_deposits_count: int
    total_deposits_count: int
    
    # Fechas importantes
    last_deposit_date: Optional[date] = None
    last_application_date: Optional[date] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Schemas para operaciones específicas
class ApplyDepositToInvoice(BaseModel):
    """Schema para aplicar depósito a factura"""
    deposit_id: int
    invoice_id: int
    amount_to_apply: Decimal = Field(..., gt=0, description="Monto a aplicar debe ser mayor a 0")
    notes: Optional[str] = None

class RefundDeposit(BaseModel):
    """Schema para devolver depósito"""
    refund_amount: Decimal = Field(..., gt=0, description="Monto a devolver debe ser mayor a 0")
    refund_reason: str
    refund_method: PaymentMethod
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class DepositReport(BaseModel):
    """Schema para reportes de depósitos"""
    period_start: date
    period_end: date
    total_deposits: Decimal
    total_applications: Decimal
    total_refunds: Decimal
    deposit_count: int
    currency: Currency

# Respuestas de operaciones
class DepositOperationResponse(BaseModel):
    """Respuesta genérica para operaciones de depósitos"""
    success: bool
    message: str
    deposit_id: Optional[int] = None
    new_available_amount: Optional[Decimal] = None