from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, desc, asc
from typing import List, Optional, Any
from datetime import date, datetime
from decimal import Decimal

from app.models.deposit import Deposit, DepositApplication, CustomerDepositSummary, DepositType, DepositStatus
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.deposit import (
    DepositCreate, DepositUpdate, DepositApplicationCreate,
    ApplyDepositToInvoice, RefundDeposit, Currency
)

class DepositCRUD:
    def __init__(self):
        pass

    def generate_deposit_number(self, db: Session) -> str:
        """Generar número de depósito con formato DEP2025090001"""
        today = date.today()
        year = today.year
        month = today.month
        
        # Buscar el último número de depósito del mes actual
        prefix = f"DEP{year}{month:02d}"
        last_deposit = db.query(Deposit).filter(
            Deposit.deposit_number.like(f"{prefix}%")
        ).order_by(desc(Deposit.deposit_number)).first()
        
        if last_deposit:
            # Extraer el número secuencial del último número
            deposit_number_str = str(last_deposit.deposit_number)
            last_number = int(deposit_number_str[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"{prefix}{new_number:04d}"

    def create_deposit(self, db: Session, deposit: DepositCreate, created_by_id: int) -> Deposit:
        """Crear nuevo depósito"""
        # Verificar que el cliente existe
        customer = db.query(Customer).filter(Customer.id == deposit.customer_id).first()
        if not customer:
            raise ValueError("Cliente no encontrado")
        
        # Generar número de depósito
        deposit_number = self.generate_deposit_number(db)
        
        # Crear depósito
        db_deposit = Deposit(
            deposit_number=deposit_number,
            customer_id=deposit.customer_id,
            deposit_type=deposit.deposit_type,
            amount=deposit.amount,
            currency=deposit.currency,
            deposit_date=deposit.deposit_date,
            expiry_date=deposit.expiry_date,
            status=DepositStatus.ACTIVE,
            applied_amount=Decimal('0'),
            available_amount=deposit.amount,
            payment_method=deposit.payment_method,
            reference_number=deposit.reference_number,
            bank_name=deposit.bank_name,
            notes=deposit.notes,
            project_reference=deposit.project_reference,
            contract_number=deposit.contract_number,
            created_by_id=created_by_id
        )
        
        db.add(db_deposit)
        db.commit()
        db.refresh(db_deposit)
        
        # Actualizar resumen del cliente
        self.update_customer_deposit_summary(db, int(deposit.customer_id))  # type: ignore
        
        return db_deposit

    def get_deposit(self, db: Session, deposit_id: int) -> Optional[Deposit]:
        """Obtener depósito por ID con detalles"""
        return db.query(Deposit).options(
            joinedload(Deposit.customer),
            joinedload(Deposit.created_by),
            joinedload(Deposit.applications)
        ).filter(Deposit.id == deposit_id).first()

    def get_deposits(self, db: Session, skip: int = 0, limit: int = 100,
                    customer_id: Optional[int] = None,
                    status: Optional[str] = None,
                    deposit_type: Optional[str] = None,
                    currency: Optional[str] = None,
                    start_date: Optional[date] = None,
                    end_date: Optional[date] = None) -> List[Deposit]:
        """Obtener lista de depósitos con filtros"""
        query = db.query(Deposit).join(Customer)
        
        # Aplicar filtros
        if customer_id:
            query = query.filter(Deposit.customer_id == customer_id)
        
        if status:
            query = query.filter(Deposit.status == status)
            
        if deposit_type:
            query = query.filter(Deposit.deposit_type == deposit_type)
            
        if currency:
            query = query.filter(Deposit.currency == currency)
        
        if start_date:
            query = query.filter(Deposit.deposit_date >= start_date)
            
        if end_date:
            query = query.filter(Deposit.deposit_date <= end_date)
        
        return query.order_by(desc(Deposit.created_at)).offset(skip).limit(limit).all()

    def update_deposit(self, db: Session, deposit_id: int, deposit_update: DepositUpdate) -> Optional[Deposit]:
        """Actualizar depósito"""
        db_deposit = db.query(Deposit).filter(Deposit.id == deposit_id).first()
        
        if not db_deposit:
            return None
        
        # Actualizar campos
        for field, value in deposit_update.dict(exclude_unset=True).items():
            setattr(db_deposit, field, value)
        
        db.commit()
        db.refresh(db_deposit)
        return db_deposit

    def apply_deposit_to_invoice(self, db: Session, application: ApplyDepositToInvoice, applied_by_id: int) -> DepositApplication:
        """Aplicar depósito a una factura"""
        # Verificar que el depósito existe y está activo
        deposit = db.query(Deposit).filter(Deposit.id == application.deposit_id).first()
        if not deposit:
            raise ValueError("Depósito no encontrado")
        
        if str(deposit.status) != DepositStatus.ACTIVE:  # type: ignore
            raise ValueError("Solo se pueden aplicar depósitos activos")
        
        # Verificar que la factura existe
        invoice = db.query(Invoice).filter(Invoice.id == application.invoice_id).first()
        if not invoice:
            raise ValueError("Factura no encontrada")
        
        # Verificar que el depósito y la factura son del mismo cliente
        if int(deposit.customer_id) != int(invoice.customer_id):  # type: ignore
            raise ValueError("El depósito y la factura deben ser del mismo cliente")
        
        # Verificar que las monedas coinciden
        if str(deposit.currency) != str(invoice.currency):  # type: ignore
            raise ValueError(f"La moneda del depósito ({deposit.currency}) no coincide con la moneda de la factura ({invoice.currency})")
        
        # Verificar que hay saldo disponible
        available_amt = Decimal(str(deposit.available_amount))  # type: ignore
        if application.amount_to_apply > available_amt:
            raise ValueError(f"Monto a aplicar ({application.amount_to_apply}) excede el disponible ({available_amt})")
        
        # Verificar que no excede el balance de la factura
        balance_due = Decimal(str(invoice.balance_due))  # type: ignore
        if application.amount_to_apply > balance_due:
            raise ValueError(f"Monto a aplicar ({application.amount_to_apply}) excede el balance de la factura ({balance_due})")
        
        # Crear la aplicación
        db_application = DepositApplication(
            deposit_id=application.deposit_id,
            invoice_id=application.invoice_id,
            amount_applied=application.amount_to_apply,
            application_date=date.today(),
            notes=application.notes,
            applied_by_id=applied_by_id
        )
        
        db.add(db_application)
        
        # Actualizar el depósito
        new_applied = Decimal(str(deposit.applied_amount)) + application.amount_to_apply  # type: ignore
        new_available = Decimal(str(deposit.available_amount)) - application.amount_to_apply  # type: ignore
        deposit.applied_amount = new_applied  # type: ignore
        deposit.available_amount = new_available  # type: ignore
        
        # Si el depósito se agotó, cambiar estado
        if new_available <= 0:
            deposit.status = DepositStatus.APPLIED  # type: ignore
        
        # Actualizar la factura
        new_paid = Decimal(str(invoice.paid_amount)) + application.amount_to_apply  # type: ignore
        new_balance = Decimal(str(invoice.balance_due)) - application.amount_to_apply  # type: ignore
        invoice.paid_amount = new_paid  # type: ignore
        invoice.balance_due = new_balance  # type: ignore
        
        # Actualizar estado de la factura si está totalmente pagada
        if new_balance <= 0:
            invoice.status = "PAID"  # type: ignore
        
        db.commit()
        db.refresh(db_application)
        
        # Actualizar resumen del cliente
        self.update_customer_deposit_summary(db, int(deposit.customer_id))  # type: ignore
        
        return db_application

    def refund_deposit(self, db: Session, deposit_id: int, refund_data: RefundDeposit, refunded_by_id: int) -> Deposit:
        """Devolver depósito (total o parcial)"""
        deposit = db.query(Deposit).filter(Deposit.id == deposit_id).first()
        if not deposit:
            raise ValueError("Depósito no encontrado")
        
        if str(deposit.status) not in [DepositStatus.ACTIVE, DepositStatus.APPLIED]:  # type: ignore
            raise ValueError("Solo se pueden devolver depósitos activos o aplicados")
        
        # Verificar que no excede el monto disponible
        available_amt = Decimal(str(deposit.available_amount))  # type: ignore
        if refund_data.refund_amount > available_amt:
            raise ValueError(f"Monto a devolver ({refund_data.refund_amount}) excede el disponible ({available_amt})")
        
        # Actualizar el depósito
        current_available = Decimal(str(deposit.available_amount))  # type: ignore
        new_available = current_available - refund_data.refund_amount
        deposit.available_amount = new_available  # type: ignore
        
        # Si se devolvió todo el saldo disponible, cambiar estado
        if new_available <= 0:
            deposit.status = DepositStatus.REFUNDED  # type: ignore
        
        # Agregar nota de devolución
        refund_note = f"DEVOLUCIÓN: {refund_data.refund_amount} {str(deposit.currency)} - {refund_data.refund_reason}"  # type: ignore
        current_notes = str(deposit.notes) if deposit.notes else None  # type: ignore
        if current_notes:
            deposit.notes = f"{current_notes}\n{refund_note}"  # type: ignore
        else:
            deposit.notes = refund_note  # type: ignore
        
        db.commit()
        db.refresh(deposit)
        
        # Actualizar resumen del cliente
        self.update_customer_deposit_summary(db, int(deposit.customer_id))  # type: ignore
        
        return deposit

    def get_customer_deposits(self, db: Session, customer_id: int, active_only: bool = False) -> List[Deposit]:
        """Obtener depósitos de un cliente específico"""
        query = db.query(Deposit).filter(Deposit.customer_id == customer_id)
        
        if active_only:
            query = query.filter(Deposit.status == DepositStatus.ACTIVE)
        
        return query.order_by(desc(Deposit.created_at)).all()

    def get_customer_deposit_summary(self, db: Session, customer_id: int) -> Optional[CustomerDepositSummary]:
        """Obtener resumen de depósitos de un cliente"""
        return db.query(CustomerDepositSummary).filter(
            CustomerDepositSummary.customer_id == customer_id
        ).first()

    def update_customer_deposit_summary(self, db: Session, customer_id: int):
        """Actualizar resumen de depósitos de un cliente"""
        # Calcular saldos por moneda
        pyg_totals = db.query(
            func.coalesce(func.sum(Deposit.amount), 0).label('total'),
            func.coalesce(func.sum(Deposit.available_amount), 0).label('available'),
            func.coalesce(func.sum(Deposit.applied_amount), 0).label('applied'),
            func.count(Deposit.id).label('count'),
            func.count(Deposit.id).filter(Deposit.status == DepositStatus.ACTIVE).label('active_count')
        ).filter(
            Deposit.customer_id == customer_id,
            Deposit.currency == 'PYG'
        ).first()
        
        usd_totals = db.query(
            func.coalesce(func.sum(Deposit.amount), 0).label('total'),
            func.coalesce(func.sum(Deposit.available_amount), 0).label('available'),
            func.coalesce(func.sum(Deposit.applied_amount), 0).label('applied'),
            func.count(Deposit.id).label('count'),
            func.count(Deposit.id).filter(Deposit.status == DepositStatus.ACTIVE).label('active_count')
        ).filter(
            Deposit.customer_id == customer_id,
            Deposit.currency == 'USD'
        ).first()
        
        # Obtener fechas importantes
        last_deposit = db.query(func.max(Deposit.deposit_date)).filter(
            Deposit.customer_id == customer_id
        ).scalar()
        
        last_application = db.query(func.max(DepositApplication.application_date)).join(
            Deposit
        ).filter(Deposit.customer_id == customer_id).scalar()
        
        # Buscar resumen existente o crear nuevo
        summary = db.query(CustomerDepositSummary).filter(
            CustomerDepositSummary.customer_id == customer_id
        ).first()
        
        if not summary:
            summary = CustomerDepositSummary(customer_id=customer_id)
            db.add(summary)
        
        # Actualizar valores
        summary.total_deposits_pyg = Decimal(str(getattr(pyg_totals, 'total', 0) or 0))  # type: ignore
        summary.available_deposits_pyg = Decimal(str(getattr(pyg_totals, 'available', 0) or 0))  # type: ignore
        summary.applied_deposits_pyg = Decimal(str(getattr(pyg_totals, 'applied', 0) or 0))  # type: ignore
        
        summary.total_deposits_usd = Decimal(str(getattr(usd_totals, 'total', 0) or 0))  # type: ignore
        summary.available_deposits_usd = Decimal(str(getattr(usd_totals, 'available', 0) or 0))  # type: ignore
        summary.applied_deposits_usd = Decimal(str(getattr(usd_totals, 'applied', 0) or 0))  # type: ignore
        
        pyg_count = int(getattr(pyg_totals, 'count', 0) or 0)
        usd_count = int(getattr(usd_totals, 'count', 0) or 0)
        summary.total_deposits_count = pyg_count + usd_count  # type: ignore
        
        pyg_active = int(getattr(pyg_totals, 'active_count', 0) or 0)
        usd_active = int(getattr(usd_totals, 'active_count', 0) or 0)
        summary.active_deposits_count = pyg_active + usd_active  # type: ignore
        
        summary.last_deposit_date = last_deposit  # type: ignore
        summary.last_application_date = last_application  # type: ignore
        summary.updated_at = datetime.now()  # type: ignore
        
        db.commit()

# Instancia global
deposit_crud = DepositCRUD()