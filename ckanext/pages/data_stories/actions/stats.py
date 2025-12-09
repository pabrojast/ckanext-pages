"""
Analytics and statistics actions for data stories.

Handles view tracking and statistics generation.
"""

import datetime
import logging

from ckan import model
import ckan.plugins.toolkit as tk
from sqlalchemy import func

from ckanext.pages.data_stories.db.models import DataStory
from ckanext.pages.data_stories.db.utils import table_dictize

log = logging.getLogger(__name__)


def data_story_record_view(context, data_dict):
    """
    Record a view of a data story.

    Increments the view count for analytics.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (required)

    Returns:
        Dict with success status and new view count
    """
    log.info("[DATA_STORY_RECORD_VIEW] Recording view")

    # Get story
    story_id = data_dict.get('id')
    if not story_id:
        raise tk.ValidationError({'id': ['Story ID is required']})

    story = DataStory.get(id=story_id)
    if not story:
        raise tk.ObjectNotFound(f"Story not found: {story_id}")

    # Increment view count
    story.view_count = (story.view_count or 0) + 1

    # Save
    story.save()
    session = context.get('session', model.Session)
    session.add(story)
    session.commit()

    log.info(f"[DATA_STORY_RECORD_VIEW] Recorded view for story: {story_id}, count: {story.view_count}")

    return {
        'success': True,
        'view_count': story.view_count
    }


def data_story_stats(context, data_dict):
    """
    Get statistics for a data story or all stories.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (optional, for single story stats)

    Returns:
        Dict with statistics
    """
    log.info("[DATA_STORY_STATS] Getting statistics")

    # Check authorization
    tk.check_access('data_story_stats', context, data_dict)

    story_id = data_dict.get('id')

    if story_id:
        # Single story stats
        story = DataStory.get(id=story_id)
        if not story:
            raise tk.ObjectNotFound(f"Story not found: {story_id}")

        from ckanext.pages.data_stories.db.models import (
            DataStorySection,
            DataStoryDataset,
            DataStoryComment,
        )

        section_count = model.Session.query(DataStorySection).filter(
            DataStorySection.story_id == story_id
        ).count()

        dataset_count = model.Session.query(DataStoryDataset).filter(
            DataStoryDataset.story_id == story_id
        ).count()

        comment_count = model.Session.query(DataStoryComment).filter(
            DataStoryComment.story_id == story_id
        ).count()

        unresolved_comment_count = model.Session.query(DataStoryComment).filter(
            DataStoryComment.story_id == story_id,
            DataStoryComment.is_resolved == False
        ).count()

        stats = {
            'story_id': story_id,
            'view_count': story.view_count or 0,
            'section_count': section_count,
            'dataset_count': dataset_count,
            'comment_count': comment_count,
            'unresolved_comment_count': unresolved_comment_count,
            'status': story.status,
            'is_public': story.is_public,
            'is_featured': story.is_featured,
            'created_at': story.created_at.isoformat() if story.created_at else None,
            'published_at': story.published_at.isoformat() if story.published_at else None,
        }

    else:
        # Global stats
        total_stories = model.Session.query(DataStory).count()

        published_stories = model.Session.query(DataStory).filter(
            DataStory.status == 'published'
        ).count()

        draft_stories = model.Session.query(DataStory).filter(
            DataStory.status == 'draft'
        ).count()

        under_review_stories = model.Session.query(DataStory).filter(
            DataStory.status.in_(['submitted', 'under_review'])
        ).count()

        # Get total views
        total_views = model.Session.query(
            func.sum(DataStory.view_count)
        ).scalar() or 0

        # Get most viewed stories
        most_viewed = model.Session.query(DataStory).order_by(
            DataStory.view_count.desc()
        ).limit(5).all()

        most_viewed_list = [
            {
                'id': story.id,
                'title': story.title,
                'slug': story.slug,
                'view_count': story.view_count or 0
            }
            for story in most_viewed
        ]

        # Get recently published
        recently_published = model.Session.query(DataStory).filter(
            DataStory.status == 'published'
        ).order_by(
            DataStory.published_at.desc()
        ).limit(5).all()

        recently_published_list = [
            {
                'id': story.id,
                'title': story.title,
                'slug': story.slug,
                'published_at': story.published_at.isoformat() if story.published_at else None
            }
            for story in recently_published
        ]

        stats = {
            'total_stories': total_stories,
            'published_stories': published_stories,
            'draft_stories': draft_stories,
            'under_review_stories': under_review_stories,
            'total_views': total_views,
            'most_viewed': most_viewed_list,
            'recently_published': recently_published_list,
        }

    log.info("[DATA_STORY_STATS] Returned statistics")

    return stats
