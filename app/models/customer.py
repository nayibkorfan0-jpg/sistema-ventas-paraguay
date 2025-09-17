from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String, nullable=False)
    contact_name = Column(String)
    email = Column(String, index=True)
    phone = Column(String)
    address = Column(Text)
    city = Column(String)
    state = Column(String)
    postal_code = Column(String)
    country = Column(String, default="Paraguay")
    tax_id = Column(String)  # RUC en Paraguay
    credit_limit = Column(Numeric(10, 2), default=0)
    payment_terms = Column(Integer, default=30)  # días
    is_active = Column(Boolean, default=True)
    
    # Campos específicos para régimen de turismo Paraguay
    tourism_regime = Column(Boolean, default=False)  # Cliente con régimen de turismo (exento de impuestos)
    tourism_regime_pdf = Column(String)  # Nombre del archivo PDF del régimen
    tourism_regime_expiry = Column(Date)  # Fecha de vencimiento del régimen de turismo
    
    notes = Column(Text)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    created_by = relationship("User", back_populates="created_customers")
    contacts = relationship("Contact", back_populates="customer")
    quotes = relationship("Quote", back_populates="customer")
    orders = relationship("SalesOrder", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")
    deposits = relationship("Deposit", back_populates="customer")
    deposit_summary = relationship("CustomerDepositSummary", back_populates="customer", uselist=False)

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    name = Column(String, nullable=False)
    title = Column(String)
    email = Column(String)
    phone = Column(String)
    mobile = Column(String)
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    customer = relationship("Customer", back_populates="contacts")