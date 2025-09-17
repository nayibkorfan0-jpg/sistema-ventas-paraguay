from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_database
from app.core.auth import verify_token
from app.crud.user import user_crud
from app.models.user import User

# Configurar security scheme
security = HTTPBearer()

def get_current_user(
    db: Session = Depends(get_database),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Obtener usuario actual desde JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    username = verify_token(credentials.credentials)
    if username is None:
        raise credentials_exception
        
    user = user_crud.get_by_username(db, username=username)
    if user is None:
        raise credentials_exception
        
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Obtener usuario actual activo"""
    if not user_crud.is_active(current_user):
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Obtener usuario actual que sea superusuario"""
    if not user_crud.is_superuser(current_user):
        raise HTTPException(
            status_code=400, 
            detail="El usuario no tiene suficientes privilegios"
        )
    return current_user

# ===== NEW ROLE-BASED ACCESS CONTROL =====

def get_admin_or_manager(current_user: User = Depends(get_current_user)) -> User:
    """Requiere usuario con rol admin o manager"""
    from app.models.user import UserRole
    
    allowed_roles = [UserRole.ADMIN, UserRole.MANAGER]
    if current_user.role not in allowed_roles and not bool(current_user.is_superuser):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Se requiere rol de administrador o gerente"
        )
    return current_user

def get_admin_only(current_user: User = Depends(get_current_user)) -> User:
    """Requiere usuario con rol admin solamente"""
    from app.models.user import UserRole
    
    if current_user.role != UserRole.ADMIN and not bool(current_user.is_superuser):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Se requiere rol de administrador"
        )
    return current_user

def check_user_permission(permission: str):
    """Decorator para verificar permisos específicos del usuario"""
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if bool(current_user.is_superuser):
            return current_user
            
        # Check specific permissions
        user_permissions = {
            'manage_inventory': getattr(current_user, 'can_manage_inventory', False),
            'view_reports': getattr(current_user, 'can_view_reports', False),
            'manage_tourism_regime': getattr(current_user, 'can_manage_tourism_regime', False),
            'manage_deposits': getattr(current_user, 'can_manage_deposits', False),
            'export_data': getattr(current_user, 'can_export_data', False)
        }
        
        if not user_permissions.get(permission, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: No tiene permisos para {permission}"
            )
        return current_user
    return permission_checker

# ===== USAGE LIMIT ENFORCEMENT =====

def check_user_limits(limit_type: str):
    """Decorator para verificar límites de uso del usuario"""
    def limit_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_database)
    ) -> User:
        from app.models.user import UserRole
        
        if bool(current_user.is_superuser) or current_user.role == UserRole.ADMIN:  # type: ignore
            return current_user  # Admin users have no limits
            
        # Get current usage from database
        from app.crud.usage_limits import get_user_usage
        
        current_usage = get_user_usage(db, int(current_user.id), limit_type)  # type: ignore
        user_limits = {
            'customers': int(getattr(current_user, 'max_customers', 0)),
            'quotes': int(getattr(current_user, 'max_quotes', 0)),
            'orders': int(getattr(current_user, 'max_orders', 0)),
            'invoices': int(getattr(current_user, 'max_invoices', 0))
        }
        
        max_allowed = user_limits.get(limit_type, 0)
        
        if current_usage >= max_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Límite excedido: Máximo {max_allowed} {limit_type} permitidos para su rol ({current_user.role})"
            )
        return current_user
    return limit_checker