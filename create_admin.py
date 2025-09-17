#!/usr/bin/env python3
"""
Script para crear usuario administrador
"""
from app.core.database import SessionLocal
from app.models.user import User
from app.core.auth import get_password_hash

def create_admin_user():
    """Crear usuario administrador por defecto"""
    db = SessionLocal()
    
    try:
        # Verificar si ya existe el usuario admin
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            print("✅ El usuario admin ya existe")
            print("=" * 50)
            print("📧 Usuario: admin")
            print("🔑 Contraseña: admin123")
            print("=" * 50)
            return
        
        from app.models.user import UserRole
        
        # Crear nuevo usuario administrador
        admin_user = User(
            username="admin",
            email="admin@empresa.py",
            full_name="Administrador Sistema",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True,
            role=UserRole.ADMIN,
            # Permisos completos para admin
            can_create_customers=True,
            can_manage_inventory=True,
            can_view_reports=True,
            can_manage_tourism_regime=True,
            can_manage_deposits=True,
            can_export_data=True,
            # Límites altos para admin
            max_customers=10000,
            max_quotes=10000,
            max_orders=10000,
            max_invoices=10000
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Usuario administrador creado exitosamente!")
        print("=" * 50)
        print("📧 Usuario: admin")
        print("🔑 Contraseña: admin123")
        print("=" * 50)
        print("⚠️  IMPORTANTE: Cambie esta contraseña después del primer login")
        
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Creando usuario administrador para el sistema...")
    create_admin_user()