from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import io

from app.core.database import get_database
from app.core.dependencies import get_current_active_user, check_user_limits
from app.models.user import User
from app.schemas.invoice import (
    Invoice, InvoiceList, InvoiceWithDetails, InvoiceCreate, InvoiceUpdate,
    InvoiceFromOrder, InvoiceSummary, PaymentCreate, Payment,
    InvoiceStatus, parse_invoice_status
)
from app.crud.invoice import invoice_crud
from app.utils.paraguay_fiscal import ParaguayFiscalValidator
from app.crud.company import company_settings_crud

router = APIRouter(prefix="/invoices", tags=["invoices"])

@router.post("/", response_model=Invoice)
async def create_invoice(
    invoice: InvoiceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
    _: User = Depends(check_user_limits('invoices'))
):
    """Crear nueva factura con validaciones fiscales paraguayas"""
    try:
        # Validar timbrado antes de crear factura
        company_settings = company_settings_crud.get_settings(db)
        if company_settings:
            # Asegurar que obtenemos los valores actuales, no objetos Column
            timbrado_val = getattr(company_settings, 'timbrado', None)
            timbrado_str = str(timbrado_val) if timbrado_val is not None else ""
            fecha_vencimiento_val = getattr(company_settings, 'timbrado_fecha_vencimiento', None)
            
            timbrado_validation = ParaguayFiscalValidator.validate_timbrado(
                timbrado_str, 
                fecha_vencimiento_val
            )
            
            if not timbrado_validation["valid"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Error de timbrado: {timbrado_validation['error']}"
                )
            
            # Advertir si el timbrado está próximo a vencer
            if timbrado_validation.get("warning"):
                # Podrías loggear esta advertencia
                pass
        
        user_id = getattr(current_user, 'id', 0)
        return invoice_crud.create_invoice(db=db, invoice=invoice, created_by_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/from-order", response_model=Invoice)
async def create_invoice_from_order(
    invoice_data: InvoiceFromOrder,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
    _: User = Depends(check_user_limits('invoices'))
):
    """Crear factura desde orden de venta con validaciones fiscales paraguayas"""
    try:
        # Validar timbrado antes de crear factura
        company_settings = company_settings_crud.get_settings(db)
        if company_settings:
            # Asegurar que obtenemos los valores actuales, no objetos Column
            timbrado_val = getattr(company_settings, 'timbrado', None)
            timbrado_str = str(timbrado_val) if timbrado_val is not None else ""
            fecha_vencimiento_val = getattr(company_settings, 'timbrado_fecha_vencimiento', None)
            
            timbrado_validation = ParaguayFiscalValidator.validate_timbrado(
                timbrado_str, 
                fecha_vencimiento_val
            )
            
            if not timbrado_validation["valid"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Error de timbrado: {timbrado_validation['error']}"
                )
        
        user_id = getattr(current_user, 'id', 0)
        return invoice_crud.create_from_sales_order(
            db=db, 
            invoice_data=invoice_data, 
            created_by_id=user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/", response_model=List[InvoiceList])
async def list_invoices(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver"),
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    start_date: Optional[date] = Query(None, description="Fecha de inicio"),
    end_date: Optional[date] = Query(None, description="Fecha de fin"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Obtener lista de facturas con filtros"""
    # Parsear estado si se proporciona
    status_enum = None
    if status:
        status_enum = parse_invoice_status(status)
    
    invoices = invoice_crud.get_invoices(
        db=db, 
        skip=skip, 
        limit=limit,
        customer_id=customer_id,
        status=status_enum,
        start_date=start_date,
        end_date=end_date
    )
    
    # Convertir a formato de lista
    invoice_list = []
    for invoice in invoices:
        customer_name = invoice.customer.company_name if invoice.customer else "Cliente desconocido"
        
        invoice_list.append({
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "customer_id": invoice.customer_id,
            "customer_name": customer_name,
            "invoice_date": invoice.invoice_date,
            "due_date": invoice.due_date,
            "status": invoice.status,
            "total_amount": invoice.total_amount,
            "balance_due": invoice.balance_due,
            "created_at": invoice.created_at
        })
    
    return invoice_list

@router.get("/{invoice_id}", response_model=InvoiceWithDetails)
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Obtener detalles de una factura específica"""
    invoice = invoice_crud.get_invoice(db=db, invoice_id=invoice_id)
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # Preparar datos completos
    result = {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "sales_order_id": invoice.sales_order_id,
        "customer_id": invoice.customer_id,
        "invoice_date": invoice.invoice_date,
        "due_date": invoice.due_date,
        "status": invoice.status,
        "subtotal": invoice.subtotal,
        "tax_amount": invoice.tax_amount,
        "total_amount": invoice.total_amount,
        "paid_amount": invoice.paid_amount,
        "balance_due": invoice.balance_due,
        "notes": invoice.notes,
        "payment_terms": invoice.payment_terms,
        "created_at": invoice.created_at,
        "updated_at": invoice.updated_at,
        "customer_name": invoice.customer.company_name if invoice.customer else None,
        "customer_email": invoice.customer.email if invoice.customer else None,
        "sales_order_number": invoice.sales_order.order_number if invoice.sales_order else None,
        "lines": [],
        "payments": []
    }
    
    # Agregar líneas con información de productos
    for line in invoice.lines:
        line_data = {
            "id": line.id,
            "invoice_id": line.invoice_id,
            "product_id": line.product_id,
            "quantity": line.quantity,
            "unit_price": line.unit_price,
            "discount_percent": line.discount_percent,
            "line_total": line.line_total,
            "description": line.description,
            "product_name": line.product.name if line.product else None,
            "product_code": line.product.product_code if line.product else None
        }
        result["lines"].append(line_data)
    
    # Agregar pagos
    for payment in invoice.payments:
        payment_data = {
            "id": payment.id,
            "invoice_id": payment.invoice_id,
            "payment_date": payment.payment_date,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "reference_number": payment.reference_number,
            "notes": payment.notes,
            "created_at": payment.created_at
        }
        result["payments"].append(payment_data)
    
    return result

@router.put("/{invoice_id}", response_model=Invoice)
async def update_invoice(
    invoice_id: int,
    invoice_update: InvoiceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Actualizar factura"""
    updated_invoice = invoice_crud.update_invoice(
        db=db, 
        invoice_id=invoice_id, 
        invoice_update=invoice_update
    )
    
    if not updated_invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    return updated_invoice

@router.post("/{invoice_id}/payments", response_model=Payment)
async def add_payment(
    invoice_id: int,
    payment: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Agregar pago a una factura"""
    # Verificar que el invoice_id coincida
    if payment.invoice_id != invoice_id:
        raise HTTPException(status_code=400, detail="ID de factura no coincide")
    
    try:
        return invoice_crud.add_payment(db=db, payment=payment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Generar y descargar PDF de factura"""
    invoice = invoice_crud.get_invoice(db=db, invoice_id=invoice_id)
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    try:
        # Importar aquí para evitar errores de importación circular
        from app.services.pdf_generator import pdf_generator
        
        # Generar PDF de factura en buffer
        pdf_buffer = pdf_generator.generate_invoice_pdf(invoice)
        pdf_buffer.seek(0)  # Resetear posición del buffer para lectura
        
        # Nombre del archivo PDF
        filename = f"factura_{invoice.invoice_number}.pdf"
        
        # Retornar como streaming response
        return StreamingResponse(
            io.BytesIO(pdf_buffer.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando PDF de factura: {str(e)}")

@router.get("/summary/statistics", response_model=InvoiceSummary)
async def get_invoice_summary(
    start_date: Optional[date] = Query(None, description="Fecha de inicio"),
    end_date: Optional[date] = Query(None, description="Fecha de fin"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Obtener resumen estadístico de facturas"""
    summary = invoice_crud.get_invoice_summary(
        db=db, 
        start_date=start_date, 
        end_date=end_date
    )
    
    return summary

@router.post("/update-overdue")
async def update_overdue_invoices(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Actualizar facturas vencidas (tarea administrativa)"""
    if not bool(current_user.is_superuser):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    count = invoice_crud.update_overdue_invoices(db=db)
    
    return {
        "message": f"Se actualizaron {count} facturas vencidas",
        "updated_count": count
    }