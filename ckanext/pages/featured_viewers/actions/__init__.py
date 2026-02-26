"""
Featured Viewers Actions

This module provides all CKAN action functions for featured viewers.
"""

from ckanext.pages.featured_viewers.actions.create import (
    featured_viewer_create,
)

from ckanext.pages.featured_viewers.actions.read import (
    featured_viewer_show,
    featured_viewer_list,
)

from ckanext.pages.featured_viewers.actions.update import (
    featured_viewer_update,
    featured_viewer_record_view,
    featured_viewer_link_dataset,
    featured_viewer_unlink_dataset,
)

from ckanext.pages.featured_viewers.actions.delete import (
    featured_viewer_delete,
)

__all__ = [
    'featured_viewer_create',
    'featured_viewer_show',
    'featured_viewer_list',
    'featured_viewer_update',
    'featured_viewer_delete',
    'featured_viewer_record_view',
    'featured_viewer_link_dataset',
    'featured_viewer_unlink_dataset',
]
