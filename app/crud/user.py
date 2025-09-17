from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user import User
from app.schemas.auth import UserCreate, UserUpdate
from app.core.auth import get_password_hash, verify_password

class CRUDUser:
    def get(self, db: Session, user_id: int) -> Optional[User]:
        """Obtener usuario por ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        return db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Obtener usuario por username"""
        return db.query(User).filter(User.username == username).first()
    
    def create(self, db: Session, user_in: UserCreate) -> User:
        """Crear nuevo usuario"""
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            username=user_in.username,
            full_name=user_in.full_name,
            hashed_password=hashed_password,
            is_active=user_in.is_active,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def update(self, db: Session, db_user: User, user_in: UserUpdate) -> User:
        """Actualizar usuario"""
        update_data = user_in.dict(exclude_unset=True)
        
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
            
        for field, value in update_data.items():
            setattr(db_user, field, value)
            
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def authenticate(self, db: Session, username: str, password: str) -> Optional[User]:
        """Autenticar usuario"""
        user = self.get_by_username(db, username=username)
        if not user:
            user = self.get_by_email(db, email=username)
        if not user or not verify_password(password, str(user.hashed_password)):
            return None
        return user
    
    def is_active(self, user: User) -> bool:
        """Verificar si usuario está activo"""
        return bool(user.is_active)
    
    def is_superuser(self, user: User) -> bool:
        """Verificar si usuario es superusuario"""
        return bool(user.is_superuser)

# Instancia única del CRUD
user_crud = CRUDUser()