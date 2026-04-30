"""
Featured viewer creation actions.
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
    featured_viewer_schema, generate_slug, validate_slug,
    map_room_schema,
)

log = logging.getLogger(__name__)


def featured_viewer_create(context, data_dict):
    """
    Create a new featured viewer.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - title (required)
            - slug (auto-generated if not provided)
            - description, category, icon_class, thumbnail_url
            - terria_share_link, terria_config, map_layers
            - tags, countries, organization_id
    Returns:
        Dict with created viewer data
    """
    log.info("[FEATURED_VIEWER_CREATE] Starting creation")

    tk.check_access('featured_viewer_create', context, data_dict)

    user = context.get('user')
    if not user:
        raise tk.NotAuthorized("Must be logged in")

    user_obj = model.User.get(user)
    if not user_obj:
        raise tk.NotAuthorized("User not found")

    # Capture JSONB fields before validation
    countries_raw = data_dict.get('countries')
    tags_raw = data_dict.get('tags')
    map_layers_raw = data_dict.get('map_layers')
    terria_config_raw = data_dict.get('terria_config')
    map_tabs_raw = data_dict.get('map_tabs')
    datasets_raw = data_dict.get('datasets_data')

    schema = featured_viewer_schema()
    data, errors = df.validate(data_dict, schema, context)
    if errors:
        raise tk.ValidationError(errors)

    if not data.get('slug'):
        data['slug'] = generate_slug(data['title'])
    else:
        is_valid, error_msg = validate_slug(data['slug'])
        if not is_valid:
            raise tk.ValidationError({'slug': [error_msg]})

    # Check slug uniqueness
    existing = FeaturedViewer.get(slug=data['slug'])
    if existing:
        raise tk.ValidationError({'slug': ['A viewer with this slug already exists']})

    viewer = FeaturedViewer()
    viewer.id = make_uuid()
    viewer.title = data['title']
    viewer.slug = data['slug']
    viewer.description = data.get('description', '')
    viewer.category = data.get('category', 'general')
    viewer.initiative = data.get('initiative') or data_dict.get('initiative') or None
    viewer.icon_class = data.get('icon_class', '')
    viewer.thumbnail_url = data.get('thumbnail_url', '')
    viewer.terria_share_link = data.get('terria_share_link', '')
    viewer.meta_description = data.get('meta_description', '')

    # JSONB fields
    viewer.terria_config = _parse_json_field(terria_config_raw)
    viewer.map_layers = _parse_json_field(map_layers_raw) or []
    viewer.tags = _parse_json_field(tags_raw) or []
    viewer.countries = _parse_json_field(countries_raw) or []
    viewer.map_tabs = _normalize_map_tabs(_parse_json_field(map_tabs_raw))

    # Map height (clamp to a sane range)
    height_raw = data_dict.get('map_height')
    try:
        height_val = int(height_raw) if height_raw not in (None, '') else None
    except (ValueError, TypeError):
        height_val = None
    if height_val is not None:
        height_val = max(300, min(2000, height_val))
    viewer.map_height = height_val

    viewer.author_id = user_obj.id
    viewer.organization_id = data.get('organization_id') or None

    viewer.status = 'draft'
    viewer.is_public = True
    viewer.is_featured = False
    viewer.view_count = 0
    viewer.order_index = 0

    now = datetime.datetime.utcnow()
    viewer.created_at = now
    viewer.updated_at = now

    session = context.get('session', model.Session)
    session.add(viewer)
    session.flush()

    # Sync user-supplied dataset links
    parsed_datasets = _parse_json_field(datasets_raw) or []
    _sync_viewer_datasets(session, viewer.id, parsed_datasets)

    session.commit()

    log.info(f"[FEATURED_VIEWER_CREATE] Created viewer: {viewer.id} - {viewer.title}")

    viewer_dict = table_dictize(viewer, context)
    viewer_dict['datasets'] = []
    return viewer_dict


def _normalize_map_tabs(tabs):
    """Coerce map_tabs payload into a clean list of dicts.

    Each tab keeps: id, title, terria_share_link, terria_config.
    """
    if not isinstance(tabs, list):
        return []
    out = []
    for idx, tab in enumerate(tabs):
        if not isinstance(tab, dict):
            continue
        share_link = (tab.get('terria_share_link') or '').strip()
        title = (tab.get('title') or '').strip()
        if not share_link and not title:
            continue
        out.append({
            'id': tab.get('id') or make_uuid(),
            'title': title or f'Tab {idx + 1}',
            'terria_share_link': share_link,
            'terria_config': tab.get('terria_config') or None,
        })
    return out


def _sync_viewer_datasets(session, viewer_id, datasets):
    """Replace ViewerDataset rows for a viewer to match the supplied list.

    Each entry in `datasets` is expected to be a dict with at least
    `dataset_id` (a CKAN package id or name); `description` is optional.
    """
    if not isinstance(datasets, list):
        datasets = []

    existing = session.query(ViewerDataset).filter(
        ViewerDataset.viewer_id == viewer_id
    ).all()
    for row in existing:
        session.delete(row)
    session.flush()

    seen = set()
    for idx, item in enumerate(datasets):
        if not isinstance(item, dict):
            continue
        dataset_id = (item.get('dataset_id') or item.get('id') or '').strip()
        if not dataset_id or dataset_id in seen:
            continue
        seen.add(dataset_id)
        link = ViewerDataset()
        link.id = make_uuid()
        link.viewer_id = viewer_id
        link.dataset_id = dataset_id
        desc = item.get('description') or ''
        link.description = desc.strip() if isinstance(desc, str) else ''
        link.order_index = idx
        link.created_at = datetime.datetime.utcnow()
        session.add(link)


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


def map_room_create(context, data_dict):
    """Create a new map room."""
    from ckanext.pages.featured_viewers.db.models import MapRoom

    tk.check_access('map_room_create', context, data_dict)

    user = context.get('user')
    user_obj = model.User.get(user)
    if not user_obj:
        raise tk.NotAuthorized("Must be logged in")

    schema = map_room_schema()
    data, errors = df.validate(data_dict, schema, context)
    if errors:
        raise tk.ValidationError(errors)

    if not data.get('slug'):
        data['slug'] = generate_slug(data['title'])
    else:
        is_valid, error_msg = validate_slug(data['slug'])
        if not is_valid:
            raise tk.ValidationError({'slug': [error_msg]})

    existing = MapRoom.get(slug=data['slug'])
    if existing:
        raise tk.ValidationError(
            {'slug': ['A room with this slug already exists']}
        )

    room = MapRoom()
    room.id = make_uuid()
    room.title = data['title']
    room.slug = data['slug']
    room.description = data.get('description', '')
    room.thumbnail_url = data.get('thumbnail_url', '')
    room.category = data.get('category', 'general')
    room.initiative = data.get('initiative') or data_dict.get('initiative') or None
    room.organization_id = data.get('organization_id') or data_dict.get('organization_id') or None
    room.countries = data.get('countries') or data_dict.get('countries') or None
    room.author_id = user_obj.id
    room.status = data_dict.get('status', 'draft')
    room.is_featured = bool(data_dict.get('is_featured', False))
    room.order_index = int(data_dict.get('order_index', 0))

    now = datetime.datetime.utcnow()
    room.created_at = now
    room.updated_at = now

    session = context.get('session', model.Session)
    session.add(room)
    session.commit()

    log.info(f"[MAP_ROOM_CREATE] Created room: {room.id} - {room.title}")
    return table_dictize(room, context)
