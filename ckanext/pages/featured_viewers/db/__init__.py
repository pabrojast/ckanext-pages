"""
Database package for Featured Viewers.
"""

from ckanext.pages.featured_viewers.db.models import (
    FeaturedViewer,
    ViewerDataset,
    MapRoom,
    MapRoomViewer,
)
from ckanext.pages.featured_viewers.db.utils import (
    init_tables,
    table_dictize,
    make_uuid,
)

__all__ = [
    'FeaturedViewer',
    'ViewerDataset',
    'MapRoom',
    'MapRoomViewer',
    'init_tables',
    'table_dictize',
    'make_uuid',
]
