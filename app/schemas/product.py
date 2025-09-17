from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class CurrencyEnum(str, Enum):
    PYG = "PYG"
    USD = "USD"

# Schemas para ProductCategory
class ProductCategoryBase(BaseModel):
    name: str = Field(..., description="Nombre de la categoría")
    description: Optional[str] = Field(None, description="Descripción de la categoría")
    is_active: bool = Field(True, description="Categoría activa")

class ProductCategoryCreate(ProductCategoryBase):
    pass

class ProductCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ProductCategory(ProductCategoryBase):
    id: int
    created_at: datetime
    
    @field_validator('is_active', mode='before')
    @classmethod
    def validate_is_active(cls, v):
        # Convert None to True (default value)
        if v is None:
            return True
        return v
    
    class Config:
        from_attributes = True

# Schemas para Product
class ProductBase(BaseModel):
    name: str = Field(..., description="Nombre del producto")
    description: Optional[str] = Field(None, description="Descripción del producto")
    category_id: Optional[int] = Field(None, description="ID de la categoría")
    unit_of_measure: str = Field("PZA", description="Unidad de medida")
    cost_price: Decimal = Field(Decimal("0.00"), ge=0, description="Precio de costo")
    selling_price: Decimal = Field(..., ge=0, description="Precio de venta")
    min_stock_level: int = Field(0, ge=0, description="Nivel mínimo de stock")
    max_stock_level: int = Field(0, ge=0, description="Nivel máximo de stock")
    is_active: bool = Field(True, description="Producto activo")
    is_trackable: bool = Field(True, description="Maneja inventario")
    image_url: Optional[str] = Field(None, description="URL de imagen")
    barcode: Optional[str] = Field(None, description="Código de barras")
    weight: Optional[Decimal] = Field(None, ge=0, description="Peso en kg")
    expiry_date: Optional[date] = Field(None, description="Fecha de vencimiento")
    currency: CurrencyEnum = Field(CurrencyEnum.PYG, description="Moneda (PYG, USD)")

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit_of_measure: Optional[str] = None
    cost_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    min_stock_level: Optional[int] = None
    max_stock_level: Optional[int] = None
    is_active: Optional[bool] = None
    is_trackable: Optional[bool] = None
    image_url: Optional[str] = None
    barcode: Optional[str] = None
    weight: Optional[Decimal] = None
    expiry_date: Optional[date] = None
    currency: Optional[CurrencyEnum] = None

class Product(ProductBase):
    id: int
    product_code: str
    current_stock: int
    expiry_date: Optional[date] = None
    currency: CurrencyEnum
    created_at: datetime
    updated_at: Optional[datetime] = None
    category_name: Optional[str] = None
    
    @field_validator('is_active', mode='before')
    @classmethod
    def validate_is_active(cls, v):
        # Convert None to True (default value)
        if v is None:
            return True
        return v
    
    @field_validator('is_trackable', mode='before')
    @classmethod
    def validate_is_trackable(cls, v):
        # Convert None to True (default value)
        if v is None:
            return True
        return v
    
    class Config:
        from_attributes = True

class ProductList(BaseModel):
    id: int
    product_code: str
    name: str
    category_name: Optional[str] = None
    selling_price: Decimal
    current_stock: int
    is_active: bool
    is_trackable: bool
    currency: CurrencyEnum
    expiry_date: Optional[date] = None
    
    @field_validator('is_active', mode='before')
    @classmethod
    def validate_is_active(cls, v):
        # Convert None to True (default value)
        if v is None:
            return True
        return v
    
    @field_validator('is_trackable', mode='before')
    @classmethod
    def validate_is_trackable(cls, v):
        # Convert None to True (default value)
        if v is None:
            return True
        return v
    
    class Config:
        from_attributes = True

# Schemas para StockMovement
class StockMovementBase(BaseModel):
    product_id: int = Field(..., description="ID del producto")
    movement_type: str = Field(..., description="Tipo de movimiento: IN, OUT, ADJUSTMENT")
    quantity: int = Field(..., description="Cantidad (positiva para IN, negativa para OUT)")
    unit_cost: Optional[Decimal] = Field(None, ge=0, description="Costo unitario")
    reference_type: Optional[str] = Field(None, description="Tipo de referencia: SALE, PURCHASE, ADJUSTMENT")
    reference_id: Optional[int] = Field(None, description="ID de referencia")
    notes: Optional[str] = Field(None, description="Notas del movimiento")

class StockMovementCreate(StockMovementBase):
    pass

class StockMovement(StockMovementBase):
    id: int
    created_at: datetime
    product_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class StockAdjustment(BaseModel):
    product_id: int = Field(..., description="ID del producto")
    new_quantity: int = Field(..., ge=0, description="Nueva cantidad en inventario")
    reason: str = Field(..., description="Razón del ajuste")
    unit_cost: Optional[Decimal] = Field(None, ge=0, description="Costo unitario")