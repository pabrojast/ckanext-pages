"""
Database utilities for Featured Viewers
"""

import datetime
import logging
import uuid as uuid_module
from typing import Dict, Any

try:
    from sqlalchemy.engine import Row
except ImportError:
    try:
        from sqlalchemy.engine.result import RowProxy as Row
    except ImportError:
        class Row:
            pass

from sqlalchemy.orm import class_mapper

from ckan import model

log = logging.getLogger(__name__)


def make_uuid() -> str:
    """Generate a UUID for new entities."""
    return str(uuid_module.uuid4())


def init_tables(engine):
    """
    Initialize database tables for featured viewers.

    Creates tables if they don't exist. Safe to call multiple times.
    """
    from ckanext.pages.featured_viewers.db.models import (  # noqa: F401
        FeaturedViewer,
        ViewerDataset,
        MapRoom,
        MapRoomViewer,
    )

    try:
        from ckan.plugins.toolkit import BaseModel
    except ImportError:
        from ckan.model.meta import metadata
        from sqlalchemy.ext.declarative import declarative_base
        BaseModel = declarative_base(metadata=metadata)

    BaseModel.metadata.create_all(engine)

    # Add new columns to existing tables (safe to run multiple times)
    _add_column_if_not_exists(engine, 'featured_viewers', 'initiative', 'VARCHAR(100)')
    _add_column_if_not_exists(engine, 'featured_viewers', 'map_tabs', 'JSONB')
    _add_column_if_not_exists(engine, 'featured_viewers', 'map_height', 'INTEGER')
    _add_column_if_not_exists(engine, 'map_rooms', 'initiative', 'VARCHAR(100)')
    _add_column_if_not_exists(engine, 'map_rooms', 'organization_id', 'VARCHAR(100)')
    _add_column_if_not_exists(engine, 'map_rooms', 'countries', 'JSONB')

    log.info("Featured Viewers tables initialized")


def _add_column_if_not_exists(engine, table, column, col_type):
    """Add a column to an existing table if it doesn't already exist."""
    from sqlalchemy import text
    try:
        engine.execute(text(
            f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}"
        ))
    except Exception:
        try:
            with engine.connect() as conn:
                conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}"
                ))
                conn.commit()
        except Exception as e:
            log.debug(f"Column {column} on {table} may already exist: {e}")


def table_dictize(obj, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Convert a model object to a dictionary."""
    result_dict = {}

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
            except Exception as e:
                log.error(f"Error processing field {name}: {str(e)}")
                continue

        result_dict.update(kwargs)
        return result_dict

    except Exception as e:
        log.error(f"Error in table_dictize: {str(e)}")
        return {}


def dictize_datasets(datasets, context: Dict[str, Any]) -> list:
    """Convert a list of dataset link objects to dicts, enriched with CKAN info."""
    import ckan.plugins.toolkit as tk

    result = []
    for dataset_link in datasets:
        link_dict = table_dictize(dataset_link, context)

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


def get_user_info(user_id: str) -> Dict[str, Any]:
    """Get basic user information."""
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
    """Get basic organization information."""
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
