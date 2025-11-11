"""
Data story deletion actions.

Handles soft and hard deletion of stories and sections.
"""

import datetime
import logging

from ckan import model
import ckan.plugins.toolkit as tk

from ckanext.pages.data_stories.db.models import DataStory, DataStorySection

log = logging.getLogger(__name__)


def data_story_delete(context, data_dict):
    """
    Delete a data story.

    By default, performs soft delete (changes status to 'archived').
    Admins can perform hard delete.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (required)
            - hard_delete: Permanently delete (admin only) (default: False)

    Returns:
        Dict with success status

    Raises:
        NotFound: If story doesn't exist
        NotAuthorized: If user lacks permission
    """
    log.info("[DATA_STORY_DELETE] Starting deletion")

    # Check authorization
    tk.check_access('data_story_delete', context, data_dict)

    # Get story
    story_id = data_dict.get('id')
    if not story_id:
        raise tk.ValidationError({'id': ['Story ID is required']})

    story = DataStory.get(id=story_id)
    if not story:
        raise tk.ObjectNotFound(f"Story not found: {story_id}")

    # Check if hard delete requested
    hard_delete = data_dict.get('hard_delete', False)

    session = context.get('session', model.Session)

    if hard_delete:
        # Hard delete - only admins can do this
        is_admin = False
        try:
            is_admin = tk.check_access('sysadmin', context, {})
        except Exception:
            pass

        if not is_admin:
            raise tk.NotAuthorized("Only administrators can permanently delete stories")

        # Delete from database (cascades to sections, datasets, etc.)
        session.delete(story)
        session.commit()

        log.info(f"[DATA_STORY_DELETE] Hard deleted story: {story_id}")

        return {'success': True, 'deleted': True, 'hard_delete': True}

    else:
        # Soft delete - archive the story
        story.status = 'archived'
        story.is_public = False
        story.updated_at = datetime.datetime.utcnow()

        story.save()
        session.add(story)
        session.commit()

        log.info(f"[DATA_STORY_DELETE] Soft deleted (archived) story: {story_id}")

        return {'success': True, 'deleted': True, 'hard_delete': False}


def data_story_section_delete(context, data_dict):
    """
    Delete a story section.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Section ID (required)

    Returns:
        Dict with success status

    Raises:
        NotFound: If section doesn't exist
        NotAuthorized: If user lacks permission
    """
    log.info("[DATA_STORY_SECTION_DELETE] Starting section deletion")

    # Check authorization
    tk.check_access('data_story_section_delete', context, data_dict)

    # Get section
    section_id = data_dict.get('id')
    if not section_id:
        raise tk.ValidationError({'id': ['Section ID is required']})

    section = DataStorySection.get(id=section_id)
    if not section:
        raise tk.ObjectNotFound(f"Section not found: {section_id}")

    # Get parent story for timestamp update
    story_id = section.story_id

    # Delete section
    session = context.get('session', model.Session)
    session.delete(section)

    # Update parent story timestamp
    story = DataStory.get(id=story_id)
    if story:
        story.updated_at = datetime.datetime.utcnow()
        session.add(story)

    session.commit()

    log.info(f"[DATA_STORY_SECTION_DELETE] Deleted section: {section_id}")

    return {'success': True, 'deleted': True}
