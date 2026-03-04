"""
Featured viewer publication workflow actions.

Handles submission, review, and publication processes,
mirroring the data-stories workflow.
"""

import logging

import ckan.plugins.toolkit as tk

from ckanext.pages.featured_viewers.db.models import FeaturedViewer
from ckanext.pages.featured_viewers.logic.workflow import transition_state

log = logging.getLogger(__name__)


def featured_viewer_submit(context, data_dict):
    """
    Submit a viewer for review.

    Changes status from 'draft' to 'submitted'.
    """
    log.info("[FEATURED_VIEWER_SUBMIT] Starting submission")

    tk.check_access('featured_viewer_submit', context, data_dict)

    viewer_id = data_dict.get('id')
    if not viewer_id:
        raise tk.ValidationError({'id': ['Viewer ID is required']})

    viewer = FeaturedViewer.get(id=viewer_id)
    if not viewer:
        raise tk.ObjectNotFound(f"Viewer not found: {viewer_id}")

    updated_viewer = transition_state(viewer_id, 'submitted', context)

    log.info(f"[FEATURED_VIEWER_SUBMIT] Submitted viewer: {viewer_id}")

    return updated_viewer


def featured_viewer_review(context, data_dict):
    """
    Transition viewer to under_review status.

    Only available to sysadmins and org admins.
    """
    log.info("[FEATURED_VIEWER_REVIEW] Starting review")

    tk.check_access('featured_viewer_review', context, data_dict)

    viewer_id = data_dict.get('id')
    if not viewer_id:
        raise tk.ValidationError({'id': ['Viewer ID is required']})

    viewer = FeaturedViewer.get(id=viewer_id)
    if not viewer:
        raise tk.ObjectNotFound(f"Viewer not found: {viewer_id}")

    updated_viewer = transition_state(viewer_id, 'under_review', context)

    log.info(f"[FEATURED_VIEWER_REVIEW] Viewer under review: {viewer_id}")

    return updated_viewer


def featured_viewer_approve(context, data_dict):
    """
    Approve and publish a viewer.

    Changes status to 'published' and makes viewer public.
    """
    log.info("[FEATURED_VIEWER_APPROVE] Starting approval")

    tk.check_access('featured_viewer_approve', context, data_dict)

    viewer_id = data_dict.get('id')
    if not viewer_id:
        raise tk.ValidationError({'id': ['Viewer ID is required']})

    viewer = FeaturedViewer.get(id=viewer_id)
    if not viewer:
        raise tk.ObjectNotFound(f"Viewer not found: {viewer_id}")

    updated_viewer = transition_state(viewer_id, 'published', context)

    log.info(f"[FEATURED_VIEWER_APPROVE] Approved and published viewer: {viewer_id}")

    return updated_viewer


def featured_viewer_request_changes(context, data_dict):
    """
    Request changes to a submitted viewer.

    Returns viewer to 'draft' status.
    """
    log.info("[FEATURED_VIEWER_REQUEST_CHANGES] Requesting changes")

    tk.check_access('featured_viewer_request_changes', context, data_dict)

    viewer_id = data_dict.get('id')
    if not viewer_id:
        raise tk.ValidationError({'id': ['Viewer ID is required']})

    required_changes = data_dict.get('required_changes')
    if not required_changes:
        raise tk.ValidationError(
            {'required_changes': ['Description of required changes is required']}
        )

    viewer = FeaturedViewer.get(id=viewer_id)
    if not viewer:
        raise tk.ObjectNotFound(f"Viewer not found: {viewer_id}")

    updated_viewer = transition_state(viewer_id, 'draft', context)

    log.info(f"[FEATURED_VIEWER_REQUEST_CHANGES] Requested changes for viewer: {viewer_id}")

    return updated_viewer
