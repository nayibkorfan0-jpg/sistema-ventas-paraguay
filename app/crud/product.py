from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.product import Product, ProductCategory, StockMovement
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductCategoryCreate, ProductCategoryUpdate,
    StockMovementCreate, StockAdjustment
)

class ProductCategoryCRUD:
    def get(self, db: Session, category_id: int) -> Optional[ProductCategory]:
        """Obtener categoría por ID"""
        return db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
    
    def get_by_name(self, db: Session, name: str) -> Optional[ProductCategory]:
        """Obtener categoría por nombre"""
        return db.query(ProductCategory).filter(ProductCategory.name == name).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[ProductCategory]:
        """Obtener múltiples categorías"""
        query = db.query(ProductCategory)
        
        if is_active is not None:
            query = query.filter(ProductCategory.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, category_in: ProductCategoryCreate) -> ProductCategory:
        """Crear nueva categoría"""
        db_category = ProductCategory(**category_in.dict())
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category
    
    def update(self, db: Session, db_category: ProductCategory, category_in: ProductCategoryUpdate) -> ProductCategory:
        """Actualizar categoría existente"""
        update_data = category_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)
        
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category

class ProductCRUD:
    def get(self, db: Session, product_id: int) -> Optional[Product]:
        """Obtener producto por ID"""
        return db.query(Product).filter(Product.id == product_id).first()
    
    def get_by_code(self, db: Session, product_code: str) -> Optional[Product]:
        """Obtener producto por código"""
        return db.query(Product).filter(Product.product_code == product_code).first()
    
    def get_by_barcode(self, db: Session, barcode: str) -> Optional[Product]:
        """Obtener producto por código de barras"""
        return db.query(Product).filter(Product.barcode == barcode).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        category_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_trackable: Optional[bool] = None,
        low_stock: bool = False,
        search: Optional[str] = None
    ) -> List[Product]:
        """Obtener múltiples productos con filtros"""
        query = db.query(Product)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        
        if is_trackable is not None:
            query = query.filter(Product.is_trackable == is_trackable)
        
        if low_stock:
            query = query.filter(
                and_(
                    Product.is_trackable == True,
                    Product.current_stock <= Product.min_stock_level
                )
            )
        
        if search:
            search_filter = or_(
                Product.name.ilike(f"%{search}%"),
                Product.product_code.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
                Product.barcode.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, product_in: ProductCreate) -> Product:
        """Crear nuevo producto"""
        # Generar código de producto automáticamente
        last_product = db.query(Product).order_by(Product.id.desc()).first()
        if last_product:
            last_number = int(last_product.product_code.replace("PROD", ""))
            new_number = last_number + 1
        else:
            new_number = 1
        
        product_code = f"PROD{new_number:06d}"
        
        db_product = Product(
            product_code=product_code,
            current_stock=0,
            **product_in.dict()
        )
        
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    
    def update(self, db: Session, db_product: Product, product_in: ProductUpdate) -> Product:
        """Actualizar producto existente"""
        update_data = product_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_product, field, value)
        
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    
    def adjust_stock(self, db: Session, adjustment: StockAdjustment) -> Product:
        """Ajustar stock de producto"""
        product = self.get(db, adjustment.product_id)
        if not product:
            raise ValueError(f"Producto con ID {adjustment.product_id} no encontrado")
        
        if not product.is_trackable:
            raise ValueError("No se puede ajustar stock de productos no rastreables")
        
        # Calcular diferencia (manejar current_stock None)
        current_stock = product.current_stock or 0
        difference = adjustment.new_quantity - current_stock
        
        # Crear movimiento de stock
        movement = StockMovement(
            product_id=adjustment.product_id,
            movement_type="ADJUSTMENT",
            quantity=difference,
            unit_cost=adjustment.unit_cost,
            reference_type="ADJUSTMENT",
            notes=adjustment.reason
        )
        db.add(movement)
        
        # Actualizar stock actual
        product.current_stock = adjustment.new_quantity
        db.add(product)
        
        db.commit()
        db.refresh(product)
        return product
    
    def update_stock(self, db: Session, product_id: int, quantity_change: int, 
                    movement_type: str, reference_type: Optional[str] = None,
                    reference_id: Optional[int] = None, unit_cost: Optional[Decimal] = None,
                    notes: Optional[str] = None) -> Product:
        """Actualizar stock de producto"""
        product = self.get(db, product_id)
        if not product:
            raise ValueError(f"Producto con ID {product_id} no encontrado")
        
        if not product.is_trackable:
            raise ValueError("No se puede actualizar stock de productos no rastreables")
        
        # Validar que no resulte en stock negativo (manejar current_stock None)
        current_stock = product.current_stock or 0
        new_stock = current_stock + quantity_change
        if new_stock < 0:
            raise ValueError(f"Stock insuficiente. Stock actual: {current_stock}, Cambio solicitado: {quantity_change}")
        
        # Crear movimiento de stock
        movement = StockMovement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity_change,
            unit_cost=unit_cost,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes
        )
        db.add(movement)
        
        # Actualizar stock actual
        product.current_stock = new_stock
        db.add(product)
        
        db.commit()
        db.refresh(product)
        return product

class StockMovementCRUD:
    def get_by_product(self, db: Session, product_id: int, limit: int = 100) -> List[StockMovement]:
        """Obtener movimientos de stock por producto"""
        return db.query(StockMovement).filter(
            StockMovement.product_id == product_id
        ).order_by(desc(StockMovement.created_at)).limit(limit).all()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        product_id: Optional[int] = None,
        movement_type: Optional[str] = None,
        reference_type: Optional[str] = None
    ) -> List[StockMovement]:
        """Obtener múltiples movimientos con filtros"""
        query = db.query(StockMovement)
        
        if product_id:
            query = query.filter(StockMovement.product_id == product_id)
        
        if movement_type:
            query = query.filter(StockMovement.movement_type == movement_type)
        
        if reference_type:
            query = query.filter(StockMovement.reference_type == reference_type)
        
        return query.order_by(desc(StockMovement.created_at)).offset(skip).limit(limit).all()
    
    def create(self, db: Session, movement_in: StockMovementCreate) -> StockMovement:
        """Crear movimiento de stock"""
        db_movement = StockMovement(**movement_in.dict())
        db.add(db_movement)
        db.commit()
        db.refresh(db_movement)
        return db_movement

# Instancias globales
product_category_crud = ProductCategoryCRUD()
product_crud = ProductCRUD()
stock_movement_crud = StockMovementCRUD()