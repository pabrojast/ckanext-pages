"""
Data story publication workflow actions.

Handles submission, review, and publication processes.
"""

import datetime
import logging

from ckan import model
import ckan.plugins.toolkit as tk

from ckanext.pages.data_stories.db.models import DataStory
from ckanext.pages.data_stories.db.utils import table_dictize
from ckanext.pages.data_stories.logic.workflow import transition_state
from ckanext.pages.data_stories.logic.validation import validate_story_completeness

log = logging.getLogger(__name__)


def data_story_submit(context, data_dict):
    """
    Submit a story for review.

    Changes status from 'draft' to 'submitted'.
    Validates that all required sections are present.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (required)
            - submission_notes: Notes for reviewers (optional)

    Returns:
        Dict with updated story data

    Raises:
        NotFound: If story doesn't exist
        NotAuthorized: If user lacks permission
        ValidationError: If story is incomplete
    """
    log.info("[DATA_STORY_SUBMIT] Starting submission")

    # Check authorization
    tk.check_access('data_story_submit', context, data_dict)

    # Get story
    story_id = data_dict.get('id')
    if not story_id:
        raise tk.ValidationError({'id': ['Story ID is required']})

    story = DataStory.get(id=story_id)
    if not story:
        raise tk.ObjectNotFound(f"Story not found: {story_id}")

    # Validate story completeness
    # Get full story with sections
    story_dict = tk.get_action('data_story_show')(context, {
        'id': story_id,
        'include_sections': True
    })

    is_complete, errors = validate_story_completeness(story_dict)

    if not is_complete:
        error_messages = '; '.join(errors)
        raise tk.ValidationError({
            'completeness': [f"Story is not complete: {error_messages}"]
        })

    # Transition to submitted
    updated_story = transition_state(story_id, 'submitted', context)

    log.info(f"[DATA_STORY_SUBMIT] Submitted story: {story_id}")

    # TODO: Send email notification to reviewers

    return updated_story


def data_story_review(context, data_dict):
    """
    Transition story to under_review status.

    Only available to users with reviewer role.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (required)

    Returns:
        Dict with updated story data

    Raises:
        NotFound: If story doesn't exist
        NotAuthorized: If user lacks permission
    """
    log.info("[DATA_STORY_REVIEW] Starting review")

    # Check authorization
    tk.check_access('data_story_review', context, data_dict)

    # Get story
    story_id = data_dict.get('id')
    if not story_id:
        raise tk.ValidationError({'id': ['Story ID is required']})

    story = DataStory.get(id=story_id)
    if not story:
        raise tk.ObjectNotFound(f"Story not found: {story_id}")

    # Transition to under_review
    updated_story = transition_state(story_id, 'under_review', context)

    log.info(f"[DATA_STORY_REVIEW] Story under review: {story_id}")

    # TODO: Send email notification to author

    return updated_story


def data_story_approve(context, data_dict):
    """
    Approve and publish a story.

    Changes status to 'published' and makes story public.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (required)
            - approval_notes: Notes for author (optional)

    Returns:
        Dict with published story data

    Raises:
        NotFound: If story doesn't exist
        NotAuthorized: If user lacks permission
    """
    log.info("[DATA_STORY_APPROVE] Starting approval")

    # Check authorization
    tk.check_access('data_story_approve', context, data_dict)

    # Get story
    story_id = data_dict.get('id')
    if not story_id:
        raise tk.ValidationError({'id': ['Story ID is required']})

    story = DataStory.get(id=story_id)
    if not story:
        raise tk.ObjectNotFound(f"Story not found: {story_id}")

    # Transition to published
    updated_story = transition_state(story_id, 'published', context)

    log.info(f"[DATA_STORY_APPROVE] Approved and published story: {story_id}")

    # TODO: Send email notification to author

    return updated_story


def data_story_request_changes(context, data_dict):
    """
    Request changes to a submitted story.

    Returns story to 'draft' status with reviewer comments.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (required)
            - required_changes: Description of changes needed (required)

    Returns:
        Dict with updated story data

    Raises:
        NotFound: If story doesn't exist
        NotAuthorized: If user lacks permission
        ValidationError: If required_changes not provided
    """
    log.info("[DATA_STORY_REQUEST_CHANGES] Requesting changes")

    # Check authorization
    tk.check_access('data_story_request_changes', context, data_dict)

    # Get story
    story_id = data_dict.get('id')
    if not story_id:
        raise tk.ValidationError({'id': ['Story ID is required']})

    required_changes = data_dict.get('required_changes')
    if not required_changes:
        raise tk.ValidationError({'required_changes': ['Description of required changes is required']})

    story = DataStory.get(id=story_id)
    if not story:
        raise tk.ObjectNotFound(f"Story not found: {story_id}")

    # Transition back to draft
    updated_story = transition_state(story_id, 'draft', context)

    log.info(f"[DATA_STORY_REQUEST_CHANGES] Requested changes for story: {story_id}")

    # TODO: Create a comment with the required changes
    # TODO: Send email notification to author

    return updated_story
