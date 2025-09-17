from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"           # Administrador completo
    MANAGER = "manager"       # Gerente con acceso amplio 
    SELLER = "seller"         # Vendedor con limitaciones
    VIEWER = "viewer"         # Solo lectura
    ACCOUNTANT = "accountant" # Contador - acceso financiero

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    is_active: bool = True
    role: UserRole = UserRole.SELLER
    
    # Limitaciones de uso
    max_customers: int = 10
    max_quotes: int = 20
    max_orders: int = 15
    max_invoices: int = 10
    
    # Permisos específicos
    can_create_customers: bool = True
    can_create_quotes: bool = True
    can_manage_inventory: bool = False
    can_view_reports: bool = True
    can_manage_tourism_regime: bool = False
    can_manage_deposits: bool = False
    can_export_data: bool = False
    
    # Información adicional para Paraguay
    notes: Optional[str] = None
    department: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    
    # Limitaciones opcionales para actualizar
    max_customers: Optional[int] = None
    max_quotes: Optional[int] = None
    max_orders: Optional[int] = None
    max_invoices: Optional[int] = None
    
    # Permisos opcionales para actualizar
    can_create_customers: Optional[bool] = None
    can_create_quotes: Optional[bool] = None
    can_manage_inventory: Optional[bool] = None
    can_view_reports: Optional[bool] = None
    can_manage_tourism_regime: Optional[bool] = None
    can_manage_deposits: Optional[bool] = None
    can_export_data: Optional[bool] = None
    
    # Info adicional opcional
    notes: Optional[str] = None
    department: Optional[str] = None

class UserInDB(UserBase):
    id: int
    hashed_password: str
    is_superuser: bool = False
    
    model_config = {"from_attributes": True}

class User(UserBase):
    id: int
    is_superuser: bool = False
    
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str