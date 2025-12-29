"""
Data story import/export actions.

Provides functionality to export and import data stories as JSON,
allowing migration between CKAN instances.
"""

import datetime
import json
import logging

from ckan import model
import ckan.plugins.toolkit as tk

from ckanext.pages.data_stories.db.models import (
    DataStory,
    DataStorySection,
    DataStoryDataset,
    DataStoryContributor,
)
from ckanext.pages.data_stories.db.utils import make_uuid, table_dictize

log = logging.getLogger(__name__)

# Current export format version for compatibility checks
EXPORT_FORMAT_VERSION = '1.0'


def data_story_export(context, data_dict):
    """
    Export a data story as a JSON-serializable dict.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (optional if slug provided)
            - slug: Story slug (optional if id provided)
            - include_metadata: Include export metadata (default: True)

    Returns:
        Dict with complete story data ready for import

    Raises:
        NotAuthorized: If user is not sysadmin
        ObjectNotFound: If story doesn't exist
    """
    log.info("[DATA_STORY_EXPORT] Starting export")

    # Check authorization (sysadmin only)
    tk.check_access('data_story_export', context, data_dict)

    story_id = data_dict.get('id')
    slug = data_dict.get('slug')
    include_metadata = data_dict.get('include_metadata', True)

    if not story_id and not slug:
        raise tk.ValidationError({'id': ['Either id or slug must be provided']})

    # Get story
    if story_id:
        story = DataStory.get(id=story_id)
    else:
        story = DataStory.get(slug=slug)

    if not story:
        identifier = story_id or slug
        raise tk.ObjectNotFound(f"Story not found: {identifier}")

    # Build export data
    export_data = {
        'format_version': EXPORT_FORMAT_VERSION,
        'story': _serialize_story(story, context),
    }

    if include_metadata:
        export_data['export_metadata'] = {
            'exported_at': datetime.datetime.utcnow().isoformat(),
            'exported_by': context.get('user'),
            'source_ckan_version': tk.config.get('ckan.version', 'unknown'),
        }

    log.info(f"[DATA_STORY_EXPORT] Exported story: {story.id}")

    return export_data


def data_story_import(context, data_dict):
    """
    Import a data story from exported JSON data.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - data: The exported story data (required)
            - slug_conflict: Action on slug conflict: 'rename', 'overwrite', 'error' (default: 'rename')
            - owner_user_id: User ID to assign as author (optional, defaults to current user)
            - organization_id: Organization ID to assign (optional)
            - status: Status for imported story (default: 'draft')

    Returns:
        Dict with imported story data

    Raises:
        NotAuthorized: If user is not sysadmin
        ValidationError: If data is invalid
    """
    log.info("[DATA_STORY_IMPORT] Starting import")

    # Check authorization (sysadmin only)
    tk.check_access('data_story_import', context, data_dict)

    export_data = data_dict.get('data')
    if not export_data:
        raise tk.ValidationError({'data': ['Export data is required']})

    # Handle JSON string input
    if isinstance(export_data, str):
        try:
            export_data = json.loads(export_data)
        except json.JSONDecodeError as e:
            raise tk.ValidationError({'data': [f'Invalid JSON: {str(e)}']})

    # Validate format version
    format_version = export_data.get('format_version')
    if not format_version:
        raise tk.ValidationError({'data': ['Missing format_version in export data']})

    story_data = export_data.get('story')
    if not story_data:
        raise tk.ValidationError({'data': ['Missing story data in export']})

    # Get options
    slug_conflict = data_dict.get('slug_conflict', 'rename')
    owner_user_id = data_dict.get('owner_user_id')
    organization_id = data_dict.get('organization_id')
    target_status = data_dict.get('status', 'draft')

    # Get current user as default owner
    user = context.get('user')
    if not user:
        raise tk.NotAuthorized("Must be logged in to import stories")

    user_obj = model.User.get(user)
    if not user_obj:
        raise tk.NotAuthorized("User not found")

    # Determine author
    if owner_user_id:
        author = model.User.get(owner_user_id)
        if not author:
            raise tk.ValidationError({'owner_user_id': ['User not found']})
        author_id = author.id
    else:
        author_id = user_obj.id

    # Handle slug conflicts
    slug = story_data.get('slug', '')
    original_slug = slug

    if slug:
        existing = DataStory.get(slug=slug)
        if existing:
            if slug_conflict == 'error':
                raise tk.ValidationError({'slug': [f'Story with slug "{slug}" already exists']})
            elif slug_conflict == 'overwrite':
                # Delete existing story
                log.warning(f"[DATA_STORY_IMPORT] Overwriting existing story: {existing.id}")
                tk.get_action('data_story_delete')(context, {'id': existing.id})
            else:  # rename
                slug = _generate_unique_slug(slug)
                log.info(f"[DATA_STORY_IMPORT] Renamed slug from {original_slug} to {slug}")

    # Create new story
    now = datetime.datetime.utcnow()

    story = DataStory()
    story.id = make_uuid()
    story.title = story_data.get('title', 'Imported Story')
    story.slug = slug or _generate_unique_slug('imported-story')
    story.abstract = story_data.get('abstract', '')
    story.research_question = story_data.get('research_question', '')
    story.study_area = story_data.get('study_area', '')
    story.paper_doi = story_data.get('paper_doi', '')
    story.paper_citation = story_data.get('paper_citation', '')
    story.countries = story_data.get('countries', [])
    story.partners = story_data.get('partners', [])
    story.project_type = story_data.get('project_type')
    story.uploaded_images = story_data.get('uploaded_images', [])
    story.meta_description = story_data.get('meta_description', '')
    story.meta_keywords = story_data.get('meta_keywords', '')

    # Set ownership
    story.author_id = author_id
    story.organization_id = organization_id or story_data.get('organization_id')

    # Set status
    story.status = target_status
    story.is_public = False
    story.is_featured = False
    story.view_count = 0
    story.version = 1

    # Timestamps
    story.created_at = now
    story.updated_at = now

    # Save story
    session = context.get('session', model.Session)
    session.add(story)

    # Import sections
    sections_data = story_data.get('sections', [])
    imported_sections = []

    for idx, section_data in enumerate(sections_data):
        section = DataStorySection()
        section.id = make_uuid()
        section.story_id = story.id
        section.section_type = section_data.get('section_type', 'text')
        section.title = section_data.get('title', '')
        section.content = section_data.get('content', '')
        section.order_index = section_data.get('order_index', idx)
        section.image_url = section_data.get('image_url')
        section.video_url = section_data.get('video_url')
        section.terria_config = section_data.get('terria_config')
        section.terria_share_link = section_data.get('terria_share_link')
        section.blocks_metadata = section_data.get('blocks_metadata')
        section.is_visible = section_data.get('is_visible', True)
        section.created_at = now
        section.updated_at = now

        session.add(section)
        imported_sections.append(section)

    # Import contributors (optional)
    contributors_data = story_data.get('contributors', [])
    for contrib_data in contributors_data:
        contributor = DataStoryContributor()
        contributor.id = make_uuid()
        contributor.story_id = story.id
        contributor.name = contrib_data.get('name', '')
        contributor.email = contrib_data.get('email', '')
        contributor.affiliation = contrib_data.get('affiliation', '')
        contributor.orcid = contrib_data.get('orcid', '')
        contributor.role = contrib_data.get('role', '')
        contributor.order_index = contrib_data.get('order_index', 0)
        contributor.created_at = now
        # Note: user_id is not imported as users may not exist in target system

        session.add(contributor)

    # Commit all changes
    session.commit()

    log.info(f"[DATA_STORY_IMPORT] Imported story: {story.id} with {len(imported_sections)} sections")

    # Return the imported story
    result = table_dictize(story, context)
    result['sections'] = [table_dictize(s, context) for s in imported_sections]
    result['import_info'] = {
        'original_slug': original_slug,
        'final_slug': story.slug,
        'sections_imported': len(imported_sections),
        'contributors_imported': len(contributors_data),
    }

    return result


