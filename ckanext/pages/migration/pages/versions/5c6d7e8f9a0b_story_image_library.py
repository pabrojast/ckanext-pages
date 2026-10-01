"""Add personal story image library.

Revision ID: 5c6d7e8f9a0b
Revises: 4b5c6d7e8f9a
"""
from alembic import op
import sqlalchemy as sa

revision = '5c6d7e8f9a0b'
down_revision = '4b5c6d7e8f9a'
branch_labels = None
depends_on = None


def upgrade():
    # CKAN db init (and Pages' legacy init_tables) may create registered models.
    if sa.inspect(op.get_bind()).has_table('ckanext_pages_story_images'):
        return
    op.create_table('ckanext_pages_story_images',
        sa.Column('id', sa.UnicodeText, primary_key=True),
        sa.Column('owner_id', sa.UnicodeText, sa.ForeignKey('user.id', ondelete='SET NULL')),
        *[sa.Column(name, sa.UnicodeText, nullable=False) for name in
          ('filename', 'storage_kind', 'original_name', 'mime', 'alt', 'caption', 'credit')],
        sa.Column('digest', sa.String(64), nullable=False),
        *[sa.Column(name, sa.Integer, nullable=False) for name in ('size', 'width', 'height')],
        sa.Column('archived', sa.Boolean, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('owner_id', 'digest', name='story_image_owner_digest'))
    op.create_index('story_image_owner_created', 'ckanext_pages_story_images', ['owner_id', 'created_at'])


def downgrade():
    op.drop_table('ckanext_pages_story_images')
