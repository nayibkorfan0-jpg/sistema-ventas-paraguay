from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.database import get_database
from app.core.dependencies import get_current_active_user, check_user_limits
from app.models.user import User
from app.schemas.deposit import (
    Deposit, DepositList, DepositCreate, DepositUpdate,
    DepositApplication, DepositApplicationCreate,
    ApplyDepositToInvoice, RefundDeposit,
    CustomerDepositSummary, DepositOperationResponse,
    DepositType, DepositStatus, Currency
)
from app.crud.deposit import deposit_crud

router = APIRouter(prefix="/deposits", tags=["deposits"])

@router.post("/", response_model=Deposit)
async def create_deposit(
    deposit: DepositCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Crear nuevo depósito"""
    # Verificar permisos
    if not bool(current_user.can_manage_deposits):
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar depósitos")
    
    try:
        user_id = getattr(current_user, 'id', 0)
        return deposit_crud.create_deposit(db=db, deposit=deposit, created_by_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/", response_model=List[DepositList])
async def list_deposits(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver"),
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    status: Optional[DepositStatus] = Query(None, description="Filtrar por estado"),
    deposit_type: Optional[DepositType] = Query(None, description="Filtrar por tipo"),
    currency: Optional[Currency] = Query(None, description="Filtrar por moneda"),
    start_date: Optional[date] = Query(None, description="Fecha de inicio"),
    end_date: Optional[date] = Query(None, description="Fecha de fin"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Obtener lista de depósitos con filtros"""
    deposits = deposit_crud.get_deposits(
        db=db,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        status=status.value if status else None,
        deposit_type=deposit_type.value if deposit_type else None,
        currency=currency.value if currency else None,
        start_date=start_date,
        end_date=end_date
    )
    
    # Convertir a formato de lista
    deposit_list = []
    for deposit in deposits:
        customer_name = deposit.customer.company_name if deposit.customer else "Cliente desconocido"
        
        deposit_list.append({
            "id": deposit.id,
            "deposit_number": deposit.deposit_number,
            "customer_id": deposit.customer_id,
            "customer_name": customer_name,
            "deposit_type": deposit.deposit_type,
            "amount": deposit.amount,
            "currency": deposit.currency,
            "deposit_date": deposit.deposit_date,
            "status": deposit.status,
            "available_amount": deposit.available_amount,
            "created_at": deposit.created_at
        })
    
    return deposit_list

@router.get("/{deposit_id}", response_model=Deposit)
async def get_deposit(
    deposit_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Obtener detalles de un depósito específico"""
    deposit = deposit_crud.get_deposit(db=db, deposit_id=deposit_id)
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Depósito no encontrado")
    
    # Preparar datos con información del cliente
    result = {
        "id": deposit.id,
        "deposit_number": deposit.deposit_number,
        "customer_id": deposit.customer_id,
        "deposit_type": deposit.deposit_type,
        "amount": deposit.amount,
        "currency": deposit.currency,
        "deposit_date": deposit.deposit_date,
        "expiry_date": deposit.expiry_date,
        "status": deposit.status,
        "applied_amount": deposit.applied_amount,
        "available_amount": deposit.available_amount,
        "payment_method": deposit.payment_method,
        "reference_number": deposit.reference_number,
        "bank_name": deposit.bank_name,
        "notes": deposit.notes,
        "project_reference": deposit.project_reference,
        "contract_number": deposit.contract_number,
        "created_by_id": deposit.created_by_id,
        "created_at": deposit.created_at,
        "updated_at": deposit.updated_at,
        "customer_name": deposit.customer.company_name if deposit.customer else None
    }
    
    return result

@router.put("/{deposit_id}", response_model=Deposit)
async def update_deposit(
    deposit_id: int,
    deposit_update: DepositUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Actualizar depósito"""
    # Verificar permisos
    if not bool(current_user.can_manage_deposits):
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar depósitos")
    
    deposit = deposit_crud.update_deposit(db=db, deposit_id=deposit_id, deposit_update=deposit_update)
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Depósito no encontrado")
    
    return deposit

@router.post("/apply-to-invoice", response_model=DepositApplication)
async def apply_deposit_to_invoice(
    application: ApplyDepositToInvoice,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Aplicar depósito a una factura"""
    # Verificar permisos
    if not bool(current_user.can_manage_deposits):
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar depósitos")
    
    try:
        user_id = getattr(current_user, 'id', 0)
        return deposit_crud.apply_deposit_to_invoice(
            db=db,
            application=application,
            applied_by_id=user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/{deposit_id}/refund", response_model=DepositOperationResponse)
async def refund_deposit(
    deposit_id: int,
    refund_data: RefundDeposit,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Devolver depósito (total o parcial)"""
    # Verificar permisos
    if not bool(current_user.can_manage_deposits):
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar depósitos")
    
    try:
        user_id = getattr(current_user, 'id', 0)
        updated_deposit = deposit_crud.refund_deposit(
            db=db,
            deposit_id=deposit_id,
            refund_data=refund_data,
            refunded_by_id=user_id
        )
        
        return {
            "success": True,
            "message": f"Devolución de {refund_data.refund_amount} {updated_deposit.currency} procesada exitosamente",
            "deposit_id": deposit_id,
            "new_available_amount": updated_deposit.available_amount
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/customer/{customer_id}", response_model=List[Deposit])
async def get_customer_deposits(
    customer_id: int,
    active_only: bool = Query(False, description="Solo depósitos activos"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Obtener depósitos de un cliente específico"""
    deposits = deposit_crud.get_customer_deposits(
        db=db,
        customer_id=customer_id,
        active_only=active_only
    )
    
    return deposits

@router.get("/customer/{customer_id}/summary", response_model=CustomerDepositSummary)
async def get_customer_deposit_summary(
    customer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Obtener resumen de depósitos de un cliente"""
    summary = deposit_crud.get_customer_deposit_summary(db=db, customer_id=customer_id)
    
    if not summary:
        # Si no existe resumen, crear uno vacío
        summary = {
            "customer_id": customer_id,
            "customer_name": None,
            "total_deposits_pyg": 0,
            "available_deposits_pyg": 0,
            "applied_deposits_pyg": 0,
            "total_deposits_usd": 0,
            "available_deposits_usd": 0,
            "applied_deposits_usd": 0,
            "active_deposits_count": 0,
            "total_deposits_count": 0,
            "last_deposit_date": None,
            "last_application_date": None,
            "updated_at": None
        }
    
    return summary

@router.post("/customer/{customer_id}/update-summary")
async def update_customer_deposit_summary(
    customer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Actualizar manualmente el resumen de depósitos de un cliente"""
    # Verificar permisos (solo admin/manager)
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Solo administradores y gerentes pueden actualizar resúmenes")
    
    try:
        deposit_crud.update_customer_deposit_summary(db=db, customer_id=customer_id)
        return {"message": "Resumen de depósitos actualizado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error actualizando resumen")

# Endpoints de reportes
@router.get("/reports/summary")
async def get_deposits_summary_report(
    start_date: Optional[date] = Query(None, description="Fecha de inicio"),
    end_date: Optional[date] = Query(None, description="Fecha de fin"),
    currency: Optional[Currency] = Query(None, description="Filtrar por moneda"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Reporte resumen de depósitos"""
    # Verificar permisos
    if not bool(current_user.can_view_reports):
        raise HTTPException(status_code=403, detail="No tiene permisos para ver reportes")
    
    # Lógica básica de reporte
    deposits = deposit_crud.get_deposits(
        db=db,
        skip=0,
        limit=10000,  # Obtener todos para el reporte
        currency=currency.value if currency else None,
        start_date=start_date,
        end_date=end_date
    )
    
    # Calcular estadísticas
    total_deposits = sum(d.amount for d in deposits)
    total_available = sum(d.available_amount for d in deposits)
    total_applied = sum(d.applied_amount for d in deposits)
    
    by_type = {}
    by_status = {}
    
    for deposit in deposits:
        # Por tipo
        if deposit.deposit_type not in by_type:
            by_type[deposit.deposit_type] = {"count": 0, "amount": 0}
        by_type[deposit.deposit_type]["count"] += 1
        by_type[deposit.deposit_type]["amount"] += deposit.amount
        
        # Por estado
        if deposit.status not in by_status:
            by_status[deposit.status] = {"count": 0, "amount": 0}
        by_status[deposit.status]["count"] += 1
        by_status[deposit.status]["amount"] += deposit.amount
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "currency": currency.value if currency else "ALL"
        },
        "totals": {
            "total_deposits": total_deposits,
            "total_available": total_available,
            "total_applied": total_applied,
            "deposit_count": len(deposits)
        },
        "by_type": by_type,
        "by_status": by_status
    }