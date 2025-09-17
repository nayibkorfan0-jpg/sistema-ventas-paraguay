from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship, synonym
from sqlalchemy.sql import func
from app.core.database import Base

class Quote(Base):
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_number = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    quote_date = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=False)
    status = Column(String, default="DRAFT")  # DRAFT, SENT, APPROVED, REJECTED, EXPIRED
    subtotal = Column(Numeric(12, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(12, 2), default=0)
    notes = Column(Text)
    terms_conditions = Column(Text)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    customer = relationship("Customer", back_populates="quotes")
    created_by = relationship("User", back_populates="created_quotes")
    lines = relationship("QuoteLine", back_populates="quote", cascade="all, delete-orphan")
    sales_orders = relationship("SalesOrder", back_populates="quote")

class QuoteLine(Base):
    __tablename__ = "quote_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    line_total = Column(Numeric(12, 2), nullable=False)
    description = Column(Text)
    
    # Relaciones
    quote = relationship("Quote", back_populates="lines")
    product = relationship("Product", back_populates="quote_lines")

class SalesOrder(Base):
    __tablename__ = "sales_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=False)
    quote_id = Column(Integer, ForeignKey("quotes.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_date = Column(Date, nullable=False)
    delivery_date = Column(Date)
    status = Column(String, default="PENDING")  # PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED
    subtotal = Column(Numeric(12, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(12, 2), default=0)
    shipping_cost = Column(Numeric(10, 2), default=0)
    notes = Column(Text)
    shipping_address = Column(Text)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    quote = relationship("Quote", back_populates="sales_orders")
    customer = relationship("Customer", back_populates="orders")
    created_by = relationship("User", back_populates="created_orders")
    lines = relationship("SalesOrderLine", back_populates="order", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="sales_order")

class SalesOrderLine(Base):
    __tablename__ = "sales_order_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    line_total = Column(Numeric(12, 2), nullable=False)
    total_amount = synonym('line_total')  # Backward compatibility alias
    description = Column(Text)
    quantity_shipped = Column(Integer, default=0)
    quantity_invoiced = Column(Integer, default=0)
    
    # Relaciones
    order = relationship("SalesOrder", back_populates="lines")
    product = relationship("Product", back_populates="order_lines")