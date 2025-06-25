from flask import Blueprint

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
