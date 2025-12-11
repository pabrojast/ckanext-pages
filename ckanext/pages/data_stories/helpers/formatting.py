# encoding: utf-8
"""
Formatting and display helpers for data stories templates.

Provides utilities for rendering dates, text, status badges, and other
UI elements in data story templates.
"""

import re
import logging
from datetime import datetime
from typing import Optional

log = logging.getLogger(__name__)


def render_story_date(date_obj: Optional[datetime],
                     format_string: str = '%B %d, %Y',
                     with_time: bool = False) -> str:
    """
    Render a datetime object as a formatted string.

    Args:
        date_obj: Datetime object to format
        format_string: strftime format string (default: 'Month DD, YYYY')
        with_time: Include time in output (default False)

    Returns:
        str: Formatted date string, or 'Not set' if None

    Example:
        >>> render_story_date(datetime.now())
        'January 15, 2024'
        >>> render_story_date(datetime.now(), with_time=True)
        'January 15, 2024 at 3:45 PM'
    """
    if not date_obj:
        return 'Not set'

    try:
        if with_time:
            format_string = '%B %d, %Y at %I:%M %p'

        return date_obj.strftime(format_string)

    except Exception as e:
        log.error(f"Error formatting date: {str(e)}")
        return str(date_obj)


def render_story_abstract(abstract: Optional[str],
                          max_length: int = 200,
                          strip_html: bool = True) -> str:
    """
    Render a story abstract with optional truncation.

    Args:
        abstract: Abstract text (may contain HTML/Markdown)
        max_length: Maximum character length (default 200)
        strip_html: Remove HTML tags (default True)

    Returns:
        str: Formatted abstract text

    Example:
        >>> render_story_abstract('This is a long abstract...', max_length=50)
        'This is a long abstract...'
    """
    if not abstract:
        return ''

    # Strip HTML if needed
    if strip_html:
        abstract = _strip_html_tags(abstract)

    # Truncate if needed
    if len(abstract) > max_length:
        abstract = truncate_text(abstract, max_length)

    return abstract


def get_story_status_badge(status: str) -> dict:
    """
    Get CSS class and label for a story status badge.

    Args:
        status: Story status (draft, submitted, under_review, published, archived)

    Returns:
        dict: Contains 'class', 'label', and 'icon' keys

    Example:
        >>> badge = get_story_status_badge('published')
        >>> print(f'<span class="{badge["class"]}">{badge["label"]}</span>')
    """
    status_map = {
        'draft': {
            'class': 'label label-default',
            'label': 'Draft',
            'icon': 'fa-pencil',
        },
        'submitted': {
            'class': 'label label-info',
            'label': 'Submitted',
            'icon': 'fa-paper-plane',
        },
        'under_review': {
            'class': 'label label-warning',
            'label': 'Under Review',
            'icon': 'fa-search',
        },
        'published': {
            'class': 'label label-success',
            'label': 'Published',
            'icon': 'fa-check-circle',
        },
        'archived': {
            'class': 'label label-danger',
            'label': 'Archived',
            'icon': 'fa-archive',
        },
    }

    return status_map.get(status, {
        'class': 'label label-default',
        'label': status.replace('_', ' ').title(),
        'icon': 'fa-question-circle',
    })


def get_section_icon(section_type: str) -> str:
    """
    Get Font Awesome icon class for a section type.

    Args:
        section_type: Section type identifier

    Returns:
        str: Font Awesome icon class (e.g., 'fa-book')

    Example:
        >>> icon = get_section_icon('introduction')
        >>> print(f'<i class="fa {icon}"></i>')
    """
    icon_map = {
        'introduction': 'fa-book',
        'research_question': 'fa-question-circle',
        'study_area': 'fa-map-marker',
        'data_sources': 'fa-database',
        'methodology': 'fa-cogs',
        'spatial_analysis': 'fa-globe',
        'results': 'fa-bar-chart',
        'discussion': 'fa-comments',
        'conclusions': 'fa-flag-checkered',
        'references': 'fa-link',
        'acknowledgments': 'fa-heart',
        'custom': 'fa-file-text',
    }

    return icon_map.get(section_type, 'fa-file-text')


def get_section_title(section_type: str, custom_title: Optional[str] = None) -> str:
    """
    Get display title for a section, using custom title if provided.

    Args:
        section_type: Section type identifier
        custom_title: Optional custom title to override default

    Returns:
        str: Display title for the section

    Example:
        >>> get_section_title('introduction', 'My Custom Intro')
        'My Custom Intro'
        >>> get_section_title('methodology')
        'Methodology'
    """
    if custom_title:
        return custom_title

    title_map = {
        'introduction': 'Introduction',
        'research_question': 'Research Question',
        'study_area': 'Study Area',
        'data_sources': 'Data Sources',
        'methodology': 'Methodology',
        'spatial_analysis': 'Spatial Analysis',
        'results': 'Results',
        'discussion': 'Discussion',
        'conclusions': 'Conclusions',
        'references': 'References',
        'acknowledgments': 'Acknowledgments',
        'custom': 'Custom Section',
    }

    return title_map.get(section_type, section_type.replace('_', ' ').title())


