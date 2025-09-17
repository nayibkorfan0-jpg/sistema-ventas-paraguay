from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, desc, asc
from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.models.invoice import Invoice, InvoiceLine, Payment
from app.models.customer import Customer
from app.models.sales import SalesOrder, SalesOrderLine
from app.models.product import Product
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceFromOrder,
    PaymentCreate, InvoiceStatus, PaymentMethod
)
from app.utils.paraguay_fiscal import ParaguayIVACalculator, ParaguayFiscalUtils
from app.crud.company import company_settings_crud

class InvoiceCRUD:
    def __init__(self):
        self.tax_rate = Decimal('0.16')  # 16% IVA

    def generate_invoice_number(self, db: Session) -> str:
        """Generar número de factura con formato paraguayo"""
        try:
            # Obtener configuración de empresa para punto de expedición
            company_settings = company_settings_crud.get_settings(db)
            if company_settings:
                # Obtener valores actuales, no objetos Column
                punto_expedicion_val = getattr(company_settings, 'punto_expedicion', None) or "001"
                numero_actual_val = getattr(company_settings, 'numeracion_facturas_actual', 1)
                
                # Formatear número paraguayo: 001-0000001
                invoice_number = ParaguayFiscalUtils.format_invoice_number(
                    numero_actual_val, punto_expedicion_val
                )
                
                # Actualizar contador en la configuración
                company_settings_crud.increment_invoice_number(db)
                
                return invoice_number
            else:
                # Fallback si no hay configuración
                today = date.today()
                year = today.year
                month = today.month
                prefix = f"FAC{year}{month:02d}"
                return f"{prefix}0001"
        except Exception:
            # Fallback en caso de error
            today = date.today()
            year = today.year
            month = today.month
            prefix = f"FAC{year}{month:02d}"
            return f"{prefix}0001"

    def create_invoice(self, db: Session, invoice: InvoiceCreate, created_by_id: int) -> Invoice:
        """Crear nueva factura con líneas"""
        # Generar número de factura
        invoice_number = self.generate_invoice_number(db)
        
        # Obtener configuración de empresa para tasas de IVA
        company_settings = company_settings_crud.get_settings(db)
        # Obtener valores actuales, no objetos Column
        iva_10_val = getattr(company_settings, 'iva_10_porciento', None) if company_settings else None
        iva_5_val = getattr(company_settings, 'iva_5_porciento', None) if company_settings else None
        iva_10_rate = Decimal(str(iva_10_val)) if iva_10_val is not None else Decimal('10.00')
        iva_5_rate = Decimal(str(iva_5_val)) if iva_5_val is not None else Decimal('5.00')
        
        # Obtener información del cliente para verificar régimen de turismo
        customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
        
        # Preparar líneas para cálculo paraguayo
        lines_data = []
        for line in invoice.lines:
            line_total = line.quantity * line.unit_price
            if line.discount_percent > 0:
                line_total = line_total * (1 - line.discount_percent / 100)
            
            lines_data.append({
                "line_total": line_total,
                "iva_category": getattr(line, 'iva_category', '10')
            })
        
        # Calcular totales paraguayos
        totals = ParaguayIVACalculator.calculate_iva_breakdown(
            lines_data, iva_10_rate, iva_5_rate
        )
        
        # Aplicar régimen turístico si corresponde
        tourism_regime_applied = False
        tourism_regime_percentage = Decimal('0')
        if customer and bool(customer.tourism_regime):  # type: ignore
            if customer.tourism_regime_expiry and customer.tourism_regime_expiry >= date.today():  # type: ignore
                tourism_regime_applied = True
                tourism_regime_percentage = Decimal('100')  # 100% exención
                totals = ParaguayIVACalculator.apply_tourism_regime(
                    totals, tourism_regime_percentage
                )
        
        subtotal = totals['subtotal']
        tax_amount = totals['total_iva']
        total_amount = totals['total']
        
        # Obtener configuración adicional para campos paraguayos
        punto_expedicion_val = getattr(company_settings, 'punto_expedicion', None) if company_settings else None
        lugar_emision_val = getattr(company_settings, 'ciudad', None) if company_settings else None
        punto_expedicion = str(punto_expedicion_val) if punto_expedicion_val is not None else "001"
        lugar_emision = str(lugar_emision_val) if lugar_emision_val is not None else "Asunción"
        
        # Crear factura con campos paraguayos
        db_invoice = Invoice(
            invoice_number=invoice_number,
            sales_order_id=invoice.sales_order_id,
            customer_id=invoice.customer_id,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            status=InvoiceStatus.PENDING,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            paid_amount=Decimal('0'),
            balance_due=total_amount,
            notes=invoice.notes,
            payment_terms=invoice.payment_terms,
            
            # CAMPOS FISCALES ESPECÍFICOS PARA PARAGUAY
            punto_expedicion=punto_expedicion,
            condicion_venta=getattr(invoice, 'condicion_venta', 'CREDITO'),
            lugar_emision=lugar_emision,
            
            # DESGLOSE DE IVA PARAGUAYO
            subtotal_gravado_10=totals['subtotal_gravado_10'],
            subtotal_gravado_5=totals['subtotal_gravado_5'],
            subtotal_exento=totals['subtotal_exento'],
            iva_10=totals['iva_10'],
            iva_5=totals['iva_5'],
            
            # RÉGIMEN DE TURISMO PARAGUAY
            tourism_regime_applied=tourism_regime_applied,
            tourism_regime_percentage=tourism_regime_percentage,
        )
        
        db.add(db_invoice)
        db.flush()  # Para obtener el ID
        
        # Crear líneas de factura con campos paraguayos
        for i, line in enumerate(invoice.lines):
            line_total = line.quantity * line.unit_price
            if line.discount_percent > 0:
                line_total = line_total * (1 - line.discount_percent / 100)
            
            # Calcular IVA por línea
            iva_category = getattr(line, 'iva_category', '10')
            iva_amount = Decimal('0')
            
            if iva_category == '10':
                iva_amount = line_total * (iva_10_rate / Decimal('100'))
            elif iva_category == '5':
                iva_amount = line_total * (iva_5_rate / Decimal('100'))
            # Para 'EXENTO', iva_amount permanece en 0
                
            db_line = InvoiceLine(
                invoice_id=db_invoice.id,
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_percent=line.discount_percent,
                line_total=line_total,
                description=line.description,
                
                # CAMPOS FISCALES PARA IVA PARAGUAYO
                iva_category=iva_category,
                iva_amount=iva_amount
            )
            db.add(db_line)
        
        db.commit()
        db.refresh(db_invoice)
        return db_invoice

    def create_from_sales_order(self, db: Session, invoice_data: InvoiceFromOrder, created_by_id: int) -> Invoice:
        """Crear factura desde orden de venta"""
        # Obtener la orden de venta con sus líneas
        sales_order = db.query(SalesOrder).options(
            joinedload(SalesOrder.lines)
        ).filter(SalesOrder.id == invoice_data.sales_order_id).first()
        
        if not sales_order:
            raise ValueError("Orden de venta no encontrada")
        
        if sales_order.status not in ["CONFIRMED", "SHIPPED", "DELIVERED"]:
            raise ValueError("Solo se pueden facturar órdenes confirmadas, enviadas o entregadas")
        
        # Verificar si ya existe una factura para esta orden
        existing_invoice = db.query(Invoice).filter(
            Invoice.sales_order_id == sales_order.id
        ).first()
        
        if existing_invoice:
            raise ValueError(f"Ya existe una factura ({existing_invoice.invoice_number}) para esta orden")
        
        # Crear líneas de factura desde las líneas de la orden
        invoice_lines = []
        for order_line in sales_order.lines:
            invoice_lines.append({
                'product_id': getattr(order_line, 'product_id', 0),
                'quantity': getattr(order_line, 'quantity', 0),
                'unit_price': getattr(order_line, 'unit_price', Decimal('0')),
                'discount_percent': getattr(order_line, 'discount_percent', Decimal('0')),
                'description': getattr(order_line, 'description', None)
            })
        
        # Crear objeto InvoiceCreate
        # Type conversions to handle SQLAlchemy model attributes
        # Using getattr to safely access SQLAlchemy model properties
        sales_order_id_val = getattr(sales_order, 'id', None)
        customer_id_val = getattr(sales_order, 'customer_id', None)
        
        # Ensure proper type handling for required fields
        if customer_id_val is None:
            raise ValueError("Customer ID is required")
            
        invoice_create = InvoiceCreate(
            sales_order_id=sales_order_id_val,
            customer_id=customer_id_val,
            invoice_date=invoice_data.invoice_date or date.today(),
            due_date=invoice_data.due_date or date.today(),
            payment_terms=invoice_data.payment_terms,
            notes=invoice_data.notes,
            lines=invoice_lines
        )
        
        return self.create_invoice(db, invoice_create, created_by_id)

    def get_invoice(self, db: Session, invoice_id: int) -> Optional[Invoice]:
        """Obtener factura por ID con detalles"""
        return db.query(Invoice).options(
            joinedload(Invoice.customer),
            joinedload(Invoice.sales_order),
            joinedload(Invoice.lines).joinedload(InvoiceLine.product),
            joinedload(Invoice.payments)
        ).filter(Invoice.id == invoice_id).first()

    def get_invoices(self, db: Session, skip: int = 0, limit: int = 100, 
                    customer_id: Optional[int] = None,
                    status: Optional[InvoiceStatus] = None,
                    start_date: Optional[date] = None,
                    end_date: Optional[date] = None) -> List[Invoice]:
        """Obtener lista de facturas con filtros"""
        query = db.query(Invoice).join(Customer)
        
        # Aplicar filtros
        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)
        
        if status:
            query = query.filter(Invoice.status == status)
        
        if start_date:
            query = query.filter(Invoice.invoice_date >= start_date)
            
        if end_date:
            query = query.filter(Invoice.invoice_date <= end_date)
        
        return query.order_by(desc(Invoice.created_at)).offset(skip).limit(limit).all()

    def update_invoice(self, db: Session, invoice_id: int, invoice_update: InvoiceUpdate) -> Optional[Invoice]:
        """Actualizar factura"""
        db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not db_invoice:
            return None
        
        # Actualizar campos
        for field, value in invoice_update.dict(exclude_unset=True).items():
            setattr(db_invoice, field, value)
        
        db.commit()
        db.refresh(db_invoice)
        return db_invoice

    def add_payment(self, db: Session, payment: PaymentCreate) -> Payment:
        """Agregar pago a una factura"""
        # Verificar que la factura existe
        invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
        if not invoice:
            raise ValueError("Factura no encontrada")
        
        # Crear el pago
        db_payment = Payment(
            invoice_id=payment.invoice_id,
            payment_date=payment.payment_date,
            amount=payment.amount,
            payment_method=payment.payment_method,
            reference_number=payment.reference_number,
            notes=payment.notes
        )
        
        db.add(db_payment)
        
        # Actualizar montos de la factura
        current_paid_amount = Decimal(str(invoice.paid_amount))
        total_amount = Decimal(str(invoice.total_amount))
        current_status = str(invoice.status)
        
        new_paid_amount = current_paid_amount + payment.amount
        new_balance_due = total_amount - new_paid_amount
        
        # Actualizar estado si está completamente pagada
        new_status = current_status
        if new_balance_due <= Decimal('0'):
            new_status = InvoiceStatus.PAID.value
        elif new_paid_amount > Decimal('0') and current_status == InvoiceStatus.PENDING.value:
            new_status = InvoiceStatus.SENT.value
        
        # Actualizar factura
        setattr(invoice, 'paid_amount', new_paid_amount)
        setattr(invoice, 'balance_due', max(new_balance_due, Decimal('0')))
        setattr(invoice, 'status', new_status)
        
        db.commit()
        db.refresh(db_payment)
        return db_payment

    def get_invoice_summary(self, db: Session, 
                          start_date: Optional[date] = None,
                          end_date: Optional[date] = None) -> dict:
        """Obtener resumen de facturas"""
        query = db.query(Invoice)
        
        if start_date:
            query = query.filter(Invoice.invoice_date >= start_date)
        if end_date:
            query = query.filter(Invoice.invoice_date <= end_date)
        
        invoices = query.all()
        
        total_invoices = len(invoices)
        total_amount = sum(inv.total_amount for inv in invoices)
        paid_amount = sum(inv.paid_amount for inv in invoices)
        pending_amount = sum(Decimal(str(inv.balance_due)) for inv in invoices if str(inv.status) in [InvoiceStatus.PENDING.value, InvoiceStatus.SENT.value])
        overdue_amount = sum(Decimal(str(inv.balance_due)) for inv in invoices if str(inv.status) == InvoiceStatus.OVERDUE.value)
        
        return {
            "total_invoices": total_invoices,
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "pending_amount": pending_amount,
            "overdue_amount": overdue_amount
        }

    def update_overdue_invoices(self, db: Session) -> int:
        """Actualizar facturas vencidas (ejecutar diariamente)"""
        today = date.today()
        
        overdue_invoices = db.query(Invoice).filter(
            and_(
                Invoice.due_date < today,
                Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.SENT]),
                Invoice.balance_due > 0
            )
        ).all()
        
        count = 0
        for invoice in overdue_invoices:
            setattr(invoice, 'status', InvoiceStatus.OVERDUE.value)
            count += 1
        
        if count > 0:
            db.commit()
        
        return count

# Instancia global
invoice_crud = InvoiceCRUD()