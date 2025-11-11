"""
Business logic validation for data stories.

Separate from schema validation - these are business rules.
"""

import json
import logging
import re
from typing import Tuple, Dict, Any, List

from ckan import model
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

# Required sections for story submission
REQUIRED_SECTIONS = [
    'introduction',
    'data_sources',
    'methodology',
    'spatial_analysis',
    'conclusions',
]


def validate_story_completeness(story_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if story has all required sections for submission.

    Required sections:
    - Introduction
    - Data Sources
    - Methodology
    - At least one spatial analysis section
    - Conclusions

    Args:
        story_dict: Story data dict (must include 'sections')

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check if sections exist
    sections = story_dict.get('sections', [])
    if not sections:
        errors.append("Story must have at least one section")
        return (False, errors)

    # Get section types
    section_types = [s.get('section_type') for s in sections if s.get('section_type')]

    # Check required sections
    for required_type in REQUIRED_SECTIONS:
        if required_type not in section_types:
            section_name = required_type.replace('_', ' ').title()
            errors.append(f"Missing required section: {section_name}")

    # Check that at least one spatial analysis section has Terria config
    spatial_sections = [s for s in sections if s.get('section_type') == 'spatial_analysis']
    has_terria = any(
        s.get('terria_config') or s.get('terria_share_link')
        for s in spatial_sections
    )

    if spatial_sections and not has_terria:
        errors.append("At least one Spatial Analysis section must include a Terria map")

    # Check minimum content length
    for section in sections:
        content = section.get('content', '')
        section_type = section.get('section_type', 'unknown')

        if section_type in REQUIRED_SECTIONS:
            if not content or len(content.strip()) < 50:
                section_name = section_type.replace('_', ' ').title()
                errors.append(f"{section_name} section must have at least 50 characters")

    is_valid = len(errors) == 0
    return (is_valid, errors)


def validate_terria_config(terria_config: Any) -> Tuple[bool, List[str]]:
    """
    Validate Terria initialization JSON.

    Checks for required fields and valid structure.

    Args:
        terria_config: Terria config dict or JSON string

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Handle None or empty
    if not terria_config:
        return (True, [])  # Empty is valid (optional)

    # Parse JSON if string
    if isinstance(terria_config, str):
        try:
            terria_config = json.loads(terria_config)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in Terria config: {str(e)}")
            return (False, errors)

    # Check structure
    if not isinstance(terria_config, dict):
        errors.append("Terria config must be a JSON object")
        return (False, errors)

    # Check for recommended fields
    recommended_fields = ['initSources', 'catalog', 'homeCamera']

    has_init_sources = 'initSources' in terria_config
    has_catalog = 'catalog' in terria_config

    if not has_init_sources and not has_catalog:
        errors.append("Terria config should have 'initSources' or 'catalog' field")

    # Validate initSources structure if present
    if has_init_sources:
        init_sources = terria_config.get('initSources')
        if not isinstance(init_sources, list):
            errors.append("'initSources' must be an array")
        elif len(init_sources) == 0:
            errors.append("'initSources' array cannot be empty")

    # Validate catalog structure if present
    if has_catalog:
        catalog = terria_config.get('catalog')
        if not isinstance(catalog, list):
            errors.append("'catalog' must be an array")

    is_valid = len(errors) == 0
    return (is_valid, errors)


def validate_dataset_link(dataset_id: str, story_id: str, context: Dict[str, Any] = None) -> Tuple[bool, str]:
    """
    Validate that a dataset can be linked to a story.

    Checks:
    - Dataset exists
    - User has access to dataset
    - Dataset not already linked

    Args:
        dataset_id: CKAN package ID
        story_id: Story ID
        context: CKAN context dict (optional)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if context is None:
        context = {'ignore_auth': True}

    # Check if dataset exists and user has access
    try:
        dataset = tk.get_action('package_show')(context, {'id': dataset_id})
    except tk.ObjectNotFound:
        return (False, f"Dataset '{dataset_id}' not found")
    except tk.NotAuthorized:
        return (False, f"Not authorized to access dataset '{dataset_id}'")
    except Exception as e:
        log.error(f"Error checking dataset: {str(e)}")
        return (False, f"Error validating dataset: {str(e)}")

    # Check if already linked
    from ckanext.pages.data_stories.db.models import DataStoryDataset

    existing_link = DataStoryDataset.get(story_id=story_id, dataset_id=dataset_id)
    if existing_link:
        return (False, f"Dataset '{dataset['title']}' is already linked to this story")

    return (True, "")


def validate_slug(slug: str, story_id: str = None) -> Tuple[bool, str]:
    """
    Validate story slug.

    Checks:
    - Slug format (lowercase, alphanumeric + hyphens)
    - Slug uniqueness
    - Slug length

    Args:
        slug: Proposed slug
        story_id: Story ID (for updates, to exclude self)

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check format
    if not slug:
        return (False, "Slug cannot be empty")

    if len(slug) < 3:
        return (False, "Slug must be at least 3 characters")

    if len(slug) > 255:
        return (False, "Slug must be less than 255 characters")

    # Check pattern (lowercase letters, numbers, hyphens)
    pattern = r'^[a-z0-9-]+$'
    if not re.match(pattern, slug):
        return (False, "Slug can only contain lowercase letters, numbers, and hyphens")

    # Check for consecutive hyphens
    if '--' in slug:
        return (False, "Slug cannot contain consecutive hyphens")

    # Check start/end
    if slug.startswith('-') or slug.endswith('-'):
        return (False, "Slug cannot start or end with a hyphen")

    # Check uniqueness
    from ckanext.pages.data_stories.db.models import DataStory

    existing = DataStory.get(slug=slug)
    if existing and existing.id != story_id:
        return (False, f"Slug '{slug}' is already in use")

    return (True, "")


def generate_slug(title: str, max_length: int = 100) -> str:
    """
    Generate a URL-friendly slug from a title.

    Args:
        title: Story title
        max_length: Maximum slug length

    Returns:
        Generated slug
    """
    if not title:
        return ""

    # Convert to lowercase
    slug = title.lower()

    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)

    # Remove consecutive hyphens
    slug = re.sub(r'-+', '-', slug)

    # Trim hyphens from start/end
    slug = slug.strip('-')

    # Truncate to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')

    # Ensure uniqueness by appending number if needed
    from ckanext.pages.data_stories.db.models import DataStory

    original_slug = slug
    counter = 1

    while DataStory.get(slug=slug):
        slug = f"{original_slug}-{counter}"
        counter += 1

        # Ensure still within max length
        if len(slug) > max_length:
            # Shorten original and retry
            chars_to_remove = len(slug) - max_length
            original_slug = original_slug[:-(chars_to_remove + 3)]
            slug = f"{original_slug}-{counter}"

    return slug


def validate_section_type(section_type: str) -> Tuple[bool, str]:
    """
    Validate section type.

    Args:
        section_type: Section type to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_types = [
        'introduction',
        'research_question',
        'study_area',
        'data_sources',
        'methodology',
        'spatial_analysis',
        'results',
        'discussion',
        'conclusions',
        'references',
        'acknowledgments',
    ]

    if section_type not in valid_types:
        return (False, f"Invalid section type. Must be one of: {', '.join(valid_types)}")

    return (True, "")


def validate_story_status(status: str) -> Tuple[bool, str]:
    """
    Validate story status.

    Args:
        status: Status to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_statuses = ['draft', 'submitted', 'under_review', 'published', 'archived']

    if status not in valid_statuses:
        return (False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    return (True, "")


def validate_contributor_role(role: str) -> Tuple[bool, str]:
    """
    Validate contributor role.

    Args:
        role: Role to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_roles = ['co-author', 'data-provider', 'reviewer', 'editor', 'advisor']

    if role not in valid_roles:
        return (False, f"Invalid role. Must be one of: {', '.join(valid_roles)}")

    return (True, "")
