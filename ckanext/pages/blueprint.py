from flask import Blueprint, redirect, request, url_for

import ckanext.pages.utils as utils

pages = Blueprint('pages', __name__)


def index():
    return utils.pages_list_pages('page')


def show(page):
    return utils.pages_show(page, page_type='page')


def pages_revisions(page):
    return utils.pages_revisions(page, page_type='page')


def pages_revisions_preview(page, revision):
    return utils.pages_revisions_preview(page, revision, page_type='page')


def pages_revision_restore(page, revision):
    return utils.pages_revision_restore(page, revision, page_type='page')


def pages_edit(page=None, data=None, errors=None, error_summary=None):
    return utils.pages_edit(page, data, errors, error_summary, 'page')


def pages_delete(page):
    return utils.pages_delete(page, page_type='pages')


def upload():
    return utils.pages_upload()


def blog_index():
    return utils.pages_list_pages('blog')


def blog_show(page):
    return utils.pages_show(page, page_type='blog')


def blog_edit(page=None, data=None, errors=None, error_summary=None):
    return utils.pages_edit(page, data, errors, error_summary, 'blog')


def blog_revisions(page):
    return utils.pages_revisions(page, page_type='blog')


def blog_revisions_preview(page, revision):
    return utils.pages_revisions_preview(page, revision, page_type='blog')


def blog_revision_restore(page, revision):
    return utils.pages_revision_restore(page, revision, page_type='blog')


def blog_delete(page):
    return utils.pages_delete(page, page_type='blog')


def rapid_response_index():
    return utils.pages_list_pages('rapid-response')


def rapid_response_show(page):
    return utils.pages_show(page, page_type='rapid-response')


def rapid_response_edit(page=None, data=None, errors=None, error_summary=None):
    return utils.pages_edit(page, data, errors, error_summary, 'rapid-response')


def rapid_response_revisions(page):
    return utils.pages_revisions(page, page_type='rapid-response')


def rapid_response_revisions_preview(page, revision):
    return utils.pages_revisions_preview(page, revision, page_type='rapid-response')


def rapid_response_revision_restore(page, revision):
    return utils.pages_revision_restore(page, revision, page_type='rapid-response')


def rapid_response_delete(page):
    return utils.pages_delete(page, page_type='rapid-response')


# Water Family Community of Practice endpoints
def water_news_index():
    return utils.pages_list_pages('water-news')


def water_news_show(page):
    return utils.pages_show(page, page_type='water-news')


def water_news_edit(page=None, data=None, errors=None, error_summary=None):
    return utils.pages_edit(page, data, errors, error_summary, 'water-news')


def water_news_revisions(page):
    return utils.pages_revisions(page, page_type='water-news')


def water_news_revisions_preview(page, revision):
    return utils.pages_revisions_preview(page, revision, page_type='water-news')


def water_news_revision_restore(page, revision):
    return utils.pages_revision_restore(page, revision, page_type='water-news')


def water_news_delete(page):
    return utils.pages_delete(page, page_type='water-news')


def water_events_index():
    return utils.pages_list_pages('water-events')


def water_events_show(page):
    return utils.pages_show(page, page_type='water-events')


def water_events_edit(page=None, data=None, errors=None, error_summary=None):
    return utils.pages_edit(page, data, errors, error_summary, 'water-events')


def water_events_revisions(page):
    return utils.pages_revisions(page, page_type='water-events')


def water_events_revisions_preview(page, revision):
    return utils.pages_revisions_preview(page, revision, page_type='water-events')


def water_events_revision_restore(page, revision):
    return utils.pages_revision_restore(page, revision, page_type='water-events')


def water_events_delete(page):
    return utils.pages_delete(page, page_type='water-events')


def water_publications_index():
    return utils.pages_list_pages('water-publications')


def water_publications_show(page):
    return utils.pages_show(page, page_type='water-publications')


def water_publications_edit(page=None, data=None, errors=None, error_summary=None):
    return utils.pages_edit(page, data, errors, error_summary, 'water-publications')


def water_publications_revisions(page):
    return utils.pages_revisions(page, page_type='water-publications')


