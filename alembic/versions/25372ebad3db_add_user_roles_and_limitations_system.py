"""Add user roles and limitations system

Revision ID: 25372ebad3db
Revises: 128177144df2
Create Date: 2025-09-17 03:43:28.699210

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25372ebad3db'
down_revision: Union[str, Sequence[str], None] = '128177144df2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Crear tipo ENUM para roles de usuario
    user_role_enum = sa.Enum('admin', 'manager', 'seller', 'viewer', 'accountant', name='userrole')
    user_role_enum.create(op.get_bind())
    
    # Agregar nuevos campos al modelo User
    
    # Campo de rol
    op.add_column('users', sa.Column('role', user_role_enum, nullable=False, server_default='seller'))
    
    # Limitaciones de uso
    op.add_column('users', sa.Column('max_customers', sa.Integer(), nullable=False, server_default='10'))
    op.add_column('users', sa.Column('max_quotes', sa.Integer(), nullable=False, server_default='20'))
    op.add_column('users', sa.Column('max_orders', sa.Integer(), nullable=False, server_default='15'))
    op.add_column('users', sa.Column('max_invoices', sa.Integer(), nullable=False, server_default='10'))
    
    # Permisos específicos
    op.add_column('users', sa.Column('can_manage_inventory', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('can_view_reports', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('can_manage_tourism_regime', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('can_manage_deposits', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('can_export_data', sa.Boolean(), nullable=False, server_default='false'))
    
    # Información adicional para Paraguay
    op.add_column('users', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('department', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remover campos en orden inverso
    op.drop_column('users', 'department')
    op.drop_column('users', 'notes')
    op.drop_column('users', 'can_export_data')
    op.drop_column('users', 'can_manage_deposits')
    op.drop_column('users', 'can_manage_tourism_regime')
    op.drop_column('users', 'can_view_reports')
    op.drop_column('users', 'can_manage_inventory')
    op.drop_column('users', 'max_invoices')
    op.drop_column('users', 'max_orders')
    op.drop_column('users', 'max_quotes')
    op.drop_column('users', 'max_customers')
    op.drop_column('users', 'role')
    
    # Eliminar el tipo ENUM
    user_role_enum = sa.Enum(name='userrole')
    user_role_enum.drop(op.get_bind())
