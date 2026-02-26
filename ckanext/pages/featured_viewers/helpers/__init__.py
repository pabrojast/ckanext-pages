# encoding: utf-8
"""
Template helpers for Featured Viewers.
"""

import logging
from ckanext.pages.featured_viewers.logic.schema import VIEWER_CATEGORIES

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
