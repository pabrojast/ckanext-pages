"""
Publication workflow state machine for Featured Viewers.

Manages transitions between viewer states, mirroring
the data-stories workflow.
"""

import datetime
import logging
from typing import Tuple, Dict, Any

import ckan.plugins.toolkit as tk
from ckan import model

log = logging.getLogger(__name__)


class ViewerWorkflow:
    """
    State machine for featured viewer publication workflow.
    """

    STATES = {
        'draft': {
            'allowed_transitions': ['submitted', 'published'],
            'description': 'Viewer is being drafted',
        },
        'submitted': {
            'allowed_transitions': ['under_review', 'draft', 'published'],
            'description': 'Viewer has been submitted for review',
        },
        'under_review': {
            'allowed_transitions': ['published', 'draft'],
            'description': 'Viewer is under review',
        },
        'published': {
            'allowed_transitions': ['archived', 'submitted'],
            'description': 'Viewer is published and public',
        },
        'archived': {
            'allowed_transitions': ['draft'],
            'description': 'Viewer is archived',
        },
    }

    @classmethod
    def can_transition(cls, from_state: str, to_state: str) -> Tuple[bool, str]:
        """Check if transition is allowed."""
        if from_state not in cls.STATES:
            return (False, f"Invalid current state: {from_state}")
        if to_state not in cls.STATES:
            return (False, f"Invalid target state: {to_state}")
        if to_state not in cls.STATES[from_state]['allowed_transitions']:
            return (False, f"Cannot transition from '{from_state}' to '{to_state}'")
        return (True, "")

    @classmethod
    def get_allowed_transitions(cls, from_state: str) -> list:
        """Get list of allowed transitions from a state."""
        if from_state not in cls.STATES:
            return []
        return cls.STATES[from_state]['allowed_transitions']

    @classmethod
    def get_state_description(cls, state: str) -> str:
        """Get human-readable description of a state."""
        if state not in cls.STATES:
            return ""
        return cls.STATES[state]['description']


def can_transition(from_state: str, to_state: str) -> Tuple[bool, str]:
    """Check if transition is allowed."""
    return ViewerWorkflow.can_transition(from_state, to_state)


def transition_state(viewer_id: str, to_state: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute state transition on a featured viewer.

    Args:
        viewer_id: Viewer ID
        to_state: Target state
        context: CKAN context dict

    Returns:
        Updated viewer dict
    """
    from ckanext.pages.featured_viewers.db.models import FeaturedViewer
    from ckanext.pages.featured_viewers.db.utils import table_dictize

    viewer = FeaturedViewer.get(id=viewer_id)
    if not viewer:
        raise tk.ObjectNotFound(f"Viewer not found: {viewer_id}")

    old_status = viewer.status

    allowed, reason = ViewerWorkflow.can_transition(old_status, to_state)
    if not allowed:
        raise tk.ValidationError({'status': [reason]})

    viewer.status = to_state

    if to_state == 'submitted':
        viewer.updated_at = datetime.datetime.utcnow()

    elif to_state == 'under_review':
        viewer.updated_at = datetime.datetime.utcnow()

    elif to_state == 'published':
        viewer.published_at = datetime.datetime.utcnow()
        viewer.is_public = True

    elif to_state == 'archived':
        viewer.is_public = False

    elif to_state == 'draft':
        viewer.is_public = False

    session = context.get('session', model.Session)
    session.add(viewer)
    session.commit()

    log.info(f"Viewer {viewer_id} transitioned from '{old_status}' to '{to_state}'")

    return table_dictize(viewer, context)
