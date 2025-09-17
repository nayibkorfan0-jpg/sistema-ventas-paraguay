from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"           # Administrador completo
    MANAGER = "manager"       # Gerente con acceso amplio 
    SELLER = "seller"         # Vendedor con limitaciones
    VIEWER = "viewer"         # Solo lectura
    ACCOUNTANT = "accountant" # Contador - acceso financiero

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # SISTEMA DE ROLES Y LIMITACIONES PARA PARAGUAY
    role = Column(
        PGEnum(
            UserRole,
            name="userrole",
            values_callable=lambda e: [m.value for m in e],
            create_type=False,   # don't recreate; alembic owns it
        ),
        default=UserRole.SELLER,
        nullable=False,
    )
    
    # Limitaciones de uso
    max_customers = Column(Integer, default=10, nullable=False)       # Máximo clientes que puede crear
    max_quotes = Column(Integer, default=20, nullable=False)          # Máximo cotizaciones por mes
    max_orders = Column(Integer, default=15, nullable=False)          # Máximo órdenes por mes
    max_invoices = Column(Integer, default=10, nullable=False)        # Máximo facturas por mes
    
    # Permisos específicos
    can_create_customers = Column(Boolean, default=True)             # Puede crear clientes
    can_create_quotes = Column(Boolean, default=True)               # Puede crear cotizaciones
    can_manage_inventory = Column(Boolean, default=False)             # Puede manejar inventario
    can_view_reports = Column(Boolean, default=True)                 # Puede ver reportes
    can_manage_tourism_regime = Column(Boolean, default=False)       # Puede gestionar régimen turismo
    can_manage_deposits = Column(Boolean, default=False)             # Puede manejar depósitos
    can_export_data = Column(Boolean, default=False)                 # Puede exportar datos
    
    # Información adicional para Paraguay
    notes = Column(Text, nullable=True)                              # Notas del administrador
    department = Column(String, nullable=True)                       # Departamento/Sucursal
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    created_customers = relationship("Customer", back_populates="created_by")
    created_quotes = relationship("Quote", back_populates="created_by")
    created_orders = relationship("SalesOrder", back_populates="created_by")