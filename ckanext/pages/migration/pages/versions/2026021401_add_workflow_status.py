"""Add workflow status field

Revision ID: 2026021401
Revises: 1725892d1d94
Create Date: 2026-02-14 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026021401'
down_revision = '1725892d1d94'
branch_labels = None
depends_on = None


def upgrade():
    # Add status column with default value 'approved' for existing pages
    # New pages will have 'draft' status by default
    op.add_column(
        'ckanext_pages',
        sa.Column(
            'status',
            sa.UnicodeText,
            nullable=False,
            server_default='approved'
        )
    )


def downgrade():
    op.drop_column('ckanext_pages', 'status')
