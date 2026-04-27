"""Add featured flag column

Revision ID: 4b5c6d7e8f9a
Revises: 3a4b5c6d7e8f
Create Date: 2026-04-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b5c6d7e8f9a'
down_revision = '3a4b5c6d7e8f'
branch_labels = None
depends_on = None


def _column_exists(table_name, column_name):
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(col['name'] == column_name for col in insp.get_columns(table_name))


def upgrade():
    if not _column_exists('ckanext_pages', 'featured'):
        op.add_column(
            'ckanext_pages',
            sa.Column(
                'featured',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('false'),
            ),
        )


def downgrade():
    if _column_exists('ckanext_pages', 'featured'):
        op.drop_column('ckanext_pages', 'featured')
