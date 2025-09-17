from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.sales import SalesOrder, SalesOrderLine, Quote, QuoteLine
from app.models.customer import Customer
from app.models.product import Product
from app.schemas.sales_order import SalesOrderCreate, SalesOrderUpdate, SalesOrderStatus

class SalesOrderCRUD:
    def get(self, db: Session, order_id: int) -> Optional[SalesOrder]:
        """Obtener orden por ID"""
        return db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    
    def get_by_number(self, db: Session, order_number: str) -> Optional[SalesOrder]:
        """Obtener orden por número"""
        return db.query(SalesOrder).filter(SalesOrder.order_number == order_number).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        customer_id: Optional[int] = None,
        status: Optional[SalesOrderStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None
    ) -> List[SalesOrder]:
        """Obtener múltiples órdenes con filtros"""
        query = db.query(SalesOrder).join(Customer)
        
        if customer_id:
            query = query.filter(SalesOrder.customer_id == customer_id)
        
        if status:
            query = query.filter(SalesOrder.status == status.value)
        
        if date_from:
            query = query.filter(SalesOrder.order_date >= date_from)
        
        if date_to:
            query = query.filter(SalesOrder.order_date <= date_to)
        
        if search:
            search_filter = or_(
                SalesOrder.order_number.ilike(f"%{search}%"),
                Customer.company_name.ilike(f"%{search}%"),
                SalesOrder.notes.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        return query.order_by(desc(SalesOrder.created_at)).offset(skip).limit(limit).all()
    
    def create(self, db: Session, order_in: SalesOrderCreate, created_by_id: int) -> SalesOrder:
        """Crear nueva orden de venta"""
        # Generar número de orden
        today = datetime.now()
        year_month = today.strftime("%Y%m")
        
        # Buscar el último número de orden del mes
        last_order = db.query(SalesOrder).filter(
            SalesOrder.order_number.like(f"ORD{year_month}%")
        ).order_by(desc(SalesOrder.order_number)).first()
        
        if last_order:
            last_number = int(last_order.order_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
        
        order_number = f"ORD{year_month}{new_number:04d}"
        
        # Crear orden
        db_order = SalesOrder(
            order_number=order_number,
            quote_id=order_in.quote_id,
            customer_id=order_in.customer_id,
            order_date=order_in.order_date,
            delivery_date=order_in.delivery_date,
            status=SalesOrderStatus.pending.value,
            shipping_cost=order_in.shipping_cost,
            shipping_address=order_in.shipping_address,
            notes=order_in.notes,
            created_by_id=created_by_id
        )
        
        db.add(db_order)
        db.flush()  # Para obtener el ID
        
        # Crear líneas de orden
        total_subtotal = Decimal("0.00")
        for line_data in order_in.lines:
            # Obtener información del producto
            product = db.query(Product).filter(Product.id == line_data.product_id).first()
            if not product:
                raise ValueError(f"Producto con ID {line_data.product_id} no encontrado")
            
            # Calcular total de la línea
            line_subtotal = Decimal(str(line_data.quantity)) * line_data.unit_price
            discount_amount = line_subtotal * (line_data.discount_percent / 100)
            line_total = line_subtotal - discount_amount
            
            db_line = SalesOrderLine(
                order_id=db_order.id,
                product_id=line_data.product_id,
                quantity=line_data.quantity,
                unit_price=line_data.unit_price,
                discount_percent=line_data.discount_percent,
                line_total=line_total,
                description=line_data.description,
                quantity_shipped=0,
                quantity_invoiced=0
            )
            db.add(db_line)
            total_subtotal += line_total
        
        # Calcular totales (IVA 16%)
        tax_rate = Decimal("0.16")
        db_order.subtotal = total_subtotal
        db_order.tax_amount = total_subtotal * tax_rate
        db_order.total_amount = total_subtotal + db_order.tax_amount + db_order.shipping_cost
        
        db.commit()
        db.refresh(db_order)
        return db_order
    
    def create_from_quote(self, db: Session, quote_id: int, created_by_id: int, 
                         delivery_date: Optional[date] = None,
                         shipping_address: Optional[str] = None) -> SalesOrder:
        """Crear orden de venta desde cotización"""
        # Obtener cotización
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise ValueError(f"Cotización con ID {quote_id} no encontrada")
        
        # Verificar que la cotización esté aceptada
        if quote.status.upper() != "ACCEPTED":
            raise ValueError("Solo se pueden convertir cotizaciones aceptadas a órdenes")
        
        # Generar número de orden
        today = datetime.now()
        year_month = today.strftime("%Y%m")
        
        last_order = db.query(SalesOrder).filter(
            SalesOrder.order_number.like(f"ORD{year_month}%")
        ).order_by(desc(SalesOrder.order_number)).first()
        
        if last_order:
            last_number = int(last_order.order_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
        
        order_number = f"ORD{year_month}{new_number:04d}"
        
        # Crear orden desde cotización
        db_order = SalesOrder(
            order_number=order_number,
            quote_id=quote_id,
            customer_id=quote.customer_id,
            order_date=date.today(),
            delivery_date=delivery_date,
            status=SalesOrderStatus.pending.value,
            subtotal=quote.subtotal,
            tax_amount=quote.tax_amount,
            total_amount=quote.total_amount,
            shipping_cost=Decimal("0.00"),
            shipping_address=shipping_address,
            notes=quote.notes,
            created_by_id=created_by_id
        )
        
        db.add(db_order)
        db.flush()
        
        # Copiar líneas de cotización
        for quote_line in quote.lines:
            db_line = SalesOrderLine(
                order_id=db_order.id,
                product_id=quote_line.product_id,
                quantity=quote_line.quantity,
                unit_price=quote_line.unit_price,
                discount_percent=quote_line.discount_percent,
                line_total=quote_line.line_total,
                description=quote_line.description,
                quantity_shipped=0,
                quantity_invoiced=0
            )
            db.add(db_line)
        
        db.commit()
        db.refresh(db_order)
        return db_order
    
    def update(self, db: Session, db_order: SalesOrder, order_in: SalesOrderUpdate) -> SalesOrder:
        """Actualizar orden existente"""
        update_data = order_in.dict(exclude_unset=True, exclude={"lines"})
        
        # Actualizar campos de la orden
        for field, value in update_data.items():
            if field == "status" and value:
                setattr(db_order, field, value.value)
            else:
                setattr(db_order, field, value)
        
        # Si se proporcionan líneas, actualizar la lista completa
        if order_in.lines is not None:
            # Solo permitir si está en estado pending
            if db_order.status != SalesOrderStatus.pending.value:
                raise ValueError("Solo se pueden actualizar líneas en órdenes pendientes")
            
            # Eliminar líneas existentes
            db.query(SalesOrderLine).filter(SalesOrderLine.order_id == db_order.id).delete()
            
            # Crear nuevas líneas
            total_subtotal = Decimal("0.00")
            for line_data in order_in.lines:
                # Obtener información del producto
                product = db.query(Product).filter(Product.id == line_data.product_id).first()
                if not product:
                    raise ValueError(f"Producto con ID {line_data.product_id} no encontrado")
                
                # Calcular total de la línea
                line_subtotal = Decimal(str(line_data.quantity)) * line_data.unit_price
                discount_amount = line_subtotal * (line_data.discount_percent / 100)
                line_total = line_subtotal - discount_amount
                
                db_line = SalesOrderLine(
                    order_id=db_order.id,
                    product_id=line_data.product_id,
                    quantity=line_data.quantity,
                    unit_price=line_data.unit_price,
                    discount_percent=line_data.discount_percent,
                    line_total=line_total,
                    description=line_data.description,
                    quantity_shipped=0,
                    quantity_invoiced=0
                )
                db.add(db_line)
                total_subtotal += line_total
            
            # Recalcular totales
            tax_rate = Decimal("0.16")
            db_order.subtotal = total_subtotal
            db_order.tax_amount = total_subtotal * tax_rate
            db_order.total_amount = total_subtotal + db_order.tax_amount + db_order.shipping_cost
        
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        return db_order
    
    def update_status(self, db: Session, order_id: int, new_status: SalesOrderStatus) -> Optional[SalesOrder]:
        """Actualizar estado de orden"""
        db_order = self.get(db, order_id)
        if db_order:
            db_order.status = new_status.value
            db.add(db_order)
            db.commit()
            db.refresh(db_order)
        return db_order
    
    def cancel(self, db: Session, order_id: int) -> bool:
        """Cancelar orden (solo si está pendiente o confirmada)"""
        db_order = self.get(db, order_id)
        if db_order and db_order.status in [SalesOrderStatus.pending.value, SalesOrderStatus.confirmed.value]:
            db_order.status = SalesOrderStatus.cancelled.value
            db.add(db_order)
            db.commit()
            return True
        return False

# Instancia global
sales_order_crud = SalesOrderCRUD()