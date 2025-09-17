from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_database
from app.core.dependencies import get_current_active_user, check_user_limits
from app.crud.sales_order import sales_order_crud
from app.crud.quote import quote_crud
from app.schemas.sales_order import (
    SalesOrder, SalesOrderCreate, SalesOrderUpdate, SalesOrderList, 
    SalesOrderStatus, SalesOrderLine, parse_sales_order_status
)
from app.models.user import User

router = APIRouter(prefix="/sales-orders", tags=["órdenes de venta"])

@router.get("/", response_model=List[SalesOrderList])
def list_sales_orders(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    status: Optional[SalesOrderStatus] = Query(None, description="Filtrar por estado"),
    date_from: Optional[date] = Query(None, description="Fecha desde"),
    date_to: Optional[date] = Query(None, description="Fecha hasta"),
    search: Optional[str] = Query(None, description="Buscar por número, cliente o notas")
):
    """Obtener lista de órdenes de venta con filtros opcionales"""
    orders = sales_order_crud.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        search=search
    )
    
    # Mapear a SalesOrderList
    orders_list = []
    for order in orders:
        order_list = SalesOrderList(
            id=order.id,
            order_number=order.order_number,
            customer_id=order.customer_id,
            customer_name=order.customer.company_name if order.customer else "",
            order_date=order.order_date,
            delivery_date=order.delivery_date,
            status=parse_sales_order_status(str(order.status)),
            total_amount=order.total_amount,
            created_at=order.created_at
        )
        orders_list.append(order_list)
    
    return orders_list

@router.get("/{order_id}", response_model=SalesOrder)
def get_sales_order(
    order_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener orden de venta específica por ID"""
    order = sales_order_crud.get(db=db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de venta no encontrada"
        )
    
    # Convertir a esquema de respuesta
    order_response = SalesOrder(
        id=order.id,
        order_number=order.order_number,
        quote_id=order.quote_id,
        customer_id=order.customer_id,
        order_date=order.order_date,
        delivery_date=order.delivery_date,
        status=parse_sales_order_status(str(order.status)),
        subtotal=order.subtotal,
        tax_amount=order.tax_amount,
        total_amount=order.total_amount,
        shipping_cost=order.shipping_cost,
        shipping_address=order.shipping_address,
        notes=order.notes,
        created_by_id=order.created_by_id,
        created_at=order.created_at,
        updated_at=order.updated_at,
        lines=[],
        customer_name=order.customer.company_name if order.customer else "",
        customer_email=order.customer.email if order.customer else ""
    )
    
    # Agregar líneas
    for line in order.lines:
        order_line = SalesOrderLine(
            id=line.id,
            order_id=line.order_id,
            product_id=line.product_id,
            quantity=line.quantity,
            unit_price=line.unit_price,
            discount_percent=line.discount_percent,
            line_total=line.line_total,
            description=line.description,
            quantity_shipped=line.quantity_shipped,
            quantity_invoiced=line.quantity_invoiced
        )
        order_response.lines.append(order_line)
    
    return order_response

@router.post("/", response_model=SalesOrder)
def create_sales_order(
    order_in: SalesOrderCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
    _: User = Depends(check_user_limits('orders'))
):
    """Crear nueva orden de venta"""
    try:
        order = sales_order_crud.create(
            db=db,
            order_in=order_in,
            created_by_id=int(current_user.id)
        )
        
        # Obtener la orden completa con relaciones
        created_order = sales_order_crud.get(db=db, order_id=int(order.id))
        if not created_order:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener la orden creada"
            )
        
        # Convertir a esquema de respuesta
        order_response = SalesOrder(
            id=created_order.id,
            order_number=created_order.order_number,
            quote_id=created_order.quote_id,
            customer_id=created_order.customer_id,
            order_date=created_order.order_date,
            delivery_date=created_order.delivery_date,
            status=parse_sales_order_status(str(created_order.status)),
            subtotal=created_order.subtotal,
            tax_amount=created_order.tax_amount,
            total_amount=created_order.total_amount,
            shipping_cost=created_order.shipping_cost,
            shipping_address=created_order.shipping_address,
            notes=created_order.notes,
            created_by_id=created_order.created_by_id,
            created_at=created_order.created_at,
            updated_at=created_order.updated_at,
            lines=[],
            customer_name=created_order.customer.company_name if created_order.customer else "",
            customer_email=created_order.customer.email if created_order.customer else ""
        )
        
        # Agregar líneas
        for line in created_order.lines:
            order_line = SalesOrderLine(
                id=line.id,
                order_id=line.order_id,
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_percent=line.discount_percent,
                line_total=line.line_total,
                description=line.description,
                quantity_shipped=line.quantity_shipped,
                quantity_invoiced=line.quantity_invoiced
            )
            order_response.lines.append(order_line)
        
        return order_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/from-quote/{quote_id}", response_model=SalesOrder)
def create_order_from_quote(
    quote_id: int,
    delivery_date: Optional[date] = Query(None, description="Fecha de entrega"),
    shipping_address: Optional[str] = Query(None, description="Dirección de envío"),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Crear orden de venta desde cotización aceptada"""
    try:
        order = sales_order_crud.create_from_quote(
            db=db,
            quote_id=quote_id,
            created_by_id=int(current_user.id),
            delivery_date=delivery_date,
            shipping_address=shipping_address
        )
        
        # Obtener la orden completa con relaciones
        created_order = sales_order_crud.get(db=db, order_id=int(order.id))
        if not created_order:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener la orden creada desde cotización"
            )
        
        # Convertir a esquema de respuesta
        order_response = SalesOrder(
            id=created_order.id,
            order_number=created_order.order_number,
            quote_id=created_order.quote_id,
            customer_id=created_order.customer_id,
            order_date=created_order.order_date,
            delivery_date=created_order.delivery_date,
            status=parse_sales_order_status(str(created_order.status)),
            subtotal=created_order.subtotal,
            tax_amount=created_order.tax_amount,
            total_amount=created_order.total_amount,
            shipping_cost=created_order.shipping_cost,
            shipping_address=created_order.shipping_address,
            notes=created_order.notes,
            created_by_id=created_order.created_by_id,
            created_at=created_order.created_at,
            updated_at=created_order.updated_at,
            lines=[],
            customer_name=created_order.customer.company_name if created_order.customer else "",
            customer_email=created_order.customer.email if created_order.customer else ""
        )
        
        # Agregar líneas
        for line in created_order.lines:
            order_line = SalesOrderLine(
                id=line.id,
                order_id=line.order_id,
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_percent=line.discount_percent,
                line_total=line.line_total,
                description=line.description,
                quantity_shipped=line.quantity_shipped,
                quantity_invoiced=line.quantity_invoiced
            )
            order_response.lines.append(order_line)
        
        return order_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{order_id}", response_model=SalesOrder)
