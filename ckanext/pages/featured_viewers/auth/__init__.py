"""
Authorization module for Featured Viewers and Map Rooms.
"""

from ckanext.pages.featured_viewers.auth.permissions import (
    featured_viewer_create,
    featured_viewer_show,
    featured_viewer_list,
    featured_viewer_update,
    featured_viewer_delete,
    featured_viewer_record_view,
    featured_viewer_link_dataset,
    featured_viewer_unlink_dataset,
    map_room_create,
    map_room_show,
    map_room_list,
    map_room_update,
    map_room_delete,
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
    'map_room_create',
    'map_room_show',
    'map_room_list',
    'map_room_update',
    'map_room_delete',
]