def water_publications_revisions_preview(page, revision):
    return utils.pages_revisions_preview(page, revision, page_type='water-publications')


def water_publications_revision_restore(page, revision):
    return utils.pages_revision_restore(page, revision, page_type='water-publications')


def water_publications_delete(page):
    return utils.pages_delete(page, page_type='water-publications')


def water_family_index():
    return utils.water_family_main_page()


def water_admin_dashboard():
    return utils.water_admin_dashboard()


def water_admin_approve(page, page_type):
    return utils.water_admin_approve(page, page_type)


def water_admin_reject(page, page_type):
    return utils.water_admin_reject(page, page_type)


def water_family_upload():
    """Handle file uploads for water-family content types.

    This endpoint handles uploads for water-news, water-events, and water-publications
    with specific validation and metadata handling for each content type.
    """
    return utils.water_family_upload()


def open_source_admin_dashboard():
    return utils.open_source_admin_dashboard()


def open_source_admin_approve(page):
    return utils.open_source_admin_approve(page)


def open_source_admin_reject(page):
    return utils.open_source_admin_reject(page)


def open_source_admin_change_org(page):
    return utils.open_source_admin_change_org(page)


# AI Water Tools endpoints
def ai_water_tools_index():
    return utils.pages_list_pages('ai-water-tools')


def ai_water_tools_show(page):
    return utils.pages_show(page, page_type='ai-water-tools')


def ai_water_tools_edit(page=None, data=None, errors=None, error_summary=None):
    return utils.pages_edit(page, data, errors, error_summary, 'ai-water-tools')


def ai_water_tools_revisions(page):
    return utils.pages_revisions(page, page_type='ai-water-tools')


def ai_water_tools_revisions_preview(page, revision):
    return utils.pages_revisions_preview(page, revision, page_type='ai-water-tools')


def ai_water_tools_revision_restore(page, revision):
    return utils.pages_revision_restore(page, revision, page_type='ai-water-tools')


def ai_water_tools_delete(page):
    return utils.pages_delete(page, page_type='ai-water-tools')


def ai_water_admin_dashboard():
    return utils.ai_water_admin_dashboard()


def ai_water_admin_approve(page):
    return utils.ai_water_admin_approve(page)


def ai_water_admin_reject(page):
    return utils.ai_water_admin_reject(page)


def ai_water_admin_change_org(page):
    return utils.ai_water_admin_change_org(page)


# Open Source Software endpoints
def open_source_software_index():
    return utils.pages_list_pages('open-source-software')


def open_source_software_show(page):
    return utils.pages_show(page, page_type='open-source-software')


def open_source_software_edit(page=None, data=None, errors=None, error_summary=None):
    return utils.pages_edit(page, data, errors, error_summary, 'open-source-software')


def open_source_software_revisions(page):
    return utils.pages_revisions(page, page_type='open-source-software')


def open_source_software_revisions_preview(page, revision):
    return utils.pages_revisions_preview(page, revision, page_type='open-source-software')


def open_source_software_revision_restore(page, revision):
    return utils.pages_revision_restore(page, revision, page_type='open-source-software')


def open_source_software_delete(page):
    return utils.pages_delete(page, page_type='open-source-software')


# Redirect functions for legacy /open-source-software URLs to canonical /open-source-tools
def _redirect_with_query(target_url):
    if request.query_string:
        return redirect(f"{target_url}?{request.query_string.decode('utf-8')}", code=301)
    return redirect(target_url, code=301)


def redirect_open_source_software_index():
    return _redirect_with_query(url_for('pages.open_source_software_index'))


def redirect_open_source_software_show(page):
    return _redirect_with_query(url_for('pages.open_source_software_show', page=page))


def redirect_open_source_software_revisions(page):
    return _redirect_with_query(url_for('pages.open_source_software_revisions', page=page))


def redirect_open_source_software_revisions_preview(page, revision):
    return _redirect_with_query(url_for('pages.open_source_software_revisions_preview', page=page, revision=revision))


def redirect_open_source_software_revision_restore(page, revision):
    return _redirect_with_query(url_for('pages.open_source_software_revision_restore', page=page, revision=revision))


