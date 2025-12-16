"""
Database utilities for Data Stories

Provides helper functions for database operations.
"""

import datetime
import json
import logging
import uuid as uuid_module
from typing import Dict, Any

try:
    # SQLAlchemy 1.4+
    from sqlalchemy.engine import Row  # type: ignore
except ImportError:  # pragma: no cover - fallback for older SQLAlchemy
    try:
        from sqlalchemy.engine.result import RowProxy as Row  # type: ignore
    except ImportError:
        class Row:  # type: ignore
            """Minimal stand-in used when SQLAlchemy row classes are unavailable."""

            pass

from sqlalchemy.orm import class_mapper

from ckan import model

log = logging.getLogger(__name__)


def make_uuid() -> str:
    """Generate a UUID for new entities."""
    return str(uuid_module.uuid4())


def _ensure_blocks_metadata_column(engine):
    """
    Ensure the blocks_metadata column exists in data_story_sections table.

    Uses direct SQL for maximum compatibility across different SQLAlchemy versions.
    This handles the migration automatically when the plugin starts.
    """
    import sqlalchemy as sa

    # Check if column exists using information_schema (PostgreSQL compatible)
    check_column_sql = sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'data_story_sections'
        AND column_name = 'blocks_metadata'
    """)

    # Check if table exists
    check_table_sql = sa.text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name = 'data_story_sections'
    """)

    try:
        with engine.connect() as conn:
            # First check if table exists
            result = conn.execute(check_table_sql)
            table_exists = result.fetchone() is not None

            if not table_exists:
                log.info("data_story_sections table does not exist yet, will be created by metadata.create_all()")
                return

            # Check if column exists
            result = conn.execute(check_column_sql)
            column_exists = result.fetchone() is not None

            if not column_exists:
                log.info("Adding blocks_metadata column to data_story_sections table...")
                add_column_sql = sa.text(
                    'ALTER TABLE data_story_sections ADD COLUMN blocks_metadata JSONB'
                )
                conn.execute(add_column_sql)

                # Handle commit for different SQLAlchemy versions
                try:
                    conn.commit()
                except AttributeError:
                    # SQLAlchemy 2.0+ with autocommit or different transaction handling
                    pass

                log.info("Successfully added blocks_metadata column to data_story_sections")
            else:
                log.debug("blocks_metadata column already exists in data_story_sections")

    except Exception as e:
        log.error(f"Error ensuring blocks_metadata column: {str(e)}")
        # Try alternative approach with IF NOT EXISTS (PostgreSQL 9.6+)
        try:
            with engine.connect() as conn:
                # PostgreSQL 9.6+ supports ADD COLUMN IF NOT EXISTS
                add_column_sql = sa.text(
                    'ALTER TABLE data_story_sections ADD COLUMN IF NOT EXISTS blocks_metadata JSONB'
                )
                conn.execute(add_column_sql)
                try:
                    conn.commit()
                except AttributeError:
                    pass
                log.info("Added blocks_metadata column using IF NOT EXISTS fallback")
        except Exception as e2:
            log.warning(f"Could not add blocks_metadata column: {str(e2)}")


def _ensure_countries_column(engine):
    """
    Ensure the countries column exists in data_stories table.

    Adds the column when missing to keep existing installations aligned with
    new multi-country support.
    """
    import sqlalchemy as sa

    check_table_sql = sa.text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name = 'data_stories'
    """)

    check_column_sql = sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'data_stories'
        AND column_name = 'countries'
    """)

    try:
        with engine.connect() as conn:
            table_exists = conn.execute(check_table_sql).fetchone() is not None
            if not table_exists:
                log.info("data_stories table does not exist yet, will be created by metadata.create_all()")
                return

            column_exists = conn.execute(check_column_sql).fetchone() is not None
            if column_exists:
                log.debug("countries column already exists in data_stories")
                return

            log.info("Adding countries column to data_stories table...")
            add_column_sql = sa.text('ALTER TABLE data_stories ADD COLUMN countries JSONB')
            conn.execute(add_column_sql)
            try:
                conn.commit()
            except AttributeError:
                pass
            log.info("Successfully added countries column to data_stories")
    except Exception as e:
        log.warning(f"Could not ensure countries column on data_stories: {str(e)}")


