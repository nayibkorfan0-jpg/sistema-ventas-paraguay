from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_database
from app.core.dependencies import get_current_active_user, check_user_limits
from app.crud.quote import quote_crud
from app.schemas.quote import (
    Quote, QuoteCreate, QuoteUpdate, QuoteList, QuoteStatus, QuotePDFResponse, QuoteLine, parse_quote_status
)
from app.services.pdf_generator import pdf_generator
from app.models.user import User

router = APIRouter(prefix="/quotes", tags=["cotizaciones"])

@router.get("/", response_model=List[QuoteList])
def list_quotes(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    status: Optional[QuoteStatus] = Query(None, description="Filtrar por estado"),
    date_from: Optional[date] = Query(None, description="Fecha desde"),
    date_to: Optional[date] = Query(None, description="Fecha hasta"),
    search: Optional[str] = Query(None, description="Buscar por número, cliente o notas")
):
    """Obtener lista de cotizaciones con filtros opcionales"""
    quotes = quote_crud.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        search=search
    )
    
    # Mapear a QuoteList (solo campos necesarios para listado)
    quotes_list = []
    for quote in quotes:
        quote_list = QuoteList(
            id=quote.id,
            quote_number=quote.quote_number,
            customer_id=quote.customer_id,
            customer_name=quote.customer.company_name if quote.customer else "",
            quote_date=quote.quote_date,
            valid_until=quote.valid_until,
            status=parse_quote_status(str(quote.status)),
            total_amount=quote.total_amount,
            created_at=quote.created_at
        )
        quotes_list.append(quote_list)
    
    return quotes_list

@router.get("/{quote_id}", response_model=Quote)
def get_quote(
    quote_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener cotización específica por ID"""
    quote = quote_crud.get(db=db, quote_id=quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización no encontrada"
        )
    
    # Convertir a esquema de respuesta
    quote_response = Quote(
        id=quote.id,
        quote_number=quote.quote_number,
        customer_id=quote.customer_id,
        quote_date=quote.quote_date,
        valid_until=quote.valid_until,
        status=parse_quote_status(str(quote.status)),
        subtotal=quote.subtotal,
        tax_amount=quote.tax_amount,
        total_amount=quote.total_amount,
        notes=quote.notes,
        terms_conditions=quote.terms_conditions,
        created_by_id=quote.created_by_id,
        created_at=quote.created_at,
        updated_at=quote.updated_at,
        lines=[],
        customer_name=quote.customer.company_name if quote.customer else "",
        customer_email=quote.customer.email if quote.customer else ""
    )
    
    # Agregar líneas
    for line in quote.lines:
        quote_line = QuoteLine(
            id=line.id,
            quote_id=line.quote_id,
            product_id=line.product_id,
            quantity=line.quantity,
            unit_price=line.unit_price,
            discount_percent=line.discount_percent,
            line_total=line.line_total,
            description=line.description
        )
        quote_response.lines.append(quote_line)
    
    return quote_response

@router.post("/", response_model=Quote)
def create_quote(
    quote_in: QuoteCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
    _: User = Depends(check_user_limits('quotes'))
):
    """Crear nueva cotización"""
    try:
        quote = quote_crud.create(
            db=db,
            quote_in=quote_in,
            created_by_id=int(current_user.id)
        )
        
        # Obtener la cotización completa con relaciones
        created_quote = quote_crud.get(db=db, quote_id=int(quote.id))
        if not created_quote:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener la cotización creada"
            )
        
        # Convertir a esquema de respuesta
        quote_response = Quote(
            id=created_quote.id,
            quote_number=created_quote.quote_number,
            customer_id=created_quote.customer_id,
            quote_date=created_quote.quote_date,
            valid_until=created_quote.valid_until,
            status=parse_quote_status(str(created_quote.status)),
            subtotal=created_quote.subtotal,
            tax_amount=created_quote.tax_amount,
            total_amount=created_quote.total_amount,
            notes=created_quote.notes,
            terms_conditions=created_quote.terms_conditions,
            created_by_id=created_quote.created_by_id,
            created_at=created_quote.created_at,
            updated_at=created_quote.updated_at,
            lines=[],
            customer_name=created_quote.customer.company_name if created_quote.customer else "",
            customer_email=created_quote.customer.email if created_quote.customer else ""
        )
        
        # Agregar líneas
        for line in created_quote.lines:
            quote_line = QuoteLine(
                id=line.id,
                quote_id=line.quote_id,
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_percent=line.discount_percent,
                line_total=line.line_total,
                description=line.description
            )
            quote_response.lines.append(quote_line)
        
        return quote_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{quote_id}", response_model=Quote)
def update_quote(
    quote_id: int,
    quote_in: QuoteUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar cotización existente"""
    db_quote = quote_crud.get(db=db, quote_id=quote_id)
    if not db_quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización no encontrada"
        )
    
    # Solo permitir actualización si está en borrador
    if parse_quote_status(str(db_quote.status)) != QuoteStatus.draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden actualizar cotizaciones en borrador"
        )
    
    try:
        quote = quote_crud.update(db=db, db_quote=db_quote, quote_in=quote_in)
        
        # Obtener la cotización actualizada con relaciones
        updated_quote = quote_crud.get(db=db, quote_id=int(quote.id))
        if not updated_quote:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener la cotización actualizada"
            )
        
        # Convertir a esquema de respuesta
        quote_response = Quote(
            id=updated_quote.id,
            quote_number=updated_quote.quote_number,
            customer_id=updated_quote.customer_id,
            quote_date=updated_quote.quote_date,
            valid_until=updated_quote.valid_until,
            status=parse_quote_status(str(updated_quote.status)),
            subtotal=updated_quote.subtotal,
            tax_amount=updated_quote.tax_amount,
            total_amount=updated_quote.total_amount,
            notes=updated_quote.notes,
            terms_conditions=updated_quote.terms_conditions,
            created_by_id=updated_quote.created_by_id,
            created_at=updated_quote.created_at,
            updated_at=updated_quote.updated_at,
            lines=[],
            customer_name=updated_quote.customer.company_name if updated_quote.customer else "",
            customer_email=updated_quote.customer.email if updated_quote.customer else ""
        )
        
        # Agregar líneas
        for line in updated_quote.lines:
            quote_line = QuoteLine(
                id=line.id,
                quote_id=line.quote_id,
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_percent=line.discount_percent,
                line_total=line.line_total,
                description=line.description
            )
            quote_response.lines.append(quote_line)
        
        return quote_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.patch("/{quote_id}/status")
