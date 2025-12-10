"""
Data story retrieval actions.

Handles fetching stories, sections, and related data.
"""

import logging

from ckan import model, authz
import ckan.plugins.toolkit as tk
from sqlalchemy import or_, and_, func

from ckanext.pages.data_stories.db.models import (
    DataStory,
    DataStorySection,
    DataStoryDataset,
    DataStoryContributor,
)
from ckanext.pages.data_stories.db.utils import (
    table_dictize,
    dictize_sections,
    dictize_datasets,
    dictize_contributors,
    get_user_info,
    get_organization_info,
)

log = logging.getLogger(__name__)


def data_story_show(context, data_dict):
    """
    Get a single data story by ID or slug.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (optional)
            - slug: Story slug (optional)
            - include_sections: Include sections (default: True)
            - include_datasets: Include linked datasets (default: True)
            - include_contributors: Include contributors (default: True)

    Returns:
        Dict with story data

    Raises:
        NotFound: If story doesn't exist
        NotAuthorized: If story is private and user lacks access
    """
    log.info("[DATA_STORY_SHOW] Fetching story")

    # Check authorization
    tk.check_access('data_story_show', context, data_dict)

    # Get story by ID or slug
    story_id = data_dict.get('id')
    slug = data_dict.get('slug')

    if not story_id and not slug:
        raise tk.ValidationError({'id': ['Either id or slug must be provided']})

    if story_id:
        story = DataStory.get(id=story_id)
    else:
        story = DataStory.get(slug=slug)

    if not story:
        identifier = story_id or slug
        raise tk.ObjectNotFound(f"Story not found: {identifier}")

    # Convert to dict
    story_dict = table_dictize(story, context)

    # Add author info
    if story.author_id:
        story_dict['author'] = get_user_info(story.author_id)

    # Add organization info
    if story.organization_id:
        story_dict['organization'] = get_organization_info(story.organization_id)

    # Add reviewer info
    if story.reviewer_id:
        story_dict['reviewer'] = get_user_info(story.reviewer_id)

    # Include sections if requested
    include_sections = data_dict.get('include_sections', True)
    if include_sections:
        sections = DataStorySection.all(story_id=story.id)
        story_dict['sections'] = dictize_sections(sections, context)
        story_dict['section_count'] = len(sections)
    else:
        story_dict['sections'] = []
        story_dict['section_count'] = 0

    # Include datasets if requested
    include_datasets = data_dict.get('include_datasets', True)
    if include_datasets:
        datasets = DataStoryDataset.all(story_id=story.id)
        story_dict['datasets'] = dictize_datasets(datasets, context)
        story_dict['dataset_count'] = len(datasets)
    else:
        story_dict['datasets'] = []
        story_dict['dataset_count'] = 0

    # Include contributors if requested
    include_contributors = data_dict.get('include_contributors', True)
    if include_contributors:
        contributors = DataStoryContributor.all(story_id=story.id)
        story_dict['contributors'] = dictize_contributors(contributors, context)
        story_dict['contributor_count'] = len(contributors)
    else:
        story_dict['contributors'] = []
        story_dict['contributor_count'] = 0

    log.info(f"[DATA_STORY_SHOW] Returned story: {story.id}")

    return story_dict


