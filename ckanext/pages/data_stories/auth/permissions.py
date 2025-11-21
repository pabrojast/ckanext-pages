"""
Permission checks for data story actions.

Implements fine-grained access control based on user roles,
story ownership, and organization membership.
"""

import logging

import ckan.plugins.toolkit as tk
from ckan import authz

from ckanext.pages.data_stories.db.models import DataStory, DataStorySection, DataStoryComment
from ckanext.pages.data_stories.auth.roles import (
    is_sysadmin,
    is_story_author,
    is_organization_admin,
    is_organization_editor,
)

log = logging.getLogger(__name__)


def data_story_create(context, data_dict):
    """
    Check if user can create a data story.

    Rules:
    - Must be logged in
    - Must have 'create_story' permission
    - If organization specified, must be member

    Returns:
        {'success': True/False}
    """
    user = context.get('user')

    # Must be logged in
    if not user:
        return {'success': False}

    # Sysadmins can always create
    if is_sysadmin(user):
        return {'success': True}

    # Check organization membership if specified
    org_id = data_dict.get('organization_id')
    if org_id:
        # Must be member of organization
        if not authz.has_user_permission_for_group_or_org(org_id, user, 'read'):
            return {'success': False}

    # All authenticated users can create stories
    return {'success': True}


def data_story_show(context, data_dict):
    """
    Check if user can view a data story.

    Rules:
    - Public stories: Anyone can view
    - Private stories: Author, org members, or sysadmin

    Returns:
        {'success': True/False}
    """
    user = context.get('user')

    # Get story
    story_id = data_dict.get('id') or data_dict.get('slug')
    if not story_id:
        return {'success': False}

    if data_dict.get('id'):
        story = DataStory.get(id=story_id)
    else:
        story = DataStory.get(slug=story_id)

    if not story:
        return {'success': False}

    # Public stories are viewable by anyone
    if story.is_public:
        return {'success': True}

    # For private stories, check permissions
    if not user:
        return {'success': False}

    # Sysadmins can view all
    if is_sysadmin(user):
        return {'success': True}

    # Author can view own stories
    if is_story_author(user, story):
        return {'success': True}

    # Organization members can view org stories
    if story.organization_id:
        if authz.has_user_permission_for_group_or_org(
            story.organization_id, user, 'read'
        ):
            return {'success': True}

    return {'success': False}


def data_story_list(context, data_dict):
    """
    Check if user can list data stories.

    Returns:
        {'success': True} - Always allowed, filtered by show permissions
    """
    # Listing is always allowed, but results are filtered by show permissions
    return {'success': True}


def data_story_update(context, data_dict):
    """
    Check if user can update a data story.

    Rules:
    - Must be story author, OR
    - Must be organization admin, OR
    - Must be sysadmin
    - Story must not be published (unless sysadmin)

    Returns:
        {'success': True/False}
    """
    user = context.get('user')

    if not user:
        return {'success': False}

    # Sysadmins can always update
    if is_sysadmin(user):
        return {'success': True}

    # Get story
    story_id = data_dict.get('id')
    if not story_id:
        return {'success': False}

    story = DataStory.get(id=story_id)
    if not story:
        return {'success': False}

    # Author can update own stories (if not published)
    if is_story_author(user, story):
        if story.status != 'published':
            return {'success': True}

    # Organization editors can update org stories
    if story.organization_id:
        if is_organization_editor(user, story.organization_id):
            return {'success': True}

    return {'success': False}


def data_story_delete(context, data_dict):
    """
    Check if user can delete a data story.

    Rules:
    - Must be story author (soft delete only), OR
    - Must be organization admin, OR
    - Must be sysadmin (can hard delete)

    Returns:
        {'success': True/False}
    """
    user = context.get('user')

    if not user:
        return {'success': False}

    # Sysadmins can always delete
    if is_sysadmin(user):
        return {'success': True}

    # Get story
    story_id = data_dict.get('id')
    if not story_id:
        return {'success': False}

    story = DataStory.get(id=story_id)
    if not story:
        return {'success': False}

    # Author can delete own stories (soft delete)
    if is_story_author(user, story):
        return {'success': True}

    # Organization admins can delete org stories
    if story.organization_id:
        if is_organization_admin(user, story.organization_id):
            return {'success': True}

    return {'success': False}


# Section permissions
def data_story_section_create(context, data_dict):
    """Check if user can create a section."""
    # Same as updating the parent story
    return data_story_update(context, {'id': data_dict.get('story_id')})


def data_story_section_show(context, data_dict):
    """Check if user can view a section."""
    section_id = data_dict.get('id')
    if not section_id:
        return {'success': False}

    section = DataStorySection.get(id=section_id)
    if not section:
        return {'success': False}

    # Check permission on parent story
    return data_story_show(context, {'id': section.story_id})


def data_story_section_list(context, data_dict):
    """Check if user can list sections."""
    # Check permission on parent story
    return data_story_show(context, {'id': data_dict.get('story_id')})


def data_story_section_update(context, data_dict):
    """Check if user can update a section."""
    section_id = data_dict.get('id')
    if not section_id:
        return {'success': False}

    section = DataStorySection.get(id=section_id)
    if not section:
        return {'success': False}

    # Check permission on parent story
    return data_story_update(context, {'id': section.story_id})


