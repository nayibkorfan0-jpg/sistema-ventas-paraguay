from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, index=True, nullable=False)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, SENT, PAID, OVERDUE, CANCELLED
    subtotal = Column(Numeric(12, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(12, 2), default=0)
    paid_amount = Column(Numeric(12, 2), default=0)
    balance_due = Column(Numeric(12, 2), default=0)
    currency = Column(String(3), default="PYG", nullable=False)  # PYG, USD
    notes = Column(Text)
    payment_terms = Column(String)
    
    # CAMPOS FISCALES ESPECÍFICOS PARA PARAGUAY
    punto_expedicion = Column(String(10), nullable=True, comment="Punto de expedición (ej: 001)")
    condicion_venta = Column(String(20), default="CREDITO", nullable=False, comment="CONTADO o CREDITO")
    lugar_emision = Column(String(100), nullable=True, comment="Ciudad de emisión de la factura")
    
    # DESGLOSE DE IVA PARAGUAYO
    subtotal_gravado_10 = Column(Numeric(12, 2), default=0, comment="Subtotal gravado al 10%")
    subtotal_gravado_5 = Column(Numeric(12, 2), default=0, comment="Subtotal gravado al 5%")
    subtotal_exento = Column(Numeric(12, 2), default=0, comment="Subtotal exento de IVA")
    iva_10 = Column(Numeric(12, 2), default=0, comment="IVA 10%")
    iva_5 = Column(Numeric(12, 2), default=0, comment="IVA 5%")
    
    # RÉGIMEN DE TURISMO PARAGUAY
    tourism_regime_applied = Column(Boolean, default=False, comment="Se aplicó régimen turístico")
    tourism_regime_percentage = Column(Numeric(5, 2), default=0, comment="Porcentaje de exención turística")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    sales_order = relationship("SalesOrder", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")

class InvoiceLine(Base):
    __tablename__ = "invoice_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    line_total = Column(Numeric(12, 2), nullable=False)
    description = Column(Text)
    
    # CAMPOS FISCALES PARA IVA PARAGUAYO
    iva_category = Column(String(10), default="10", nullable=False, comment="Categoría IVA: 10, 5, EXENTO")
    iva_amount = Column(Numeric(10, 2), default=0, comment="Monto de IVA de esta línea")
    
    # Relaciones
    invoice = relationship("Invoice", back_populates="lines")
    product = relationship("Product", back_populates="invoice_lines")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String, nullable=False)  # CASH, TRANSFER, CHECK, CARD
    reference_number = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    invoice = relationship("Invoice", back_populates="payments")