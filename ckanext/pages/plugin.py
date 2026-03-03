import logging
import json
import re
import hashlib
import time
from functools import lru_cache
from html import escape as html_escape

from six.moves.urllib.parse import quote, urlencode

from ckan.plugins import toolkit as tk

import ckan.plugins as p
from ckan.lib.helpers import build_nav_main as core_build_nav_main

from ckanext.pages import actions
from ckanext.pages import auth
from ckanext.pages import blueprint


log = logging.getLogger(__name__)

DATA_STORIES_AVAILABLE = False
data_stories_blueprint = None
ds_actions = None
ds_auth = None
init_data_stories_tables = None

FEATURED_VIEWERS_AVAILABLE = False
featured_viewers_blueprint = None
fv_actions = None
fv_auth = None
init_featured_viewers_tables = None

# Import data stories modules
try:
    from ckanext.pages.data_stories.helpers import (
        parse_terria_share_link,
        generate_terria_embed_url,
        validate_terria_init_json,
        extract_terria_catalog_items,
        get_terria_base_url,
        get_terria_iframe_html,
        is_terria_url,
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
    from ckanext.pages.data_stories import actions as ds_actions
    from ckanext.pages.data_stories import auth as ds_auth
    from ckanext.pages.data_stories.blueprint import data_stories_blueprint
    from ckanext.pages.data_stories.db.utils import init_tables as init_data_stories_tables

    DATA_STORIES_AVAILABLE = True
except ImportError as e:
    log.warning("Data stories modules not available: %s", str(e))

# Import featured viewers modules
try:
    from ckanext.pages.featured_viewers.helpers import (
        get_viewer_categories,
        get_viewer_category_info,
        get_viewer_category_title,
        get_viewer_category_icon,
        get_viewer_category_color,
        get_viewer_status_badge,
        format_viewer_view_count,
        get_available_icons,
        json_loads as fv_json_loads,
    )
    from ckanext.pages.featured_viewers import actions as fv_actions
    from ckanext.pages.featured_viewers import auth as fv_auth
    from ckanext.pages.featured_viewers.blueprint.routes import featured_viewers_blueprint
    from ckanext.pages.featured_viewers.db.utils import init_tables as init_featured_viewers_tables

    FEATURED_VIEWERS_AVAILABLE = True
except ImportError as e:
    log.warning("Featured viewers modules not available: %s", str(e))


from ckan.lib.plugins import DefaultTranslation

# Import database initialization utilities
try:
    from ckanext.pages.db_init import repair_table_if_needed, ensure_pages_table_exists
except ImportError:
    # Fallback functions if db_init is not available
    def repair_table_if_needed():
        return True
    def ensure_pages_table_exists():
        pass



def build_pages_nav_main(*args):

    about_menu = tk.asbool(tk.config.get('ckanext.pages.about_menu', True))
    group_menu = tk.asbool(tk.config.get('ckanext.pages.group_menu', True))
    org_menu = tk.asbool(tk.config.get('ckanext.pages.organization_menu', True))
    root_path = tk.config.get('ckan.root_path', '/')

    new_args = []
    for arg in args:
        if arg[0] in 'home.about' and not about_menu:
            continue
        if arg[0] in 'home.group_index' and not org_menu:
            continue
        if arg[0] in 'home.organizations_index' and not group_menu:
            continue
        new_args.append(arg)

    output = core_build_nav_main(*new_args)

    # do not display any private pages in menu even for sysadmins
    try:
        pages_list = tk.get_action('ckanext_pages_list')(None, {'order': True, 'private': False})
    except Exception as e:
        log.error("Error getting pages list for navigation: %s", str(e))
        error_str = str(e).lower()
        
        # Check for database connection issues
        if any(keyword in error_str for keyword in [
            'server closed the connection',
            'connection unexpectedly',
            'nonetype',
            'cursor',
            'connection refused',
            'no connection to the server',
            'database is locked',
            'connection timeout'
        ]):
            log.warning("Database connection issue detected in navigation. Skipping pages menu to prevent cascading errors.")
            return output
        
        # Try to repair the table if there's a table-specific database issue
        try:
            if "ckanext_pages" in error_str:
                log.info("Attempting to repair ckanext_pages table...")
                if repair_table_if_needed():
                    # Try again after repair
                    pages_list = tk.get_action('ckanext_pages_list')(None, {'order': True, 'private': False})
                    log.info("Successfully repaired table and retrieved pages list")
                else:
                    log.error("Table repair failed")
                    return output
            else:
                return output
        except Exception as repair_error:
            log.error("Error during table repair: %s", str(repair_error))
            return output

    page_name = ''
    is_current_page = tk.get_endpoint() in (('pages', 'show'), ('pages', 'blog_show'))

    if is_current_page:
        page_name = tk.request.path.split('/')[-1]

    try:
        # Safely check if pages_list is valid before processing
        if not pages_list or not isinstance(pages_list, list):
            log.debug("Pages list is empty or invalid, skipping navigation menu")
            return output
            
        for page in pages_list:
            try:
                # Safely extract page data with defaults
                page_type = page.get('page_type', 'pages')
                page_name_raw = page.get('name', '')
                page_title = page.get('title', '')
                
                # Skip pages with missing essential data
                if not page_name_raw or not page_title:
                    log.warning("Skipping page with missing name or title: %s", page)
                    continue
                
                type_ = 'blog' if page_type == 'blog' else 'pages'
                if page_type == 'rapid-response':
                    type_ = 'rapid-response'
                elif page_type == 'open-source-software':
                    type_ = 'open-source-tools'
                    
                name = quote(page_name_raw)
                title = html_escape(page_title)
                link = tk.h.literal(u'<a href="{}/{}/{}">{}</a>'.format(root_path, type_, name, title))
                
                if page_name_raw == page_name:
                    li = tk.literal('<li class="active">') + link + tk.literal('</li>')
                else:
                    li = tk.literal('<li>') + link + tk.literal('</li>')
                output = output + li
            except Exception as page_error:
                log.warning("Error processing individual page for navigation: %s. Page data: %s", 
                          str(page_error), page)
                continue
                
    except Exception as e:
        log.error("Error building pages navigation: %s", str(e))
        # Continue with basic navigation if there's an error processing pages

    return output


def render_content(content):
    allow_html = tk.asbool(tk.config.get('ckanext.pages.allow_html', False))
    return tk.h.render_markdown(content, allow_html=allow_html)


def strip_html_tags(content):
    """Remove HTML tags from content for plain text display"""
    if not content:
        return ''
    # Remove HTML tags
    clean_text = re.sub('<[^<]+?>', '', content)
    # Replace multiple spaces/newlines with single spaces
    clean_text = re.sub(r'\s+', ' ', clean_text)
    # Strip leading/trailing whitespace
    return clean_text.strip()


def has_meaningful_content(content):
    """Check if content has meaningful text beyond HTML tags and whitespace"""
    if not content:
        return False
    
    # Remove HTML tags and decode HTML entities
    clean_text = re.sub('<[^<]+?>', '', content)
    clean_text = re.sub(r'&[a-zA-Z0-9#]+;', '', clean_text)
    
    # Remove all whitespace characters (spaces, tabs, newlines)
    clean_text = re.sub(r'\s+', '', clean_text)
    
    # Remove common empty content patterns
    clean_text = re.sub(r'&nbsp;', '', clean_text)
    clean_text = re.sub(r'<br\s*/?>', '', clean_text)
    
    # Check if there's any meaningful content left
    return len(clean_text) > 0


def sanitize_html_content(content):
    """Sanitize HTML content to fix common encoding issues from WYSIWYG editors.
    
    This helper cleans up content that may have encoding issues or strange characters
    from editors like Quill, CKEditor, etc.
    """
    if not content:
        return content
    
    import html
    
    # First, decode any HTML entities that might have been double-encoded
    try:
        content = html.unescape(content)
    except Exception:
        pass
    
    # Fix common problematic patterns
    replacements = [
        # Double-encoded entities
        ('&amp;nbsp;', ' '),
        ('&amp;lt;', '<'),
        ('&amp;gt;', '>'),
        ('&amp;amp;', '&'),
        ('&amp;quot;', '"'),
        # Common problematic characters
        ('\u00a0', ' '),  # Non-breaking space
        ('\u200b', ''),   # Zero-width space
        ('\u200c', ''),   # Zero-width non-joiner
        ('\u200d', ''),   # Zero-width joiner
        ('\ufeff', ''),   # BOM
        # Smart quotes to regular quotes
        ('\u2018', "'"),  # Left single quote
        ('\u2019', "'"),  # Right single quote
        ('\u201c', '"'),  # Left double quote
        ('\u201d', '"'),  # Right double quote
        # Dashes
        ('\u2013', '-'),  # En dash
        ('\u2014', '-'),  # Em dash
        # Ellipsis
        ('\u2026', '...'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    return content


def gravatar_url(email, size=40, default='identicon', rating='g'):
    """Return a gravatar URL for the given email, falling back gracefully."""
    if not email:
        email = ''
    email_bytes = email.strip().lower().encode('utf-8')
    email_hash = hashlib.md5(email_bytes).hexdigest()

    params = {'s': str(size)}
    if default:
        params['d'] = default
    if rating:
        params['r'] = rating

    return 'https://www.gravatar.com/avatar/{}?{}'.format(
        email_hash,
        urlencode(params)
    )


def get_wysiwyg_editor():
    return tk.config.get('ckanext.pages.editor', '')


def _get_recent_blog_posts(number, exclude):
    try:
        limit = number + 1 if exclude else number
        blog_list = tk.get_action('ckanext_pages_list')(
            None, {'order_publish_date': True, 'private': False,
                   'page_type': 'blog', 'limit': limit}
        )
    except Exception as e:
        log.error("Error getting blog posts list: %s", str(e))
        return []

    new_list = []
    for blog in blog_list:
        if exclude and blog.get('name') == exclude:
            continue
        new_list.append(blog)
        if len(new_list) == number:
            break

    return new_list


@lru_cache(maxsize=64)
def _get_recent_blog_posts_cached(number, exclude, cache_buster):
    return _get_recent_blog_posts(number, exclude)


def _get_recent_blog_cache_ttl():
    try:
        return max(0, tk.asint(tk.config.get('ckanext.pages.recent_blog_cache_ttl', 300)))
    except Exception:
        return 300


def get_recent_blog_posts(number=5, exclude=None):
    cache_ttl = _get_recent_blog_cache_ttl()
    if cache_ttl <= 0:
        return _get_recent_blog_posts(number, exclude)
    cache_buster = int(time.time() / cache_ttl)
    return _get_recent_blog_posts_cached(number, exclude, cache_buster)


def get_recent_rapid_response_posts(number=5, exclude=None):
    try:
        rapid_response_list = tk.get_action('ckanext_pages_list')(
            None, {'order_publish_date': True, 'private': False,
                   'page_type': 'rapid-response'}
        )
    except Exception as e:
        log.error("Error getting rapid response posts list: %s", str(e))
        return []
        
    new_list = []
    for rr_post in rapid_response_list:
        if exclude and rr_post.get('name') == exclude:
            continue
        new_list.append(rr_post)
        if len(new_list) == number:
            break

    return new_list


def get_recent_water_news(number=5, exclude=None):
    """Get recent water family news"""
    try:
        news_list = tk.get_action('ckanext_pages_list')(
            None, {'order_publish_date': True, 'private': False,
                   'page_type': 'water-news'}
        )
        new_list = []
        for news_post in news_list:
            if exclude and news_post.get('name') == exclude:
                continue
            new_list.append(news_post)
            if len(new_list) == number:
                break
        return new_list
    except Exception as e:
        log.error("Error getting water news list: %s", str(e))
        return []


def get_recent_water_events(number=5, exclude=None):
    """Get recent water family events"""
    try:
        events_list = tk.get_action('ckanext_pages_list')(
            None, {'order_publish_date': True, 'private': False,
                   'page_type': 'water-events'}
        )
        new_list = []
        for event_post in events_list:
            if exclude and event_post.get('name') == exclude:
                continue
            new_list.append(event_post)
            if len(new_list) == number:
                break
        return new_list
    except Exception as e:
        log.error("Error getting water events list: %s", str(e))
        return []


def get_recent_water_publications(number=5, exclude=None):
    """Get recent water family publications"""
    try:
        publications_list = tk.get_action('ckanext_pages_list')(
            None, {'order_publish_date': True, 'private': False,
                   'page_type': 'water-publications'}
        )
        new_list = []
        for pub_post in publications_list:
            if exclude and pub_post.get('name') == exclude:
                continue
            new_list.append(pub_post)
            if len(new_list) == number:
                break
        return new_list
    except Exception as e:
        log.error("Error getting water publications list: %s", str(e))
        return []


def get_recent_open_source_software(number=5, exclude=None):
    """Get recent open source software entries - only show approved public entries"""
    try:
        software_list = tk.get_action('ckanext_pages_list')(
            None, {'order_publish_date': True, 'private': False,
                   'page_type': 'open-source-software',
                   'submission_status': 'approved'}
        )
        new_list = []
        for software_post in software_list:
            if exclude and software_post.get('name') == exclude:
                continue
            # Double-check that entry is approved and public
            if software_post.get('submission_status') == 'approved' and not software_post.get('private'):
                new_list.append(software_post)
            if len(new_list) == number:
                break
        return new_list
    except Exception as e:
        log.error("Error getting open source software list: %s", str(e))
        return []


def get_recent_ai_water_tools(number=5, exclude=None):
    """Get recent AI water tools entries - only show approved public entries"""
    try:
        tools_list = tk.get_action('ckanext_pages_list')(
            None, {'order_publish_date': True, 'private': False,
                   'page_type': 'ai-water-tools',
                   'submission_status': 'approved'}
        )
        new_list = []
        for tool_post in tools_list:
            if exclude and tool_post.get('name') == exclude:
                continue
            if tool_post.get('submission_status') == 'approved' and not tool_post.get('private'):
                new_list.append(tool_post)
            if len(new_list) == number:
                break
        return new_list
    except Exception as e:
        log.error("Error getting AI water tools list: %s", str(e))
        return []


def safe_json_loads(json_string):
    """Safely parse JSON string and return empty list if parsing fails"""
    if not json_string:
        return []
    try:
        return json.loads(json_string)
    except (ValueError, TypeError, json.JSONDecodeError):
        return []


def get_event_status(page):
    """Determine event status based on timeline events"""
    if not page.get('timeline_events'):
        return 'active'
    
    try:
        timeline_events = json.loads(page['timeline_events'])
        if not timeline_events:
            return 'active'
        
        # Check for closure events
        closure_types = ['closure', 'closed', 'end', 'completed', 'resolved']
        for event in timeline_events:
            event_type = event.get('type', '').lower()
            description = event.get('description', '').lower()
            
            # Check if event type or description indicates closure
            if (event_type in closure_types or 
                any(closure_word in description for closure_word in closure_types)):
                return 'closed'
        
        return 'active'
    except:
        return 'active'


def get_event_status_badge_class(status):
    """Get CSS class for event status badge"""
    if status == 'closed':
        return 'status-closed'
    elif status == 'active':
        return 'status-active'
    else:
        return 'status-unknown'


def count_unique_countries(pages):
    """Count unique countries from pages' countries_affected field and fallback to key_info"""
    countries = set()
    for page in pages:
        # First, try new format - countries_affected field with JSON array
        if page.get('countries_affected'):
            try:
                import json
                countries_data = json.loads(page['countries_affected'])
                if isinstance(countries_data, list):
                    for country_obj in countries_data:
                        if isinstance(country_obj, dict) and 'name' in country_obj:
                            countries.add(country_obj['name'])
                        elif isinstance(country_obj, str):
                            countries.add(country_obj)
            except (json.JSONDecodeError, TypeError):
                # If JSON parsing fails, treat as string
                country_text = str(page['countries_affected'])
                for country in country_text.split(','):
                    country = country.strip()
                    if country:
                        countries.add(country)
        
        # Fallback to legacy country field (comma-separated string)
        elif page.get('country'):
            country_text = str(page['country'])
            for country in country_text.split(','):
                country = country.strip()
                if country:
                    countries.add(country)
        
        # Fallback to key_info field (legacy format)
        elif page.get('key_info'):
            lines = page['key_info'].split('\n')
            for line in lines:
                line = line.strip()
                if line.lower().startswith('countries affected:') or line.lower().startswith('country affected:'):
                    # Extract the country part after the colon
                    country_part = line.split(':', 1)
                    if len(country_part) > 1:
                        country_text = country_part[1].strip()
                        # Split by comma in case multiple countries are listed
                        for country in country_text.split(','):
                            country = country.strip()
                            if country:
                                countries.add(country)
    return len(countries)


def get_software_category_class(category):
    """Get CSS class for software category"""
    category_classes = {
        'gis': 'category-gis',
        'data-processing': 'category-data',
        'visualization': 'category-viz',
        'web-platform': 'category-web',
        'desktop-app': 'category-desktop',
        'mobile-app': 'category-mobile',
        'library': 'category-library',
        'framework': 'category-framework',
        'api': 'category-api',
        'tool': 'category-tool'
    }
    return category_classes.get(category.lower(), 'category-default')


def clean_categories_string(categories_str):
    """Clean categories string by removing duplicates and empty values

    Handles various input formats:
    - Comma-separated strings: "Python,JavaScript,R"
    - JSON-like strings: '["Python", "JavaScript"]'
    - Malformed JSON: '["Python"' or '["Python", "JavaScript"]'
    """
    if not categories_str:
        return ''

    # Try to parse as JSON first (handles list format)
    import json
    import re

    # Remove leading/trailing whitespace
    cleaned = categories_str.strip()

    # Check if it looks like a JSON array (starts with '[')
    if cleaned.startswith('['):
        # Try to parse as JSON
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                categories = [str(item).strip() for item in parsed if item]
            else:
                categories = [str(parsed).strip()]
        except (json.JSONDecodeError, ValueError):
            # If JSON parsing fails, treat as comma-separated
            # Remove brackets and quotes manually
            cleaned = re.sub(r'[\[\]"\']', '', cleaned)
            categories = [cat.strip() for cat in cleaned.split(',') if cat.strip()]
    else:
        # Handle comma-separated format
        # Also clean any quotes that might be present
        cleaned = re.sub(r'^["\']|["\']$', '', cleaned)
        categories = [cat.strip() for cat in cleaned.split(',') if cat.strip()]

    # Remove duplicates while preserving order
    unique_categories = []
    seen = set()
    for cat in categories:
        # Remove any remaining quotes
        cat_clean = cat.strip().strip('"\'')
        if cat_clean and cat_clean not in seen:
            unique_categories.append(cat_clean)
            seen.add(cat_clean)

    return ','.join(unique_categories)


def get_categories_list(categories_str):
    """Get categories as a list for template iteration"""
    if not categories_str:
        return []

    clean_categories = clean_categories_string(categories_str)
    if not clean_categories:
        return []

    return [cat.strip() for cat in clean_categories.split(',') if cat.strip()]


def count_software_by_category(pages):
    """Count software entries by category"""
    categories = {}
    for page in pages:
        category = page.get('software_category', 'other').lower()
        categories[category] = categories.get(category, 0) + 1
    return categories


def get_software_difficulty_class(difficulty):
    """Get CSS class for software difficulty level"""
    difficulty_classes = {
        'beginner': 'difficulty-beginner',
        'intermediate': 'difficulty-intermediate', 
        'advanced': 'difficulty-advanced',
        'expert': 'difficulty-expert'
    }
    return difficulty_classes.get(difficulty, 'difficulty-beginner')


def get_ai_technique_class(technique):
    """Get CSS class for AI technique category"""
    technique_classes = {
        'machine-learning': 'technique-ml',
        'deep-learning': 'technique-dl',
        'nlp': 'technique-nlp',
        'computer-vision': 'technique-cv',
        'reinforcement-learning': 'technique-rl',
        'time-series-forecasting': 'technique-ts',
        'optimization': 'technique-opt',
        'hybrid': 'technique-hybrid',
    }
    return technique_classes.get(technique.lower() if technique else '', 'technique-default')


def count_ai_tools_by_technique(pages):
    """Count AI water tools entries by technique"""
    techniques = {}
    for page in pages:
        technique = page.get('ai_technique', 'other').lower()
        techniques[technique] = techniques.get(technique, 0) + 1
    return techniques


def count_ai_tools_by_application(pages):
    """Count AI water tools entries by water application domain"""
    applications = {}
    for page in pages:
        application = page.get('water_application', 'other').lower()
        applications[application] = applications.get(application, 0) + 1
    return applications


def get_priority_sort_key(page):
    """Get numeric sort key for priority level (higher number = higher priority)"""
    priority = page.get('priority', 'high').lower()
    priority_weights = {
        'urgent': 4,
        'high': 3,
        'medium': 2,
        'low': 1
    }
    return priority_weights.get(priority, 3)  # Default to high priority


def get_severity_sort_key(page):
    """Get numeric sort key for severity level (higher number = higher severity)"""
    severity = page.get('severity', '').lower()
    severity_weights = {
        'moderate': 2,
        'low': 1
    }
    return severity_weights.get(severity, 0)  # Default to 0 if no severity set


def get_priority_class(priority):
    """Get CSS class for priority level"""
    priority_classes = {
        'urgent': 'priority-urgent',
        'high': 'priority-high',
        'medium': 'priority-medium',
        'low': 'priority-low'
    }
    return priority_classes.get(priority, 'priority-high')


def get_severity_class(severity):
    """Get CSS class for severity level"""
    severity_classes = {
        'moderate': 'severity-moderate',
        'low': 'severity-low'
    }
    return severity_classes.get(severity, '')


def get_event_types(active_only=True):
    """Get list of event types for templates"""
    try:
        event_types = tk.get_action('ckanext_event_types_list')(
            {}, {'active_only': active_only}
        )
        return event_types
    except:
        # Fallback to default types
        return [
            {'id': 'tropical-cyclone', 'name': 'tropical-cyclone', 'title': 'Tropical Cyclone', 'title_plural': 'Tropical Cyclones'},
            {'id': 'earthquake', 'name': 'earthquake', 'title': 'Earthquake', 'title_plural': 'Earthquakes'},
            {'id': 'tsunami', 'name': 'tsunami', 'title': 'Tsunami', 'title_plural': 'Tsunamis'},
            {'id': 'flood', 'name': 'flood', 'title': 'Flood', 'title_plural': 'Floods'},
            {'id': 'wildfire', 'name': 'wildfire', 'title': 'Wildfire', 'title_plural': 'Wildfires'},
            {'id': 'volcanic-eruption', 'name': 'volcanic-eruption', 'title': 'Volcanic Eruption', 'title_plural': 'Volcanic Eruptions'},
            {'id': 'drought', 'name': 'drought', 'title': 'Drought', 'title_plural': 'Droughts'},
            {'id': 'armed-conflict', 'name': 'armed-conflict', 'title': 'Armed Conflict', 'title_plural': 'Armed Conflicts'}
        ]


def get_event_type_by_id(event_type_id):
    """Get a specific event type by ID"""
    try:
        event_type = tk.get_action('ckanext_event_types_show')(
            {}, {'id': event_type_id}
        )
        return event_type
    except:
        # Fallback to default types
        default_types = get_event_types(active_only=False)
        return next((et for et in default_types if et['id'] == event_type_id), None)


def is_sysadmin():
    """Check if current user is sysadmin"""
    try:
        import ckan.authz as authz
        return authz.is_sysadmin(tk.g.user)
    except Exception:
        return False


def get_pending_approval_count():
    """Return total pending approval count for sysadmins (used in header badge)."""
    try:
        import ckan.authz as authz
        if not tk.g.user or not authz.is_sysadmin(tk.g.user):
            return 0
        from ckanext.pages.db import Page
        from ckan import model
        count = model.Session.query(Page).filter(
            Page.page_type.in_(
                ['water-news', 'water-events', 'water-publications',
                 'open-source-software']
            ),
            Page.private == True,
            Page.submission_status == 'pending',
            Page.group_id == None
        ).count()
        # Include pending data stories
        try:
            from ckanext.pages.data_stories.db.models import DataStory
            count += model.Session.query(DataStory).filter(
                DataStory.status.in_(['submitted', 'under_review'])
            ).count()
        except Exception:
            pass
        return count
    except Exception:
        return 0


def get_pending_stories_count():
    """Return pending data stories count for sysadmins."""
    try:
        import ckan.authz as authz
        if not tk.g.user or not authz.is_sysadmin(tk.g.user):
            return 0
        from ckanext.pages.data_stories.db.models import DataStory
        from ckan import model
        return model.Session.query(DataStory).filter(
            DataStory.status.in_(['submitted', 'under_review'])
        ).count()
    except Exception:
        return 0


def get_pending_oss_count():
    """Return pending open-source-software count for sysadmins."""
    try:
        import ckan.authz as authz
        if not tk.g.user or not authz.is_sysadmin(tk.g.user):
            return 0
        from ckanext.pages.db import Page
        from ckan import model
        return model.Session.query(Page).filter(
            Page.page_type == 'open-source-software',
            Page.private == True,
            Page.submission_status == 'pending',
            Page.group_id == None
        ).count()
    except Exception:
        return 0


def user_can_create_dataset(user_id):
    """Check if a user can create datasets in any organization."""
    try:
        if not user_id:
            return False
        from ckan import model
        user = model.User.get(user_id)
        if not user:
            return False
        orgs = tk.get_action('organization_list_for_user')(
            {'user': user.name, 'ignore_auth': True},
            {'permission': 'create_dataset'}
        )
        return len(orgs) > 0
    except Exception:
        return False


def get_ihp_organizations():
    """Get all organizations that are marked as IHP WINS organizations"""
    try:
        import ckan.model as model
        
        # Get all organizations
        orgs = model.Session.query(model.Group).filter(
            model.Group.type == 'organization',
            model.Group.state == 'active'
        ).order_by(model.Group.title, model.Group.name).all()
        
        # For now, return all organizations
        # In the future, you could add a custom field to mark IHP organizations
        return orgs
        
    except Exception as e:
        log.error("Error getting IHP organizations: %s", str(e))
        return []


def get_user_organization():
    """Get the organization associated with the current user"""
    try:
        if not tk.g.user:
            return None
            
        import ckan.model as model
        
        # Get user's organizations (as a member)
        user_obj = model.User.get(tk.g.user)
        if not user_obj:
            return None
            
        # Get organizations where user is a member (prioritize admin/editor roles)
        member_orgs = model.Session.query(model.Member).filter(
            model.Member.table_name == 'user',
            model.Member.table_id == user_obj.id,
            model.Member.group_id.in_(
                model.Session.query(model.Group.id).filter(
                    model.Group.type == 'organization',
                    model.Group.state == 'active'
                )
            ),
            model.Member.state == 'active'
        ).order_by(
            # Prioritize admin and editor roles
            model.Member.capacity.desc()
        ).all()
        
        if member_orgs:
            # Return the first organization (prioritized by role)
            org_id = member_orgs[0].group_id
            return model.Group.get(org_id)
            
        return None
        
    except Exception as e:
        log.error("Error getting user organization: %s", str(e))
        return None


class PagesPluginBase(p.SingletonPlugin, DefaultTranslation):
    p.implements(p.ITranslation, inherit=True)


class PagesPlugin(PagesPluginBase):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)
    p.implements(p.IActions, inherit=True)
    p.implements(p.IAuthFunctions, inherit=True)
    p.implements(p.IConfigurable, inherit=True)
    p.implements(p.IBlueprint)
    p.implements(p.IClick)

    def _data_stories_enabled(self):
        return tk.asbool(tk.config.get('ckanext.data_stories.enabled', False))

    def _featured_viewers_enabled(self):
        return tk.asbool(tk.config.get('ckanext.featured_viewers.enabled', False))

    def get_blueprint(self):
        blueprints = [blueprint.pages]
        # Register data stories blueprint only when enabled
        if self._data_stories_enabled() and DATA_STORIES_AVAILABLE and data_stories_blueprint:
            blueprints.append(data_stories_blueprint)
            log.info("Data stories blueprint registered")
        if self._featured_viewers_enabled() and FEATURED_VIEWERS_AVAILABLE and featured_viewers_blueprint:
            blueprints.append(featured_viewers_blueprint)
            log.info("Featured viewers blueprint registered")
        return blueprints

    # IClick
    def get_commands(self):
        import click
        from ckanext.pages.commands import get_commands as _get_cmds

        @click.group()
        def pages():
            """ckanext-pages management commands."""
            pass

        for cmd in _get_cmds():
            pages.add_command(cmd)

        return [pages]

    def update_config(self, config):
        self.organization_pages = tk.asbool(config.get('ckanext.pages.organization', False))
        self.group_pages = tk.asbool(config.get('ckanext.pages.group', False))
        self.data_stories_enabled = tk.asbool(config.get('ckanext.data_stories.enabled', False))
        self.featured_viewers_enabled = tk.asbool(config.get('ckanext.featured_viewers.enabled', False))

        tk.add_template_directory(config, 'theme/templates_main')
        if self.group_pages:
            tk.add_template_directory(config, 'theme/templates_group')
        if self.organization_pages:
            tk.add_template_directory(config, 'theme/templates_organization')

        tk.add_resource('assets', 'pages')

        tk.add_public_directory(config, 'assets/')
        tk.add_public_directory(config, 'assets/vendor/ckeditor/')
        tk.add_public_directory(config, 'assets/vendor/ckeditor/skins/moono-lisa')
        tk.add_public_directory(config, 'public/')
        tk.add_public_directory(config, 'theme/public')

    def configure(self, config):
        '''
        Called when the plugin is loaded.
        Initialize the database if needed.
        '''
        try:
            # Ensure the database table exists and is properly configured
            log.info("Initializing ckanext-pages database...")
            ensure_pages_table_exists()
            log.info("ckanext-pages database initialization completed")
        except Exception as e:
            log.error("Error initializing ckanext-pages database: %s", str(e))
            # Don't raise the error to avoid breaking the entire CKAN startup
            # The error handling in the other methods will handle cases where the table doesn't exist

        if self._data_stories_enabled() and DATA_STORIES_AVAILABLE and init_data_stories_tables:
            try:
                from ckan import model

                log.info("Initializing data stories database tables...")
                init_data_stories_tables(model.meta.engine)
                log.info("Data stories database initialization completed")
            except Exception as e:
                log.error("Error initializing data stories database: %s", str(e))

        if self._featured_viewers_enabled() and FEATURED_VIEWERS_AVAILABLE and init_featured_viewers_tables:
            try:
                from ckan import model

                log.info("Initializing featured viewers database tables...")
                init_featured_viewers_tables(model.meta.engine)
                log.info("Featured viewers database initialization completed")
            except Exception as e:
                log.error("Error initializing featured viewers database: %s", str(e))

    def get_helpers(self):
        helpers = {
            'build_nav_main': build_pages_nav_main,
            'render_content': render_content,
            'strip_html_tags': strip_html_tags,
            'has_meaningful_content': has_meaningful_content,
            'sanitize_html_content': sanitize_html_content,
            'gravatar_url': gravatar_url,
            'pages_get_wysiwyg_editor': get_wysiwyg_editor,
            'get_recent_blog_posts': get_recent_blog_posts,
            'get_recent_rapid_response_posts': get_recent_rapid_response_posts,
            'get_recent_water_news': get_recent_water_news,
            'get_recent_water_events': get_recent_water_events,
            'get_recent_water_publications': get_recent_water_publications,
            'get_recent_open_source_software': get_recent_open_source_software,
            'get_recent_ai_water_tools': get_recent_ai_water_tools,
            'json_loads': safe_json_loads,
            'get_event_status': get_event_status,
            'get_event_status_badge_class': get_event_status_badge_class,
            'count_unique_countries': count_unique_countries,
            'get_software_category_class': get_software_category_class,
            'count_software_by_category': count_software_by_category,
            'get_software_difficulty_class': get_software_difficulty_class,
            'get_ai_technique_class': get_ai_technique_class,
            'count_ai_tools_by_technique': count_ai_tools_by_technique,
            'count_ai_tools_by_application': count_ai_tools_by_application,
            'get_priority_sort_key': get_priority_sort_key,
            'get_severity_sort_key': get_severity_sort_key,
            'get_priority_class': get_priority_class,
            'get_severity_class': get_severity_class,
            'get_event_types': get_event_types,
            'get_event_type_by_id': get_event_type_by_id,
            'is_sysadmin': is_sysadmin,
            'get_ihp_organizations': get_ihp_organizations,
            'get_user_organization': get_user_organization,
            'get_pending_approval_count': get_pending_approval_count,
            'get_pending_stories_count': get_pending_stories_count,
            'get_pending_oss_count': get_pending_oss_count,
            'user_can_create_dataset': user_can_create_dataset,
            'clean_categories_string': clean_categories_string,
            'get_categories_list': get_categories_list,
        }

        # Always add data stories helpers if available
        if DATA_STORIES_AVAILABLE:
            helpers.update({
                # Terria helpers
                'parse_terria_share_link': parse_terria_share_link,
                'generate_terria_embed_url': generate_terria_embed_url,
                'validate_terria_init_json': validate_terria_init_json,
                'extract_terria_catalog_items': extract_terria_catalog_items,
                'get_terria_base_url': get_terria_base_url,
                'get_terria_iframe_html': get_terria_iframe_html,
                'is_terria_url': is_terria_url,
                # Formatting helpers
                'render_story_date': render_story_date,
                'render_story_abstract': render_story_abstract,
                'get_story_status_badge': get_story_status_badge,
                'get_section_icon': get_section_icon,
                'get_section_title': get_section_title,
                'markdown_to_html': markdown_to_html,
                'truncate_text': truncate_text,
                'pluralize': pluralize,
                'get_user_display_name': get_user_display_name,
                'format_file_size': format_file_size,
                'highlight_search_terms': highlight_search_terms,
            })

        # Add featured viewers helpers if available
        if FEATURED_VIEWERS_AVAILABLE:
            helpers.update({
                'get_viewer_categories': get_viewer_categories,
                'get_viewer_category_info': get_viewer_category_info,
                'get_viewer_category_title': get_viewer_category_title,
                'get_viewer_category_icon': get_viewer_category_icon,
                'get_viewer_category_color': get_viewer_category_color,
                'get_viewer_status_badge': get_viewer_status_badge,
                'format_viewer_view_count': format_viewer_view_count,
                'get_available_icons': get_available_icons,
                'fv_json_loads': fv_json_loads,
            })

        return helpers

    def get_actions(self):
        actions_dict = {
            'ckanext_pages_show': actions.pages_show,
            'ckanext_pages_update': actions.pages_update,
            'ckanext_pages_revision_restore': actions.pages_revision_restore,
            'ckanext_pages_delete': actions.pages_delete,
            'ckanext_pages_list': actions.pages_list,
            'ckanext_pages_upload': actions.pages_upload,
            # Water Family Upload
            'ckanext_water_family_upload': actions.water_family_upload,
            # Event Types Management
            'ckanext_event_types_list': actions.event_types_list,
            'ckanext_event_types_show': actions.event_types_show,
            'ckanext_event_types_create': actions.event_types_create,
            'ckanext_event_types_update': actions.event_types_update,
            'ckanext_event_types_delete': actions.event_types_delete,
        }
        if self.organization_pages:
            org_actions = {
                'ckanext_org_pages_show': actions.org_pages_show,
                'ckanext_org_pages_update': actions.org_pages_update,
                'ckanext_org_pages_delete': actions.org_pages_delete,
                'ckanext_org_pages_list': actions.org_pages_list,
            }
            actions_dict.update(org_actions)
        if self.group_pages:
            group_actions = {
                'ckanext_group_pages_show': actions.group_pages_show,
                'ckanext_group_pages_update': actions.group_pages_update,
                'ckanext_group_pages_delete': actions.group_pages_delete,
                'ckanext_group_pages_list': actions.group_pages_list,
            }
            actions_dict.update(group_actions)

        # Register data stories actions only when enabled
        if self._data_stories_enabled() and DATA_STORIES_AVAILABLE and ds_actions:
            data_stories_actions = {
                'data_story_create': ds_actions.data_story_create,
                'data_story_section_create': ds_actions.data_story_section_create,
                'data_story_show': ds_actions.data_story_show,
                'data_story_list': ds_actions.data_story_list,
                'data_story_section_show': ds_actions.data_story_section_show,
                'data_story_section_list': ds_actions.data_story_section_list,
                'data_story_update': ds_actions.data_story_update,
                'data_story_section_update': ds_actions.data_story_section_update,
                'data_story_reorder_sections': ds_actions.data_story_reorder_sections,
                'data_story_delete': ds_actions.data_story_delete,
                'data_story_section_delete': ds_actions.data_story_section_delete,
                'data_story_submit': ds_actions.data_story_submit,
                'data_story_review': ds_actions.data_story_review,
                'data_story_approve': ds_actions.data_story_approve,
                'data_story_request_changes': ds_actions.data_story_request_changes,
                'data_story_link_dataset': ds_actions.data_story_link_dataset,
                'data_story_unlink_dataset': ds_actions.data_story_unlink_dataset,
                'data_story_datasets': ds_actions.data_story_datasets,
                'data_story_comment_create': ds_actions.data_story_comment_create,
                'data_story_comment_list': ds_actions.data_story_comment_list,
                'data_story_comment_update': ds_actions.data_story_comment_update,
                'data_story_comment_delete': ds_actions.data_story_comment_delete,
                'data_story_comment_resolve': ds_actions.data_story_comment_resolve,
                'data_story_record_view': ds_actions.data_story_record_view,
                'data_story_stats': ds_actions.data_story_stats,
                'data_story_export': ds_actions.data_story_export,
                'data_story_import': ds_actions.data_story_import,
            }
            actions_dict.update(data_stories_actions)

        # Register featured viewers actions only when enabled
        if self._featured_viewers_enabled() and FEATURED_VIEWERS_AVAILABLE and fv_actions:
            featured_viewers_actions = {
                'featured_viewer_create': fv_actions.featured_viewer_create,
                'featured_viewer_show': fv_actions.featured_viewer_show,
                'featured_viewer_list': fv_actions.featured_viewer_list,
                'featured_viewer_update': fv_actions.featured_viewer_update,
                'featured_viewer_delete': fv_actions.featured_viewer_delete,
                'featured_viewer_record_view': fv_actions.featured_viewer_record_view,
                'featured_viewer_link_dataset': fv_actions.featured_viewer_link_dataset,
                'featured_viewer_unlink_dataset': fv_actions.featured_viewer_unlink_dataset,
                'map_room_create': fv_actions.map_room_create,
                'map_room_show': fv_actions.map_room_show,
                'map_room_list': fv_actions.map_room_list,
                'map_room_update': fv_actions.map_room_update,
                'map_room_delete': fv_actions.map_room_delete,
                'map_room_add_viewer': fv_actions.map_room_add_viewer,
                'map_room_remove_viewer': fv_actions.map_room_remove_viewer,
            }
            actions_dict.update(featured_viewers_actions)
        return actions_dict

    def get_auth_functions(self):
        auth_functions = {
            'ckanext_pages_show': auth.pages_show,
            'ckanext_pages_update': auth.pages_update,
            'ckanext_pages_delete': auth.pages_delete,
            'ckanext_pages_list': auth.pages_list,
            'ckanext_pages_upload': auth.pages_upload,
            'ckanext_org_pages_show': auth.org_pages_show,
            'ckanext_org_pages_update': auth.org_pages_update,
            'ckanext_org_pages_delete': auth.org_pages_delete,
            'ckanext_org_pages_list': auth.org_pages_list,
            'ckanext_group_pages_show': auth.group_pages_show,
            'ckanext_group_pages_update': auth.group_pages_update,
            'ckanext_group_pages_delete': auth.group_pages_delete,
            'ckanext_group_pages_list': auth.group_pages_list,
            # Water Family specific permissions
            'ckanext_water_family_upload': auth.water_family_upload,
            'ckanext_water_news_update': auth.water_news_update,
            'ckanext_water_news_delete': auth.water_news_delete,
            'ckanext_water_events_update': auth.water_events_update,
            'ckanext_water_events_delete': auth.water_events_delete,
            'ckanext_water_publications_update': auth.water_publications_update,
            'ckanext_water_publications_delete': auth.water_publications_delete,
            # Event Types Management
            'ckanext_event_types_list': auth.event_types_list,
            'ckanext_event_types_show': auth.event_types_show,
            'ckanext_event_types_create': auth.event_types_create,
            'ckanext_event_types_update': auth.event_types_update,
            'ckanext_event_types_delete': auth.event_types_delete,
        }

        # Register data stories auth only when enabled
        if self._data_stories_enabled() and DATA_STORIES_AVAILABLE and ds_auth:
            data_stories_auth = {
                'data_story_create': ds_auth.data_story_create,
                'data_story_show': ds_auth.data_story_show,
                'data_story_list': ds_auth.data_story_list,
                'data_story_update': ds_auth.data_story_update,
                'data_story_delete': ds_auth.data_story_delete,
                'data_story_section_create': ds_auth.data_story_section_create,
                'data_story_section_show': ds_auth.data_story_section_show,
                'data_story_section_list': ds_auth.data_story_section_list,
                'data_story_section_update': ds_auth.data_story_section_update,
                'data_story_section_delete': ds_auth.data_story_section_delete,
                'data_story_reorder_sections': ds_auth.data_story_reorder_sections,
                'data_story_submit': ds_auth.data_story_submit,
                'data_story_review': ds_auth.data_story_review,
                'data_story_approve': ds_auth.data_story_approve,
                'data_story_request_changes': ds_auth.data_story_request_changes,
                'data_story_link_dataset': ds_auth.data_story_link_dataset,
                'data_story_unlink_dataset': ds_auth.data_story_unlink_dataset,
                'data_story_datasets': ds_auth.data_story_datasets,
                'data_story_comment_create': ds_auth.data_story_comment_create,
                'data_story_comment_list': ds_auth.data_story_comment_list,
                'data_story_comment_update': ds_auth.data_story_comment_update,
                'data_story_comment_delete': ds_auth.data_story_comment_delete,
                'data_story_comment_resolve': ds_auth.data_story_comment_resolve,
                'data_story_stats': ds_auth.data_story_stats,
                'data_story_export': ds_auth.data_story_export,
                'data_story_import': ds_auth.data_story_import,
            }
            auth_functions.update(data_stories_auth)

        # Register featured viewers auth only when enabled
        if self._featured_viewers_enabled() and FEATURED_VIEWERS_AVAILABLE and fv_auth:
            featured_viewers_auth = {
                'featured_viewer_create': fv_auth.featured_viewer_create,
                'featured_viewer_show': fv_auth.featured_viewer_show,
                'featured_viewer_list': fv_auth.featured_viewer_list,
                'featured_viewer_update': fv_auth.featured_viewer_update,
                'featured_viewer_delete': fv_auth.featured_viewer_delete,
                'featured_viewer_record_view': fv_auth.featured_viewer_record_view,
                'featured_viewer_link_dataset': fv_auth.featured_viewer_link_dataset,
                'featured_viewer_unlink_dataset': fv_auth.featured_viewer_unlink_dataset,
                'map_room_create': fv_auth.map_room_create,
                'map_room_show': fv_auth.map_room_show,
                'map_room_list': fv_auth.map_room_list,
                'map_room_update': fv_auth.map_room_update,
                'map_room_delete': fv_auth.map_room_delete,
            }
            auth_functions.update(featured_viewers_auth)

        return auth_functions


class TextBoxView(p.SingletonPlugin):

    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IResourceView, inherit=True)

    def update_config(self, config):
        tk.add_resource('textbox/theme', 'textbox')
        tk.add_template_directory(config, 'textbox/templates')

    def info(self):
        ignore_missing = tk.get_validator('ignore_missing')
        schema = {
            'content': [ignore_missing],
        }

        return {'name': 'wysiwyg',
                'title': 'Free Text',
                'icon': 'pencil',
                'iframed': False,
                'schema': schema,
                }

    def can_view(self, data_dict):
        return True

    def view_template(self, context, data_dict):
        return 'textbox_view.html'

    def form_template(self, context, data_dict):
        return 'textbox_form.html'

    def setup_template_variables(self, context, data_dict):
        return