def update_quote_status(
    quote_id: int,
    new_status: QuoteStatus,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar estado de cotización"""
    quote = quote_crud.update_status(db=db, quote_id=quote_id, status=new_status)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización no encontrada"
        )
    
    return {"message": f"Estado de cotización actualizado a {new_status.value}"}

@router.delete("/{quote_id}")
def delete_quote(
    quote_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar cotización (solo si está en borrador)"""
    success = quote_crud.delete(db=db, quote_id=quote_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar la cotización. Solo se permiten eliminar cotizaciones en borrador."
        )
    
    return {"message": "Cotización eliminada exitosamente"}

@router.get("/{quote_id}/pdf", response_model=QuotePDFResponse)
def generate_quote_pdf(
    quote_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Generar PDF de cotización"""
    quote = quote_crud.get(db=db, quote_id=quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización no encontrada"
        )
    
    try:
        # Generar PDF
        pdf_path = pdf_generator.generate_quote_pdf(quote)
        filename = f"cotizacion_{quote.quote_number}.pdf"
        
        return QuotePDFResponse(
            quote_id=quote.id,
            pdf_filename=filename,
            download_url=f"/api/quotes/{quote_id}/pdf/download"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando PDF: {str(e)}"
        )

@router.get("/{quote_id}/pdf/download")
def download_quote_pdf(
    quote_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Descargar PDF de cotización"""
    quote = quote_crud.get(db=db, quote_id=quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización no encontrada"
        )
    
    from fastapi.responses import FileResponse
    import os
    
    try:
        # Generar PDF si no existe
        pdf_path = pdf_generator.generate_quote_pdf(quote)
        
        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Archivo PDF no encontrado"
            )
        
        filename = f"cotizacion_{quote.quote_number}.pdf"
        return FileResponse(
            path=pdf_path,
            filename=filename,
            media_type="application/pdf"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error descargando PDF: {str(e)}"
        )