def redirect_open_source_software_edit(page=None):
    if page:
        return _redirect_with_query(url_for('pages.open_source_software_edit', page=page))
    return _redirect_with_query(url_for('pages.open_source_software_new'))


def redirect_open_source_software_delete(page):
    return _redirect_with_query(url_for('pages.open_source_software_delete', page=page))


def org_show(id, page=None):
    return utils.group_show(id, 'organization', page)


def org_delete(id, page):
    return utils.group_delete(id, 'organization', page)


def org_edit(id, page=None, data=None, errors=None, error_summary=None):
    return utils.group_edit(id, 'organization', page, data, errors, error_summary)


def group_show(id, page=None):
    return utils.group_show(id, 'group', page)


def group_delete(id, page):
    return utils.group_delete(id, 'group', page)


def group_edit(id, page=None, data=None, errors=None, error_summary=None):
    return utils.group_edit(id, 'group', page, data, errors, error_summary)


# Event Types Management Functions
def event_types_admin():
    """Admin page for managing event types"""
    return utils.event_types_admin()


def event_types_new(data=None, errors=None, error_summary=None):
    """Create new event type"""
    return utils.event_types_edit(None, data, errors, error_summary)


def event_types_edit(event_type_id=None, data=None, errors=None, error_summary=None):
    """Edit existing event type"""
    return utils.event_types_edit(event_type_id, data, errors, error_summary)


def event_types_delete(event_type_id):
    """Delete event type"""
    return utils.event_types_delete(event_type_id)


# --- CRIDA Case Study view functions ---

def crida_index():
    return utils.crida_main_page()


def crida_case_studies_index():
    return utils.pages_list_pages('crida-case-study')


def crida_case_study_show(page):
    return utils.pages_show(page, page_type='crida-case-study')


def crida_case_study_edit(page=None, data=None, errors=None, error_summary=None):
    return utils.pages_edit(page, data, errors, error_summary, 'crida-case-study')


def crida_case_study_revisions(page):
    return utils.pages_revisions(page, page_type='crida-case-study')


def crida_case_study_revisions_preview(page, revision):
    return utils.pages_revisions_preview(page, revision, page_type='crida-case-study')


def crida_case_study_revision_restore(page, revision):
    return utils.pages_revision_restore(page, revision, page_type='crida-case-study')


def crida_case_study_delete(page):
    return utils.pages_delete(page, page_type='crida-case-study')


def crida_admin_dashboard():
    return utils.crida_admin_dashboard()


def crida_admin_approve(page):
    return utils.crida_admin_approve(page)


def crida_admin_reject(page):
    return utils.crida_admin_reject(page)


def crida_geojson_api():
    return utils.crida_geojson_api()


pages.add_url_rule("/pages", view_func=index, endpoint="pages_index")
pages.add_url_rule("/pages/<page>", view_func=show)
pages.add_url_rule("/pages/<page>/revisions", view_func=pages_revisions)
pages.add_url_rule("/pages/<page>/revisions/<revision>", view_func=pages_revisions_preview)
pages.add_url_rule("/pages/<page>/revisions/<revision>/restore", view_func=pages_revision_restore, methods=['GET'])
pages.add_url_rule("/pages_edit", view_func=pages_edit, endpoint='new', methods=['GET', 'POST'])
pages.add_url_rule("/pages_edit/", view_func=pages_edit, endpoint='new', methods=['GET', 'POST'])
pages.add_url_rule("/pages_edit/<page>", view_func=pages_edit, endpoint='edit', methods=['GET', 'POST'])
pages.add_url_rule("/pages_delete/<page>", view_func=pages_delete, endpoint='delete', methods=['GET', 'POST'])

pages.add_url_rule("/pages_upload", view_func=upload, methods=['POST'])


