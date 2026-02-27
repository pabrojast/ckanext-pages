"""
Featured viewer retrieval actions.
"""

import logging

from ckan import model, authz
import ckan.plugins.toolkit as tk
from sqlalchemy import or_, func

from ckanext.pages.featured_viewers.db.models import FeaturedViewer, ViewerDataset
from ckanext.pages.featured_viewers.db.utils import (
    table_dictize, dictize_datasets, get_user_info, get_organization_info,
)

log = logging.getLogger(__name__)


def featured_viewer_show(context, data_dict):
    """
    Get a single featured viewer by ID or slug.

    Args:
        context: CKAN context dict
        data_dict: id or slug, include_datasets (default True)
    Returns:
        Dict with viewer data
    """
    tk.check_access('featured_viewer_show', context, data_dict)

    viewer_id = data_dict.get('id')
    slug = data_dict.get('slug')

    if not viewer_id and not slug:
        raise tk.ValidationError({'id': ['Either id or slug must be provided']})

    viewer = FeaturedViewer.get(id=viewer_id) if viewer_id else FeaturedViewer.get(slug=slug)

    if not viewer:
        raise tk.ObjectNotFound(f"Viewer not found: {viewer_id or slug}")

    viewer_dict = table_dictize(viewer, context)

    if viewer.author_id:
        viewer_dict['author'] = get_user_info(viewer.author_id)
    if viewer.organization_id:
        viewer_dict['organization'] = get_organization_info(viewer.organization_id)

    include_datasets = data_dict.get('include_datasets', True)
    if include_datasets:
        datasets = ViewerDataset.all(viewer_id=viewer.id)
        viewer_dict['datasets'] = dictize_datasets(datasets, context)
        viewer_dict['dataset_count'] = len(datasets)
    else:
        viewer_dict['datasets'] = []
        viewer_dict['dataset_count'] = 0

    # Count map layers
    layers = viewer_dict.get('map_layers') or []
    viewer_dict['layer_count'] = len(layers) if isinstance(layers, list) else 0

    return viewer_dict


def featured_viewer_list(context, data_dict):
    """
    List featured viewers with filtering and pagination.

    Args:
        context: CKAN context dict
        data_dict: status, category, is_featured, q, sort, limit, offset
    Returns:
        Dict with viewers, count, facets
    """
    tk.check_access('featured_viewer_list', context, data_dict)

    query = model.Session.query(FeaturedViewer).autoflush(False)

    # Filters
    status = data_dict.get('status')
    if status:
        query = query.filter(FeaturedViewer.status == status)

    category = data_dict.get('category')
    if category:
        query = query.filter(FeaturedViewer.category == category)

    is_featured = data_dict.get('is_featured')
    if is_featured is not None:
        query = query.filter(FeaturedViewer.is_featured == is_featured)

    author_id = data_dict.get('author_id')
    if author_id:
        query = query.filter(FeaturedViewer.author_id == author_id)

    # Search
    q = data_dict.get('q')
    if q:
        search_filter = or_(
            FeaturedViewer.title.ilike(f'%{q}%'),
            FeaturedViewer.description.ilike(f'%{q}%'),
        )
        query = query.filter(search_filter)

    # Permission filtering
    user = context.get('user')
    auth_user_obj = context.get('auth_user_obj')
    is_admin = False

    if auth_user_obj and getattr(auth_user_obj, 'sysadmin', False):
        is_admin = True
    elif user:
        try:
            is_admin = authz.is_sysadmin(user)
        except Exception:
            is_admin = False

    if not is_admin:
        if user:
            user_obj = model.User.get(user)
            if user_obj:
                query = query.filter(
                    or_(
                        FeaturedViewer.status == 'published',
                        FeaturedViewer.author_id == user_obj.id,
                    )
                )
            else:
                query = query.filter(FeaturedViewer.status == 'published')
        else:
            query = query.filter(FeaturedViewer.status == 'published')

    total_count = query.count()

    # Sorting
    sort = data_dict.get('sort', 'recent')
    if sort == 'recent':
        query = query.order_by(FeaturedViewer.created_at.desc())
    elif sort == 'popular':
        query = query.order_by(FeaturedViewer.view_count.desc())
    elif sort == 'alphabetical':
        query = query.order_by(FeaturedViewer.title.asc())
    elif sort == 'order':
        query = query.order_by(FeaturedViewer.order_index.asc())
    else:
        query = query.order_by(FeaturedViewer.created_at.desc())

    # Pagination
    limit = data_dict.get('limit', 20)
    offset = data_dict.get('offset', 0)
    query = query.limit(limit).offset(offset)

    viewers = query.all()

    viewer_list = []
    for viewer in viewers:
        viewer_dict = table_dictize(viewer, context)
        if viewer.author_id:
            viewer_dict['author'] = get_user_info(viewer.author_id)
        if viewer.organization_id:
            viewer_dict['organization'] = get_organization_info(viewer.organization_id)

        dataset_count = model.Session.query(ViewerDataset).filter(
            ViewerDataset.viewer_id == viewer.id
        ).count()
        viewer_dict['dataset_count'] = dataset_count

        layers = viewer_dict.get('map_layers') or []
        viewer_dict['layer_count'] = len(layers) if isinstance(layers, list) else 0

        viewer_list.append(viewer_dict)

    # Build category facets
    facets = _build_facets(context)

    return {
        'viewers': viewer_list,
        'count': total_count,
        'facets': facets,
    }


