"""Add submission workflow columns

Revision ID: 3a4b5c6d7e8f
Revises: 1725892d1d94
Create Date: 2026-02-15 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a4b5c6d7e8f'
down_revision = '1725892d1d94'
branch_labels = None
depends_on = None


def _column_exists(table_name, column_name):
    """Return True if the given column already exists."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(col['name'] == column_name for col in insp.get_columns(table_name))


def upgrade():
    columns = [
        ('submission_status', sa.Column('submission_status', sa.UnicodeText(), nullable=True, server_default=sa.text("'draft'"))),
        ('ihp_organization', sa.Column('ihp_organization', sa.UnicodeText(), nullable=True)),
        ('submitted_at', sa.Column('submitted_at', sa.DateTime(), nullable=True)),
        ('reviewed_at', sa.Column('reviewed_at', sa.DateTime(), nullable=True)),
        ('reviewed_by', sa.Column('reviewed_by', sa.UnicodeText(), nullable=True)),
    ]
    for col_name, col_def in columns:
        if not _column_exists('ckanext_pages', col_name):
            op.add_column('ckanext_pages', col_def)


def downgrade():
    for col_name in ['submission_status', 'ihp_organization', 'submitted_at', 'reviewed_at', 'reviewed_by']:
        if _column_exists('ckanext_pages', col_name):
            op.drop_column('ckanext_pages', col_name)
