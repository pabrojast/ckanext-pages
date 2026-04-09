"""
Data Stories Actions

This module provides all CKAN action functions for data stories.
Actions are organized into separate files for maintainability.
"""

from ckanext.pages.data_stories.actions.create import (
    data_story_create,
    data_story_section_create,
)

from ckanext.pages.data_stories.actions.read import (
    data_story_show,
    data_story_list,
    data_story_section_show,
    data_story_section_list,
)

from ckanext.pages.data_stories.actions.update import (
    data_story_update,
    data_story_section_update,
    data_story_reorder_sections,
)

from ckanext.pages.data_stories.actions.delete import (
    data_story_delete,
    data_story_section_delete,
)

from ckanext.pages.data_stories.actions.publish import (
    data_story_submit,
    data_story_review,
    data_story_approve,
    data_story_request_changes,
)

from ckanext.pages.data_stories.actions.datasets import (
    data_story_link_dataset,
    data_story_unlink_dataset,
    data_story_datasets,
)

from ckanext.pages.data_stories.actions.comments import (
    data_story_comment_create,
    data_story_comment_list,
    data_story_comment_update,
    data_story_comment_delete,
    data_story_comment_resolve,
)

from ckanext.pages.data_stories.actions.stats import (
    data_story_record_view,
    data_story_stats,
)

from ckanext.pages.data_stories.actions.import_export import (
    data_story_export,
    data_story_import,
    data_story_bulk_export,
    data_story_bulk_import,
)

__all__ = [
    # Create
    'data_story_create',
    'data_story_section_create',
    # Read
    'data_story_show',
    'data_story_list',
    'data_story_section_show',
    'data_story_section_list',
    # Update
    'data_story_update',
    'data_story_section_update',
    'data_story_reorder_sections',
    # Delete
    'data_story_delete',
    'data_story_section_delete',
    # Publish workflow
    'data_story_submit',
    'data_story_review',
    'data_story_approve',
    'data_story_request_changes',
    # Dataset linking
    'data_story_link_dataset',
    'data_story_unlink_dataset',
    'data_story_datasets',
    # Comments
    'data_story_comment_create',
    'data_story_comment_list',
    'data_story_comment_update',
    'data_story_comment_delete',
    'data_story_comment_resolve',
    # Stats
    'data_story_record_view',
    'data_story_stats',
    # Import/Export
    'data_story_export',
    'data_story_import',
    'data_story_bulk_export',
    'data_story_bulk_import',
]
