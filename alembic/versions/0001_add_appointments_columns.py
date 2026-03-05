"""add appointments columns

Revision ID: 0001_add_appointments_columns
Revises: 
Create Date: 2026-02-17 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_appointments_columns'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add columns to appointments table if they don't exist
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = [c['name'] for c in insp.get_columns('appointments')]

    if 'client_phone' not in cols:
        op.add_column('appointments', sa.Column('client_phone', sa.String(), nullable=True))
    if 'client_email' not in cols:
        op.add_column('appointments', sa.Column('client_email', sa.String(), nullable=True))
    if 'service_price' not in cols:
        op.add_column('appointments', sa.Column('service_price', sa.Float(), nullable=True))
    if 'payment_status' not in cols:
        op.add_column('appointments', sa.Column('payment_status', sa.String(), nullable=True, server_default='unpaid'))
    if 'payment_method' not in cols:
        op.add_column('appointments', sa.Column('payment_method', sa.String(), nullable=True))
    if 'created_at' not in cols:
        op.add_column('appointments', sa.Column('created_at', sa.String(), nullable=True))


def downgrade():
    # Downgrade: drop the columns if exist (SQLite may not support drop in older versions)
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = [c['name'] for c in insp.get_columns('appointments')]

    # Alembic + SQLite: dropping columns is not supported by simple op.drop_column in older SQLite.
    # We try to drop using op.drop_column where possible; if not supported, keep no-op to avoid data loss.
    try:
        if 'created_at' in cols:
            op.drop_column('appointments', 'created_at')
        if 'payment_method' in cols:
            op.drop_column('appointments', 'payment_method')
        if 'payment_status' in cols:
            op.drop_column('appointments', 'payment_status')
        if 'service_price' in cols:
            op.drop_column('appointments', 'service_price')
        if 'client_email' in cols:
            op.drop_column('appointments', 'client_email')
        if 'client_phone' in cols:
            op.drop_column('appointments', 'client_phone')
    except Exception:
        # If drop isn't supported, do nothing to avoid breaking existing DBs.
        pass
