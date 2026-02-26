"""
Featured Viewers Module

A system for creating and managing thematic map viewers with pre-configured
Terria map rooms, providing direct access to curated geospatial data layers.

This module provides:
- Viewer creation and management
- Terria map room integration
- Dataset linking
- Category-based organization
- Simplified publication workflow (draft/published)
"""

__version__ = '1.0.0'

from ckanext.pages.featured_viewers.db.models import (
    FeaturedViewer,
    ViewerDataset,
)

__all__ = [
    'FeaturedViewer',
    'ViewerDataset',
]
