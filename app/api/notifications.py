from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime

from app.core.dependencies import get_database, get_current_user
from app.models.user import User, UserRole
from app.services.notification_service import NotificationService, trigger_expiry_check_manually

router = APIRouter()

@router.get("/tourism-expiry-check", response_model=Dict[str, Any])
async def check_tourism_expiry_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Endpoint para verificar manualmente notificaciones de vencimiento del régimen de turismo
    Solo para administradores y managers
    """
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        # Ejecutar verificación manual
        result = NotificationService.process_expiry_notifications(db)
        
        return {
            "message": "Verificación de vencimientos completada",
            "result": result,
            "user": current_user.username
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en verificación: {str(e)}")

@router.post("/tourism-expiry-task", response_model=Dict[str, str])
async def trigger_tourism_expiry_task(
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para ejecutar manualmente el task de Celery
    Solo para administradores
    """
    # Verificar permisos de admin
    if current_user.role != UserRole.ADMIN:  # type: ignore
        raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar tasks")
    
    try:
        # Ejecutar task de Celery
        task = trigger_expiry_check_manually()
        
        return {
            "message": "Task de verificación de vencimientos iniciado",
            "task_id": task.id,
            "user": current_user.username
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ejecutando task: {str(e)}")

@router.get("/customers-expiring-tourism")
async def get_customers_with_expiring_tourism(
    days_ahead: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Obtiene lista de clientes cuyo régimen de turismo vence pronto
    """
    # Verificar permisos
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        customers = NotificationService.get_customers_with_expiring_tourism(db, days_ahead)
        
        return {
            "customers": [
                {
                    "id": customer.id,
                    "company_name": customer.company_name,
                    "contact_name": customer.contact_name,
                    "tourism_regime_expiry": customer.tourism_regime_expiry.isoformat() if customer.tourism_regime_expiry is not None else None,
                    "days_until_expiry": (customer.tourism_regime_expiry - datetime.now().date()).days if customer.tourism_regime_expiry is not None else None
                }
                for customer in customers
            ],
            "total": len(customers),
            "days_ahead": days_ahead
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo clientes: {str(e)}")