def _serialize_story(story, context):
    """
    Serialize a story and its related entities for export.
    """
    story_dict = {
        'title': story.title,
        'slug': story.slug,
        'abstract': story.abstract,
        'research_question': story.research_question,
        'study_area': story.study_area,
        'paper_doi': story.paper_doi,
        'paper_citation': story.paper_citation,
        'countries': story.countries or [],
        'partners': story.partners or [],
        'project_type': story.project_type,
        'uploaded_images': story.uploaded_images or [],
        'meta_description': story.meta_description,
        'meta_keywords': story.meta_keywords,
        'status': story.status,
        'created_at': story.created_at.isoformat() if story.created_at else None,
        'published_at': story.published_at.isoformat() if story.published_at else None,
    }

    # Include organization name (not ID, as it may differ across instances)
    if story.organization_id:
        org = model.Group.get(story.organization_id)
        if org:
            story_dict['organization_name'] = org.name
            story_dict['organization_title'] = org.title

    # Include sections
    sections = DataStorySection.all(story_id=story.id)
    story_dict['sections'] = []

    for section in sections:
        section_dict = {
            'section_type': section.section_type,
            'title': section.title,
            'content': section.content,
            'order_index': section.order_index,
            'image_url': section.image_url,
            'video_url': section.video_url,
            'terria_config': section.terria_config,
            'terria_share_link': section.terria_share_link,
            'blocks_metadata': section.blocks_metadata,
            'is_visible': section.is_visible,
        }
        story_dict['sections'].append(section_dict)

    # Include contributors
    contributors = DataStoryContributor.all(story_id=story.id)
    story_dict['contributors'] = []

    for contrib in contributors:
        contrib_dict = {
            'name': contrib.name,
            'email': contrib.email,
            'affiliation': contrib.affiliation,
            'orcid': contrib.orcid,
            'role': contrib.role,
            'order_index': contrib.order_index,
        }
        story_dict['contributors'].append(contrib_dict)

    # Include dataset references (by name, not ID)
    datasets = DataStoryDataset.all(story_id=story.id)
    story_dict['dataset_references'] = []

    for ds_link in datasets:
        try:
            pkg = model.Package.get(ds_link.dataset_id)
            if pkg:
                ds_ref = {
                    'dataset_name': pkg.name,
                    'dataset_title': pkg.title,
                    'relationship_type': ds_link.relationship_type,
                    'description': ds_link.description,
                    'order_index': ds_link.order_index,
                }
                story_dict['dataset_references'].append(ds_ref)
        except Exception as e:
            log.warning(f"Could not export dataset reference {ds_link.dataset_id}: {str(e)}")

    return story_dict


def _generate_unique_slug(base_slug):
    """
    Generate a unique slug by appending a number if necessary.
    """
    slug = base_slug
    counter = 1

    while DataStory.get(slug=slug):
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug
