# encoding: utf-8
"""
Helpers package for data stories functionality.

Provides template helpers, formatting utilities, and Terria integration.
"""

from ckanext.pages.data_stories.helpers.terria import (
    parse_terria_share_link,
    generate_terria_embed_url,
    validate_terria_init_json,
    extract_terria_catalog_items,
    get_terria_base_url,
    get_terria_iframe_html,
    is_terria_url,
)

from ckanext.pages.data_stories.helpers.formatting import (
    render_story_date,
    render_story_abstract,
    get_story_status_badge,
    get_section_icon,
    get_section_title,
    markdown_to_html,
    truncate_text,
    pluralize,
    get_user_display_name,
    format_file_size,
    highlight_search_terms,
)

__all__ = [
    # Terria helpers
    'parse_terria_share_link',
    'generate_terria_embed_url',
    'validate_terria_init_json',
    'extract_terria_catalog_items',
    'get_terria_base_url',
    'get_terria_iframe_html',
    'is_terria_url',
    # Formatting helpers
    'render_story_date',
    'render_story_abstract',
    'get_story_status_badge',
    'get_section_icon',
    'get_section_title',
    'markdown_to_html',
    'truncate_text',
    'pluralize',
    'get_user_display_name',
    'format_file_size',
    'highlight_search_terms',
]
