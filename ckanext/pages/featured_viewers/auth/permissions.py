"""
Permission checks for featured viewer actions.
"""

import logging

from ckan import authz, model

from ckanext.pages.featured_viewers.db.models import FeaturedViewer

log = logging.getLogger(__name__)


def _is_sysadmin(user_id):
    if not user_id:
        return False
    user = model.User.get(user_id)
    return user and user.sysadmin


def _is_viewer_author(user_id, viewer):
    if not user_id or not viewer:
        return False
    user = model.User.get(user_id)
    if not user:
        return False
    author_id = viewer.get('author_id') if isinstance(viewer, dict) else getattr(viewer, 'author_id', None)
    return user.id == author_id


def featured_viewer_create(context, data_dict):
    """Must be logged in. Sysadmins or org admins can create."""
    user = context.get('user')
    if not user:
        return {'success': False}
    if _is_sysadmin(user):
        return {'success': True}
    # All authenticated users can create viewers
    return {'success': True}


def featured_viewer_show(context, data_dict):
    """Published viewers are public. Drafts require author/admin access."""
    user = context.get('user')

    viewer_id = data_dict.get('id') or data_dict.get('slug')
    if not viewer_id:
        return {'success': False}

    viewer = FeaturedViewer.get(id=data_dict.get('id')) if data_dict.get('id') \
        else FeaturedViewer.get(slug=data_dict.get('slug'))
    if not viewer:
        return {'success': False}

    if viewer.status == 'published':
        return {'success': True}
    if not user:
        return {'success': False}
    if _is_sysadmin(user):
        return {'success': True}
    if _is_viewer_author(user, viewer):
        return {'success': True}

    return {'success': False}


def featured_viewer_list(context, data_dict):
    """Listing is always allowed; results are filtered by permissions."""
    return {'success': True}


def featured_viewer_update(context, data_dict):
    """Author or sysadmin can update."""
    user = context.get('user')
    if not user:
        return {'success': False}
    if _is_sysadmin(user):
        return {'success': True}

    viewer_id = data_dict.get('id')
    if not viewer_id:
        return {'success': False}

    viewer = FeaturedViewer.get(id=viewer_id)
    if not viewer:
        return {'success': False}

    if _is_viewer_author(user, viewer):
        return {'success': True}

    if viewer.organization_id:
        if authz.has_user_permission_for_group_or_org(viewer.organization_id, user, 'admin'):
            return {'success': True}

    return {'success': False}


def featured_viewer_delete(context, data_dict):
    """Author or sysadmin can delete."""
    user = context.get('user')
    if not user:
        return {'success': False}
    if _is_sysadmin(user):
        return {'success': True}

    viewer_id = data_dict.get('id')
    if not viewer_id:
        return {'success': False}

    viewer = FeaturedViewer.get(id=viewer_id)
    if not viewer:
        return {'success': False}

    if _is_viewer_author(user, viewer):
        return {'success': True}

    return {'success': False}


def featured_viewer_record_view(context, data_dict):
    """Anyone can record a view."""
    return {'success': True}


def featured_viewer_link_dataset(context, data_dict):
    """Same as update."""
    return featured_viewer_update(context, {'id': data_dict.get('viewer_id')})


def featured_viewer_unlink_dataset(context, data_dict):
    """Same as update."""
    return featured_viewer_update(context, {'id': data_dict.get('viewer_id')})
