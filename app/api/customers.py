from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import uuid
from datetime import datetime

from app.core.database import get_database
from app.core.dependencies import get_current_active_user, check_user_limits
from app.crud.customer import customer_crud, contact_crud
from app.schemas.customer import (
    Customer, CustomerCreate, CustomerUpdate, CustomerList,
    Contact, ContactCreate, ContactUpdate
)
from app.models.user import User

router = APIRouter(prefix="/customers", tags=["clientes"])

# Endpoints para Clientes
@router.get("/", response_model=List[CustomerList])
def list_customers(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    search: Optional[str] = Query(None, description="Buscar por nombre, código o email"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo")
):
    """Obtener lista de clientes con filtros opcionales"""
    customers = customer_crud.get_multi(
        db=db, 
        skip=skip, 
        limit=limit, 
        search=search, 
        is_active=is_active
    )
    return customers

@router.get("/{customer_id}", response_model=Customer)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener cliente específico por ID"""
    customer = customer_crud.get(db=db, customer_id=customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return customer

@router.post("/", response_model=Customer)
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
    _: User = Depends(check_user_limits('customers'))
):
    """Crear nuevo cliente"""
    # Verificar si ya existe un cliente con el mismo email
    if customer_in.email:
        existing_customer = customer_crud.get_by_email(db=db, email=customer_in.email)
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un cliente con este email"
            )
    
    customer = customer_crud.create(
        db=db, 
        customer_in=customer_in, 
        created_by_id=getattr(current_user, 'id', 0)
    )
    return customer

@router.put("/{customer_id}", response_model=Customer)
def update_customer(
    customer_id: int,
    customer_in: CustomerUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar cliente existente"""
    db_customer = customer_crud.get(db=db, customer_id=customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    # Verificar email único si se está actualizando
    if customer_in.email and customer_in.email != db_customer.email:
        existing_customer = customer_crud.get_by_email(db=db, email=customer_in.email)
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un cliente con este email"
            )
    
    customer = customer_crud.update(db=db, db_customer=db_customer, customer_in=customer_in)
    return customer

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Desactivar cliente (eliminación suave)"""
    success = customer_crud.delete(db=db, customer_id=customer_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return {"message": "Cliente desactivado exitosamente"}

# Endpoints para Contactos
@router.get("/{customer_id}/contacts", response_model=List[Contact])
def list_customer_contacts(
    customer_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener todos los contactos de un cliente"""
    # Verificar que el cliente existe
    customer = customer_crud.get(db=db, customer_id=customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    contacts = contact_crud.get_by_customer(db=db, customer_id=customer_id)
    return contacts

@router.post("/{customer_id}/contacts", response_model=Contact)
def create_contact(
    customer_id: int,
    contact_in: ContactCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Crear nuevo contacto para un cliente"""
    # Verificar que el cliente existe
    customer = customer_crud.get(db=db, customer_id=customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    # Asegurar que el contact_in tenga el customer_id correcto
    contact_in.customer_id = customer_id
    contact = contact_crud.create(db=db, contact_in=contact_in)
    return contact

@router.get("/contacts/{contact_id}", response_model=Contact)
def get_contact(
    contact_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener contacto específico por ID"""
    contact = contact_crud.get(db=db, contact_id=contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contacto no encontrado"
        )
    return contact

@router.put("/contacts/{contact_id}", response_model=Contact)
def update_contact(
    contact_id: int,
    contact_in: ContactUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar contacto existente"""
    db_contact = contact_crud.get(db=db, contact_id=contact_id)
    if not db_contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contacto no encontrado"
        )
    
    contact = contact_crud.update(db=db, db_contact=db_contact, contact_in=contact_in)
    return contact

@router.delete("/contacts/{contact_id}")
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Desactivar contacto (eliminación suave)"""
    success = contact_crud.delete(db=db, contact_id=contact_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contacto no encontrado"
        )
    return {"message": "Contacto desactivado exitosamente"}

# ===== ENDPOINTS PARA GESTIÓN DE PDFs DE RÉGIMEN DE TURISMO =====

@router.post("/{customer_id}/upload-tourism-pdf")
async def upload_tourism_pdf(
    customer_id: int,
    pdf_file: UploadFile = File(..., description="Archivo PDF del régimen de turismo"),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Subir PDF del régimen de turismo para un cliente específico"""
    
    # Verificar que el cliente existe
    customer = customer_crud.get(db=db, customer_id=customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    # Leer el contenido del archivo para validaciones
    pdf_content = await pdf_file.read()
    
    # SECURITY: Validar que es realmente un archivo PDF verificando los magic bytes
    if not pdf_content.startswith(b'%PDF-'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no es un PDF válido"
        )
    
    # Validación adicional de content-type (defensa en profundidad)
    if not pdf_file.content_type == "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos PDF"
        )
    
    # Validar tamaño del archivo (máximo 10MB)
    if len(pdf_content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo es demasiado grande. Máximo permitido: 10MB"
        )
    
    # Generar nombre único para el archivo
    file_extension = ".pdf"
    unique_filename = f"tourism_regime_{customer_id}_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d')}{file_extension}"
    
    # Asegurar que el directorio existe
    upload_dir = "uploads/tourism_pdfs"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Guardar el archivo
    file_path = os.path.join(upload_dir, unique_filename)
    with open(file_path, "wb") as buffer:
        buffer.write(pdf_content)
    
    # Actualizar el cliente con el nombre del archivo PDF usando el método seguro dedicado
    customer_crud.update_tourism_pdf(db=db, customer_id=customer_id, pdf_filename=unique_filename)
    
    return {
        "message": "PDF del régimen de turismo subido exitosamente",
        "filename": unique_filename,
        "customer_id": customer_id,
        "file_size_bytes": len(pdf_content)
    }

@router.get("/{customer_id}/tourism-pdf")
async def download_tourism_pdf(
    customer_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Descargar PDF del régimen de turismo de un cliente específico"""
    
    # Verificar que el cliente existe
    customer = customer_crud.get(db=db, customer_id=customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    # Verificar que el cliente tiene un PDF
    tourism_pdf_filename = str(customer.tourism_regime_pdf) if customer.tourism_regime_pdf is not None else None
    if not tourism_pdf_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Este cliente no tiene un PDF de régimen de turismo"
        )
    
    # SECURITY: Sanitize filename to prevent path traversal attacks
    safe_filename = os.path.basename(tourism_pdf_filename)
    
    # SECURITY: Validate filename doesn't contain directory separators or malicious patterns
    if ".." in tourism_pdf_filename or "/" in tourism_pdf_filename or "\\" in tourism_pdf_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre de archivo inválido"
        )
    
    # SECURITY: Ensure the file path stays within the uploads directory
    upload_dir = os.path.abspath("uploads/tourism_pdfs")
    file_path = os.path.join(upload_dir, safe_filename)
    
    # SECURITY: Verify the resolved path is still within the upload directory
    if not os.path.abspath(file_path).startswith(upload_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Acceso no autorizado al archivo"
        )
    
    # Verificar que el archivo existe en el sistema
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo PDF no encontrado en el servidor"
        )
    
    # Devolver el archivo para descarga
    return FileResponse(
        path=file_path,
        filename=f"regimen_turismo_{customer.company_name}_{safe_filename}",
        media_type="application/pdf"
    )

@router.delete("/{customer_id}/tourism-pdf")
async def delete_tourism_pdf(
    customer_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar PDF del régimen de turismo de un cliente específico"""
    
    # Verificar que el cliente existe
    customer = customer_crud.get(db=db, customer_id=customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    # Verificar que el cliente tiene un PDF
    tourism_pdf_filename = str(customer.tourism_regime_pdf) if customer.tourism_regime_pdf is not None else None
    if not tourism_pdf_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Este cliente no tiene un PDF de régimen de turismo"
        )
    
    # SECURITY: Sanitize filename to prevent path traversal attacks
    safe_filename = os.path.basename(tourism_pdf_filename)
    
    # SECURITY: Validate filename doesn't contain directory separators or malicious patterns
    if ".." in tourism_pdf_filename or "/" in tourism_pdf_filename or "\\" in tourism_pdf_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre de archivo inválido"
        )
    
    # SECURITY: Ensure the file path stays within the uploads directory
    upload_dir = os.path.abspath("uploads/tourism_pdfs")
    file_path = os.path.join(upload_dir, safe_filename)
    
    # SECURITY: Verify the resolved path is still within the upload directory
    if not os.path.abspath(file_path).startswith(upload_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Acceso no autorizado al archivo"
        )
    
    # Eliminar el archivo del sistema de archivos si existe
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Actualizar el cliente removiendo la referencia al PDF (using direct CRUD method to bypass schema)
    customer_crud.update_tourism_pdf(db=db, customer_id=customer_id, pdf_filename=None, regime_active=False, expiry_date=None)
    
    return {
        "message": "PDF del régimen de turismo eliminado exitosamente",
        "customer_id": customer_id
    }