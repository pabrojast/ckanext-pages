import ckan.plugins as p

import ckan.authz as authz

from ckanext.pages import db


def sysadmin(context, data_dict):
    '''Check if user is a sysadmin'''
    return {'success': authz.is_sysadmin(context.get('user', ''))}


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


def pages_update_with_org_check(context, data_dict):
    '''
    Allow pages update if user is:
    1. Sysadmin (can edit anything)
    2. Member of the organization that owns the page (for open-source-software)
    3. Author of the page (for their own submissions)
    '''
    # First check if user is sysadmin
    if sysadmin(context, data_dict)['success']:
        return {'success': True}
    
    user = context.get('user')
    if not user:
        return {'success': False}
    
    # Get the page to check its organization and author
    page_name = data_dict.get('page')
    if not page_name:
        return {'success': False}
        
    try:
        from ckanext.pages.db import Page
        page = Page.get(name=page_name)
        
        if not page:
            return {'success': False}
        
        # Check if user is the author of the page
        import ckan.model as model
        user_obj = model.User.get(user)
        if user_obj and page.user_id == user_obj.id:
            return {'success': True}
            
        # For open-source-software, check organization membership
        if page.page_type == 'open-source-software' and page.ihp_organization:
            # Check if user is a member of the page's organization
            member_query = model.Session.query(model.Member).filter(
                model.Member.table_name == 'user',
                model.Member.table_id == user_obj.id if user_obj else None,
                model.Member.group_id == page.ihp_organization,
                model.Member.state == 'active'
            )
            
            if member_query.first():
                return {'success': True}
                
    except Exception as e:
        # Log error but don't fail authentication
        import logging
        log = logging.getLogger(__name__)
        log.error("Error in pages_update_with_org_check: %s", str(e))
        
    return {'success': False}


def pages_upload_auth(context, data_dict):
    '''Allow sysadmins or authenticated users to upload assets'''
    if authz.is_sysadmin(context.get('user', '')):
        return {'success': True}

    return user_authenticated(context, data_dict)

pages_show = page_privacy
pages_update = pages_update_with_org_check
pages_delete = sysadmin
pages_list = anyone
pages_upload = pages_upload_auth
org_pages_show = page_privacy
org_pages_update = page_group_admin
org_pages_delete = page_group_admin
org_pages_list = anyone
group_pages_show = page_privacy
group_pages_update = page_group_admin
group_pages_delete = page_group_admin
group_pages_list = anyone


def user_authenticated(context, data_dict):
    '''Check if user is authenticated (logged in)'''
    user = context.get('user')
    if user:
        return {'success': True}
    else:
        return {'success': False, 'msg': p.toolkit._('You must be logged in')}


def water_family_upload(context, data_dict):
    '''Allow authenticated users to upload files for water family content they own or are creating'''
    import logging
    log = logging.getLogger(__name__)

    result = user_authenticated(context, data_dict)
    if not result.get('success'):
        return result

    # If uploading to an existing page, verify ownership or admin
    page_name = data_dict.get('page') or data_dict.get('name')
    if page_name:
        try:
            sysadmin_result = sysadmin(context, data_dict)
            if sysadmin_result.get('success'):
                return {'success': True}
        except (p.toolkit.NotAuthorized, Exception):
            pass

        try:
            page_obj = db.Page.get(name=page_name)
            if page_obj:
                if not page_obj.user_id:
                    # Orphaned content without owner - only admins can upload
                    return {'success': False, 'msg': p.toolkit._('Not authorized to upload to this content')}
                from ckan import model
                user_obj = model.User.get(context.get('user'))
                if user_obj and page_obj.user_id == user_obj.id:
                    return {'success': True}
                return {'success': False, 'msg': p.toolkit._('Not authorized to upload to this content')}
        except Exception as e:
            log.error("Error checking upload permission: %s", str(e))

    return {'success': True}


def water_content_create(context, data_dict):
    '''Allow authenticated users to create water family content (will be saved as private/pending)'''
    return user_authenticated(context, data_dict)


def water_content_edit(context, data_dict):
    '''Allow the author or admin to edit water family content'''
    import logging
    log = logging.getLogger(__name__)

    # Check if user is sysadmin
    try:
        result = sysadmin(context, data_dict)
        if result.get('success'):
            return result
    except p.toolkit.NotAuthorized:
        pass
    except Exception as e:
        log.error("Error checking sysadmin in water_content_edit: %s", str(e))

    # Check if user is the author of the content
    user = context.get('user')
    page = data_dict.get('page')

    if user and page:
        try:
            page_obj = db.Page.get(name=page)
            if page_obj and page_obj.user_id:
                from ckan import model
                user_obj = model.User.get(user)
                if user_obj and page_obj.user_id == user_obj.id:
                    return {'success': True}
        except Exception as e:
            log.error("Error checking page ownership in water_content_edit: %s", str(e))

    return {'success': False, 'msg': p.toolkit._('Not authorized to edit this content')}


# Water Family specific permissions
# Update uses water_content_edit: only author or sysadmin can edit
water_news_update = water_content_edit
water_news_delete = sysadmin  # Only admins can delete

water_events_update = water_content_edit
water_events_delete = sysadmin

water_publications_update = water_content_edit
water_publications_delete = sysadmin


# Event Types Management Authorization (sysadmin only)
@p.toolkit.auth_allow_anonymous_access
def event_types_show(context, data_dict):
    '''Anyone can view event types (used for dropdowns)'''
    return {'success': True}


@p.toolkit.auth_allow_anonymous_access  
def event_types_list(context, data_dict):
    '''Anyone can list event types (used for filters and dropdowns)'''
    return {'success': True}


def event_types_create(context, data_dict):
    '''Only sysadmin can create event types'''
    return sysadmin(context, data_dict)


def event_types_update(context, data_dict):
    '''Only sysadmin can update event types'''
    return sysadmin(context, data_dict)


def event_types_delete(context, data_dict):
    '''Only sysadmin can delete event types'''
    return sysadmin(context, data_dict)
