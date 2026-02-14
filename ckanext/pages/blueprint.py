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


def pages_submit(page):
    return utils.pages_workflow_action(page, 'submit_for_review', 'pages')


def pages_approve(page):
    return utils.pages_workflow_action(page, 'approve', 'pages')


def pages_reject(page):
    return utils.pages_workflow_action(page, 'reject', 'pages')


def blog_submit(page):
    return utils.pages_workflow_action(page, 'submit_for_review', 'blog')


def blog_approve(page):
    return utils.pages_workflow_action(page, 'approve', 'blog')


def blog_reject(page):
    return utils.pages_workflow_action(page, 'reject', 'blog')


def org_submit(id, page):
    return utils.pages_workflow_action(page, 'submit_for_review', 'organization', id)


def org_approve(id, page):
    return utils.pages_workflow_action(page, 'approve', 'organization', id)


def org_reject(id, page):
    return utils.pages_workflow_action(page, 'reject', 'organization', id)


def group_submit(id, page):
    return utils.pages_workflow_action(page, 'submit_for_review', 'group', id)


def group_approve(id, page):
    return utils.pages_workflow_action(page, 'approve', 'group', id)


def group_reject(id, page):
    return utils.pages_workflow_action(page, 'reject', 'group', id)


pages.add_url_rule("/pages", view_func=index, endpoint="pages_index")
pages.add_url_rule("/pages/<page>", view_func=show)
pages.add_url_rule("/pages/<page>/revisions", view_func=pages_revisions)
pages.add_url_rule("/pages/<page>/revisions/<revision>", view_func=pages_revisions_preview)
pages.add_url_rule("/pages/<page>/revisions/<revision>/restore", view_func=pages_revision_restore, methods=['GET'])
pages.add_url_rule("/pages_edit", view_func=pages_edit, endpoint='new', methods=['GET', 'POST'])
pages.add_url_rule("/pages_edit/", view_func=pages_edit, endpoint='new', methods=['GET', 'POST'])
pages.add_url_rule("/pages_edit/<page>", view_func=pages_edit, endpoint='edit', methods=['GET', 'POST'])
pages.add_url_rule("/pages_delete/<page>", view_func=pages_delete, endpoint='delete', methods=['GET', 'POST'])

# Workflow action routes for pages
pages.add_url_rule("/pages_submit/<page>", view_func=pages_submit, endpoint='submit', methods=['POST'])
pages.add_url_rule("/pages_approve/<page>", view_func=pages_approve, endpoint='approve', methods=['POST'])
pages.add_url_rule("/pages_reject/<page>", view_func=pages_reject, endpoint='reject', methods=['POST'])

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

# Workflow action routes for blog
pages.add_url_rule("/blog_submit/<page>", view_func=blog_submit, endpoint='blog_submit', methods=['POST'])
pages.add_url_rule("/blog_approve/<page>", view_func=blog_approve, endpoint='blog_approve', methods=['POST'])
pages.add_url_rule("/blog_reject/<page>", view_func=blog_reject, endpoint='blog_reject', methods=['POST'])


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

# Workflow action routes for organization pages
pages.add_url_rule("/organization/pages_submit/<id>/<page>", view_func=org_submit,
                   endpoint='organization_pages_submit', methods=['POST'])
pages.add_url_rule("/organization/pages_approve/<id>/<page>", view_func=org_approve,
                   endpoint='organization_pages_approve', methods=['POST'])
pages.add_url_rule("/organization/pages_reject/<id>/<page>", view_func=org_reject,
                   endpoint='organization_pages_reject', methods=['POST'])

pages.add_url_rule("/group/pages/<id>", view_func=group_show, endpoint='group_pages_index')
pages.add_url_rule("/group/pages/<id>/<page>", view_func=group_show, endpoint='group_pages_show')
pages.add_url_rule("/group/pages_edit/<id>", view_func=group_edit, endpoint='group_pages_new', methods=['GET', 'POST'])
pages.add_url_rule("/group/pages_edit/<id>/", view_func=group_edit, endpoint='group_pages_new', methods=['GET', 'POST'])
pages.add_url_rule("/group/pages_edit/<id>/<page>", view_func=group_edit,
                   endpoint='group_pages_edit', methods=['GET', 'POST'])
pages.add_url_rule("/group/pages_delete/<id>/<page>", view_func=group_delete,
                   endpoint='group_pages_delete', methods=['GET', 'POST'])

# Workflow action routes for group pages
pages.add_url_rule("/group/pages_submit/<id>/<page>", view_func=group_submit,
                   endpoint='group_pages_submit', methods=['POST'])
pages.add_url_rule("/group/pages_approve/<id>/<page>", view_func=group_approve,
                   endpoint='group_pages_approve', methods=['POST'])
pages.add_url_rule("/group/pages_reject/<id>/<page>", view_func=group_reject,
                   endpoint='group_pages_reject', methods=['POST'])
