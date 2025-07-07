import logging
import json
from html import escape as html_escape

from six.moves.urllib.parse import quote

from ckan.plugins import toolkit as tk

import ckan.plugins as p
from ckan.lib.helpers import build_nav_main as core_build_nav_main

from ckanext.pages import actions
from ckanext.pages import auth
from ckanext.pages import blueprint

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


log = logging.getLogger(__name__)


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
        # Try to repair the table if there's a database issue
        try:
            if "ckanext_pages" in str(e):
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
        for page in pages_list:
            type_ = 'blog' if page['page_type'] == 'blog' else 'pages'
            if page['page_type'] == 'rapid-response':
                type_ = 'rapid-response'
            elif page['page_type'] == 'open-source-software':
                type_ = 'open-source-software'
            name = quote(page['name'])
            title = html_escape(page['title'])
            link = tk.h.literal(u'<a href="{}/{}/{}">{}</a>'.format(root_path, type_, name, title))
            if page['name'] == page_name:
                li = tk.literal('<li class="active">') + link + tk.literal('</li>')
            else:
                li = tk.literal('<li>') + link + tk.literal('</li>')
            output = output + li
    except Exception as e:
        log.error("Error building pages navigation: %s", str(e))
        # Continue with basic navigation if there's an error processing pages

    return output


def render_content(content):
    allow_html = tk.asbool(tk.config.get('ckanext.pages.allow_html', False))
    return tk.h.render_markdown(content, allow_html=allow_html)


def get_wysiwyg_editor():
    return tk.config.get('ckanext.pages.editor', '')


def get_recent_blog_posts(number=5, exclude=None):
    blog_list = tk.get_action('ckanext_pages_list')(
        None, {'order_publish_date': True, 'private': False,
               'page_type': 'blog'}
    )
    new_list = []
    for blog in blog_list:
        if exclude and blog['name'] == exclude:
            continue
        new_list.append(blog)
        if len(new_list) == number:
            break

    return new_list


def get_recent_rapid_response_posts(number=5, exclude=None):
    rapid_response_list = tk.get_action('ckanext_pages_list')(
        None, {'order_publish_date': True, 'private': False,
               'page_type': 'rapid-response'}
    )
    new_list = []
    for rr_post in rapid_response_list:
        if exclude and rr_post['name'] == exclude:
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
            if exclude and news_post['name'] == exclude:
                continue
            new_list.append(news_post)
            if len(new_list) == number:
                break
        return new_list
    except:
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
            if exclude and event_post['name'] == exclude:
                continue
            new_list.append(event_post)
            if len(new_list) == number:
                break
        return new_list
    except:
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
            if exclude and pub_post['name'] == exclude:
                continue
            new_list.append(pub_post)
            if len(new_list) == number:
                break
        return new_list
    except:
        return []


def get_recent_open_source_software(number=5, exclude=None):
    """Get recent open source software entries"""
    try:
        software_list = tk.get_action('ckanext_pages_list')(
            None, {'order_publish_date': True, 'private': False,
                   'page_type': 'open-source-software'}
        )
        new_list = []
        for software_post in software_list:
            if exclude and software_post['name'] == exclude:
                continue
            new_list.append(software_post)
            if len(new_list) == number:
                break
        return new_list
    except:
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
    """Count unique countries from pages' key_info field"""
    countries = set()
    for page in pages:
        if page.get('key_info'):
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
        'critical': 4,
        'high': 3,
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
        'critical': 'severity-critical',
        'high': 'severity-high', 
        'moderate': 'severity-moderate',
        'low': 'severity-low'
    }
    return severity_classes.get(severity, '')


class PagesPluginBase(p.SingletonPlugin, DefaultTranslation):
    p.implements(p.ITranslation, inherit=True)


class PagesPlugin(PagesPluginBase):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)
    p.implements(p.IActions, inherit=True)
    p.implements(p.IAuthFunctions, inherit=True)
    p.implements(p.IConfigurable, inherit=True)
    p.implements(p.IBlueprint)

    def get_blueprint(self):
        return [blueprint.pages]

    def update_config(self, config):
        self.organization_pages = tk.asbool(config.get('ckanext.pages.organization', False))
        self.group_pages = tk.asbool(config.get('ckanext.pages.group', False))

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

    def get_helpers(self):
        return {
            'build_nav_main': build_pages_nav_main,
            'render_content': render_content,
            'pages_get_wysiwyg_editor': get_wysiwyg_editor,
            'get_recent_blog_posts': get_recent_blog_posts,
            'get_recent_rapid_response_posts': get_recent_rapid_response_posts,
            'get_recent_water_news': get_recent_water_news,
            'get_recent_water_events': get_recent_water_events,
            'get_recent_water_publications': get_recent_water_publications,
            'get_recent_open_source_software': get_recent_open_source_software,
            'json_loads': safe_json_loads,
            'get_event_status': get_event_status,
            'get_event_status_badge_class': get_event_status_badge_class,
            'count_unique_countries': count_unique_countries,
            'get_software_category_class': get_software_category_class,
            'count_software_by_category': count_software_by_category,
            'get_software_difficulty_class': get_software_difficulty_class,
            'get_priority_sort_key': get_priority_sort_key,
            'get_severity_sort_key': get_severity_sort_key,
            'get_priority_class': get_priority_class,
            'get_severity_class': get_severity_class,
        }

    def get_actions(self):
        actions_dict = {
            'ckanext_pages_show': actions.pages_show,
            'ckanext_pages_update': actions.pages_update,
            'ckanext_pages_revision_restore': actions.pages_revision_restore,
            'ckanext_pages_delete': actions.pages_delete,
            'ckanext_pages_list': actions.pages_list,
            'ckanext_pages_upload': actions.pages_upload,
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
        return actions_dict

    def get_auth_functions(self):
        return {
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
            'ckanext_water_news_update': auth.water_news_update,
            'ckanext_water_news_delete': auth.water_news_delete,
            'ckanext_water_events_update': auth.water_events_update,
            'ckanext_water_events_delete': auth.water_events_delete,
            'ckanext_water_publications_update': auth.water_publications_update,
            'ckanext_water_publications_delete': auth.water_publications_delete,
        }


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
