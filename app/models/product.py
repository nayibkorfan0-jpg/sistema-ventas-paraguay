from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ProductCategory(Base):
    __tablename__ = "product_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("product_categories.id"))
    unit_of_measure = Column(String, default="PZA")  # PZA, KG, M, etc.
    cost_price = Column(Numeric(10, 2), default=0)
    selling_price = Column(Numeric(10, 2), nullable=False)
    min_stock_level = Column(Integer, default=0)
    max_stock_level = Column(Integer, default=0)
    current_stock = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_trackable = Column(Boolean, default=True)  # Si maneja inventario
    image_url = Column(String)
    barcode = Column(String)
    weight = Column(Numeric(8, 3))  # en kg
    expiry_date = Column(Date)  # fecha de vencimiento para productos perecederos
    currency = Column(String, default="PYG")  # PYG, USD
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    category = relationship("ProductCategory", back_populates="products")
    quote_lines = relationship("QuoteLine", back_populates="product")
    order_lines = relationship("SalesOrderLine", back_populates="product")
    invoice_lines = relationship("InvoiceLine", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")

class StockMovement(Base):
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    movement_type = Column(String, nullable=False)  # IN, OUT, ADJUSTMENT
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2))
    reference_type = Column(String)  # SALE, PURCHASE, ADJUSTMENT
    reference_id = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    product = relationship("Product", back_populates="stock_movements")