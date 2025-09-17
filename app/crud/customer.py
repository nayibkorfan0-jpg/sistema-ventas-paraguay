from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.customer import Customer, Contact
from app.schemas.customer import CustomerCreate, CustomerUpdate, ContactCreate, ContactUpdate

class CustomerCRUD:
    def get(self, db: Session, customer_id: int) -> Optional[Customer]:
        """Obtener cliente por ID"""
        return db.query(Customer).filter(Customer.id == customer_id).first()
    
    def get_by_code(self, db: Session, customer_code: str) -> Optional[Customer]:
        """Obtener cliente por código"""
        return db.query(Customer).filter(Customer.customer_code == customer_code).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[Customer]:
        """Obtener cliente por email"""
        return db.query(Customer).filter(Customer.email == email).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Customer]:
        """Obtener múltiples clientes con filtros opcionales"""
        query = db.query(Customer)
        
        if is_active is not None:
            query = query.filter(Customer.is_active == is_active)
        
        if search:
            search_filter = or_(
                Customer.company_name.ilike(f"%{search}%"),
                Customer.contact_name.ilike(f"%{search}%"),
                Customer.customer_code.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, customer_in: CustomerCreate, created_by_id: int) -> Customer:
        """Crear nuevo cliente"""
        # Generar código de cliente automáticamente
        last_customer = db.query(Customer).order_by(Customer.id.desc()).first()
        if last_customer:
            last_number = int(last_customer.customer_code.replace("CLI", ""))
            new_number = last_number + 1
        else:
            new_number = 1
        
        customer_code = f"CLI{new_number:06d}"
        
        db_customer = Customer(
            customer_code=customer_code,
            created_by_id=created_by_id,
            **customer_in.dict()
        )
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        return db_customer
    
    def update(self, db: Session, db_customer: Customer, customer_in: CustomerUpdate) -> Customer:
        """Actualizar cliente existente"""
        update_data = customer_in.dict(exclude_unset=True)
        
        # SECURITY: Prevent tourism_regime_pdf updates through general update (extra protection)
        update_data.pop('tourism_regime_pdf', None)
        
        for field, value in update_data.items():
            setattr(db_customer, field, value)
        
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        return db_customer
    
    def update_tourism_pdf(
        self, 
        db: Session, 
        customer_id: int, 
        pdf_filename: Optional[str], 
        regime_active: Optional[bool] = None,
        expiry_date: Optional[str] = None
    ) -> bool:
        """Método seguro para actualizar únicamente los campos relacionados con el PDF de turismo"""
        db_customer = self.get(db, customer_id)
        if not db_customer:
            return False
        
        # Actualizar únicamente campos específicos del régimen de turismo
        if pdf_filename is not None:
            setattr(db_customer, 'tourism_regime_pdf', pdf_filename)
        
        if regime_active is not None:
            setattr(db_customer, 'tourism_regime', regime_active)
            
        if expiry_date is not None:
            setattr(db_customer, 'tourism_regime_expiry', expiry_date)
        
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        return True
    
    def delete(self, db: Session, customer_id: int) -> bool:
        """Eliminar cliente (soft delete)"""
        db_customer = self.get(db, customer_id)
        if db_customer:
            setattr(db_customer, 'is_active', False)
            db.add(db_customer)
            db.commit()
            return True
        return False

class ContactCRUD:
    def get(self, db: Session, contact_id: int) -> Optional[Contact]:
        """Obtener contacto por ID"""
        return db.query(Contact).filter(Contact.id == contact_id).first()
    
    def get_by_customer(self, db: Session, customer_id: int) -> List[Contact]:
        """Obtener todos los contactos de un cliente"""
        return db.query(Contact).filter(
            and_(Contact.customer_id == customer_id, Contact.is_active == True)
        ).all()
    
    def get_primary_contact(self, db: Session, customer_id: int) -> Optional[Contact]:
        """Obtener contacto principal de un cliente"""
        return db.query(Contact).filter(
            and_(
                Contact.customer_id == customer_id,
                Contact.is_primary == True,
                Contact.is_active == True
            )
        ).first()
    
    def create(self, db: Session, contact_in: ContactCreate) -> Contact:
        """Crear nuevo contacto"""
        # Si es contacto principal, desactivar otros contactos principales del mismo cliente
        if contact_in.is_primary:
            db.query(Contact).filter(
                and_(Contact.customer_id == contact_in.customer_id, Contact.is_primary == True)
            ).update({"is_primary": False})
        
        db_contact = Contact(**contact_in.dict())
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        return db_contact
    
    def update(self, db: Session, db_contact: Contact, contact_in: ContactUpdate) -> Contact:
        """Actualizar contacto existente"""
        update_data = contact_in.dict(exclude_unset=True)
        
        # Si se marca como principal, desactivar otros contactos principales del mismo cliente
        if update_data.get("is_primary"):
            db.query(Contact).filter(
                and_(
                    Contact.customer_id == db_contact.customer_id,
                    Contact.id != db_contact.id,
                    Contact.is_primary == True
                )
            ).update({"is_primary": False})
        
        for field, value in update_data.items():
            setattr(db_contact, field, value)
        
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        return db_contact
    
    def delete(self, db: Session, contact_id: int) -> bool:
        """Eliminar contacto (soft delete)"""
        db_contact = self.get(db, contact_id)
        if db_contact:
            setattr(db_contact, 'is_active', False)
            db.add(db_contact)
            db.commit()
            return True
        return False

# Instancias globales
customer_crud = CustomerCRUD()
contact_crud = ContactCRUD()