from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_database
from app.core.dependencies import get_current_active_user
from app.crud.product import product_crud, product_category_crud, stock_movement_crud
from app.schemas.product import (
    Product, ProductCreate, ProductUpdate, ProductList,
    ProductCategory, ProductCategoryCreate, ProductCategoryUpdate,
    StockMovement, StockMovementCreate, StockAdjustment
)
from app.models.user import User

router = APIRouter(prefix="/products", tags=["productos"])

# Endpoints para Categorías
@router.get("/categories/", response_model=List[ProductCategory])
def list_categories(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None)
):
    """Obtener lista de categorías de productos"""
    categories = product_category_crud.get_multi(
        db=db, skip=skip, limit=limit, is_active=is_active
    )
    return categories

@router.post("/categories/", response_model=ProductCategory)
def create_category(
    category_in: ProductCategoryCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Crear nueva categoría de producto"""
    # Verificar si ya existe
    existing = product_category_crud.get_by_name(db=db, name=category_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una categoría con este nombre"
        )
    
    category = product_category_crud.create(db=db, category_in=category_in)
    return category

@router.put("/categories/{category_id}", response_model=ProductCategory)
def update_category(
    category_id: int,
    category_in: ProductCategoryUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar categoría existente"""
    db_category = product_category_crud.get(db=db, category_id=category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    
    category = product_category_crud.update(db=db, db_category=db_category, category_in=category_in)
    return category

# Endpoints para Productos
@router.get("/", response_model=List[ProductList])
def list_products(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    is_trackable: Optional[bool] = Query(None, description="Filtrar por rastreable"),
    low_stock: bool = Query(False, description="Solo productos con stock bajo"),
    search: Optional[str] = Query(None, description="Buscar por nombre, código o descripción")
):
    """Obtener lista de productos con filtros opcionales"""
    products = product_crud.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        is_active=is_active,
        is_trackable=is_trackable,
        low_stock=low_stock,
        search=search
    )
    
    # Mapear a ProductList usando model_validate
    products_list = []
    for product in products:
        product_dict = {
            "id": product.id,
            "product_code": product.product_code,
            "name": product.name,
            "category_name": product.category.name if product.category else None,
            "selling_price": product.selling_price,
            "current_stock": product.current_stock if product.current_stock is not None else 0,
            "is_active": product.is_active if product.is_active is not None else True,
            "is_trackable": product.is_trackable if product.is_trackable is not None else True,
            "currency": product.currency if product.currency is not None else "PYG",
            "expiry_date": product.expiry_date
        }
        products_list.append(ProductList.model_validate(product_dict))
    
    return products_list

@router.get("/{product_id}", response_model=Product)
def get_product(
    product_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener producto específico por ID"""
    product = product_crud.get(db=db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    # Convertir a esquema de respuesta usando model_validate
    product_dict = {
        "id": product.id,
        "product_code": product.product_code,
        "name": product.name,
        "description": product.description,
        "category_id": product.category_id,
        "unit_of_measure": product.unit_of_measure,
        "cost_price": product.cost_price,
        "selling_price": product.selling_price,
        "min_stock_level": product.min_stock_level,
        "max_stock_level": product.max_stock_level,
        "current_stock": product.current_stock,
        "is_active": product.is_active,
        "is_trackable": product.is_trackable,
        "image_url": product.image_url,
        "barcode": product.barcode,
        "weight": product.weight,
        "expiry_date": product.expiry_date,
        "currency": product.currency if product.currency is not None else "PYG",
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "category_name": product.category.name if product.category else None
    }
    
    return Product.model_validate(product_dict)

@router.post("/", response_model=Product)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Crear nuevo producto"""
    # Verificar código de barras único si se proporciona
    if product_in.barcode:
        existing = product_crud.get_by_barcode(db=db, barcode=product_in.barcode)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un producto con este código de barras"
            )
    
    product = product_crud.create(db=db, product_in=product_in)
    
    # Convertir a esquema de respuesta usando model_validate
    product_dict = {
        "id": product.id,
        "product_code": product.product_code,
        "name": product.name,
        "description": product.description,
        "category_id": product.category_id,
        "unit_of_measure": product.unit_of_measure,
        "cost_price": product.cost_price,
        "selling_price": product.selling_price,
        "min_stock_level": product.min_stock_level,
        "max_stock_level": product.max_stock_level,
        "current_stock": product.current_stock,
        "is_active": product.is_active,
        "is_trackable": product.is_trackable,
        "image_url": product.image_url,
        "barcode": product.barcode,
        "weight": product.weight,
        "expiry_date": product.expiry_date,
        "currency": product.currency if product.currency is not None else "PYG",
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "category_name": product.category.name if product.category else None
    }
    
    return Product.model_validate(product_dict)

@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar producto existente"""
    db_product = product_crud.get(db=db, product_id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    # Verificar código de barras único si se actualiza
    if product_in.barcode and product_in.barcode != db_product.barcode:
        existing = product_crud.get_by_barcode(db=db, barcode=product_in.barcode)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un producto con este código de barras"
            )
    
    product = product_crud.update(db=db, db_product=db_product, product_in=product_in)
    
    # Convertir a esquema de respuesta usando model_validate
    product_dict = {
        "id": product.id,
        "product_code": product.product_code,
        "name": product.name,
        "description": product.description,
        "category_id": product.category_id,
        "unit_of_measure": product.unit_of_measure,
        "cost_price": product.cost_price,
        "selling_price": product.selling_price,
        "min_stock_level": product.min_stock_level,
        "max_stock_level": product.max_stock_level,
        "current_stock": product.current_stock,
        "is_active": product.is_active,
        "is_trackable": product.is_trackable,
        "image_url": product.image_url,
        "barcode": product.barcode,
        "weight": product.weight,
        "expiry_date": product.expiry_date,
        "currency": product.currency if product.currency is not None else "PYG",
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "category_name": product.category.name if product.category else None
    }
    
    return Product.model_validate(product_dict)

# Endpoints para Gestión de Inventario
@router.post("/{product_id}/adjust-stock", response_model=Product)
def adjust_product_stock(
    product_id: int,
    adjustment: StockAdjustment,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Ajustar stock de producto"""
    try:
        # Forzar product_id del URL
        adjustment.product_id = product_id
        
        product = product_crud.adjust_stock(db=db, adjustment=adjustment)
        
        # Convertir a esquema de respuesta usando model_validate
        product_dict = {
            "id": product.id,
            "product_code": product.product_code,
            "name": product.name,
            "description": product.description,
            "category_id": product.category_id,
            "unit_of_measure": product.unit_of_measure,
            "cost_price": product.cost_price,
            "selling_price": product.selling_price,
            "min_stock_level": product.min_stock_level,
            "max_stock_level": product.max_stock_level,
            "current_stock": product.current_stock,
            "is_active": product.is_active,
            "is_trackable": product.is_trackable,
            "image_url": product.image_url,
            "barcode": product.barcode,
            "weight": product.weight,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "category_name": product.category.name if product.category else None
        }
        
        return Product.model_validate(product_dict)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{product_id}/stock-movements", response_model=List[StockMovement])
def get_product_stock_movements(
    product_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros")
):
    """Obtener movimientos de stock de un producto"""
    # Verificar que el producto existe
    product = product_crud.get(db=db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    movements = stock_movement_crud.get_by_product(db=db, product_id=product_id, limit=limit)
    
    # Mapear a esquema de respuesta
    movements_list = []
    for movement in movements:
        movement_dict = {
            "id": movement.id,
            "product_id": movement.product_id,
            "movement_type": movement.movement_type,
            "quantity": movement.quantity,
            "unit_cost": movement.unit_cost,
            "reference_type": movement.reference_type,
            "reference_id": movement.reference_id,
            "notes": movement.notes,
            "created_at": movement.created_at,
            "product_name": movement.product.name
        }
        movements_list.append(StockMovement.model_validate(movement_dict))
    
    return movements_list

@router.get("/stock-movements/", response_model=List[StockMovement])
def list_stock_movements(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    product_id: Optional[int] = Query(None, description="Filtrar por producto"),
    movement_type: Optional[str] = Query(None, description="Filtrar por tipo de movimiento"),
    reference_type: Optional[str] = Query(None, description="Filtrar por tipo de referencia")
):
    """Obtener lista de movimientos de stock con filtros"""
    movements = stock_movement_crud.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        product_id=product_id,
        movement_type=movement_type,
        reference_type=reference_type
    )
    
    # Mapear a esquema de respuesta
    movements_list = []
    for movement in movements:
        movement_dict = {
            "id": movement.id,
            "product_id": movement.product_id,
            "movement_type": movement.movement_type,
            "quantity": movement.quantity,
            "unit_cost": movement.unit_cost,
            "reference_type": movement.reference_type,
            "reference_id": movement.reference_id,
            "notes": movement.notes,
            "created_at": movement.created_at,
            "product_name": movement.product.name
        }
        movements_list.append(StockMovement.model_validate(movement_dict))
    
    return movements_list