# encoding: utf-8
"""
Template helpers for Featured Viewers and Map Rooms.
"""

import logging
from ckanext.pages.featured_viewers.logic.schema import (
    VIEWER_CATEGORIES, AVAILABLE_ICONS,
)

log = logging.getLogger(__name__)


def get_viewer_categories():
    """Return the dict of available viewer categories."""
    return VIEWER_CATEGORIES


def get_category_info(category_id):
    """Get display info for a category ID."""
    return VIEWER_CATEGORIES.get(category_id, VIEWER_CATEGORIES.get('general', {}))


def get_category_title(category_id):
    """Get category display title."""
    info = get_category_info(category_id)
    return info.get('title', category_id or 'General')


def get_category_icon(category_id):
    """Get Font Awesome icon class for a category."""
    info = get_category_info(category_id)
    return info.get('icon', 'fa-map')


def get_category_color(category_id):
    """Get theme color for a category."""
    info = get_category_info(category_id)
    return info.get('color', '#0072BC')


def get_viewer_status_badge(status):
    """Get HTML class and label for a viewer status."""
    badges = {
        'draft': {'class': 'badge-draft', 'label': 'Draft', 'icon': 'fa-pencil'},
        'submitted': {'class': 'badge-submitted', 'label': 'Submitted', 'icon': 'fa-paper-plane'},
        'under_review': {'class': 'badge-review', 'label': 'Under Review', 'icon': 'fa-eye'},
        'published': {'class': 'badge-published', 'label': 'Published', 'icon': 'fa-check'},
        'archived': {'class': 'badge-archived', 'label': 'Archived', 'icon': 'fa-archive'},
    }
    return badges.get(status, badges['draft'])


def format_view_count(count):
    """Format a view count for display (e.g., 1234 -> 1.2k)."""
    if not count:
        return '0'
    count = int(count)
    if count >= 1000000:
        return f'{count / 1000000:.1f}M'
    if count >= 1000:
        return f'{count / 1000:.1f}k'
    return str(count)


# Aliases used by plugin.py and templates (prefixed with 'viewer_')
get_viewer_category_info = get_category_info
get_viewer_category_title = get_category_title
get_viewer_category_icon = get_category_icon
get_viewer_category_color = get_category_color
format_viewer_view_count = format_view_count


def get_available_icons():
    """Return list of icons for the visual icon picker."""
    return AVAILABLE_ICONS


def json_loads(value):
    """Safely parse JSON, returning [] on failure."""
    import json
    if not value:
        return []
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return []


def _get_member_state_names():
    """Return set of group names that are children of the 'member-states' parent group."""
    from ckan import model
    try:
        ms_group = model.Group.get('member-states')
        if not ms_group:
            return {'member-states'}
        ms_rows = (
            model.Session.query(model.Group.name)
            .join(model.Member, model.Member.table_id == model.Group.id)
            .filter(
                model.Member.group_id == ms_group.id,
                model.Member.state == 'active',
                model.Member.table_name == 'group',
                model.Group.state == 'active',
            )
            .all()
        )
        names = {'member-states'}
        names.update(g.name for g in ms_rows)
        return names
    except Exception:
        return {'member-states'}


def get_available_initiatives():
    """Return list of CKAN groups that are initiatives (excluding member states)."""
    from ckan import model
    try:
        ms_names = _get_member_state_names()
        group_rows = (
            model.Session.query(model.Group.name, model.Group.title)
            .filter(
                model.Group.state == 'active',
                model.Group.type == 'group',
                ~model.Group.name.in_(ms_names) if ms_names else True,
            )
            .order_by(model.Group.title)
            .all()
        )
        return [
            {'name': g.name, 'title': g.title or g.name}
            for g in group_rows
        ]
    except Exception:
        return []


def get_available_member_states():
    """Return list of CKAN groups that are member states (children of 'member-states' group)."""
    from ckan import model
    try:
        ms_group = model.Group.get('member-states')
        if not ms_group:
            return []
        ms_rows = (
            model.Session.query(model.Group.name, model.Group.title)
            .join(model.Member, model.Member.table_id == model.Group.id)
            .filter(
                model.Member.group_id == ms_group.id,
                model.Member.state == 'active',
                model.Member.table_name == 'group',
                model.Group.state == 'active',
            )
            .order_by(model.Group.title)
            .all()
        )
        return [
            {'name': g.name, 'title': g.title or g.name}
            for g in ms_rows
        ]
    except Exception:
        return []
