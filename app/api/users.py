from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_database
from app.core.dependencies import get_current_user, get_current_active_user, get_current_superuser, get_admin_only, get_admin_or_manager
from app.crud.user import user_crud
from app.schemas.auth import User, UserCreate, UserUpdate
from app.models.user import User as UserModel

router = APIRouter(prefix="/users", tags=["usuarios"])

@router.get("/me", response_model=User)
def get_current_user_info(
    current_user: UserModel = Depends(get_current_active_user)
):
    """Obtener información del usuario actual"""
    return current_user

@router.get("/", response_model=List[User])
def list_users(
    db: Session = Depends(get_database),
    current_user: UserModel = Depends(get_admin_or_manager),
    skip: int = 0,
    limit: int = 100
):
    """Listar todos los usuarios (admin o manager)"""
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=User)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_database),
    current_user: UserModel = Depends(get_admin_only)
):
    """Crear nuevo usuario (solo administradores)"""
    # Verificar si el usuario ya existe
    user = user_crud.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="El email ya está registrado"
        )
    
    user = user_crud.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="El nombre de usuario ya está en uso"
        )
    
    # Crear nuevo usuario
    user = user_crud.create(db, user_in=user_in)
    return user

@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: int,
    db: Session = Depends(get_database),
    current_user: UserModel = Depends(get_admin_or_manager)
):
    """Obtener usuario por ID (admin o manager)"""
    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_database),
    current_user: UserModel = Depends(get_admin_only)
):
    """Actualizar usuario por ID (solo administradores)"""
    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Prevent downgrading superuser status unless current user is superuser
    if not current_user.is_superuser and user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="No se puede modificar un superusuario"
        )
    
    # Update user
    updated_user = user_crud.update(db, db_user=user, user_in=user_in)
    return updated_user

@router.get("/usage/{user_id}")
def get_user_usage_stats(
    user_id: int,
    db: Session = Depends(get_database),
    current_user: UserModel = Depends(get_admin_or_manager)
):
    """Obtener estadísticas de uso del usuario (admin o manager)"""
    from app.crud.usage_limits import get_user_limits_summary
    
    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    user_limits = {
        "max_customers": user.max_customers,
        "max_quotes": user.max_quotes,
        "max_orders": user.max_orders,
        "max_invoices": user.max_invoices
    }
    
    return get_user_limits_summary(db, user_id, user_limits)

@router.put("/me", response_model=User)
def update_current_user(
    user_in: UserUpdate,
    db: Session = Depends(get_database),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Actualizar información del usuario actual"""
    # Los usuarios no pueden cambiar su propio estado is_superuser
    if user_in.dict().get("is_superuser") is not None:
        del user_in.__dict__["is_superuser"]
    
    user = user_crud.update(db, db_user=current_user, user_in=user_in)
    return user