pages.add_url_rule("/blog", view_func=blog_index)
pages.add_url_rule("/blog/<page>", view_func=blog_show)
pages.add_url_rule("/blog/<page>/revisions", view_func=blog_revisions)
pages.add_url_rule("/blog/<page>/revisions/<revision>", view_func=blog_revisions_preview)
pages.add_url_rule("/blog/<page>/revisions/<revision>/restore", view_func=blog_revision_restore, methods=['GET'])
pages.add_url_rule("/blog_edit", view_func=blog_edit, endpoint='blog_new', methods=['GET', 'POST'])
pages.add_url_rule("/blog_edit/", view_func=blog_edit, endpoint='blog_new', methods=['GET', 'POST'])
pages.add_url_rule("/blog_edit/<page>", view_func=blog_edit, endpoint='blog_edit', methods=['GET', 'POST'])
pages.add_url_rule("/blog_delete/<page>", view_func=blog_delete, endpoint='blog_delete', methods=['GET', 'POST'])


pages.add_url_rule("/rapid-response", view_func=rapid_response_index, endpoint='rapid_response_index')
pages.add_url_rule("/rapid-response/<page>", view_func=rapid_response_show, endpoint='rapid_response_show')
pages.add_url_rule("/rapid-response/<page>/revisions", view_func=rapid_response_revisions)
pages.add_url_rule("/rapid-response/<page>/revisions/<revision>", view_func=rapid_response_revisions_preview)
pages.add_url_rule("/rapid-response/<page>/revisions/<revision>/restore", view_func=rapid_response_revision_restore, methods=['GET'])
pages.add_url_rule("/rapid-response_edit", view_func=rapid_response_edit, endpoint='rapid_response_new', methods=['GET', 'POST'])
pages.add_url_rule("/rapid-response_edit/", view_func=rapid_response_edit, endpoint='rapid_response_new', methods=['GET', 'POST'])
pages.add_url_rule("/rapid-response_edit/<page>", view_func=rapid_response_edit, endpoint='rapid_response_edit', methods=['GET', 'POST'])
pages.add_url_rule("/rapid-response_delete/<page>", view_func=rapid_response_delete, endpoint='rapid_response_delete', methods=['GET', 'POST'])


pages.add_url_rule("/organization/pages/<id>", view_func=org_show, endpoint='organization_pages_index')
pages.add_url_rule("/organization/pages/<id>/<page>", view_func=org_show, endpoint='organization_pages_show')
pages.add_url_rule("/organization/pages_edit/<id>", view_func=org_edit,
                   endpoint='organization_pages_new', methods=['GET', 'POST'])
pages.add_url_rule("/organization/pages_edit/<id>/", view_func=org_edit,
                   endpoint='organization_pages_new', methods=['GET', 'POST'])
pages.add_url_rule("/organization/pages_edit/<id>/<page>", view_func=org_edit,
                   endpoint='organization_pages_edit', methods=['GET', 'POST'])
pages.add_url_rule("/organization/pages_delete/<id>/<page>", view_func=org_delete,
                   endpoint='organization_pages_delete', methods=['GET', 'POST'])

pages.add_url_rule("/group/pages/<id>", view_func=group_show, endpoint='group_pages_index')
pages.add_url_rule("/group/pages/<id>/<page>", view_func=group_show, endpoint='group_pages_show')
pages.add_url_rule("/group/pages_edit/<id>", view_func=group_edit, endpoint='group_pages_new', methods=['GET', 'POST'])
pages.add_url_rule("/group/pages_edit/<id>/", view_func=group_edit, endpoint='group_pages_new', methods=['GET', 'POST'])
pages.add_url_rule("/group/pages_edit/<id>/<page>", view_func=group_edit,
                   endpoint='group_pages_edit', methods=['GET', 'POST'])
pages.add_url_rule("/group/pages_delete/<id>/<page>", view_func=group_delete,
                   endpoint='group_pages_delete', methods=['GET', 'POST'])


# Water Family Community of Practice URLs
pages.add_url_rule("/water-family", view_func=water_family_index, endpoint='water_family_index')

