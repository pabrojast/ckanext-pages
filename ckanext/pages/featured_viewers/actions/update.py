"""
Featured viewer update actions.
"""

import datetime
import json
import logging

from ckan import model
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df

from ckanext.pages.featured_viewers.db.models import FeaturedViewer, ViewerDataset
from ckanext.pages.featured_viewers.db.utils import make_uuid, table_dictize
from ckanext.pages.featured_viewers.logic.schema import (
    featured_viewer_schema, validate_slug,
)

log = logging.getLogger(__name__)


def featured_viewer_update(context, data_dict):
    """
    Update an existing featured viewer.
    """
    log.info("[FEATURED_VIEWER_UPDATE] Starting update")

    tk.check_access('featured_viewer_update', context, data_dict)

    viewer_id = data_dict.get('id')
    if not viewer_id:
        raise tk.ValidationError({'id': ['Viewer ID is required']})

    viewer = FeaturedViewer.get(id=viewer_id)
    if not viewer:
        raise tk.ObjectNotFound(f"Viewer not found: {viewer_id}")

    # Capture JSONB fields before validation
    countries_raw = data_dict.get('countries')
    tags_raw = data_dict.get('tags')
    map_layers_raw = data_dict.get('map_layers')
    terria_config_raw = data_dict.get('terria_config')

    schema = featured_viewer_schema()
    data, errors = df.validate(data_dict, schema, context)
    if errors:
        raise tk.ValidationError(errors)

    # Update slug if changed
    new_slug = data.get('slug')
    if new_slug and new_slug != viewer.slug:
        is_valid, error_msg = validate_slug(new_slug)
        if not is_valid:
            raise tk.ValidationError({'slug': [error_msg]})
        existing = FeaturedViewer.get(slug=new_slug)
        if existing and existing.id != viewer.id:
            raise tk.ValidationError({'slug': ['A viewer with this slug already exists']})
        viewer.slug = new_slug

    # Update fields
    if 'title' in data:
        viewer.title = data['title']
    if 'description' in data:
        viewer.description = data['description']
    if 'category' in data:
        viewer.category = data['category']
    if 'icon_class' in data:
        viewer.icon_class = data['icon_class']
    if 'thumbnail_url' in data:
        viewer.thumbnail_url = data['thumbnail_url']
    if 'terria_share_link' in data:
        viewer.terria_share_link = data['terria_share_link']
    if 'meta_description' in data:
        viewer.meta_description = data['meta_description']
    if 'organization_id' in data:
        viewer.organization_id = data['organization_id'] or None

    # JSONB fields
    if terria_config_raw is not None:
        viewer.terria_config = _parse_json_field(terria_config_raw)
    if map_layers_raw is not None:
        viewer.map_layers = _parse_json_field(map_layers_raw) or []
    if tags_raw is not None:
        viewer.tags = _parse_json_field(tags_raw) or []
    if countries_raw is not None:
        viewer.countries = _parse_json_field(countries_raw) or []

    # Visibility fields from raw data_dict
    if 'is_featured' in data_dict:
        viewer.is_featured = bool(data_dict['is_featured'])
    if 'is_public' in data_dict:
        viewer.is_public = bool(data_dict['is_public'])
    if 'order_index' in data_dict:
        viewer.order_index = int(data_dict['order_index'])
    if 'status' in data_dict:
        new_status = data_dict['status']
        if new_status in ('draft', 'published'):
            if new_status == 'published' and viewer.status != 'published':
                viewer.published_at = datetime.datetime.utcnow()
            viewer.status = new_status

    viewer.updated_at = datetime.datetime.utcnow()

    session = context.get('session', model.Session)
    session.add(viewer)
    session.commit()

    log.info(f"[FEATURED_VIEWER_UPDATE] Updated viewer: {viewer.id}")
    return table_dictize(viewer, context)


def featured_viewer_record_view(context, data_dict):
    """Increment view count for a viewer."""
    viewer_id = data_dict.get('id')
    if not viewer_id:
        return

    viewer = FeaturedViewer.get(id=viewer_id)
    if not viewer:
        return

    viewer.view_count = (viewer.view_count or 0) + 1
    session = context.get('session', model.Session)
    session.add(viewer)
    session.commit()


def featured_viewer_link_dataset(context, data_dict):
    """Link a CKAN dataset to a viewer."""
    tk.check_access('featured_viewer_update', context, {'id': data_dict.get('viewer_id')})

    viewer_id = data_dict.get('viewer_id')
    dataset_id = data_dict.get('dataset_id')

    if not viewer_id or not dataset_id:
        raise tk.ValidationError({'viewer_id': ['viewer_id and dataset_id required']})

    viewer = FeaturedViewer.get(id=viewer_id)
    if not viewer:
        raise tk.ObjectNotFound(f"Viewer not found: {viewer_id}")

    existing = ViewerDataset.get(viewer_id=viewer_id, dataset_id=dataset_id)
    if existing:
        raise tk.ValidationError({'dataset_id': ['Dataset already linked']})

    link = ViewerDataset()
    link.id = make_uuid()
    link.viewer_id = viewer_id
    link.dataset_id = dataset_id
    link.description = data_dict.get('description', '')
    link.order_index = data_dict.get('order_index', 0)
    link.created_at = datetime.datetime.utcnow()

    link.save()
    session = context.get('session', model.Session)
    session.add(link)
    session.commit()

    return table_dictize(link, context)


def featured_viewer_unlink_dataset(context, data_dict):
    """Unlink a dataset from a viewer."""
    tk.check_access('featured_viewer_update', context, {'id': data_dict.get('viewer_id')})

    link_id = data_dict.get('id')
    if not link_id:
        raise tk.ValidationError({'id': ['Link ID is required']})

    link = ViewerDataset.get(id=link_id)
    if not link:
        raise tk.ObjectNotFound(f"Dataset link not found: {link_id}")

    session = context.get('session', model.Session)
    session.delete(link)
    session.commit()

    return {'success': True}


def _parse_json_field(raw_value):
    """Parse a JSON field that may be a string, dict, list, or None."""
    if raw_value is None or raw_value == '':
        return None
    if isinstance(raw_value, (dict, list)):
        return raw_value
    if isinstance(raw_value, str):
        try:
            return json.loads(raw_value)
        except Exception:
            return None
    return None