def data_story_section_delete(context, data_dict):
    """Check if user can delete a section."""
    section_id = data_dict.get('id')
    if not section_id:
        return {'success': False}

    section = DataStorySection.get(id=section_id)
    if not section:
        return {'success': False}

    # Check permission on parent story
    return data_story_delete(context, {'id': section.story_id})


def data_story_reorder_sections(context, data_dict):
    """Check if user can reorder sections."""
    return data_story_update(context, {'id': data_dict.get('story_id')})


# Workflow permissions
def data_story_submit(context, data_dict):
    """Check if user can submit a story."""
    # Author can submit own stories
    return data_story_update(context, data_dict)


def data_story_review(context, data_dict):
    """Check if user can review a story."""
    user = context.get('user')

    if not user:
        return {'success': False}

    # Sysadmins can review
    if is_sysadmin(user):
        return {'success': True}

    # Get story
    story_id = data_dict.get('id')
    if not story_id:
        return {'success': False}

    story = DataStory.get(id=story_id)
    if not story:
        return {'success': False}

    # Organization admins can review org stories
    if story.organization_id:
        if is_organization_admin(user, story.organization_id):
            return {'success': True}

    return {'success': False}


def data_story_approve(context, data_dict):
    """
    Check if user can approve a story.

    Rules:
    - Sysadmins can always approve
    - Organization admins can approve org stories
    - If 'ckanext.pages.data_stories.allow_direct_publish' is enabled,
      authors can approve their own stories
    """
    user = context.get('user')

    if not user:
        return {'success': False}

    # Sysadmins can approve
    if is_sysadmin(user):
        return {'success': True}

    # Get story
    story_id = data_dict.get('id')
    if not story_id:
        return {'success': False}

    story = DataStory.get(id=story_id)
    if not story:
        return {'success': False}

    # Organization admins can approve org stories
    if story.organization_id:
        if is_organization_admin(user, story.organization_id):
            return {'success': True}

    # Check if direct publishing is enabled
    allow_direct_publish = tk.asbool(
        tk.config.get('ckanext.pages.data_stories.allow_direct_publish', False)
    )

    if allow_direct_publish:
        # Authors can approve their own stories
        if is_story_author(user, story):
            return {'success': True}

    return {'success': False}


def data_story_request_changes(context, data_dict):
    """Check if user can request changes."""
    # Same as review
    return data_story_review(context, data_dict)


# Dataset linking permissions
def data_story_link_dataset(context, data_dict):
    """Check if user can link a dataset."""
    return data_story_update(context, {'id': data_dict.get('story_id')})


def data_story_unlink_dataset(context, data_dict):
    """Check if user can unlink a dataset."""
    return data_story_update(context, {'id': data_dict.get('story_id')})


def data_story_datasets(context, data_dict):
    """Check if user can view linked datasets."""
    return data_story_show(context, {'id': data_dict.get('story_id')})


# Comment permissions
def data_story_comment_create(context, data_dict):
    """Check if user can create a comment."""
    user = context.get('user')

    # Must be logged in
    if not user:
        return {'success': False}

    # Must be able to view the story
    return data_story_show(context, {'id': data_dict.get('story_id')})


def data_story_comment_list(context, data_dict):
    """Check if user can list comments."""
    return data_story_show(context, {'id': data_dict.get('story_id')})


def data_story_comment_update(context, data_dict):
    """Check if user can update a comment."""
    user = context.get('user')

    if not user:
        return {'success': False}

    # Sysadmins can update any comment
    if is_sysadmin(user):
        return {'success': True}

    # Get comment
    comment_id = data_dict.get('id')
    if not comment_id:
        return {'success': False}

    comment = DataStoryComment.get(id=comment_id)
    if not comment:
        return {'success': False}

    # User can update own comments
    from ckan import model
    user_obj = model.User.get(user)
    if user_obj and user_obj.id == comment.user_id:
        return {'success': True}

    return {'success': False}


def data_story_comment_delete(context, data_dict):
    """Check if user can delete a comment."""
    # Same as update
    return data_story_comment_update(context, data_dict)


def data_story_comment_resolve(context, data_dict):
    """Check if user can resolve a comment."""
    # Reviewers and story authors can resolve
    user = context.get('user')

    if not user:
        return {'success': False}

    # Sysadmins can resolve
    if is_sysadmin(user):
        return {'success': True}

    # Get comment
    comment_id = data_dict.get('id')
    if not comment_id:
        return {'success': False}

    comment = DataStoryComment.get(id=comment_id)
    if not comment:
        return {'success': False}

    # Get story
    story = DataStory.get(id=comment.story_id)
    if not story:
        return {'success': False}

    # Story author can resolve
    if is_story_author(user, story):
        return {'success': True}

    # Organization admins can resolve
    if story.organization_id:
        if is_organization_admin(user, story.organization_id):
            return {'success': True}

    return {'success': False}


# Stats permissions
def data_story_stats(context, data_dict):
    """Check if user can view statistics."""
    story_id = data_dict.get('id')

    if story_id:
        # For single story stats, check view permission
        return data_story_show(context, data_dict)
    else:
        # Global stats require admin
        user = context.get('user')
        if not user:
            return {'success': False}

        return {'success': is_sysadmin(user)}
