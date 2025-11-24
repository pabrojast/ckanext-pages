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

                # Debug logging for JSONB fields
                if name in ('blocks_metadata', 'terria_config'):
                    log.info(f"[TABLE_DICTIZE] {obj_class_name}.{name}: type={type(value)} value={value}")
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

    Args:
        datasets: List of DataStoryDataset objects
        context: CKAN context dict

    Returns:
        List of dictionaries
    """
    return [table_dictize(dataset, context) for dataset in datasets]


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
