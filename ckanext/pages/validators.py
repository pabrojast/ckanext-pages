import ckan.plugins as p
import ckan.lib.navl.dictization_functions as df
from ckanext.pages import db


def page_name_validator(key, data, errors, context):
    session = context['session']
    page = context.get('page')
    group_id = context.get('group_id')
    if page and page == data[key]:
        return

    query = session.query(db.Page.name).filter_by(name=data[key], group_id=group_id)
    result = query.first()
    if result:
        errors[key].append(
            p.toolkit._('Page name already exists in database'))


def not_empty_if_blog(key, data, errors, context):
    value = data.get(key)
    if data.get(('page_type',), '') == 'blog':
        if value is df.missing or not value:
            errors[key].append('Publish Date Must be supplied')


def status_validator(key, data, errors, context):
    """Validate workflow status values"""
    valid_statuses = ['draft', 'pending', 'approved']
    value = data.get(key)
    
    if value and value not in valid_statuses:
        errors[key].append(
            p.toolkit._('Status must be one of: draft, pending, approved'))
    
    # If no status provided, set default to draft
    if not value or value is df.missing:
        data[key] = 'draft'
