"""
Featured viewer deletion actions.
"""

import logging

from ckan import model
import ckan.plugins.toolkit as tk

from ckanext.pages.featured_viewers.db.models import FeaturedViewer

log = logging.getLogger(__name__)


def featured_viewer_delete(context, data_dict):
    """
    Delete a featured viewer.

    Sysadmins can hard delete; authors can soft delete (archive).
    """
    tk.check_access('featured_viewer_delete', context, data_dict)

    viewer_id = data_dict.get('id')
    if not viewer_id:
        raise tk.ValidationError({'id': ['Viewer ID is required']})

    viewer = FeaturedViewer.get(id=viewer_id)
    if not viewer:
        raise tk.ObjectNotFound(f"Viewer not found: {viewer_id}")

    session = context.get('session', model.Session)

    # Sysadmins can hard delete
    user = context.get('user')
    user_obj = model.User.get(user) if user else None
    is_sysadmin = user_obj and user_obj.sysadmin

    if is_sysadmin and data_dict.get('hard_delete'):
        session.delete(viewer)
    else:
        viewer.status = 'archived'
        session.add(viewer)

    session.commit()

    log.info(f"[FEATURED_VIEWER_DELETE] Deleted viewer: {viewer_id}")
    return {'success': True}
