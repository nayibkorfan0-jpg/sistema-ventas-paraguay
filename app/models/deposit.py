from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class DepositType:
    """Tipos de depósito específicos para Paraguay"""
    ADVANCE = "ANTICIPO"        # Anticipo sobre trabajo futuro
    EARNEST = "SEÑA"           # Seña para reservar producto/servicio
    GUARANTEE = "GARANTIA"      # Garantía de cumplimiento
    SECURITY = "CAUCION"        # Caución para contratos
    PARTIAL = "PARCIAL"         # Pago parcial a cuenta

class DepositStatus:
    """Estados de depósito"""
    ACTIVE = "ACTIVO"           # Depósito disponible para aplicar
    APPLIED = "APLICADO"        # Depósito aplicado a facturas
    REFUNDED = "DEVUELTO"       # Depósito devuelto al cliente
    EXPIRED = "VENCIDO"         # Depósito vencido (si aplica)

class Deposit(Base):
    """
    Modelo para gestión de depósitos independientes
    Específico para procesos financieros de Paraguay
    """
    __tablename__ = "deposits"
    
    id = Column(Integer, primary_key=True, index=True)
    deposit_number = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Información del depósito
    deposit_type = Column(String, nullable=False)  # ANTICIPO, SEÑA, GARANTIA, etc.
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="PYG", nullable=False)  # PYG, USD
    
    # Control de fechas
    deposit_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)  # Para garantías con vencimiento
    
    # Estado y aplicación
    status = Column(String, default=DepositStatus.ACTIVE, nullable=False)
    applied_amount = Column(Numeric(12, 2), default=0, nullable=False)
    available_amount = Column(Numeric(12, 2), nullable=False)  # amount - applied_amount
    
    # Información de pago
    payment_method = Column(String, nullable=False)  # CASH, TRANSFER, CHECK, CARD
    reference_number = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)  # Para transferencias/cheques
    
    # Información adicional Paraguay
    notes = Column(Text, nullable=True)
    project_reference = Column(String, nullable=True)  # Referencia del proyecto/trabajo
    contract_number = Column(String, nullable=True)   # Número de contrato asociado
    
    # Auditoría
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    customer = relationship("Customer", back_populates="deposits")
    created_by = relationship("User")
    applications = relationship("DepositApplication", back_populates="deposit")

class DepositApplication(Base):
    """
    Registro de aplicación de depósitos a facturas
    Para auditoría y control detallado
    """
    __tablename__ = "deposit_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    deposit_id = Column(Integer, ForeignKey("deposits.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    # Información de la aplicación
    amount_applied = Column(Numeric(12, 2), nullable=False)
    application_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Auditoría
    applied_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    deposit = relationship("Deposit", back_populates="applications")
    invoice = relationship("Invoice")
    applied_by = relationship("User")

class CustomerDepositSummary(Base):
    """
    Vista/tabla para resumen rápido de depósitos por cliente
    Optimiza consultas frecuentes
    """
    __tablename__ = "customer_deposit_summary"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), unique=True, nullable=False)
    
    # Saldos por moneda
    total_deposits_pyg = Column(Numeric(12, 2), default=0, nullable=False)
    available_deposits_pyg = Column(Numeric(12, 2), default=0, nullable=False)
    applied_deposits_pyg = Column(Numeric(12, 2), default=0, nullable=False)
    
    total_deposits_usd = Column(Numeric(12, 2), default=0, nullable=False)
    available_deposits_usd = Column(Numeric(12, 2), default=0, nullable=False)
    applied_deposits_usd = Column(Numeric(12, 2), default=0, nullable=False)
    
    # Contadores
    active_deposits_count = Column(Integer, default=0, nullable=False)
    total_deposits_count = Column(Integer, default=0, nullable=False)
    
    # Información de control
    last_deposit_date = Column(Date, nullable=True)
    last_application_date = Column(Date, nullable=True)
    
    # Auditoría
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    customer = relationship("Customer", back_populates="deposit_summary")