from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.company import CompanySettings
from app.schemas.company import CompanySettingsCreate, CompanySettingsUpdate

class CRUDCompanySettings:
    def get_settings(self, db: Session) -> Optional[CompanySettings]:
        """Obtener configuración de la empresa (solo debería haber una)"""
        return db.query(CompanySettings).filter(CompanySettings.is_active == True).first()
    
    def get_by_id(self, db: Session, company_id: int) -> Optional[CompanySettings]:
        """Obtener configuración por ID"""
        return db.query(CompanySettings).filter(
            CompanySettings.id == company_id,
            CompanySettings.is_active == True
        ).first()
    
    def create(self, db: Session, company_in: CompanySettingsCreate) -> CompanySettings:
        """Crear nueva configuración de empresa"""
        # Verificar que no existe otra configuración activa
        existing = self.get_settings(db)
        if existing:
            raise ValueError("Ya existe una configuración de empresa activa. Use update() en su lugar.")
        
        try:
            db_company = CompanySettings(**company_in.model_dump())
            db.add(db_company)
            db.commit()
            db.refresh(db_company)
            return db_company
        except IntegrityError as e:
            db.rollback()
            if "ruc" in str(e):
                raise ValueError(f"El RUC {company_in.ruc} ya está registrado")
            raise ValueError("Error al crear la configuración de empresa")
    
    def update(self, db: Session, company_in: CompanySettingsUpdate) -> CompanySettings:
        """Actualizar configuración de empresa existente"""
        db_company = self.get_settings(db)
        if not db_company:
            raise ValueError("No existe configuración de empresa. Use create() primero.")
        
        try:
            update_data = company_in.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                if hasattr(db_company, field):
                    setattr(db_company, field, value)
            
            db.commit()
            db.refresh(db_company)
            return db_company
        except IntegrityError as e:
            db.rollback()
            if "ruc" in str(e):
                raise ValueError(f"El RUC ya está registrado por otra empresa")
            raise ValueError("Error al actualizar la configuración de empresa")
    
    def update_by_id(self, db: Session, company_id: int, company_in: CompanySettingsUpdate) -> CompanySettings:
        """Actualizar configuración específica por ID"""
        db_company = self.get_by_id(db, company_id)
        if not db_company:
            raise ValueError("Configuración de empresa no encontrada")
        
        try:
            update_data = company_in.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                if hasattr(db_company, field):
                    setattr(db_company, field, value)
            
            db.commit()
            db.refresh(db_company)
            return db_company
        except IntegrityError as e:
            db.rollback()
            if "ruc" in str(e):
                raise ValueError(f"El RUC ya está registrado por otra empresa")
            raise ValueError("Error al actualizar la configuración de empresa")
    
    def deactivate(self, db: Session) -> bool:
        """Desactivar configuración de empresa actual"""
        db_company = self.get_settings(db)
        if not db_company:
            return False
        
        db_company.is_active = False  # type: ignore[assignment]
        db.commit()
        return True
    
    def get_next_invoice_number(self, db: Session) -> int:
        """Obtener y actualizar el siguiente número de factura"""
        db_company = self.get_settings(db)
        if not db_company:
            raise ValueError("No hay configuración de empresa disponible")
        
        next_number = db_company.numeracion_facturas_actual  # type: ignore[assignment]
        db_company.numeracion_facturas_actual += 1  # type: ignore[assignment]
        db.commit()
        
        return next_number  # type: ignore[return-value]
    
    def increment_invoice_number(self, db: Session) -> None:
        """Incrementar contador de facturas"""
        db_company = self.get_settings(db)
        if not db_company:
            raise ValueError("No hay configuración de empresa disponible")
        
        db_company.numeracion_facturas_actual += 1  # type: ignore[assignment]
        db.commit()
    
    def get_next_quote_number(self, db: Session) -> int:
        """Obtener y actualizar el siguiente número de cotización"""
        db_company = self.get_settings(db)
        if not db_company:
            raise ValueError("No hay configuración de empresa disponible")
        
        next_number = db_company.numeracion_cotizaciones_actual  # type: ignore[assignment]
        db_company.numeracion_cotizaciones_actual += 1  # type: ignore[assignment]
        db.commit()
        
        return next_number  # type: ignore[return-value]
    
    def reset_invoice_numbering(self, db: Session, start_number: int = 1) -> CompanySettings:
        """Reiniciar numeración de facturas"""
        db_company = self.get_settings(db)
        if not db_company:
            raise ValueError("No hay configuración de empresa disponible")
        
        db_company.numeracion_facturas_actual = start_number  # type: ignore[assignment]
        db_company.numeracion_facturas_inicio = start_number  # type: ignore[assignment]
        db.commit()
        db.refresh(db_company)
        
        return db_company
    
    def reset_quote_numbering(self, db: Session, start_number: int = 1) -> CompanySettings:
        """Reiniciar numeración de cotizaciones"""
        db_company = self.get_settings(db)
        if not db_company:
            raise ValueError("No hay configuración de empresa disponible")
        
        db_company.numeracion_cotizaciones_actual = start_number  # type: ignore[assignment]
        db_company.numeracion_cotizaciones_inicio = start_number  # type: ignore[assignment]
        db.commit()
        db.refresh(db_company)
        
        return db_company
    
    def mark_configuration_complete(self, db: Session) -> CompanySettings:
        """Marcar la configuración como completa"""
        db_company = self.get_settings(db)
        if not db_company:
            raise ValueError("No hay configuración de empresa disponible")
        
        # Verificar campos obligatorios
        required_fields = [
            'razon_social', 'ruc', 'timbrado', 'direccion'
        ]
        
        for field in required_fields:
            value = getattr(db_company, field)
            if not value or (isinstance(value, str) and value.strip() == ""):
                raise ValueError(f"Campo obligatorio faltante: {field}")
        
        db_company.configuracion_completa = True  # type: ignore[assignment]
        db.commit()
        db.refresh(db_company)
        
        return db_company

# Instancia única del CRUD
company_settings_crud = CRUDCompanySettings()