def _ensure_paper_doi_column(engine):
    """
    Ensure the paper_doi column exists in data_stories table.

    Adds the column when missing to support research paper linking.
    """
    import sqlalchemy as sa

    check_table_sql = sa.text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name = 'data_stories'
    """)

    check_column_sql = sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'data_stories'
        AND column_name = 'paper_doi'
    """)

    try:
        with engine.connect() as conn:
            table_exists = conn.execute(check_table_sql).fetchone() is not None
            if not table_exists:
                log.info("data_stories table does not exist yet, will be created by metadata.create_all()")
                return

            column_exists = conn.execute(check_column_sql).fetchone() is not None
            if column_exists:
                log.debug("paper_doi column already exists in data_stories")
                return

            log.info("Adding paper_doi column to data_stories table...")
            add_column_sql = sa.text('ALTER TABLE data_stories ADD COLUMN paper_doi VARCHAR(255)')
            conn.execute(add_column_sql)
            try:
                conn.commit()
            except AttributeError:
                pass
            log.info("Successfully added paper_doi column to data_stories")
    except Exception as e:
        log.warning(f"Could not ensure paper_doi column on data_stories: {str(e)}")


def _ensure_paper_citation_column(engine):
    """
    Ensure the paper_citation column exists in data_stories table.

    Adds the column when missing to support research paper citation storage.
    """
    import sqlalchemy as sa

    check_table_sql = sa.text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name = 'data_stories'
    """)

    check_column_sql = sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'data_stories'
        AND column_name = 'paper_citation'
    """)

    try:
        with engine.connect() as conn:
            table_exists = conn.execute(check_table_sql).fetchone() is not None
            if not table_exists:
                log.info("data_stories table does not exist yet, will be created by metadata.create_all()")
                return

            column_exists = conn.execute(check_column_sql).fetchone() is not None
            if column_exists:
                log.debug("paper_citation column already exists in data_stories")
                return

            log.info("Adding paper_citation column to data_stories table...")
            add_column_sql = sa.text('ALTER TABLE data_stories ADD COLUMN paper_citation TEXT')
            conn.execute(add_column_sql)
            try:
                conn.commit()
            except AttributeError:
                pass
            log.info("Successfully added paper_citation column to data_stories")
    except Exception as e:
        log.warning(f"Could not ensure paper_citation column on data_stories: {str(e)}")


def _ensure_uploaded_images_column(engine):
    """
    Ensure the uploaded_images column exists in data_stories table.

    Adds the column when missing to support image gallery metadata storage.
    """
    import sqlalchemy as sa

    check_table_sql = sa.text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name = 'data_stories'
    """)

    check_column_sql = sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'data_stories'
        AND column_name = 'uploaded_images'
    """)

    try:
        with engine.connect() as conn:
            table_exists = conn.execute(check_table_sql).fetchone() is not None
            if not table_exists:
                log.info("data_stories table does not exist yet, will be created by metadata.create_all()")
                return

            column_exists = conn.execute(check_column_sql).fetchone() is not None
            if column_exists:
                log.debug("uploaded_images column already exists in data_stories")
                return

            log.info("Adding uploaded_images column to data_stories table...")
            add_column_sql = sa.text('ALTER TABLE data_stories ADD COLUMN uploaded_images JSONB')
            conn.execute(add_column_sql)
            try:
                conn.commit()
            except AttributeError:
                pass
            log.info("Successfully added uploaded_images column to data_stories")
    except Exception as e:
        log.warning(f"Could not ensure uploaded_images column on data_stories: {str(e)}")


