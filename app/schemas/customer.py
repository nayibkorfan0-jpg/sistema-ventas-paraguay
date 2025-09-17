from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, model_validator

# Schemas para Contact
class ContactBase(BaseModel):
    name: str = Field(..., description="Nombre del contacto")
    title: Optional[str] = Field(None, description="Cargo del contacto")
    email: Optional[EmailStr] = Field(None, description="Email del contacto")
    phone: Optional[str] = Field(None, description="Teléfono del contacto")
    mobile: Optional[str] = Field(None, description="Teléfono móvil del contacto")
    is_primary: bool = Field(False, description="Es contacto principal")
    is_active: bool = Field(True, description="Contacto activo")

class ContactCreate(ContactBase):
    customer_id: int = Field(..., description="ID del cliente")

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None

class Contact(ContactBase):
    id: int
    customer_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Schemas para Customer
class CustomerBase(BaseModel):
    company_name: str = Field(..., description="Razón social de empresa o nombre de persona individual")
    contact_name: Optional[str] = Field(None, description="Nombre del contacto principal")
    email: Optional[EmailStr] = Field(None, description="Email principal")
    phone: Optional[str] = Field(None, description="Teléfono principal")
    address: Optional[str] = Field(None, description="Dirección")
    city: Optional[str] = Field(None, description="Ciudad")
    state: Optional[str] = Field(None, description="Estado/Provincia")
    postal_code: Optional[str] = Field(None, description="Código postal")
    country: str = Field("Paraguay", description="País")
    tax_id: Optional[str] = Field(None, description="RUC o identificación fiscal")
    credit_limit: Decimal = Field(Decimal("0.00"), description="Límite de crédito")
    payment_terms: int = Field(30, description="Términos de pago en días")
    is_active: bool = Field(True, description="Cliente activo")
    
    # Campos específicos para régimen de turismo Paraguay
    tourism_regime: bool = Field(False, description="Cliente con régimen de turismo (exento de impuestos)")
    tourism_regime_pdf: Optional[str] = Field(None, description="Archivo PDF del régimen de turismo")
    tourism_regime_expiry: Optional[date] = Field(None, description="Fecha de vencimiento del régimen de turismo")
    
    notes: Optional[str] = Field(None, description="Notas adicionales")

class CustomerCreate(BaseModel):
    # Inherited fields from CustomerBase (excluding tourism_regime_pdf which is managed separately)
    company_name: str = Field(..., description="Razón social de empresa o nombre de persona individual")
    contact_name: Optional[str] = Field(None, description="Nombre del contacto principal")
    email: Optional[EmailStr] = Field(None, description="Email principal")
    phone: Optional[str] = Field(None, description="Teléfono principal")
    address: Optional[str] = Field(None, description="Dirección")
    city: Optional[str] = Field(None, description="Ciudad")
    state: Optional[str] = Field(None, description="Estado/Provincia")
    postal_code: Optional[str] = Field(None, description="Código postal")
    country: str = Field("Paraguay", description="País")
    tax_id: Optional[str] = Field(None, description="RUC o identificación fiscal")
    credit_limit: Decimal = Field(Decimal("0.00"), description="Límite de crédito")
    payment_terms: int = Field(30, description="Términos de pago en días")
    is_active: bool = Field(True, description="Cliente activo")
    
    # Campos específicos para régimen de turismo Paraguay
    # NOTE: tourism_regime_pdf is excluded - it's managed via separate upload endpoint
    tourism_regime: bool = Field(False, description="Cliente con régimen de turismo (exento de impuestos)")
    tourism_regime_expiry: Optional[date] = Field(None, description="Fecha de vencimiento del régimen de turismo")
    
    notes: Optional[str] = Field(None, description="Notas adicionales")
    
    @model_validator(mode='after')
    def validate_tourism_regime(self):
        """Validar que si tourism_regime=True, debe tener fecha de vencimiento futura"""
        if self.tourism_regime:
            if not self.tourism_regime_expiry:
                raise ValueError("Si el cliente tiene régimen de turismo, debe proporcionar la fecha de vencimiento del régimen")
            
            # Verificar que la fecha de vencimiento no sea pasada
            if self.tourism_regime_expiry <= date.today():
                raise ValueError("La fecha de vencimiento del régimen de turismo debe ser futura")
        
        return self

class CustomerUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    payment_terms: Optional[int] = None
    is_active: Optional[bool] = None
    
    # Campos específicos para régimen de turismo Paraguay
    # SECURITY: tourism_regime_pdf is read-only and managed only through dedicated upload/delete endpoints
    tourism_regime: Optional[bool] = None
    tourism_regime_expiry: Optional[date] = None
    
    notes: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_tourism_regime_update(self):
        """Validar que si se activa tourism_regime=True, debe tener fecha de vencimiento futura"""
        if self.tourism_regime is True:  # Específicamente True, no None
            if not self.tourism_regime_expiry:
                raise ValueError("Si activa el régimen de turismo, debe proporcionar la fecha de vencimiento del régimen")
            
            # Verificar que la fecha de vencimiento no sea pasada
            if self.tourism_regime_expiry <= date.today():
                raise ValueError("La fecha de vencimiento del régimen de turismo debe ser futura")
        
        return self

class Customer(CustomerBase):
    id: int
    customer_code: str
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    contacts: List[Contact] = []
    
    class Config:
        from_attributes = True

class CustomerList(BaseModel):
    id: int
    customer_code: str
    company_name: str
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    is_active: bool
    tourism_regime: bool = False  # Indicador visual de régimen de turismo
    created_at: datetime
    
    class Config:
        from_attributes = True