from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_database
from app.core.dependencies import get_current_active_user
from app.crud.company import company_settings_crud
from app.schemas.company import CompanySettings, CompanySettingsCreate, CompanySettingsUpdate, CompanySettingsPublic
from app.schemas.auth import User

router = APIRouter(prefix="/company", tags=["configuración de empresa"])

@router.get("/settings", response_model=CompanySettings)
def get_company_settings(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener configuración de la empresa"""
    try:
        settings = company_settings_crud.get_settings(db)
        if not settings:
            # Si no existe configuración, devolver estructura básica
            raise HTTPException(
                status_code=404,
                detail="No existe configuración de empresa. Por favor, configure los datos de su empresa."
            )
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener configuración de empresa: {str(e)}"
        )

@router.get("/settings/public", response_model=CompanySettingsPublic)
def get_company_settings_public(
    db: Session = Depends(get_database)
):
    """Obtener configuración pública de la empresa (sin autenticación)"""
    try:
        settings = company_settings_crud.get_settings(db)
        if not settings:
            raise HTTPException(
                status_code=404,
                detail="No existe configuración de empresa"
            )
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener configuración pública: {str(e)}"
        )

@router.post("/settings", response_model=CompanySettings)
def create_company_settings(
    company_in: CompanySettingsCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Crear nueva configuración de empresa (solo administradores)"""
    # Verificar permisos de administrador
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden crear configuración de empresa"
        )
    
    try:
        return company_settings_crud.create(db, company_in=company_in)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear configuración de empresa: {str(e)}"
        )

@router.put("/settings", response_model=CompanySettings)
def update_company_settings(
    company_in: CompanySettingsUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar configuración de empresa existente"""
    # Verificar permisos
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden modificar la configuración de empresa"
        )
    
    try:
        return company_settings_crud.update(db, company_in=company_in)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar configuración de empresa: {str(e)}"
        )

@router.post("/settings/complete", response_model=CompanySettings)
def mark_configuration_complete(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Marcar la configuración de empresa como completa"""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden completar la configuración"
        )
    
    try:
        return company_settings_crud.mark_configuration_complete(db)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al completar configuración: {str(e)}"
        )

@router.get("/numbering/next-invoice")
def get_next_invoice_number(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener siguiente número de factura"""
    try:
        next_number = company_settings_crud.get_next_invoice_number(db)
        return {"next_number": next_number}
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener número de factura: {str(e)}"
        )

@router.get("/numbering/next-quote")
def get_next_quote_number(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener siguiente número de cotización"""
    try:
        next_number = company_settings_crud.get_next_quote_number(db)
        return {"next_number": next_number}
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener número de cotización: {str(e)}"
        )

@router.put("/numbering/reset-invoices")
def reset_invoice_numbering(
    start_number: int = 1,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Reiniciar numeración de facturas (solo administradores)"""
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores principales pueden reiniciar la numeración"
        )
    
    try:
        settings = company_settings_crud.reset_invoice_numbering(db, start_number)
        return {
            "message": f"Numeración de facturas reiniciada desde {start_number}",
            "new_number": settings.numeracion_facturas_actual
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al reiniciar numeración: {str(e)}"
        )

@router.put("/numbering/reset-quotes")
def reset_quote_numbering(
    start_number: int = 1,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Reiniciar numeración de cotizaciones (solo administradores)"""
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores principales pueden reiniciar la numeración"
        )
    
    try:
        settings = company_settings_crud.reset_quote_numbering(db, start_number)
        return {
            "message": f"Numeración de cotizaciones reiniciada desde {start_number}",
            "new_number": settings.numeracion_cotizaciones_actual
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al reiniciar numeración: {str(e)}"
        )