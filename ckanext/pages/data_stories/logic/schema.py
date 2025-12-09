"""
Schema definitions for data stories.

Uses CKAN validators for consistency.
"""

import json

import ckan.plugins.toolkit as tk


def _get_json_validator():
    """
    Return CKAN's json_validator when available, otherwise use a local fallback.

    Some installations (older CKAN versions) don't expose json_validator via
    toolkit, so we provide a simple validator that checks JSON formatting.
    """
    try:
        return tk.get_validator('json_validator')
    except Exception:
        def _json_validator(key, data, errors, context):
            value = data.get(key)

            if not value:
                return

            if isinstance(value, (dict, list)):
                return

            try:
                json.loads(value)
            except (TypeError, ValueError):
                errors[key].append('Invalid JSON format')

        return _json_validator


def data_story_schema():
    """
    Schema for creating/updating data stories.

    Returns:
        Dict of field validators
    """
    ignore_empty = tk.get_validator('ignore_empty')
    ignore_missing = tk.get_validator('ignore_missing')
    not_empty = tk.get_validator('not_empty')
    unicode_safe = tk.get_validator('unicode_safe')
    boolean_validator = tk.get_validator('boolean_validator')
    int_validator = tk.get_validator('int_validator')
    user_id_exists = tk.get_validator('user_id_exists')
    group_id_exists = tk.get_validator('group_id_exists')
    json_validator = _get_json_validator()

    return {
        'id': [ignore_empty, unicode_safe],
        'title': [not_empty, unicode_safe],
        'slug': [not_empty, unicode_safe],
        'abstract': [ignore_missing, unicode_safe],
        'research_question': [ignore_missing, unicode_safe],
        'study_area': [ignore_missing, unicode_safe],
        'countries': [_default_to_empty_list, json_validator],
        'paper_doi': [ignore_missing, unicode_safe],
        'paper_citation': [ignore_missing, unicode_safe],
        'author_id': [ignore_missing, user_id_exists],
        'organization_id': [ignore_missing, group_id_exists],
        'status': [ignore_missing, unicode_safe],
        'is_public': [ignore_missing, boolean_validator],
        'is_featured': [ignore_missing, boolean_validator],
    }


def _default_to_none(key, data, errors, context):
    """
    Custom validator that defaults missing values to None instead of removing the key.
    This ensures the key is present in the validated data even if empty.
    Note: Empty lists [] are preserved, not converted to None.
    """
    from ckan.lib.navl.dictization_functions import missing
    value = data.get(key)
    if value is missing or value is None or value == '':
        data[key] = None
    # Keep empty lists [] as valid values - they are intentional


def _default_to_empty_list(key, data, errors, context):
    """
    Custom validator for list fields that defaults to an empty list instead of None.
    This is useful for fields like 'countries' where an empty list is a valid value.
    """
    from ckan.lib.navl.dictization_functions import missing
    value = data.get(key)
    if value is missing or value is None or value == '':
        data[key] = []
    elif isinstance(value, list):
        data[key] = value


def _coerce_json_field(key, data, errors, context):
    """
    Preserve dict/list JSON fields or parse JSON strings; allow empty -> None.
    Prevents valid list/dict values from being dropped during validation.
    """
    from ckan.lib.navl.dictization_functions import missing

    value = data.get(key, missing)
    if value is missing or value is None or value == '':
        data[key] = None
        return

    if isinstance(value, (dict, list)):
        data[key] = value
        return

    try:
        data[key] = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        # Keep original value so it is not lost, but register a validation error
        data[key] = value
        errors[key].append('Invalid JSON format')


def data_story_section_schema():
    """
    Schema for story sections.

    Returns:
        Dict of field validators
    """
    ignore_empty = tk.get_validator('ignore_empty')
    ignore_missing = tk.get_validator('ignore_missing')
    not_empty = tk.get_validator('not_empty')
    unicode_safe = tk.get_validator('unicode_safe')
    boolean_validator = tk.get_validator('boolean_validator')
    int_validator = tk.get_validator('int_validator')

    return {
        'id': [ignore_empty, unicode_safe],
        'story_id': [not_empty, unicode_safe],
        'section_type': [not_empty, unicode_safe],
        'title': [ignore_missing, unicode_safe],
        'content': [ignore_missing, unicode_safe],
        'order_index': [not_empty, int_validator],
        'image_url': [ignore_missing, unicode_safe],
        'video_url': [ignore_missing, unicode_safe],
        'terria_config': [_coerce_json_field],
        'terria_share_link': [ignore_missing, unicode_safe],
        'blocks_metadata': [_coerce_json_field],
        'is_visible': [ignore_missing, boolean_validator],
    }


def data_story_dataset_schema():
    """
    Schema for dataset links.

    Returns:
        Dict of field validators
    """
    ignore_empty = tk.get_validator('ignore_empty')
    ignore_missing = tk.get_validator('ignore_missing')
    not_empty = tk.get_validator('not_empty')
    unicode_safe = tk.get_validator('unicode_safe')
    int_validator = tk.get_validator('int_validator')

    return {
        'id': [ignore_empty, unicode_safe],
        'story_id': [not_empty, unicode_safe],
        'dataset_id': [not_empty, unicode_safe],
        'relationship_type': [ignore_missing, unicode_safe],
        'description': [ignore_missing, unicode_safe],
        'order_index': [ignore_missing, int_validator],
    }


def data_story_contributor_schema():
    """
    Schema for contributors.

    Returns:
        Dict of field validators
    """
    ignore_empty = tk.get_validator('ignore_empty')
    ignore_missing = tk.get_validator('ignore_missing')
    not_empty = tk.get_validator('not_empty')
    unicode_safe = tk.get_validator('unicode_safe')
    int_validator = tk.get_validator('int_validator')
    user_id_exists = tk.get_validator('user_id_exists')
    email_validator = tk.get_validator('email_validator')

    return {
        'id': [ignore_empty, unicode_safe],
        'story_id': [not_empty, unicode_safe],
        'user_id': [ignore_missing, user_id_exists],
        'name': [ignore_missing, unicode_safe],
        'email': [ignore_missing, email_validator],
        'affiliation': [ignore_missing, unicode_safe],
        'orcid': [ignore_missing, unicode_safe],
        'role': [ignore_missing, unicode_safe],
        'order_index': [ignore_missing, int_validator],
    }


def data_story_comment_schema():
    """
    Schema for comments.

    Returns:
        Dict of field validators
    """
    ignore_empty = tk.get_validator('ignore_empty')
    ignore_missing = tk.get_validator('ignore_missing')
    not_empty = tk.get_validator('not_empty')
    unicode_safe = tk.get_validator('unicode_safe')
    boolean_validator = tk.get_validator('boolean_validator')
    user_id_exists = tk.get_validator('user_id_exists')

    return {
        'id': [ignore_empty, unicode_safe],
        'story_id': [not_empty, unicode_safe],
        'user_id': [not_empty, user_id_exists],
        'section_id': [ignore_missing, unicode_safe],
        'content': [not_empty, unicode_safe],
        'comment_type': [ignore_missing, unicode_safe],
        'parent_comment_id': [ignore_missing, unicode_safe],
        'is_resolved': [ignore_missing, boolean_validator],
    }