def _ensure_partners_column(engine):
    """
    Ensure the partners column exists in data_stories table.
    """
    import sqlalchemy as sa

    check_table_sql = sa.text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name = 'data_stories'
    """)

    check_column_sql = sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'data_stories'
        AND column_name = 'partners'
    """)

    try:
        with engine.connect() as conn:
            table_exists = conn.execute(check_table_sql).fetchone() is not None
            if not table_exists:
                log.info("data_stories table does not exist yet, will be created by metadata.create_all()")
                return

            column_exists = conn.execute(check_column_sql).fetchone() is not None
            if column_exists:
                log.debug("partners column already exists in data_stories")
                return

            log.info("Adding partners column to data_stories table...")
            add_column_sql = sa.text('ALTER TABLE data_stories ADD COLUMN partners JSONB')
            conn.execute(add_column_sql)
            try:
                conn.commit()
            except AttributeError:
                pass
            log.info("Successfully added partners column to data_stories")
    except Exception as e:
        log.warning(f"Could not ensure partners column on data_stories: {str(e)}")


def _ensure_project_type_column(engine):
    """
    Ensure the project_type column exists in data_stories table.
    """
    import sqlalchemy as sa

    check_table_sql = sa.text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name = 'data_stories'
    """)

    check_column_sql = sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'data_stories'
        AND column_name = 'project_type'
    """)

    try:
        with engine.connect() as conn:
            table_exists = conn.execute(check_table_sql).fetchone() is not None
            if not table_exists:
                log.info("data_stories table does not exist yet, will be created by metadata.create_all()")
                return

            column_exists = conn.execute(check_column_sql).fetchone() is not None
            if column_exists:
                log.debug("project_type column already exists in data_stories")
                return

            log.info("Adding project_type column to data_stories table...")
            add_column_sql = sa.text('ALTER TABLE data_stories ADD COLUMN project_type VARCHAR(100)')
            conn.execute(add_column_sql)
            try:
                conn.commit()
            except AttributeError:
                pass
            log.info("Successfully added project_type column to data_stories")
    except Exception as e:
        log.warning(f"Could not ensure project_type column on data_stories: {str(e)}")


def init_tables(engine):
    """
    Initialize database tables for data stories.

    Args:
        engine: SQLAlchemy engine

    This should be called during CKAN database initialization.
    """
    from ckanext.pages.data_stories.db.models import (
        DataStory,
        DataStorySection,
        DataStoryDataset,
        DataStoryContributor,
        DataStoryComment,
        DataStoryRevision,
    )
    import sqlalchemy as sa
    from sqlalchemy.dialects.postgresql import JSONB

    # Import BaseModel to get metadata
    try:
        from ckan.plugins.toolkit import BaseModel
    except ImportError:
        from ckan.model.meta import metadata
        from sqlalchemy.ext.declarative import declarative_base
        BaseModel = declarative_base(metadata=metadata)

    # Create tables
    BaseModel.metadata.create_all(engine)

    # Add missing columns to existing tables (migrations for existing installations)
    # Using direct SQL for maximum compatibility across SQLAlchemy versions
    _ensure_blocks_metadata_column(engine)
    _ensure_countries_column(engine)
    _ensure_paper_doi_column(engine)
    _ensure_paper_citation_column(engine)
    _ensure_uploaded_images_column(engine)
    _ensure_partners_column(engine)
    _ensure_project_type_column(engine)

    log.info("Data Stories tables initialized")