def data_story_list(context, data_dict):
    """
    List data stories with filtering and pagination.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - status: Filter by status (optional)
            - author_id: Filter by author (optional)
            - organization_id: Filter by organization (optional)
            - is_featured: Filter by featured status (optional)
            - q: Search query (optional)
            - sort: Sort order (recent, popular, alphabetical) (default: recent)
            - limit: Results per page (default: 20)
            - offset: Pagination offset (default: 0)

    Returns:
        Dict with:
            - stories: List of story dicts
            - count: Total number of stories
            - facets: Aggregated facet data
    """
    log.info("[DATA_STORY_LIST] Listing stories")

    # Check authorization
    tk.check_access('data_story_list', context, data_dict)

    # Build query
    query = model.Session.query(DataStory).autoflush(False)

    # Apply filters
    status = data_dict.get('status')
    if status:
        query = query.filter(DataStory.status == status)

    author_id = data_dict.get('author_id')
    if author_id:
        query = query.filter(DataStory.author_id == author_id)

    organization_id = data_dict.get('organization_id')
    if organization_id:
        query = query.filter(DataStory.organization_id == organization_id)

    is_featured = data_dict.get('is_featured')
    if is_featured is not None:
        query = query.filter(DataStory.is_featured == is_featured)

    # Search query
    q = data_dict.get('q')
    if q:
        search_filter = or_(
            DataStory.title.ilike(f'%{q}%'),
            DataStory.abstract.ilike(f'%{q}%'),
            DataStory.research_question.ilike(f'%{q}%'),
        )
        query = query.filter(search_filter)

    # Check permissions - only show public stories unless user has permission
    user = context.get('user')
    auth_user_obj = context.get('auth_user_obj')
    is_admin = False

    if auth_user_obj and getattr(auth_user_obj, 'sysadmin', False):
        is_admin = True
    elif user:
        try:
            is_admin = authz.is_sysadmin(user)
        except Exception:
            is_admin = False

    # If filtering by review statuses (submitted, under_review), skip is_public filter for admin/reviewers
    review_statuses = ['submitted', 'under_review']
    is_review_filter = status in review_statuses if status else False

    if not is_admin:
        if is_review_filter:
            # For review statuses, allow org admins to see stories in their orgs
            if user:
                user_obj = model.User.get(user)
                if user_obj:
                    # Get orgs where user is admin
                    user_org_ids = []
                    org_memberships = model.Session.query(model.Member).filter(
                        model.Member.table_name == 'user',
                        model.Member.table_id == user_obj.id,
                        model.Member.capacity == 'admin',
                        model.Member.state == 'active'
                    ).all()
                    for membership in org_memberships:
                        user_org_ids.append(membership.group_id)

                    if user_org_ids:
                        # Can see stories in their orgs OR their own stories
                        query = query.filter(
                            or_(
                                DataStory.organization_id.in_(user_org_ids),
                                DataStory.author_id == user_obj.id
                            )
                        )
                    else:
                        # Can only see their own stories
                        query = query.filter(DataStory.author_id == user_obj.id)
                else:
                    # No access to review statuses without login
                    query = query.filter(DataStory.id == None)  # Return nothing
            else:
                # No access to review statuses without login
                query = query.filter(DataStory.id == None)  # Return nothing
        else:
            # Show only public stories OR user's own stories
            if user:
                user_obj = model.User.get(user)
                if user_obj:
                    query = query.filter(
                        or_(
                            DataStory.is_public == True,
                            DataStory.author_id == user_obj.id
                        )
                    )
                else:
                    query = query.filter(DataStory.is_public == True)
            else:
                query = query.filter(DataStory.is_public == True)

    # Get total count before pagination
    total_count = query.count()

    # Apply sorting
    sort = data_dict.get('sort', 'recent')

    if sort == 'recent':
        query = query.order_by(DataStory.created_at.desc())
    elif sort == 'popular':
        query = query.order_by(DataStory.view_count.desc())
    elif sort == 'alphabetical':
        query = query.order_by(DataStory.title.asc())
    elif sort == 'published':
        query = query.order_by(DataStory.published_at.desc().nullslast())
    else:
        query = query.order_by(DataStory.created_at.desc())

    # Apply pagination
    limit = data_dict.get('limit', 20)
    offset = data_dict.get('offset', 0)

    query = query.limit(limit).offset(offset)

    # Execute query
    stories = query.all()

    # Convert to dicts
    story_list = []
    for story in stories:
        story_dict = table_dictize(story, context)

        # Add author info
        if story.author_id:
            story_dict['author'] = get_user_info(story.author_id)

        # Add organization info
        if story.organization_id:
            story_dict['organization'] = get_organization_info(story.organization_id)

        # Add section count
        section_count = model.Session.query(DataStorySection).filter(
            DataStorySection.story_id == story.id
        ).count()
        story_dict['section_count'] = section_count

        # Add dataset count
        dataset_count = model.Session.query(DataStoryDataset).filter(
            DataStoryDataset.story_id == story.id
        ).count()
        story_dict['dataset_count'] = dataset_count

        story_list.append(story_dict)

    log.info(f"[DATA_STORY_LIST] Returned {len(story_list)} of {total_count} stories")

    # Build facets
    facets = _build_facets(context)

    return {
        'stories': story_list,
        'count': total_count,
        'facets': facets,
    }


def data_story_section_show(context, data_dict):
    """
    Get a single story section.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Section ID (required)

    Returns:
        Dict with section data

    Raises:
        NotFound: If section doesn't exist
        NotAuthorized: If user lacks access
    """
    log.info("[DATA_STORY_SECTION_SHOW] Fetching section")

    # Check authorization
    tk.check_access('data_story_section_show', context, data_dict)

    section_id = data_dict.get('id')
    if not section_id:
        raise tk.ValidationError({'id': ['Section ID is required']})

    section = DataStorySection.get(id=section_id)

    if not section:
        raise tk.ObjectNotFound(f"Section not found: {section_id}")

    # Convert to dict
    section_dict = table_dictize(section, context)

    return section_dict


def data_story_section_list(context, data_dict):
    """
    List sections for a story.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - story_id: Story ID (required)
            - section_type: Filter by section type (optional)
            - is_visible: Filter by visibility (optional)

    Returns:
        List of section dicts
    """
    log.info("[DATA_STORY_SECTION_LIST] Listing sections")

    # Check authorization
    tk.check_access('data_story_section_list', context, data_dict)

    story_id = data_dict.get('story_id')
    if not story_id:
        raise tk.ValidationError({'story_id': ['Story ID is required']})

    # Build query
    query = model.Session.query(DataStorySection).autoflush(False)
    query = query.filter(DataStorySection.story_id == story_id)

    # Apply filters
    section_type = data_dict.get('section_type')
    if section_type:
        query = query.filter(DataStorySection.section_type == section_type)

    is_visible = data_dict.get('is_visible')
    if is_visible is not None:
        query = query.filter(DataStorySection.is_visible == is_visible)

    # Order by order_index
    query = query.order_by(DataStorySection.order_index)

    # Execute
    sections = query.all()

    # Convert to dicts
    section_list = dictize_sections(sections, context)

    log.info(f"[DATA_STORY_SECTION_LIST] Returned {len(section_list)} sections")

    return section_list


def _build_facets(context):
    """
    Build facet data for filtering.

    Args:
        context: CKAN context dict

    Returns:
        Dict with facet data
    """
    # Get status counts
    status_counts = model.Session.query(
        DataStory.status,
        func.count(DataStory.id)
    ).group_by(DataStory.status).all()

    # Get organization counts
    org_counts = model.Session.query(
        DataStory.organization_id,
        func.count(DataStory.id)
    ).filter(
        DataStory.organization_id.isnot(None)
    ).group_by(DataStory.organization_id).all()

    facets = {
        'status': {status: count for status, count in status_counts},
        'organization': {org_id: count for org_id, count in org_counts},
    }

    return facets
