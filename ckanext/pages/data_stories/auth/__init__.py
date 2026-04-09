"""
Authorization module for Data Stories

Provides permission checks and role-based access control.
"""

from ckanext.pages.data_stories.auth.permissions import (
    # Story permissions
    data_story_create,
    data_story_show,
    data_story_list,
    data_story_update,
    data_story_delete,
    # Section permissions
    data_story_section_create,
    data_story_section_show,
    data_story_section_list,
    data_story_section_update,
    data_story_section_delete,
    data_story_reorder_sections,
    # Workflow permissions
    data_story_submit,
    data_story_review,
    data_story_approve,
    data_story_request_changes,
    # Dataset permissions
    data_story_link_dataset,
    data_story_unlink_dataset,
    data_story_datasets,
    # Comment permissions
    data_story_comment_create,
    data_story_comment_list,
    data_story_comment_update,
    data_story_comment_delete,
    data_story_comment_resolve,
    # Stats permissions
    data_story_stats,
    # Import/Export permissions
    data_story_export,
    data_story_import,
    data_story_bulk_export,
    data_story_bulk_import,
)

from ckanext.pages.data_stories.auth.roles import (
    ROLES,
    has_role,
    get_user_roles,
    is_story_author,
    is_organization_admin,
)

__all__ = [
    # Permissions
    'data_story_create',
    'data_story_show',
    'data_story_list',
    'data_story_update',
    'data_story_delete',
    'data_story_section_create',
    'data_story_section_show',
    'data_story_section_list',
    'data_story_section_update',
    'data_story_section_delete',
    'data_story_reorder_sections',
    'data_story_submit',
    'data_story_review',
    'data_story_approve',
    'data_story_request_changes',
    'data_story_link_dataset',
    'data_story_unlink_dataset',
    'data_story_datasets',
    'data_story_comment_create',
    'data_story_comment_list',
    'data_story_comment_update',
    'data_story_comment_delete',
    'data_story_comment_resolve',
    'data_story_stats',
    'data_story_export',
    'data_story_import',
    'data_story_bulk_export',
    'data_story_bulk_import',
    # Roles
    'ROLES',
    'has_role',
    'get_user_roles',
    'is_story_author',
    'is_organization_admin',
]
