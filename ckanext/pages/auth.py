import ckan.plugins as p

import ckan.authz as authz

from ckanext.pages import db


def sysadmin(context, data_dict):
    return {'success':  False}


@p.toolkit.auth_allow_anonymous_access
def anyone(context, data_dict):
    return {'success': True}


def group_admin(context, data_dict):
    return {
        'success': p.toolkit.check_access('group_update', context, data_dict)
    }


def org_admin(context, data_dict):
    return {
        'success': p.toolkit.check_access('group_update', context, data_dict)
    }


def page_group_admin(context, data_dict):
    group_id = data_dict.get('org_id')
    if not group_id:
        id = data_dict.get('id')
        page = data_dict.get('page') or db.Page.get(id=id)
        if page:
            group_id = page.group_id
    return group_admin(context, {'id': group_id})


def page_group_member(context, data_dict):
    """Check if user is a member (not necessarily admin) of the group"""
    group_id = data_dict.get('org_id')
    if not group_id:
        id = data_dict.get('id')
        page_name = data_dict.get('page')
        page = db.Page.get(id=id) if id else db.Page.get(name=page_name)
        if page:
            group_id = page.group_id
    
    if not group_id:
        return {'success': False}
    
    group = context['model'].Group.get(group_id)
    user = context.get('user')
    
    # Check if user has at least read permission (member)
    has_permission = authz.has_user_permission_for_group_or_org(
        group.id, user, 'read')
    
    return {'success': has_permission}


@p.toolkit.auth_allow_anonymous_access
def page_privacy(context, data_dict):
    org_id = data_dict.get('org_id')
    page = data_dict.get('page')
    out = db.Page.get(group_id=org_id, name=page)
    if out and out.private is False:
        return {'success':  True}
    # no org_id means it's a universal page
    if not org_id:
        if out and out.private:
            return {'success': False}
        return {'success': True}
    group = context['model'].Group.get(org_id)
    user = context['user']
    authorized = authz.has_user_permission_for_group_or_org(group.id,
                                                            user,
                                                            'read')
    if not authorized:
        return {'success': False,
                'msg': p.toolkit._(
                    'User %s not authorized to read this page') % user}
    else:
        return {'success': True}


pages_show = page_privacy
pages_update = sysadmin
pages_delete = sysadmin
pages_list = anyone
pages_upload = sysadmin
pages_submit_for_review = sysadmin  # Only sysadmins can submit for global pages
pages_approve = sysadmin  # Only sysadmins can approve global pages
pages_reject = sysadmin  # Only sysadmins can reject global pages
org_pages_show = page_privacy
org_pages_update = page_group_admin
org_pages_delete = page_group_admin
org_pages_list = anyone
org_pages_submit_for_review = page_group_member  # Any group member can submit
org_pages_approve = page_group_admin  # Only group admins can approve
org_pages_reject = page_group_admin  # Only group admins can reject
group_pages_show = page_privacy
group_pages_update = page_group_admin
group_pages_delete = page_group_admin
group_pages_list = anyone
group_pages_submit_for_review = page_group_member  # Any group member can submit
group_pages_approve = page_group_admin  # Only group admins can approve
group_pages_reject = page_group_admin  # Only group admins can reject
