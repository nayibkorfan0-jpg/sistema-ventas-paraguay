from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.sales import Quote, QuoteLine
from app.models.customer import Customer
from app.models.product import Product
from app.schemas.quote import QuoteCreate, QuoteUpdate, QuoteStatus

class QuoteCRUD:
    def get(self, db: Session, quote_id: int) -> Optional[Quote]:
        """Obtener cotización por ID"""
        return db.query(Quote).filter(Quote.id == quote_id).first()
    
    def get_by_number(self, db: Session, quote_number: str) -> Optional[Quote]:
        """Obtener cotización por número"""
        return db.query(Quote).filter(Quote.quote_number == quote_number).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        customer_id: Optional[int] = None,
        status: Optional[QuoteStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None
    ) -> List[Quote]:
        """Obtener múltiples cotizaciones con filtros"""
        query = db.query(Quote).join(Customer)
        
        if customer_id:
            query = query.filter(Quote.customer_id == customer_id)
        
        if status:
            query = query.filter(Quote.status == status.value)
        
        if date_from:
            query = query.filter(Quote.quote_date >= date_from)
        
        if date_to:
            query = query.filter(Quote.quote_date <= date_to)
        
        if search:
            search_filter = or_(
                Quote.quote_number.ilike(f"%{search}%"),
                Customer.company_name.ilike(f"%{search}%"),
                Quote.notes.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        return query.order_by(desc(Quote.created_at)).offset(skip).limit(limit).all()
    
    def create(self, db: Session, quote_in: QuoteCreate, created_by_id: int) -> Quote:
        """Crear nueva cotización"""
        # Generar número de cotización
        today = datetime.now()
        year_month = today.strftime("%Y%m")
        
        # Buscar el último número de cotización del mes
        last_quote = db.query(Quote).filter(
            Quote.quote_number.like(f"COT{year_month}%")
        ).order_by(desc(Quote.quote_number)).first()
        
        if last_quote:
            last_number = int(last_quote.quote_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
        
        quote_number = f"COT{year_month}{new_number:04d}"
        
        # Crear cotización
        db_quote = Quote(
            quote_number=quote_number,
            customer_id=quote_in.customer_id,
            quote_date=quote_in.quote_date,
            valid_until=quote_in.valid_until,
            status=QuoteStatus.draft.value,
            notes=quote_in.notes,
            terms_conditions=quote_in.terms_conditions,
            created_by_id=created_by_id
        )
        
        db.add(db_quote)
        db.flush()  # Para obtener el ID
        
        # Crear líneas de cotización
        total_subtotal = Decimal("0.00")
        for line_data in quote_in.lines:
            # Obtener información del producto
            product = db.query(Product).filter(Product.id == line_data.product_id).first()
            if not product:
                raise ValueError(f"Producto con ID {line_data.product_id} no encontrado")
            
            # Calcular total de la línea
            line_subtotal = Decimal(str(line_data.quantity)) * line_data.unit_price
            discount_amount = line_subtotal * (line_data.discount_percent / 100)
            line_total = line_subtotal - discount_amount
            
            db_line = QuoteLine(
                quote_id=db_quote.id,
                product_id=line_data.product_id,
                quantity=line_data.quantity,
                unit_price=line_data.unit_price,
                discount_percent=line_data.discount_percent,
                line_total=line_total,
                description=line_data.description
            )
            db.add(db_line)
            total_subtotal += line_total
        
        # Calcular totales - verificar exención de impuestos por régimen de turismo
        db_quote.subtotal = total_subtotal
        
        # Obtener información del cliente para verificar régimen de turismo
        customer = db.query(Customer).filter(Customer.id == quote_in.customer_id).first()
        
        # Verificar si cliente tiene régimen de turismo activo (no vencido)
        tax_exempt = False
        if customer and customer.tourism_regime:
            if customer.tourism_regime_expiry and customer.tourism_regime_expiry >= date.today():
                tax_exempt = True
        
        if tax_exempt:
            # Cliente con régimen de turismo válido - exento de impuestos
            db_quote.tax_amount = Decimal("0.00")
        else:
            # Aplicar IVA normal (16%)
            tax_rate = Decimal("0.16")
            db_quote.tax_amount = total_subtotal * tax_rate
            
        db_quote.total_amount = total_subtotal + db_quote.tax_amount
        
        db.commit()
        db.refresh(db_quote)
        return db_quote
    
    def update(self, db: Session, db_quote: Quote, quote_in: QuoteUpdate) -> Quote:
        """Actualizar cotización existente"""
        update_data = quote_in.dict(exclude_unset=True, exclude={"lines"})
        
        # Actualizar campos de la cotización
        for field, value in update_data.items():
            setattr(db_quote, field, value)
        
        # Si se proporcionan líneas, actualizar la lista completa
        if quote_in.lines is not None:
            # Eliminar líneas existentes
            db.query(QuoteLine).filter(QuoteLine.quote_id == db_quote.id).delete()
            
            # Crear nuevas líneas
            total_subtotal = Decimal("0.00")
            for line_data in quote_in.lines:
                # Obtener información del producto
                product = db.query(Product).filter(Product.id == line_data.product_id).first()
                if not product:
                    raise ValueError(f"Producto con ID {line_data.product_id} no encontrado")
                
                # Calcular total de la línea
                line_subtotal = Decimal(str(line_data.quantity)) * line_data.unit_price
                discount_amount = line_subtotal * (line_data.discount_percent / 100)
                line_total = line_subtotal - discount_amount
                
                db_line = QuoteLine(
                    quote_id=db_quote.id,
                    product_id=line_data.product_id,
                    quantity=line_data.quantity,
                    unit_price=line_data.unit_price,
                    discount_percent=line_data.discount_percent,
                    line_total=line_total,
                    description=line_data.description
                )
                db.add(db_line)
                total_subtotal += line_total
            
            # Recalcular totales - verificar exención de impuestos por régimen de turismo
            db_quote.subtotal = total_subtotal
            
            # Obtener información del cliente para verificar régimen de turismo
            customer = db.query(Customer).filter(Customer.id == db_quote.customer_id).first()
            
            # Verificar si cliente tiene régimen de turismo activo (no vencido)
            tax_exempt = False
            if customer and customer.tourism_regime:
                if customer.tourism_regime_expiry and customer.tourism_regime_expiry >= date.today():
                    tax_exempt = True
            
            if tax_exempt:
                # Cliente con régimen de turismo válido - exento de impuestos
                db_quote.tax_amount = Decimal("0.00")
            else:
                # Aplicar IVA normal (16%)
                tax_rate = Decimal("0.16")
                db_quote.tax_amount = total_subtotal * tax_rate
                
            db_quote.total_amount = total_subtotal + db_quote.tax_amount
        
        db.add(db_quote)
        db.commit()
        db.refresh(db_quote)
        return db_quote
    
    def update_status(self, db: Session, quote_id: int, status: QuoteStatus) -> Optional[Quote]:
        """Actualizar estado de cotización"""
        db_quote = self.get(db, quote_id)
        if db_quote:
            db_quote.status = status.value
            db.add(db_quote)
            db.commit()
            db.refresh(db_quote)
        return db_quote
    
    def delete(self, db: Session, quote_id: int) -> bool:
        """Eliminar cotización (solo si está en borrador)"""
        db_quote = self.get(db, quote_id)
        if db_quote and db_quote.status == QuoteStatus.draft.value:
            db.delete(db_quote)
            db.commit()
            return True
        return False
    
    def get_expired_quotes(self, db: Session) -> List[Quote]:
        """Obtener cotizaciones vencidas que no han sido marcadas como expiradas"""
        today = date.today()
        return db.query(Quote).filter(
            and_(
                Quote.valid_until < today,
                Quote.status.in_([QuoteStatus.draft.value, QuoteStatus.sent.value])
            )
        ).all()

# Instancia global
quote_crud = QuoteCRUD()