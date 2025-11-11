"""
Role definitions and role-based permission helpers.

Defines user roles for data stories and provides functions
to check role membership and permissions.
"""

import logging

from ckan import model
from ckan import authz

log = logging.getLogger(__name__)


ROLES = {
    'story_author': {
        'display_name': 'Story Author',
        'description': 'Can create and edit own data stories',
        'permissions': [
            'data_story_create',
            'data_story_update_own',
            'data_story_delete_own',
            'data_story_submit',
        ]
    },
    'story_reviewer': {
        'display_name': 'Story Reviewer',
        'description': 'Can review and approve submitted stories',
        'permissions': [
            'data_story_review',
            'data_story_approve',
            'data_story_request_changes',
            'data_story_comment',
        ]
    },
    'story_editor': {
        'display_name': 'Story Editor',
        'description': 'Can edit any story in their organization',
        'permissions': [
            'data_story_create',
            'data_story_update_any',
            'data_story_delete_any',
            'data_story_publish',
        ]
    },
}


def has_role(user_id, role_name, org_id=None):
    """
    Check if user has a specific role.

    Args:
        user_id: User ID or username
        role_name: Role to check
        org_id: Optional organization context

    Returns:
        Boolean
    """
    if not user_id:
        return False

    # Sysadmins have all roles
    if is_sysadmin(user_id):
        return True

    # Get user object
    user = model.User.get(user_id)
    if not user:
        return False

    # For now, use CKAN's built-in roles as proxy
    # In future, could implement custom role storage

    # Organization editors have story_editor role
    if role_name == 'story_editor':
        if org_id:
            return is_organization_editor(user.id, org_id)
        return False

    # Organization members have story_reviewer role (if they are admins)
    if role_name == 'story_reviewer':
        if org_id:
            return is_organization_admin(user.id, org_id)
        return False

    # All authenticated users have story_author role
    if role_name == 'story_author':
        return True

    return False


def get_user_roles(user_id, org_id=None):
    """
    Get all roles for a user.

    Args:
        user_id: User ID or username
        org_id: Optional organization context

    Returns:
        List of role names
    """
    roles = []

    if not user_id:
        return roles

    # Sysadmins have all roles
    if is_sysadmin(user_id):
        return list(ROLES.keys())

    # Get user object
    user = model.User.get(user_id)
    if not user:
        return roles

    # All authenticated users are story authors
    roles.append('story_author')

    # Check organization roles
    if org_id:
        if is_organization_admin(user.id, org_id):
            roles.append('story_reviewer')

        if is_organization_editor(user.id, org_id):
            roles.append('story_editor')

    return roles


def is_story_author(user_id, story):
    """
    Check if user is the author of a story.

    Args:
        user_id: User ID or username
        story: DataStory object or dict with author_id

    Returns:
        Boolean
    """
    if not user_id or not story:
        return False

    # Get user object
    user = model.User.get(user_id)
    if not user:
        return False

    # Get author_id from story
    if isinstance(story, dict):
        author_id = story.get('author_id')
    else:
        author_id = getattr(story, 'author_id', None)

    return user.id == author_id


def is_organization_admin(user_id, org_id):
    """
    Check if user is an admin of an organization.

    Args:
        user_id: User ID or username
        org_id: Organization ID

    Returns:
        Boolean
    """
    if not user_id or not org_id:
        return False

    # Get user object
    user = model.User.get(user_id)
    if not user:
        return False

    # Get organization
    org = model.Group.get(org_id)
    if not org or org.type != 'organization':
        return False

    # Check if user has admin role in organization
    return authz.has_user_permission_for_group_or_org(
        org_id, user.name, 'admin'
    )


def is_organization_editor(user_id, org_id):
    """
    Check if user is an editor of an organization.

    Args:
        user_id: User ID or username
        org_id: Organization ID

    Returns:
        Boolean
    """
    if not user_id or not org_id:
        return False

    # Get user object
    user = model.User.get(user_id)
    if not user:
        return False

    # Get organization
    org = model.Group.get(org_id)
    if not org or org.type != 'organization':
        return False

    # Check if user has admin or editor role in organization
    return (
        authz.has_user_permission_for_group_or_org(org_id, user.name, 'admin') or
        authz.has_user_permission_for_group_or_org(org_id, user.name, 'write')
    )


def is_organization_member(user_id, org_id):
    """
    Check if user is a member of an organization.

    Args:
        user_id: User ID or username
        org_id: Organization ID

    Returns:
        Boolean
    """
    if not user_id or not org_id:
        return False

    # Get user object
    user = model.User.get(user_id)
    if not user:
        return False

    # Get organization
    org = model.Group.get(org_id)
    if not org or org.type != 'organization':
        return False

    # Check if user has any role in organization
    return authz.has_user_permission_for_group_or_org(
        org_id, user.name, 'read'
    )


def is_sysadmin(user_id):
    """
    Check if user is a sysadmin.

    Args:
        user_id: User ID or username

    Returns:
        Boolean
    """
    if not user_id:
        return False

    # Get user object
    user = model.User.get(user_id)
    if not user:
        return False

    return user.sysadmin
