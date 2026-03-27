"""
Featured viewer creation actions.
"""

import datetime
import json
import logging

from ckan import model
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df

from ckanext.pages.featured_viewers.db.models import FeaturedViewer
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
    session.commit()

    log.info(f"[FEATURED_VIEWER_CREATE] Created viewer: {viewer.id} - {viewer.title}")

    viewer_dict = table_dictize(viewer, context)
    viewer_dict['datasets'] = []
    return viewer_dict


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