# Water News URLs
pages.add_url_rule("/water-news", view_func=water_news_index, endpoint='water_news_index')
pages.add_url_rule("/water-news/<page>", view_func=water_news_show, endpoint='water_news_show')
pages.add_url_rule("/water-news/<page>/revisions", view_func=water_news_revisions, endpoint='water_news_revisions')
pages.add_url_rule("/water-news/<page>/revisions/<revision>", view_func=water_news_revisions_preview, endpoint='water_news_revisions_preview')
pages.add_url_rule("/water-news/<page>/revisions/<revision>/restore", view_func=water_news_revision_restore, endpoint='water_news_revision_restore', methods=['GET'])
pages.add_url_rule("/water-news_edit", view_func=water_news_edit, endpoint='water_news_new', methods=['GET', 'POST'])
pages.add_url_rule("/water-news_edit/", view_func=water_news_edit, endpoint='water_news_new', methods=['GET', 'POST'])
pages.add_url_rule("/water-news_edit/<page>", view_func=water_news_edit, endpoint='water_news_edit', methods=['GET', 'POST'])
pages.add_url_rule("/water-news_delete/<page>", view_func=water_news_delete, endpoint='water_news_delete', methods=['GET', 'POST'])

# Water Events URLs
pages.add_url_rule("/water-events", view_func=water_events_index, endpoint='water_events_index')
pages.add_url_rule("/water-events/<page>", view_func=water_events_show, endpoint='water_events_show')
pages.add_url_rule("/water-events/<page>/revisions", view_func=water_events_revisions, endpoint='water_events_revisions')
pages.add_url_rule("/water-events/<page>/revisions/<revision>", view_func=water_events_revisions_preview, endpoint='water_events_revisions_preview')
pages.add_url_rule("/water-events/<page>/revisions/<revision>/restore", view_func=water_events_revision_restore, endpoint='water_events_revision_restore', methods=['GET'])
pages.add_url_rule("/water-events_edit", view_func=water_events_edit, endpoint='water_events_new', methods=['GET', 'POST'])
pages.add_url_rule("/water-events_edit/", view_func=water_events_edit, endpoint='water_events_new', methods=['GET', 'POST'])
pages.add_url_rule("/water-events_edit/<page>", view_func=water_events_edit, endpoint='water_events_edit', methods=['GET', 'POST'])
pages.add_url_rule("/water-events_delete/<page>", view_func=water_events_delete, endpoint='water_events_delete', methods=['GET', 'POST'])

# Water Publications URLs
pages.add_url_rule("/water-publications", view_func=water_publications_index, endpoint='water_publications_index')
pages.add_url_rule("/water-publications/<page>", view_func=water_publications_show, endpoint='water_publications_show')
pages.add_url_rule("/water-publications/<page>/revisions", view_func=water_publications_revisions, endpoint='water_publications_revisions')
pages.add_url_rule("/water-publications/<page>/revisions/<revision>", view_func=water_publications_revisions_preview, endpoint='water_publications_revisions_preview')
pages.add_url_rule("/water-publications/<page>/revisions/<revision>/restore", view_func=water_publications_revision_restore, endpoint='water_publications_revision_restore', methods=['GET'])
pages.add_url_rule("/water-publications_edit", view_func=water_publications_edit, endpoint='water_publications_new', methods=['GET', 'POST'])
pages.add_url_rule("/water-publications_edit/", view_func=water_publications_edit, endpoint='water_publications_new', methods=['GET', 'POST'])
pages.add_url_rule("/water-publications_edit/<page>", view_func=water_publications_edit, endpoint='water_publications_edit', methods=['GET', 'POST'])
pages.add_url_rule("/water-publications_delete/<page>", view_func=water_publications_delete, endpoint='water_publications_delete', methods=['GET', 'POST'])

# Water Admin URLs
pages.add_url_rule("/water-admin", view_func=water_admin_dashboard, endpoint='water_admin_dashboard')
pages.add_url_rule("/water-admin/approve/<page_type>/<page>", view_func=water_admin_approve, endpoint='water_admin_approve', methods=['POST'])
pages.add_url_rule("/water-admin/reject/<page_type>/<page>", view_func=water_admin_reject, endpoint='water_admin_reject', methods=['POST'])

# Water Family Upload URL
pages.add_url_rule("/water_family_upload", view_func=water_family_upload, endpoint='water_family_upload', methods=['POST'])

