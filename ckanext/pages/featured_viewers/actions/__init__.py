"""
Featured Viewers Actions

This module provides all CKAN action functions for featured viewers
and map rooms.
"""

from ckanext.pages.featured_viewers.actions.create import (
    featured_viewer_create,
    map_room_create,
)

from ckanext.pages.featured_viewers.actions.read import (
    featured_viewer_show,
    featured_viewer_list,
    map_room_show,
    map_room_list,
)

from ckanext.pages.featured_viewers.actions.update import (
    featured_viewer_update,
    featured_viewer_record_view,
    featured_viewer_link_dataset,
    featured_viewer_unlink_dataset,
    map_room_update,
    map_room_add_viewer,
    map_room_remove_viewer,
    sync_room_viewers,
)

from ckanext.pages.featured_viewers.actions.delete import (
    featured_viewer_delete,
    map_room_delete,
)

from ckanext.pages.featured_viewers.actions.publish import (
    featured_viewer_submit,
    featured_viewer_review,
    featured_viewer_approve,
    featured_viewer_request_changes,
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
    'featured_viewer_submit',
    'featured_viewer_review',
    'featured_viewer_approve',
    'featured_viewer_request_changes',
    'map_room_create',
    'map_room_show',
    'map_room_list',
    'map_room_update',
    'map_room_delete',
    'map_room_add_viewer',
    'map_room_remove_viewer',
    'sync_room_viewers',
]
