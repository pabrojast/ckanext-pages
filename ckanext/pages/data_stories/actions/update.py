"""
Data story update actions.

Handles modifications to existing stories and sections.
"""

import datetime
import logging

from ckan import model
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df

from ckanext.pages.data_stories.db.models import DataStory, DataStorySection
from ckanext.pages.data_stories.db.utils import table_dictize
from ckanext.pages.data_stories.logic.schema import data_story_schema, data_story_section_schema
from ckanext.pages.data_stories.logic.validation import validate_slug

log = logging.getLogger(__name__)


def data_story_update(context, data_dict):
    """
    Update an existing data story.

    Args:
        context: CKAN context dict
        data_dict: Dict containing story ID and fields to update

    Returns:
        Dict with updated story data

    Raises:
        NotFound: If story doesn't exist
        NotAuthorized: If user lacks permission
        ValidationError: If data validation fails
    """
    log.info("[DATA_STORY_UPDATE] Starting update")

    # Check authorization
    tk.check_access('data_story_update', context, data_dict)

    # Get story
    story_id = data_dict.get('id')
    if not story_id:
        raise tk.ValidationError({'id': ['Story ID is required']})

    story = DataStory.get(id=story_id)
    if not story:
        raise tk.ObjectNotFound(f"Story not found: {story_id}")

    # Validate schema
    schema = data_story_schema()
    data, errors = df.validate(data_dict, schema, context)

    if errors:
        raise tk.ValidationError(errors)

    # Validate slug if changed
    if 'slug' in data and data['slug'] != story.slug:
        is_valid, error_msg = validate_slug(data['slug'], story.id)
        if not is_valid:
            raise tk.ValidationError({'slug': [error_msg]})
        story.slug = data['slug']

    # Update fields
    if 'title' in data:
        story.title = data['title']

    if 'abstract' in data:
        story.abstract = data['abstract']

    if 'research_question' in data:
        story.research_question = data['research_question']

    if 'study_area' in data:
        story.study_area = data['study_area']

    if 'organization_id' in data:
        story.organization_id = data.get('organization_id')

    if 'is_featured' in data:
        story.is_featured = data['is_featured']

    # Update timestamp
    story.updated_at = datetime.datetime.utcnow()

    # Save
    story.save()
    session = context.get('session', model.Session)
    session.add(story)
    session.commit()

    log.info(f"[DATA_STORY_UPDATE] Updated story: {story.id}")

    # Convert to dict
    story_dict = table_dictize(story, context)

    return story_dict


def data_story_section_update(context, data_dict):
    """
    Update a story section.

    Args:
        context: CKAN context dict
        data_dict: Dict containing section ID and fields to update

    Returns:
        Dict with updated section data

    Raises:
        NotFound: If section doesn't exist
        NotAuthorized: If user lacks permission
        ValidationError: If data validation fails
    """
    log.info("[DATA_STORY_SECTION_UPDATE] Starting section update")
    log.info(f"[DATA_STORY_SECTION_UPDATE] Input data_dict blocks_metadata: {type(data_dict.get('blocks_metadata'))} = {data_dict.get('blocks_metadata')}")

    # Check authorization
    tk.check_access('data_story_section_update', context, data_dict)

    # Get section
    section_id = data_dict.get('id')
    if not section_id:
        raise tk.ValidationError({'id': ['Section ID is required']})

    section = DataStorySection.get(id=section_id)
    if not section:
        raise tk.ObjectNotFound(f"Section not found: {section_id}")

    # Validate schema
    schema = data_story_section_schema()
    data, errors = df.validate(data_dict, schema, context)
    log.info(f"[DATA_STORY_SECTION_UPDATE] After validation blocks_metadata: {type(data.get('blocks_metadata'))} = {data.get('blocks_metadata')}")

    if errors:
        raise tk.ValidationError(errors)

    # Update fields
    if 'title' in data:
        section.title = data['title']

    if 'content' in data:
        section.content = data['content']

    if 'section_type' in data:
        section.section_type = data['section_type']

    if 'order_index' in data:
        section.order_index = data['order_index']

    if 'image_url' in data:
        section.image_url = data.get('image_url')

    if 'video_url' in data:
        section.video_url = data.get('video_url')

    if 'terria_config' in data:
        section.terria_config = data.get('terria_config')

    if 'terria_share_link' in data:
        section.terria_share_link = data.get('terria_share_link')

    # Always update blocks_metadata - the _default_to_none validator ensures the key is present
    blocks_meta_value = data.get('blocks_metadata')
    log.info(f"[DATA_STORY_SECTION_UPDATE] Setting blocks_metadata: {type(blocks_meta_value)} = {blocks_meta_value}")
    section.blocks_metadata = blocks_meta_value

    if 'is_visible' in data:
        section.is_visible = data['is_visible']

    # Update timestamp
    section.updated_at = datetime.datetime.utcnow()

    # Save
    section.save()
    session = context.get('session', model.Session)
    session.add(section)

    # Update parent story timestamp
    story = DataStory.get(id=section.story_id)
    if story:
        story.updated_at = datetime.datetime.utcnow()
        session.add(story)

    session.commit()

    log.info(f"[DATA_STORY_SECTION_UPDATE] Updated section: {section.id}")
    log.info(f"[DATA_STORY_SECTION_UPDATE] After commit, section.blocks_metadata: {type(section.blocks_metadata)} = {section.blocks_metadata}")

    # Convert to dict
    section_dict = table_dictize(section, context)
    log.info(f"[DATA_STORY_SECTION_UPDATE] Returned dict blocks_metadata: {section_dict.get('blocks_metadata')}")

    return section_dict


def data_story_reorder_sections(context, data_dict):
    """
    Reorder sections within a story.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - story_id: Story ID (required)
            - section_order: List of section IDs in desired order (required)

    Returns:
        Dict with success status and updated sections

    Raises:
        NotFound: If story or sections don't exist
        NotAuthorized: If user lacks permission
        ValidationError: If data validation fails
    """
    log.info("[DATA_STORY_REORDER_SECTIONS] Starting reorder")

    # Check authorization
    tk.check_access('data_story_reorder_sections', context, data_dict)

    # Get story
    story_id = data_dict.get('story_id')
    if not story_id:
        raise tk.ValidationError({'story_id': ['Story ID is required']})

    story = DataStory.get(id=story_id)
    if not story:
        raise tk.ObjectNotFound(f"Story not found: {story_id}")

    # Get section order
    section_order = data_dict.get('section_order')
    if not section_order or not isinstance(section_order, list):
        raise tk.ValidationError({'section_order': ['Section order must be a list of section IDs']})

    # Update order_index for each section
    session = context.get('session', model.Session)

    for index, section_id in enumerate(section_order):
        section = DataStorySection.get(id=section_id)

        if not section:
            log.warning(f"Section not found: {section_id}, skipping")
            continue

        if section.story_id != story_id:
            log.warning(f"Section {section_id} does not belong to story {story_id}, skipping")
            continue

        section.order_index = index
        section.updated_at = datetime.datetime.utcnow()
        session.add(section)

    # Update story timestamp
    story.updated_at = datetime.datetime.utcnow()
    session.add(story)

    session.commit()

    log.info(f"[DATA_STORY_REORDER_SECTIONS] Reordered {len(section_order)} sections for story {story_id}")

    # Get updated sections
    sections = DataStorySection.all(story_id=story_id)
    from ckanext.pages.data_stories.db.utils import dictize_sections
    section_list = dictize_sections(sections, context)

    return {
        'success': True,
        'sections': section_list,
    }