# Open Source Software Admin URLs
pages.add_url_rule("/open-source-admin", view_func=open_source_admin_dashboard, endpoint='open_source_admin_dashboard')
pages.add_url_rule("/open-source-admin/approve/<page>", view_func=open_source_admin_approve, endpoint='open_source_admin_approve', methods=['POST'])
pages.add_url_rule("/open-source-admin/reject/<page>", view_func=open_source_admin_reject, endpoint='open_source_admin_reject', methods=['POST'])
pages.add_url_rule("/open-source-admin/change-org/<page>", view_func=open_source_admin_change_org, endpoint='open_source_admin_change_org', methods=['POST'])

# Open Source Tools URLs (primary routes)
pages.add_url_rule("/open-source-tools", view_func=open_source_software_index, endpoint='open_source_software_index')
pages.add_url_rule("/open-source-tools/<page>", view_func=open_source_software_show, endpoint='open_source_software_show')
pages.add_url_rule("/open-source-tools/<page>/revisions", view_func=open_source_software_revisions, endpoint='open_source_software_revisions')
pages.add_url_rule("/open-source-tools/<page>/revisions/<revision>", view_func=open_source_software_revisions_preview, endpoint='open_source_software_revisions_preview')
pages.add_url_rule("/open-source-tools/<page>/revisions/<revision>/restore", view_func=open_source_software_revision_restore, endpoint='open_source_software_revision_restore', methods=['GET'])
pages.add_url_rule("/open-source-tools_edit", view_func=open_source_software_edit, endpoint='open_source_software_new', methods=['GET', 'POST'])
pages.add_url_rule("/open-source-tools_edit/", view_func=open_source_software_edit, endpoint='open_source_software_new', methods=['GET', 'POST'])
pages.add_url_rule("/open-source-tools_edit/<page>", view_func=open_source_software_edit, endpoint='open_source_software_edit', methods=['GET', 'POST'])
pages.add_url_rule("/open-source-tools_delete/<page>", view_func=open_source_software_delete, endpoint='open_source_software_delete', methods=['GET', 'POST'])

# Open Source Software URLs (legacy with 301 redirects to canonical /open-source-tools)
pages.add_url_rule("/open-source-software", view_func=redirect_open_source_software_index)
pages.add_url_rule("/open-source-software/<page>", view_func=redirect_open_source_software_show)
pages.add_url_rule("/open-source-software/<page>/revisions", view_func=redirect_open_source_software_revisions)
pages.add_url_rule("/open-source-software/<page>/revisions/<revision>", view_func=redirect_open_source_software_revisions_preview)
pages.add_url_rule("/open-source-software/<page>/revisions/<revision>/restore", view_func=redirect_open_source_software_revision_restore, methods=['GET'])
pages.add_url_rule("/open-source-software_edit", view_func=redirect_open_source_software_edit, methods=['GET', 'POST'])
pages.add_url_rule("/open-source-software_edit/", view_func=redirect_open_source_software_edit, methods=['GET', 'POST'])
pages.add_url_rule("/open-source-software_edit/<page>", view_func=redirect_open_source_software_edit, methods=['GET', 'POST'])
pages.add_url_rule("/open-source-software_delete/<page>", view_func=redirect_open_source_software_delete, methods=['GET', 'POST'])

# AI Water Tools URLs
pages.add_url_rule("/ai-water-tools", view_func=ai_water_tools_index, endpoint='ai_water_tools_index')
pages.add_url_rule("/ai-water-tools/<page>", view_func=ai_water_tools_show, endpoint='ai_water_tools_show')
pages.add_url_rule("/ai-water-tools/<page>/revisions", view_func=ai_water_tools_revisions, endpoint='ai_water_tools_revisions')
pages.add_url_rule("/ai-water-tools/<page>/revisions/<revision>", view_func=ai_water_tools_revisions_preview, endpoint='ai_water_tools_revisions_preview')
pages.add_url_rule("/ai-water-tools/<page>/revisions/<revision>/restore", view_func=ai_water_tools_revision_restore, endpoint='ai_water_tools_revision_restore', methods=['GET'])
pages.add_url_rule("/ai-water-tools_edit", view_func=ai_water_tools_edit, endpoint='ai_water_tools_new', methods=['GET', 'POST'])
pages.add_url_rule("/ai-water-tools_edit/", view_func=ai_water_tools_edit, endpoint='ai_water_tools_new', methods=['GET', 'POST'])
pages.add_url_rule("/ai-water-tools_edit/<page>", view_func=ai_water_tools_edit, endpoint='ai_water_tools_edit', methods=['GET', 'POST'])
pages.add_url_rule("/ai-water-tools_delete/<page>", view_func=ai_water_tools_delete, endpoint='ai_water_tools_delete', methods=['GET', 'POST'])

