"""
Database migrations for Data Stories

Provides migration functions to create and upgrade database schema.
"""

import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

log = logging.getLogger(__name__)


def upgrade():
    """
    Upgrade database schema for data stories.

    Creates all necessary tables if they don't exist.
    """
    log.info("Running Data Stories migration: creating tables...")

    # Create data_stories table
    if not table_exists('data_stories'):
        op.create_table(
            'data_stories',
            sa.Column('id', sa.String(100), primary_key=True),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('slug', sa.String(255), nullable=False),
            sa.Column('abstract', sa.Text),
            sa.Column('research_question', sa.Text),
            sa.Column('study_area', sa.Text),
            sa.Column('paper_doi', sa.String(255), nullable=True),
            sa.Column('paper_citation', sa.Text, nullable=True),
            sa.Column('countries', JSONB),
            sa.Column('partners', JSONB),
            sa.Column('project_type', sa.String(100), nullable=True),
            sa.Column('uploaded_images', JSONB),
            sa.Column('created_at', sa.DateTime, default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
            sa.Column('published_at', sa.DateTime, nullable=True),
            sa.Column('author_id', sa.String(100), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
            sa.Column('organization_id', sa.String(100), sa.ForeignKey('group.id', ondelete='SET NULL'), nullable=True),
            sa.Column('status', sa.String(50), default='draft'),
            sa.Column('submission_date', sa.DateTime, nullable=True),
            sa.Column('review_date', sa.DateTime, nullable=True),
            sa.Column('reviewer_id', sa.String(100), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
            sa.Column('is_public', sa.Boolean, default=False),
            sa.Column('is_featured', sa.Boolean, default=False),
            sa.Column('view_count', sa.Integer, default=0),
            sa.Column('version', sa.Integer, default=1),
            sa.Column('parent_version_id', sa.String(100), sa.ForeignKey('data_stories.id', ondelete='SET NULL'), nullable=True),
            sa.Column('meta_description', sa.Text),
            sa.Column('meta_keywords', sa.Text),
        )

        # Create indexes for data_stories
        op.create_index('idx_data_stories_slug', 'data_stories', ['slug'], unique=True)
        op.create_index('idx_data_stories_status', 'data_stories', ['status'])
        op.create_index('idx_data_stories_author', 'data_stories', ['author_id'])
        op.create_index('idx_data_stories_published', 'data_stories', ['published_at'])
        op.create_index('idx_data_stories_featured', 'data_stories', ['is_featured'])

        log.info("Created data_stories table")

    # Create data_story_sections table
    if not table_exists('data_story_sections'):
        op.create_table(
            'data_story_sections',
            sa.Column('id', sa.String(100), primary_key=True),
            sa.Column('story_id', sa.String(100), sa.ForeignKey('data_stories.id', ondelete='CASCADE'), nullable=False),
            sa.Column('section_type', sa.String(50), nullable=False),
            sa.Column('title', sa.String(255)),
            sa.Column('order_index', sa.Integer, nullable=False),
            sa.Column('content', sa.Text),
            sa.Column('image_url', sa.Text),
            sa.Column('video_url', sa.Text),
            sa.Column('terria_config', JSONB),
            sa.Column('terria_share_link', sa.Text),
            sa.Column('blocks_metadata', JSONB),
            sa.Column('is_visible', sa.Boolean, default=True),
            sa.Column('created_at', sa.DateTime, default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        )

        # Create indexes for data_story_sections
        op.create_index('idx_sections_story', 'data_story_sections', ['story_id'])
        op.create_index('idx_sections_order', 'data_story_sections', ['story_id', 'order_index'])
        op.create_index('idx_sections_type', 'data_story_sections', ['section_type'])

        log.info("Created data_story_sections table")

    # Create data_story_datasets table
    if not table_exists('data_story_datasets'):
        op.create_table(
            'data_story_datasets',
            sa.Column('id', sa.String(100), primary_key=True),
            sa.Column('story_id', sa.String(100), sa.ForeignKey('data_stories.id', ondelete='CASCADE'), nullable=False),
            sa.Column('dataset_id', sa.String(100), nullable=False),
            sa.Column('relationship_type', sa.String(50)),
            sa.Column('description', sa.Text),
            sa.Column('order_index', sa.Integer),
            sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        )

        # Create indexes and constraints for data_story_datasets
        op.create_index('idx_story_datasets_story', 'data_story_datasets', ['story_id'])
        op.create_index('idx_story_datasets_dataset', 'data_story_datasets', ['dataset_id'])
        op.create_unique_constraint('uq_story_dataset', 'data_story_datasets', ['story_id', 'dataset_id'])

        log.info("Created data_story_datasets table")

    # Create data_story_contributors table
    if not table_exists('data_story_contributors'):
        op.create_table(
            'data_story_contributors',
            sa.Column('id', sa.String(100), primary_key=True),
            sa.Column('story_id', sa.String(100), sa.ForeignKey('data_stories.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.String(100), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
            sa.Column('name', sa.String(255)),
            sa.Column('email', sa.String(255)),
            sa.Column('affiliation', sa.String(255)),
            sa.Column('orcid', sa.String(50)),
            sa.Column('role', sa.String(50)),
            sa.Column('order_index', sa.Integer),
            sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        )

        # Create indexes for data_story_contributors
        op.create_index('idx_contributors_story', 'data_story_contributors', ['story_id'])
        op.create_index('idx_contributors_user', 'data_story_contributors', ['user_id'])

        log.info("Created data_story_contributors table")

    # Create data_story_comments table
    if not table_exists('data_story_comments'):
        op.create_table(
            'data_story_comments',
            sa.Column('id', sa.String(100), primary_key=True),
            sa.Column('story_id', sa.String(100), sa.ForeignKey('data_stories.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.String(100), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
            sa.Column('section_id', sa.String(100), sa.ForeignKey('data_story_sections.id', ondelete='CASCADE'), nullable=True),
            sa.Column('content', sa.Text, nullable=False),
            sa.Column('comment_type', sa.String(50), default='comment'),
            sa.Column('parent_comment_id', sa.String(100), sa.ForeignKey('data_story_comments.id', ondelete='CASCADE'), nullable=True),
            sa.Column('is_resolved', sa.Boolean, default=False),
            sa.Column('created_at', sa.DateTime, default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        )

        # Create indexes for data_story_comments
        op.create_index('idx_comments_story', 'data_story_comments', ['story_id'])
        op.create_index('idx_comments_user', 'data_story_comments', ['user_id'])
        op.create_index('idx_comments_section', 'data_story_comments', ['section_id'])

        log.info("Created data_story_comments table")

    # Create data_story_revisions table
    if not table_exists('data_story_revisions'):
        op.create_table(
            'data_story_revisions',
            sa.Column('id', sa.String(100), primary_key=True),
            sa.Column('story_id', sa.String(100), sa.ForeignKey('data_stories.id', ondelete='CASCADE'), nullable=False),
            sa.Column('version', sa.Integer, nullable=False),
            sa.Column('title', sa.String(255)),
            sa.Column('content_snapshot', JSONB),
            sa.Column('changed_by', sa.String(100), sa.ForeignKey('user.id'), nullable=False),
            sa.Column('change_summary', sa.Text),
            sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        )

        # Create indexes for data_story_revisions
        op.create_index('idx_revisions_story', 'data_story_revisions', ['story_id'])
        op.create_index('idx_revisions_version', 'data_story_revisions', ['story_id', 'version'])

        log.info("Created data_story_revisions table")

    # Add blocks_metadata column if not exists (migration for existing tables)
    if table_exists('data_story_sections') and not column_exists('data_story_sections', 'blocks_metadata'):
        op.add_column('data_story_sections', sa.Column('blocks_metadata', JSONB))
        log.info("Added blocks_metadata column to data_story_sections table")

    # Add countries column if not exists (migration for existing tables)
    if table_exists('data_stories') and not column_exists('data_stories', 'countries'):
        op.add_column('data_stories', sa.Column('countries', JSONB))
        log.info("Added countries column to data_stories table")

    # Add paper_doi column if not exists (migration for existing tables)
    if table_exists('data_stories') and not column_exists('data_stories', 'paper_doi'):
        op.add_column('data_stories', sa.Column('paper_doi', sa.String(255), nullable=True))
        log.info("Added paper_doi column to data_stories table")

    # Add paper_citation column if not exists (migration for existing tables)
    if table_exists('data_stories') and not column_exists('data_stories', 'paper_citation'):
        op.add_column('data_stories', sa.Column('paper_citation', sa.Text, nullable=True))
        log.info("Added paper_citation column to data_stories table")

    # Add uploaded_images column if not exists (migration for existing tables)
    if table_exists('data_stories') and not column_exists('data_stories', 'uploaded_images'):
        op.add_column('data_stories', sa.Column('uploaded_images', JSONB))
        log.info("Added uploaded_images column to data_stories table")

    # Add partners column if not exists (migration for existing tables)
    if table_exists('data_stories') and not column_exists('data_stories', 'partners'):
        op.add_column('data_stories', sa.Column('partners', JSONB))
        log.info("Added partners column to data_stories table")

    # Add project_type column if not exists (migration for existing tables)
    if table_exists('data_stories') and not column_exists('data_stories', 'project_type'):
        op.add_column('data_stories', sa.Column('project_type', sa.String(100), nullable=True))
        log.info("Added project_type column to data_stories table")

    log.info("Data Stories migration completed successfully")


def downgrade():
    """
    Downgrade database schema for data stories.

    Drops all data stories tables.
    """
    log.info("Running Data Stories migration: dropping tables...")

    # Drop tables in reverse order (to respect foreign keys)
    tables = [
        'data_story_revisions',
        'data_story_comments',
        'data_story_contributors',
        'data_story_datasets',
        'data_story_sections',
        'data_stories',
    ]

    for table_name in tables:
        if table_exists(table_name):
            op.drop_table(table_name)
            log.info(f"Dropped {table_name} table")

    log.info("Data Stories downgrade completed")


def table_exists(table_name):
    """
    Check if a table exists in the database.

    Args:
        table_name: Name of the table to check

    Returns:
        Boolean indicating if table exists
    """
    from ckan import model
    try:
        inspector = sa.inspect(model.Session.bind)
        table_names = inspector.get_table_names()
        return table_name in table_names
    except Exception as e:
        log.error(f"Error checking table existence: {str(e)}")
        return False


def column_exists(table_name, column_name):
    """
    Check if a column exists in a database table.

    Args:
        table_name: Name of the table
        column_name: Name of the column to check

    Returns:
        Boolean indicating if column exists
    """
    from ckan import model
    try:
        inspector = sa.inspect(model.Session.bind)
        columns = [c['name'] for c in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        log.error(f"Error checking column existence: {str(e)}")
        return False
