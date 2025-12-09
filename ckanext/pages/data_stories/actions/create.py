"""
Data story creation actions.

Handles the creation of new data stories with validation,
initial section setup, and author assignment.
"""

import datetime
import logging
import json

from ckan import model
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df

from ckanext.pages.data_stories.db.models import DataStory, DataStorySection
from ckanext.pages.data_stories.db.utils import make_uuid, table_dictize
from ckanext.pages.data_stories.logic.schema import data_story_schema, data_story_section_schema
from ckanext.pages.data_stories.logic.validation import generate_slug, validate_slug

log = logging.getLogger(__name__)


def _normalize_blocks_metadata(raw_value):
    """
    Keep list/dict values intact; attempt to parse JSON strings; return None when empty.
    """
    if raw_value in (None, '', []):
        return None

    if isinstance(raw_value, (dict, list)):
        return raw_value

    if isinstance(raw_value, str):
        cleaned = raw_value.strip()
        if not cleaned or cleaned in ('null', '[]'):
            return None
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, str):
                parsed = json.loads(parsed)
            return parsed
        except Exception:
            # If it isn't valid JSON, return the raw string so it is not lost
            return raw_value

    return raw_value


def data_story_create(context, data_dict):
    """
    Create a new data story.

    Args:
        context: CKAN context dict with user info
        data_dict: Dict containing:
            - title: Story title (required)
            - slug: URL-friendly slug (auto-generated if not provided)
            - abstract: Brief summary
            - research_question: Main research question
            - study_area: Study area description
            - organization_id: Organization ID (optional)

    Returns:
        Dict with created story data

    Raises:
        NotAuthorized: If user lacks permission
        ValidationError: If data validation fails
    """
    log.info("[DATA_STORY_CREATE] Starting creation")

    # Check authorization
    tk.check_access('data_story_create', context, data_dict)

    # Get current user
    user = context.get('user')
    if not user:
        raise tk.NotAuthorized("Must be logged in to create stories")

    user_obj = model.User.get(user)
    if not user_obj:
        raise tk.NotAuthorized("User not found")

    # Validate schema
    schema = data_story_schema()
    data, errors = df.validate(data_dict, schema, context)

    if errors:
        raise tk.ValidationError(errors)

    # Generate slug if not provided
    if not data.get('slug'):
        data['slug'] = generate_slug(data['title'])
    else:
        # Validate provided slug
        is_valid, error_msg = validate_slug(data['slug'])
        if not is_valid:
            raise tk.ValidationError({'slug': [error_msg]})

    # Create story object
    story = DataStory()
    story.id = make_uuid()
    story.title = data['title']
    story.slug = data['slug']
    story.abstract = data.get('abstract', '')
    story.research_question = data.get('research_question', '')
    story.study_area = data.get('study_area', '')

    # Research publication fields
    story.paper_doi = data.get('paper_doi', '')
    story.paper_citation = data.get('paper_citation', '')

    countries_value = data.get('countries')
    if isinstance(countries_value, str):
        try:
            countries_value = json.loads(countries_value)
        except Exception:
            log.warning("[DATA_STORY_CREATE] Could not parse countries JSON, storing raw string")
    story.countries = countries_value

    # Set author
    story.author_id = user_obj.id

    # Set organization if provided
    if data.get('organization_id'):
        story.organization_id = data['organization_id']

    # Set defaults
    story.status = 'draft'
    story.is_public = False
    story.is_featured = False
    story.view_count = 0
    story.version = 1

    # Timestamps
    now = datetime.datetime.utcnow()
    story.created_at = now
    story.updated_at = now

    # Save
    story.save()
    session = context.get('session', model.Session)
    session.add(story)
    session.commit()

    log.info(f"[DATA_STORY_CREATE] Created story: {story.id} - {story.title}")

    # Convert to dict
    story_dict = table_dictize(story, context)

    # Add empty sections list
    story_dict['sections'] = []
    story_dict['datasets'] = []
    story_dict['contributors'] = []

    return story_dict


