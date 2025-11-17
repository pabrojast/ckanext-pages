"""
Schema definitions for data stories.

Uses CKAN validators for consistency.
"""

import ckan.plugins.toolkit as tk


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

    return {
        'id': [ignore_empty, unicode_safe],
        'title': [not_empty, unicode_safe],
        'slug': [not_empty, unicode_safe],
        'abstract': [ignore_missing, unicode_safe],
        'research_question': [ignore_missing, unicode_safe],
        'study_area': [ignore_missing, unicode_safe],
        'author_id': [ignore_missing, user_id_exists],
        'organization_id': [ignore_missing, group_id_exists],
        'status': [ignore_missing, unicode_safe],
        'is_public': [ignore_missing, boolean_validator],
        'is_featured': [ignore_missing, boolean_validator],
    }


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
    json_validator = tk.get_validator('json_validator')

    return {
        'id': [ignore_empty, unicode_safe],
        'story_id': [not_empty, unicode_safe],
        'section_type': [not_empty, unicode_safe],
        'title': [ignore_missing, unicode_safe],
        'content': [ignore_missing, unicode_safe],
        'order_index': [not_empty, int_validator],
        'image_url': [ignore_missing, unicode_safe],
        'video_url': [ignore_missing, unicode_safe],
        'terria_config': [ignore_missing, json_validator],
        'terria_share_link': [ignore_missing, unicode_safe],
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
