"""
Publication workflow state machine.

Manages transitions between story states.
"""

import logging
from typing import Tuple, Dict, Any

log = logging.getLogger(__name__)


class StoryWorkflow:
    """
    State machine for data story publication workflow.
    """

    STATES = {
        'draft': {
            'allowed_transitions': ['submitted'],
            'required_permissions': ['data_story_update_own'],
            'description': 'Story is being drafted',
        },
        'submitted': {
            'allowed_transitions': ['under_review', 'draft'],
            'required_permissions': ['data_story_review'],
            'description': 'Story has been submitted for review',
        },
        'under_review': {
            'allowed_transitions': ['published', 'draft'],
            'required_permissions': ['data_story_approve'],
            'description': 'Story is under review',
        },
        'published': {
            'allowed_transitions': ['archived'],
            'required_permissions': ['data_story_update_any'],
            'description': 'Story is published and public',
        },
        'archived': {
            'allowed_transitions': ['draft'],
            'required_permissions': ['data_story_update_any'],
            'description': 'Story is archived',
        },
    }

    @classmethod
    def can_transition(cls, from_state: str, to_state: str) -> Tuple[bool, str]:
        """
        Check if transition is allowed based on workflow rules.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            Tuple of (allowed, reason)
        """
        # Validate states exist
        if from_state not in cls.STATES:
            return (False, f"Invalid current state: {from_state}")

        if to_state not in cls.STATES:
            return (False, f"Invalid target state: {to_state}")

        # Check if transition is allowed
        allowed_transitions = cls.STATES[from_state]['allowed_transitions']

        if to_state not in allowed_transitions:
            return (False, f"Cannot transition from '{from_state}' to '{to_state}'")

        return (True, "")

    @classmethod
    def get_allowed_transitions(cls, from_state: str) -> list:
        """
        Get list of allowed transitions from a state.

        Args:
            from_state: Current state

        Returns:
            List of allowed target states
        """
        if from_state not in cls.STATES:
            return []

        return cls.STATES[from_state]['allowed_transitions']

    @classmethod
    def get_state_description(cls, state: str) -> str:
        """
        Get human-readable description of a state.

        Args:
            state: State name

        Returns:
            State description
        """
        if state not in cls.STATES:
            return ""

        return cls.STATES[state]['description']


def can_transition(from_state: str, to_state: str) -> Tuple[bool, str]:
    """
    Check if transition is allowed.

    Args:
        from_state: Current state
        to_state: Target state

    Returns:
        Tuple of (allowed, reason)
    """
    return StoryWorkflow.can_transition(from_state, to_state)


def transition_state(story_id: str, to_state: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute state transition.

    Args:
        story_id: Story ID
        to_state: Target state
        context: CKAN context dict

    Returns:
        Updated story dict

    Raises:
        ValidationError: If transition not allowed
        NotFound: If story doesn't exist
    """
    import ckan.plugins.toolkit as tk
    from ckanext.pages.data_stories.db.models import DataStory
    from ckanext.pages.data_stories.db.utils import table_dictize

    # Get story
    story = DataStory.get(id=story_id)
    if not story:
        raise tk.ObjectNotFound(f"Story not found: {story_id}")

    # Check if transition is allowed
    allowed, reason = StoryWorkflow.can_transition(story.status, to_state)
    if not allowed:
        raise tk.ValidationError({'status': [reason]})

    # Update state
    story.status = to_state

    # Update related fields based on transition
    import datetime

    if to_state == 'submitted':
        story.submission_date = datetime.datetime.utcnow()

    elif to_state == 'under_review':
        story.review_date = datetime.datetime.utcnow()
        # Set reviewer to current user
        user = context.get('user')
        if user:
            story.reviewer_id = user

    elif to_state == 'published':
        story.published_at = datetime.datetime.utcnow()
        story.is_public = True

    elif to_state == 'archived':
        story.is_public = False

    elif to_state == 'draft':
        # Reset workflow fields
        story.submission_date = None
        story.review_date = None
        story.reviewer_id = None
        story.is_public = False

    # Save
    story.save()

    from ckan import model
    model.Session.add(story)
    model.Session.commit()

    log.info(f"Story {story_id} transitioned from '{story.status}' to '{to_state}'")

    return table_dictize(story, context)
