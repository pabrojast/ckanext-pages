"""
Data Stories Module

A comprehensive system for creating narrative-driven explanations of research
datasets, with deep Terria integration for spatial visualization.

This module provides:
- Story creation and management
- Section-based content organization
- Dataset linking
- Publication workflow
- Role-based access control
- Terria map integration
"""

__version__ = '1.0.0'

from ckanext.pages.data_stories.db.models import (
    DataStory,
    DataStorySection,
    DataStoryDataset,
    DataStoryContributor,
    DataStoryComment,
    DataStoryRevision,
)

__all__ = [
    'DataStory',
    'DataStorySection',
    'DataStoryDataset',
    'DataStoryContributor',
    'DataStoryComment',
    'DataStoryRevision',
]