# AI Water Tools Admin URLs
pages.add_url_rule("/ai-water-admin", view_func=ai_water_admin_dashboard, endpoint='ai_water_admin_dashboard')
pages.add_url_rule("/ai-water-admin/approve/<page>", view_func=ai_water_admin_approve, endpoint='ai_water_admin_approve', methods=['POST'])
pages.add_url_rule("/ai-water-admin/reject/<page>", view_func=ai_water_admin_reject, endpoint='ai_water_admin_reject', methods=['POST'])
pages.add_url_rule("/ai-water-admin/change-org/<page>", view_func=ai_water_admin_change_org, endpoint='ai_water_admin_change_org', methods=['POST'])

# Event Types Administration URLs (Sysadmin only)
pages.add_url_rule("/admin/event-types", view_func=event_types_admin, endpoint='event_types_admin')
pages.add_url_rule("/admin/event-types/new", view_func=event_types_new, endpoint='event_types_new', methods=['GET', 'POST'])
pages.add_url_rule("/admin/event-types/edit/<event_type_id>", view_func=event_types_edit, endpoint='event_types_edit', methods=['GET', 'POST'])
pages.add_url_rule("/admin/event-types/delete/<event_type_id>", view_func=event_types_delete, endpoint='event_types_delete', methods=['GET', 'POST'])

# CRIDA Case Study routes
pages.add_url_rule("/crida", view_func=crida_index, endpoint='crida_index')
pages.add_url_rule("/crida/case-studies", view_func=crida_case_studies_index, endpoint='crida_case_studies_index')
pages.add_url_rule("/crida/case-studies/<page>", view_func=crida_case_study_show, endpoint='crida_case_study_show')
pages.add_url_rule("/crida/case-studies/<page>/revisions", view_func=crida_case_study_revisions, endpoint='crida_case_study_revisions')
pages.add_url_rule("/crida/case-studies/<page>/revisions/<revision>", view_func=crida_case_study_revisions_preview, endpoint='crida_case_study_revisions_preview')
pages.add_url_rule("/crida/case-studies/<page>/revisions/<revision>/restore", view_func=crida_case_study_revision_restore, endpoint='crida_case_study_revision_restore', methods=['GET'])
pages.add_url_rule("/crida/case-studies_edit", view_func=crida_case_study_edit, endpoint='crida_case_study_new', methods=['GET', 'POST'])
pages.add_url_rule("/crida/case-studies_edit/", view_func=crida_case_study_edit, endpoint='crida_case_study_new_slash', methods=['GET', 'POST'])
pages.add_url_rule("/crida/case-studies_edit/<page>", view_func=crida_case_study_edit, endpoint='crida_case_study_edit', methods=['GET', 'POST'])
pages.add_url_rule("/crida/case-studies_delete/<page>", view_func=crida_case_study_delete, endpoint='crida_case_study_delete', methods=['GET', 'POST'])
pages.add_url_rule("/crida/admin", view_func=crida_admin_dashboard, endpoint='crida_admin_dashboard')
pages.add_url_rule("/crida/admin/approve/<page>", view_func=crida_admin_approve, endpoint='crida_admin_approve', methods=['POST'])
pages.add_url_rule("/crida/admin/reject/<page>", view_func=crida_admin_reject, endpoint='crida_admin_reject', methods=['POST'])
pages.add_url_rule("/crida/api/geojson", view_func=crida_geojson_api, endpoint='crida_geojson_api')