def markdown_to_html(text: Optional[str]) -> str:
    """
    Convert markdown text to HTML using CKAN's markdown renderer.

    Args:
        text: Markdown text to convert

    Returns:
        str: HTML output

    Example:
        >>> html = markdown_to_html('**Bold text**')
        >>> # Returns: '<p><strong>Bold text</strong></p>'
    """
    if not text:
        return ''

    try:
        from ckan.lib.helpers import render_markdown
        return render_markdown(text)
    except Exception as e:
        log.error(f"Error rendering markdown: {str(e)}")
        # Fall back to plain text
        return f'<p>{text}</p>'


def truncate_text(text: str, max_length: int = 200, suffix: str = '...') -> str:
    """
    Truncate text to a maximum length, breaking at word boundaries.

    Args:
        text: Text to truncate
        max_length: Maximum character length (default 200)
        suffix: Suffix to append when truncated (default '...')

    Returns:
        str: Truncated text with suffix if needed

    Example:
        >>> truncate_text('This is a very long sentence that needs truncating', 20)
        'This is a very...'
    """
    if not text or len(text) <= max_length:
        return text

    # Truncate at word boundary
    truncated = text[:max_length].rsplit(' ', 1)[0]

    # Add suffix
    return f"{truncated}{suffix}"


def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
    """
    Return singular or plural form based on count.

    Args:
        count: Number to check
        singular: Singular form of the word
        plural: Plural form (default: singular + 's')

    Returns:
        str: Appropriate form with count

    Example:
        >>> pluralize(1, 'section')
        '1 section'
        >>> pluralize(3, 'section')
        '3 sections'
        >>> pluralize(2, 'story', 'stories')
        '2 stories'
    """
    if plural is None:
        plural = f"{singular}s"

    word = singular if count == 1 else plural
    return f"{count} {word}"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size (e.g., '1.5 MB')

    Example:
        >>> format_file_size(1536000)
        '1.46 MB'
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _strip_html_tags(text: str) -> str:
    """
    Remove HTML tags from text and decode HTML entities.

    Args:
        text: Text that may contain HTML

    Returns:
        str: Text with HTML tags removed and entities decoded
    """
    if not text:
        return ''

    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)

    # Decode HTML entities (e.g., &nbsp; -> space, &lt; -> <)
    try:
        import html
        clean_text = html.unescape(clean_text)
    except Exception as e:
        log.warning(f"Error decoding HTML entities: {str(e)}")

    # Remove extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text)

    return clean_text.strip()


def get_user_display_name(user: dict) -> str:
    """
    Get display name for a user, preferring fullname over name.

    Args:
        user: User dict with name and optionally fullname

    Returns:
        str: Display name for the user

    Example:
        >>> get_user_display_name({'name': 'jdoe', 'fullname': 'John Doe'})
        'John Doe'
        >>> get_user_display_name({'name': 'jdoe'})
        'jdoe'
    """
    if not user:
        return 'Unknown user'

    return user.get('fullname') or user.get('display_name') or user.get('name', 'Unknown user')


def get_gravatar_url(email: str, size: int = 80, default: str = 'identicon') -> str:
    """
    Generate Gravatar URL for an email address.

    Args:
        email: Email address
        size: Image size in pixels (default 80)
        default: Default image type (default 'identicon')

    Returns:
        str: Gravatar URL

    Example:
        >>> get_gravatar_url('user@example.com', size=40)
        'https://www.gravatar.com/avatar/...'
    """
    try:
        from ckan.lib.helpers import gravatar as ckan_gravatar
        return ckan_gravatar(email, size=size, default=default)
    except Exception:
        # Fall back to direct construction
        import hashlib
        email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d={default}"


def highlight_search_terms(text: str, search_query: str) -> str:
    """
    Highlight search terms in text with <mark> tags.

    Args:
        text: Text to highlight
        search_query: Search query with terms to highlight

    Returns:
        str: Text with search terms wrapped in <mark> tags

    Example:
        >>> highlight_search_terms('Water resources study', 'water')
        '<mark>Water</mark> resources study'
    """
    if not text or not search_query:
        return text

    # Split query into terms
    terms = search_query.strip().split()

    # Highlight each term (case-insensitive)
    for term in terms:
        if len(term) < 3:  # Skip very short terms
            continue

        # Use regex for case-insensitive replacement
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        text = pattern.sub(lambda m: f'<mark>{m.group(0)}</mark>', text)

    return text