def data_story_section_create(context, data_dict):
    """
    Add a new section to an existing story.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - story_id: Parent story ID (required)
            - section_type: Type of section (required)
            - title: Section title
            - content: Section content
            - order_index: Position in story (auto-calculated if not provided)
            - terria_config: Terria map configuration (optional)
            - terria_share_link: Terria share link (optional)
            - image_url: Image URL (optional)
            - video_url: Video URL (optional)
            - is_visible: Visibility flag (default: True)

    Returns:
        Dict with created section data

    Raises:
        NotAuthorized: If user lacks permission
        NotFound: If story doesn't exist
        ValidationError: If data validation fails
    """
    log.info("[DATA_STORY_SECTION_CREATE] Starting section creation")
    log.info(f"[DATA_STORY_SECTION_CREATE] Input data_dict blocks_metadata: {type(data_dict.get('blocks_metadata'))} = {data_dict.get('blocks_metadata')}")

    # Preserve raw blocks metadata before validation
    raw_blocks_metadata = _normalize_blocks_metadata(data_dict.get('blocks_metadata'))
    if raw_blocks_metadata is not None:
        data_dict['blocks_metadata'] = raw_blocks_metadata

    # Check authorization
    tk.check_access('data_story_section_create', context, data_dict)

    # Validate schema
    schema = data_story_section_schema()
    data, errors = df.validate(data_dict, schema, context)
    # If validation dropped metadata, restore the normalized raw value
    if data.get('blocks_metadata') is None and raw_blocks_metadata is not None:
        data['blocks_metadata'] = raw_blocks_metadata

    log.info(f"[DATA_STORY_SECTION_CREATE] After validation blocks_metadata: {type(data.get('blocks_metadata'))} = {data.get('blocks_metadata')}")

    if errors:
        raise tk.ValidationError(errors)

    # Get parent story
    story_id = data['story_id']
    story = DataStory.get(id=story_id)

    if not story:
        raise tk.ObjectNotFound(f"Story not found: {story_id}")

    # Auto-calculate order_index if not provided
    if 'order_index' not in data or data['order_index'] is None:
        # Get max order_index for this story
        existing_sections = DataStorySection.all(story_id=story_id)
        if existing_sections:
            max_order = max(s.order_index for s in existing_sections)
            data['order_index'] = max_order + 1
        else:
            data['order_index'] = 0

    # Create section object
    section = DataStorySection()
    section.id = make_uuid()
    section.story_id = story_id
    section.section_type = data['section_type']
    section.title = data.get('title', '')
    section.content = data.get('content', '')
    section.order_index = data['order_index']

    # Media
    section.image_url = data.get('image_url')
    section.video_url = data.get('video_url')

    # Terria
    section.terria_config = data.get('terria_config')
    section.terria_share_link = data.get('terria_share_link')

    # Blocks metadata
    blocks_meta_value = data.get('blocks_metadata')
    log.info(f"[DATA_STORY_SECTION_CREATE] Setting blocks_metadata: {type(blocks_meta_value)} = {blocks_meta_value}")
    section.blocks_metadata = blocks_meta_value

    # Visibility
    section.is_visible = data.get('is_visible', True)

    # Timestamps
    now = datetime.datetime.utcnow()
    section.created_at = now
    section.updated_at = now

    # Save
    section.save()
    session = context.get('session', model.Session)
    session.add(section)

    # Update story's updated_at
    story.updated_at = now
    session.add(story)

    session.commit()

    log.info(f"[DATA_STORY_SECTION_CREATE] Created section: {section.id} - {section.section_type}")
    log.info(f"[DATA_STORY_SECTION_CREATE] After commit, section.blocks_metadata: {type(section.blocks_metadata)} = {section.blocks_metadata}")

    # Convert to dict
    section_dict = table_dictize(section, context)
    log.info(f"[DATA_STORY_SECTION_CREATE] Returned dict blocks_metadata: {section_dict.get('blocks_metadata')}")

    return section_dict
