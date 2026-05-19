"""
Comment system actions for data story reviews.

Handles creating, updating, and managing comments on stories.
"""

import datetime
import logging

from ckan import model
import ckan.plugins.toolkit as tk

from ckanext.pages.data_stories.db.models import DataStory, DataStoryComment
from ckanext.pages.data_stories.db.utils import make_uuid, table_dictize, dictize_comments

log = logging.getLogger(__name__)


def data_story_comment_create(context, data_dict):
    """
    Add a comment to a story or section.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - story_id: Story ID (required)
            - content: Comment content (required)
            - section_id: Section ID (optional)
            - comment_type: Type (comment, suggestion, required_change) (default: comment)
            - parent_comment_id: Parent comment for threading (optional)

    Returns:
        Dict with created comment data
    """
    log.info("[DATA_STORY_COMMENT_CREATE] Creating comment")

    # Check authorization
    tk.check_access('data_story_comment_create', context, data_dict)

    # Get user
    user = context.get('user')
    if not user:
        raise tk.NotAuthorized(tk._("Must be logged in to comment"))

    user_obj = model.User.get(user)
    if not user_obj:
        raise tk.NotAuthorized(tk._("User not found"))

    # Get parameters
    story_id = data_dict.get('story_id')
    content = data_dict.get('content')

    if not story_id:
        raise tk.ValidationError({'story_id': ['Story ID is required']})

    if not content:
        raise tk.ValidationError({'content': ['Comment content is required']})

    # Validate story exists
    story = DataStory.get(id=story_id)
    if not story:
        raise tk.ObjectNotFound(f"Story not found: {story_id}")

    # Create comment
    comment = DataStoryComment()
    comment.id = make_uuid()
    comment.story_id = story_id
    comment.user_id = user_obj.id
    comment.content = content
    comment.comment_type = data_dict.get('comment_type', 'comment')
    comment.section_id = data_dict.get('section_id')
    comment.parent_comment_id = data_dict.get('parent_comment_id')
    comment.is_resolved = False
    comment.created_at = datetime.datetime.utcnow()
    comment.updated_at = datetime.datetime.utcnow()

    # Save
    comment.save()
    session = context.get('session', model.Session)
    session.add(comment)
    session.commit()

    log.info(f"[DATA_STORY_COMMENT_CREATE] Created comment: {comment.id}")

    # Convert to dict
    comment_dict = table_dictize(comment, context)

    # Add user info
    from ckanext.pages.data_stories.db.utils import get_user_info
    comment_dict['user'] = get_user_info(user_obj.id)

    return comment_dict


def data_story_comment_list(context, data_dict):
    """
    List comments for a story or section.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - story_id: Story ID (required)
            - section_id: Section ID (optional)
            - is_resolved: Filter by resolution status (optional)

    Returns:
        List of comment dicts
    """
    log.info("[DATA_STORY_COMMENT_LIST] Listing comments")

    # Check authorization
    tk.check_access('data_story_comment_list', context, data_dict)

    # Get story
    story_id = data_dict.get('story_id')
    if not story_id:
        raise tk.ValidationError({'story_id': ['Story ID is required']})

    # Build query
    query = model.Session.query(DataStoryComment).autoflush(False)
    query = query.filter(DataStoryComment.story_id == story_id)

    # Filter by section if provided
    section_id = data_dict.get('section_id')
    if section_id:
        query = query.filter(DataStoryComment.section_id == section_id)

    # Filter by resolution status if provided
    is_resolved = data_dict.get('is_resolved')
    if is_resolved is not None:
        query = query.filter(DataStoryComment.is_resolved == is_resolved)

    # Order by created_at
    query = query.order_by(DataStoryComment.created_at)

    # Execute
    comments = query.all()

    # Convert to dicts
    comment_list = dictize_comments(comments, context)

    # Add user info to each comment
    from ckanext.pages.data_stories.db.utils import get_user_info
    for comment_dict in comment_list:
        if comment_dict.get('user_id'):
            comment_dict['user'] = get_user_info(comment_dict['user_id'])

    log.info(f"[DATA_STORY_COMMENT_LIST] Returned {len(comment_list)} comments")

    return comment_list


def data_story_comment_update(context, data_dict):
    """
    Update a comment.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Comment ID (required)
            - content: Updated content (optional)
            - is_resolved: Resolution status (optional)

    Returns:
        Dict with updated comment data
    """
    log.info("[DATA_STORY_COMMENT_UPDATE] Updating comment")

    # Check authorization
    tk.check_access('data_story_comment_update', context, data_dict)

    # Get comment
    comment_id = data_dict.get('id')
    if not comment_id:
        raise tk.ValidationError({'id': ['Comment ID is required']})

    comment = DataStoryComment.get(id=comment_id)
    if not comment:
        raise tk.ObjectNotFound(f"Comment not found: {comment_id}")

    # Update fields
    if 'content' in data_dict:
        comment.content = data_dict['content']

    if 'is_resolved' in data_dict:
        comment.is_resolved = data_dict['is_resolved']

    comment.updated_at = datetime.datetime.utcnow()

    # Save
    comment.save()
    session = context.get('session', model.Session)
    session.add(comment)
    session.commit()

    log.info(f"[DATA_STORY_COMMENT_UPDATE] Updated comment: {comment_id}")

    # Convert to dict
    comment_dict = table_dictize(comment, context)

    return comment_dict


def data_story_comment_delete(context, data_dict):
    """
    Delete a comment.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Comment ID (required)

    Returns:
        Dict with success status
    """
    log.info("[DATA_STORY_COMMENT_DELETE] Deleting comment")

    # Check authorization
    tk.check_access('data_story_comment_delete', context, data_dict)

    # Get comment
    comment_id = data_dict.get('id')
    if not comment_id:
        raise tk.ValidationError({'id': ['Comment ID is required']})

    comment = DataStoryComment.get(id=comment_id)
    if not comment:
        raise tk.ObjectNotFound(f"Comment not found: {comment_id}")

    # Delete
    session = context.get('session', model.Session)
    session.delete(comment)
    session.commit()

    log.info(f"[DATA_STORY_COMMENT_DELETE] Deleted comment: {comment_id}")

    return {'success': True, 'deleted': True}


def data_story_comment_resolve(context, data_dict):
    """
    Mark a comment as resolved.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Comment ID (required)

    Returns:
        Dict with updated comment data
    """
    log.info("[DATA_STORY_COMMENT_RESOLVE] Resolving comment")

    # Update comment as resolved
    data_dict['is_resolved'] = True

    return data_story_comment_update(context, data_dict)
