from datetime import timedelta
from typing import cast
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_database
from app.core.auth import create_user_token
from app.core.dependencies import get_current_active_user
from app.crud.user import user_crud
from app.schemas.auth import Token, User, UserCreate, UserLogin

router = APIRouter(prefix="/auth", tags=["autenticación"])

@router.post("/register", response_model=User)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_database)
):
    """Registrar nuevo usuario"""
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

@router.post("/login", response_model=Token)
def login_user(
    user_credentials: UserLogin,
    db: Session = Depends(get_database)
):
    """Iniciar sesión"""
    user = user_crud.authenticate(
        db, 
        username=user_credentials.username, 
        password=user_credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user_crud.is_active(user):
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    
    # Crear token de acceso
    access_token = create_user_token(cast(int, user.id), cast(str, user.username))
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=User.from_orm(user)
    )

@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_database)
):
    """Endpoint compatible con OAuth2 para obtener token"""
    user = user_crud.authenticate(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_user_token(cast(int, user.id), cast(str, user.username))
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=User.from_orm(user)
    )

@router.get("/me", response_model=User)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Obtener información del usuario actual"""
    return current_user