def update_sales_order(
    order_id: int,
    order_in: SalesOrderUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar orden de venta existente"""
    db_order = sales_order_crud.get(db=db, order_id=order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de venta no encontrada"
        )
    
    try:
        order = sales_order_crud.update(db=db, db_order=db_order, order_in=order_in)
        
        # Obtener la orden actualizada con relaciones
        updated_order = sales_order_crud.get(db=db, order_id=int(order.id))
        if not updated_order:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener la orden actualizada"
            )
        
        # Convertir a esquema de respuesta
        order_response = SalesOrder(
            id=updated_order.id,
            order_number=updated_order.order_number,
            quote_id=updated_order.quote_id,
            customer_id=updated_order.customer_id,
            order_date=updated_order.order_date,
            delivery_date=updated_order.delivery_date,
            status=parse_sales_order_status(str(updated_order.status)),
            subtotal=updated_order.subtotal,
            tax_amount=updated_order.tax_amount,
            total_amount=updated_order.total_amount,
            shipping_cost=updated_order.shipping_cost,
            shipping_address=updated_order.shipping_address,
            notes=updated_order.notes,
            created_by_id=updated_order.created_by_id,
            created_at=updated_order.created_at,
            updated_at=updated_order.updated_at,
            lines=[],
            customer_name=updated_order.customer.company_name if updated_order.customer else "",
            customer_email=updated_order.customer.email if updated_order.customer else ""
        )
        
        # Agregar líneas
        for line in updated_order.lines:
            order_line = SalesOrderLine(
                id=line.id,
                order_id=line.order_id,
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_percent=line.discount_percent,
                line_total=line.line_total,
                description=line.description,
                quantity_shipped=line.quantity_shipped,
                quantity_invoiced=line.quantity_invoiced
            )
            order_response.lines.append(order_line)
        
        return order_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    new_status: SalesOrderStatus,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar estado de orden de venta"""
    order = sales_order_crud.update_status(db=db, order_id=order_id, new_status=new_status)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de venta no encontrada"
        )
    
    return {"message": f"Estado de orden actualizado a {new_status.value}"}

@router.delete("/{order_id}")
def cancel_sales_order(
    order_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Cancelar orden de venta (solo si está pendiente o confirmada)"""
    success = sales_order_crud.cancel(db=db, order_id=order_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede cancelar la orden. Solo se permiten cancelar órdenes pendientes o confirmadas."
        )
    
    return {"message": "Orden de venta cancelada exitosamente"}