def _build_facets(context):
    """Build facet data for filtering."""
    category_counts = model.Session.query(
        FeaturedViewer.category,
        func.count(FeaturedViewer.id)
    ).filter(
        FeaturedViewer.status == 'published'
    ).group_by(FeaturedViewer.category).all()

    return {
        'category': {cat: count for cat, count in category_counts if cat},
    }


def map_room_show(context, data_dict):
    """Show a single map room with its viewers."""
    from ckanext.pages.featured_viewers.db.models import MapRoom

    room_id = data_dict.get('id')
    slug = data_dict.get('slug')

    room = None
    if room_id:
        room = MapRoom.get(id=room_id)
    elif slug:
        room = MapRoom.get(slug=slug)

    if not room:
        raise tk.ObjectNotFound('Map room not found')

    if room.status != 'published':
        tk.check_access('map_room_show', context, data_dict)

    room_dict = table_dictize(room, context)

    # Include viewers in this room
    viewers = []
    for rv in (room.room_viewers or []):
        if rv.viewer:
            v_dict = table_dictize(rv.viewer, context)
            v_dict['room_order'] = rv.order_index
            if rv.viewer.author_id:
                v_dict['author'] = get_user_info(rv.viewer.author_id)
            viewers.append(v_dict)
    room_dict['viewers'] = viewers

    if room.author_id:
        room_dict['author'] = get_user_info(room.author_id)

    return room_dict


def map_room_list(context, data_dict):
    """List map rooms with optional filtering."""
    from ckanext.pages.featured_viewers.db.models import MapRoom

    status = data_dict.get('status', 'published')
    category = data_dict.get('category')
    limit = int(data_dict.get('limit', 50))
    offset = int(data_dict.get('offset', 0))

    query = model.Session.query(MapRoom).autoflush(False)

    if status:
        query = query.filter(MapRoom.status == status)
    if category:
        query = query.filter(MapRoom.category == category)

    total = query.count()
    rooms = query.order_by(MapRoom.order_index, MapRoom.title)\
        .limit(limit).offset(offset).all()

    result = []
    for room in rooms:
        room_dict = table_dictize(room, context)
        room_dict['viewer_count'] = len(room.room_viewers or [])
        result.append(room_dict)

    return {'rooms': result, 'count': total}