def table_dictize(obj, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Convert a model object to a dictionary.

    Args:
        obj: SQLAlchemy model instance or Row
        context: CKAN context dict
        **kwargs: Additional fields to add to result

    Returns:
        Dictionary representation of the object
    """
    result_dict = {}
    obj_class_name = obj.__class__.__name__ if obj else 'None'

    try:
        if isinstance(obj, Row):
            fields = obj.keys()
        else:
            ModelClass = obj.__class__
            table = class_mapper(ModelClass).mapped_table
            fields = [field.name for field in table.c]

        for field in fields:
            name = field
            if name in ('current', 'expired_timestamp', 'expired_id', 'continuity_id'):
                continue

            try:
                value = getattr(obj, name)

                if value is None:
                    result_dict[name] = value
                elif isinstance(value, dict):
                    result_dict[name] = value
                elif isinstance(value, int):
                    result_dict[name] = value
                elif isinstance(value, bool):
                    result_dict[name] = value
                elif isinstance(value, datetime.datetime):
                    result_dict[name] = value.isoformat()
                elif isinstance(value, list):
                    result_dict[name] = value
                else:
                    result_dict[name] = str(value)

                # Debug logging for JSONB fields (only log type and length to avoid performance issues)
                if name in ('blocks_metadata', 'terria_config', 'countries', 'uploaded_images'):
                    value_len = len(str(value)) if value else 0
                    log.debug(f"[TABLE_DICTIZE] {obj_class_name}.{name}: type={type(value)} len={value_len}")
            except Exception as e:
                log.error(f"Error processing field {name}: {str(e)}")
                continue

        result_dict.update(kwargs)

        return result_dict

    except Exception as e:
        log.error(f"Error in table_dictize: {str(e)}")
        return {}


def dictize_sections(sections, context: Dict[str, Any]) -> list:
    """
    Convert a list of section objects to dictionaries.

    Args:
        sections: List of DataStorySection objects
        context: CKAN context dict

    Returns:
        List of dictionaries
    """
    return [table_dictize(section, context) for section in sections]


def dictize_datasets(datasets, context: Dict[str, Any]) -> list:
    """
    Convert a list of dataset link objects to dictionaries.
    Enriches each link with CKAN dataset information.

    Args:
        datasets: List of DataStoryDataset objects
        context: CKAN context dict

    Returns:
        List of dictionaries with dataset info included
    """
    import ckan.plugins.toolkit as tk

    result = []
    for dataset_link in datasets:
        link_dict = table_dictize(dataset_link, context)

        # Try to fetch the CKAN dataset info
        try:
            dataset_id = link_dict.get('dataset_id')
            if dataset_id:
                dataset_info = tk.get_action('package_show')(
                    {'ignore_auth': True},
                    {'id': dataset_id}
                )
                link_dict['dataset'] = dataset_info
        except Exception as e:
            log.warning(f"Could not fetch dataset {link_dict.get('dataset_id')}: {str(e)}")
            link_dict['dataset'] = {}

        result.append(link_dict)

    return result


def dictize_contributors(contributors, context: Dict[str, Any]) -> list:
    """
    Convert a list of contributor objects to dictionaries.

    Args:
        contributors: List of DataStoryContributor objects
        context: CKAN context dict

    Returns:
        List of dictionaries
    """
    return [table_dictize(contributor, context) for contributor in contributors]


def dictize_comments(comments, context: Dict[str, Any]) -> list:
    """
    Convert a list of comment objects to dictionaries.

    Args:
        comments: List of DataStoryComment objects
        context: CKAN context dict

    Returns:
        List of dictionaries
    """
    return [table_dictize(comment, context) for comment in comments]


def get_user_info(user_id: str) -> Dict[str, Any]:
    """
    Get basic user information.

    Args:
        user_id: CKAN user ID

    Returns:
        Dictionary with user info
    """
    try:
        user = model.User.get(user_id)
        if user:
            return {
                'id': user.id,
                'name': user.name,
                'fullname': user.fullname,
                'email': user.email,
            }
    except Exception as e:
        log.error(f"Error getting user info: {str(e)}")

    return {}


def get_organization_info(org_id: str) -> Dict[str, Any]:
    """
    Get basic organization information.

    Args:
        org_id: CKAN organization ID

    Returns:
        Dictionary with organization info
    """
    try:
        org = model.Group.get(org_id)
        if org and org.type == 'organization':
            return {
                'id': org.id,
                'name': org.name,
                'title': org.title,
                'description': org.description,
            }
    except Exception as e:
        log.error(f"Error getting organization info: {str(e)}")

    return {}
