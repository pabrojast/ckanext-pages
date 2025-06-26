import six

import ckan.lib.navl.dictization_functions as dict_fns
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.logic as logic
import ckan.lib.helpers as helpers

from ckanext.pages.db import Page

config = tk.config
_ = tk._


def _parse_form_data(request):
    return logic.clean_dict(
        dict_fns.unflatten(
            logic.tuplize_dict(
                logic.parse_params(request.form)
            )
        )
    )


def pages_list_pages(page_type):
    data_dict = {'org_id': None, 'page_type': page_type}
    
    # Pass search and filter parameters from request
    if tk.request.args.get('q'):
        data_dict['q'] = tk.request.args.get('q')
    if tk.request.args.get('event_type'):
        data_dict['event_type'] = tk.request.args.get('event_type')
    if tk.request.args.get('order_by'):
        data_dict['order_by'] = tk.request.args.get('order_by')
    else:
        # Default ordering for different page types
        if page_type in ['blog', 'rapid-response', 'water-news', 'water-events', 'water-publications', 'open-source-software']:
            data_dict['order_by'] = 'recent'  # Default to most recent first
    
    # For water family content, only show public items to regular users
    if page_type in ['water-news', 'water-events', 'water-publications']:
        try:
            tk.check_access('sysadmin', {'user': tk.g.user})
            # Admin can see all items including private ones
        except tk.NotAuthorized:
            # Regular users only see public items
            data_dict['private'] = False
    
    tk.g.pages_dict = tk.get_action('ckanext_pages_list')(
        context={}, data_dict=data_dict
    )
    
    # Create custom pager URL to preserve search parameters
    def pager_url_with_params(page):
        params = []
        for key, value in tk.request.args.items():
            if key != 'page' and value:
                params.append(f"{key}={value}")
        params.append(f"page={page}")
        base_url = tk.request.path
        return f"{base_url}?{'&'.join(params)}"
    
    tk.c.page = helpers.Page(
        collection=tk.g.pages_dict,
        page=tk.request.args.get('page', 1),
        url=pager_url_with_params,
        items_per_page=21
    )

    if page_type == 'blog':
        return tk.render('ckanext_pages/blog_list.html')
    elif page_type == 'rapid-response':
        return tk.render('ckanext_pages/rapid-response_list.html')
    elif page_type == 'water-news':
        return tk.render('ckanext_pages/water-news_list.html')
    elif page_type == 'water-events':
        return tk.render('ckanext_pages/water-events_list.html')
    elif page_type == 'water-publications':
        return tk.render('ckanext_pages/water-publications_list.html')
    elif page_type == 'open-source-software':
        return tk.render('ckanext_pages/open-source-software_list.html')
    return tk.render('ckanext_pages/pages_list.html')


def pages_edit(page=None, data=None, errors=None, error_summary=None, page_type='pages'):

    page_dict = None
    if page:
        if page.startswith('/'):
            page = page[1:]
        page_dict = tk.get_action('ckanext_pages_show')(
            context={}, data_dict={'org_id': None, 'page': page}
        )
    if page_dict is None:
        page_dict = {}

    try:
        tk.check_access('ckanext_pages_update', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to create or edit a page'))

    if tk.request.method == 'POST' and not data:
        data = _parse_form_data(tk.request)

        page_dict.update(data)

        page_dict['org_id'] = None
        page_dict['page'] = page
        page_dict['page_type'] = 'page' if page_type == 'pages' else page_type

        # For water family content, set as private by default for non-admin users
        if page_type in ['water-news', 'water-events', 'water-publications'] and not page:
            try:
                tk.check_access('sysadmin', {'user': tk.g.user})
                # Admin can choose public/private
            except tk.NotAuthorized:
                # Regular users create as private (pending approval)
                page_dict['private'] = 'True'

        try:
            tk.get_action('ckanext_pages_update')(
                context={}, data_dict=page_dict
            )
            
            # Show different messages based on user type and page status
            if page_type in ['water-news', 'water-events', 'water-publications']:
                try:
                    tk.check_access('sysadmin', {'user': tk.g.user})
                    if page_dict.get('private') == 'True':
                        tk.h.flash_success(_('Content saved as draft'))
                    else:
                        tk.h.flash_success(_('Content published successfully'))
                except tk.NotAuthorized:
                    tk.h.flash_success(_('Content submitted for review. It will be published after admin approval.'))
            
        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            tk.h.flash_error(error_summary)
            return pages_edit(
                page, data, errors, error_summary, page_type=page_type)

        # Handle redirects for different page types
        endpoint = 'show' if page_type in ('pages', 'page') else '%s_show' % page_type
        if page_type == 'rapid-response':
            endpoint = 'rapid_response_show'
        elif page_type == 'water-news':
            endpoint = 'water_news_show'
        elif page_type == 'water-events':
            endpoint = 'water_events_show'
        elif page_type == 'water-publications':
            endpoint = 'water_publications_show'
        elif page_type == 'open-source-software':
            endpoint = 'open_source_software_show'
        
        return tk.redirect_to('pages.%s' % endpoint, page=page_dict['name'])

    if not data:
        data = page_dict

    errors = errors or {}
    error_summary = error_summary or {}

    form_snippet = config.get('ckanext.pages.form', 'ckanext_pages/base_form.html')

    vars = {'data': data, 'errors': errors,
            'error_summary': error_summary, 'page': page or '',
            'form_snippet': form_snippet}

    return tk.render(
        'ckanext_pages/%s_edit.html' % page_type, extra_vars=vars)


def _inject_views_into_page(_page):
    # this is a good proxy to a version of CKAN with views enabled.
    if not p.plugin_loaded('image_view'):
        return
    try:
        import lxml
        import lxml.html
    except ImportError:
        return

    try:
        root = lxml.html.fromstring(_page['content'])
    # Return if any errors are found while parsing the content
    except (lxml.etree.XMLSyntaxError,
            lxml.etree.ParserError):
        return

    for element in root.findall('.//iframe'):
        embed_element = element.attrib.pop('data-ckan-view-embed', None)
        if not embed_element:
            continue
        element.tag = 'div'
        error = None

        try:
            iframe_src = element.attrib.pop('src', '')
            width = element.attrib.pop('width', '80')
            if not width.endswith('%') and not width.endswith('px'):
                width = width + 'px'
            height = element.attrib.pop('height', '80')
            if not height.endswith('%') and not height.endswith('px'):
                height = height + 'px'
            align = element.attrib.pop('align', 'none')
            style = "width: %s; height: %s; float: %s; overflow: auto; vertical-align:middle; position:relative" \
                    % (width, height, align)
            element.attrib['style'] = style
            element.attrib['class'] = 'pages-embed'
            view = tk.get_action('resource_view_show')({}, {'id': iframe_src[-36:]})
            context = {}
            resource = tk.get_action('resource_show')(context, {'id': view['resource_id']})
            package_id = context['resource'].resource_group.package_id
            package = tk.get_action('package_show')(context, {'id': package_id})
        except tk.ObjectNotFound:
            error = _('ERROR: View not found {view_id}'.format(view_id=iframe_src))

        if error:
            resource_view_html = '<h4> %s </h4>' % error
        elif not helpers.resource_view_is_iframed(view):
            resource_view_html = helpers.rendered_resource_view(view, resource, package)
        else:
            src = helpers.url_for(
                'resource.view', id=package['name'], resource_id=resource['id'],
                view_id=view['id'], _external=True
            )
            message = _('Your browser does not support iframes.')
            resource_view_html = '<iframe src="{src}" frameborder="0" width="100%" height="100%" ' \
                                 'style="display:block"> <p>{message}</p> </iframe>'.format(src=src, message=message)

        view_element = lxml.html.fromstring(resource_view_html)
        element.append(view_element)

    new_content = six.ensure_text(lxml.html.tostring(root))
    if new_content.startswith('<div>') and new_content.endswith('</div>'):
        # lxml will add a <div> tag to text that starts with an HTML tag,
        # which will cause the rendering to fail
        new_content = new_content[5:-6]
    elif new_content.startswith('<p>') and new_content.endswith('</p>'):
        # lxml will add a <p> tag to plain text snippet, which will cause the
        # rendering to fail
        new_content = new_content[3:-4]
    _page['content'] = new_content


def pages_show(page=None, page_type='page'):
    tk.c.page_type = page_type
    if page.startswith('/'):
        page = page[1:]
    if not page:
        return pages_list_pages(page_type)
    _page = tk.get_action('ckanext_pages_show')(
        context={},
        data_dict={
            'org_id': None, 'page': page}
    )
    if _page is None:
        return pages_list_pages(page_type)
    tk.c.page = _page
    _inject_views_into_page(_page)

    return tk.render('ckanext_pages/%s.html' % page_type)


def pages_revisions(page, page_type='page'):
    try:
        tk.check_access('ckanext_pages_update', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to view this page'))

    _page = Page.get(name=page)

    if not _page:
        return tk.abort(404, _('Page Not Found'))
    
    tk.c.page_type = page_type
    tk.c.page = _page
    
    # Get revisions list for the template
    revisions = []
    if _page.revisions:
        revisions = list(_page.revisions.values())
        # Sort by timestamp descending (newest first)
        revisions.sort(key=lambda x: x.get('created', ''), reverse=True)
    
    return tk.render('ckanext_pages/%s_revisions.html' % page_type, extra_vars={
        'page': _page,
        'revisions': revisions
    })


def pages_revisions_preview(page, revision, page_type='page'):
    try:
        tk.check_access('ckanext_pages_update', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to view this page'))

    _page = Page.get(name=page)
    
    if not _page:
        return tk.abort(404, _('Page Not Found'))
        
    tk.c.page_type = page_type
    tk.c.page = _page
    try:
        return tk.render('ckanext_pages/%s_revisions_preview.html' % page_type, extra_vars={
            "page": _page,
            "revision": _page.revisions[revision]
        })
    except KeyError:
        return tk.abort(404, _('Revision not found'))


def pages_revision_restore(page, revision, page_type='page'):
    try:
        tk.check_access('ckanext_pages_update', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to view this page'))

    try:
        tk.get_action('ckanext_pages_revision_restore')(
            context={}, data_dict={"page": page, "revision": revision}
        )
        _page = Page.get(name=page)
        timestamp = helpers.render_datetime(_page.revisions[revision]["created"], with_hours=True)
        tk.h.flash_success(f"Content from revision created on {timestamp} set.")
    except TypeError:
        tk.h.flash_error(
            """Bad values, please make sure that provided values exist:
                Page name - '{name}', Revision version - '{rev}'""".format(name=page, rev=revision))

    endpoint = 'show' if page_type in ('pages', 'page') else '%s_show' % page_type
    if page_type == 'rapid-response':
        endpoint = 'rapid_response_show'
    elif page_type == 'open-source-software':
        endpoint = 'open_source_software_show'
    return tk.redirect_to('pages.%s' % endpoint, page=page)


def pages_delete(page, page_type='pages'):
    if page.startswith('/'):
        page = page[1:]
    if 'cancel' in tk.request.args:
        # Handle cancellation - redirect back to edit page for this page type
        if page_type == 'rapid-response':
            return tk.redirect_to('pages.rapid_response_edit', page=page)
        elif page_type == 'water-news':
            return tk.redirect_to('pages.water_news_edit', page=page)
        elif page_type == 'water-events':
            return tk.redirect_to('pages.water_events_edit', page=page)
        elif page_type == 'water-publications':
            return tk.redirect_to('pages.water_publications_edit', page=page)
        elif page_type == 'open-source-software':
            return tk.redirect_to('pages.open_source_software_edit', page=page)
        else:
            return tk.redirect_to('pages.edit', page=page)

    try:
        tk.check_access('ckanext_pages_delete', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to delete page'))

    # Get page info for display
    try:
        page_dict = tk.get_action('ckanext_pages_show')(
            context={}, data_dict={'org_id': None, 'page': page}
        )
        if not page_dict:
            return tk.abort(404, _('Page Not Found'))
    except tk.ObjectNotFound:
        return tk.abort(404, _('Page Not Found'))

    if tk.request.method == 'POST':
        try:
            tk.get_action('ckanext_pages_delete')({}, {'page': page})
            
            # Handle redirects for different page types after successful deletion
            endpoint = page_type + '_index'
            if page_type == 'rapid-response':
                endpoint = 'rapid_response_index'
                tk.h.flash_success(_('Emergency event deleted successfully'))
            elif page_type == 'water-news':
                endpoint = 'water_news_index'
                tk.h.flash_success(_('News article deleted successfully'))
            elif page_type == 'water-events':
                endpoint = 'water_events_index'
                tk.h.flash_success(_('Event deleted successfully'))
            elif page_type == 'water-publications':
                endpoint = 'water_publications_index'
                tk.h.flash_success(_('Publication deleted successfully'))
            elif page_type == 'open-source-software':
                endpoint = 'open_source_software_index'
                tk.h.flash_success(_('Software entry deleted successfully'))
            else:
                endpoint = 'pages_index'
                tk.h.flash_success(_('Page deleted successfully'))
            
            return tk.redirect_to('pages.%s' % endpoint)
        except tk.ObjectNotFound:
            return tk.abort(404, _('Page Not Found'))
        except Exception as e:
            tk.h.flash_error(_('Error deleting page: %s') % str(e))
            # Redirect back to edit page on error
            if page_type == 'rapid-response':
                return tk.redirect_to('pages.rapid_response_edit', page=page)
            else:
                return tk.redirect_to('pages.edit', page=page)
    else:
        # GET request - show confirmation page
        # Determine the correct delete URL for the form action
        if page_type == 'rapid-response':
            delete_url = tk.h.url_for('pages.rapid_response_delete', page=page)
        elif page_type == 'water-news':
            delete_url = tk.h.url_for('pages.water_news_delete', page=page)
        elif page_type == 'water-events':
            delete_url = tk.h.url_for('pages.water_events_delete', page=page)
        elif page_type == 'water-publications':
            delete_url = tk.h.url_for('pages.water_publications_delete', page=page)
        elif page_type == 'open-source-software':
            delete_url = tk.h.url_for('pages.open_source_software_delete', page=page)
        else:
            delete_url = tk.h.url_for('pages.delete', page=page)
        
        return tk.render('ckanext_pages/confirm_delete.html', extra_vars={
            'page': page,
            'page_dict': page_dict,
            'page_type': page_type,
            'delete_url': delete_url
        })


def pages_upload():
    if not tk.request.method == 'POST':
        tk.abort(409, _('Only Posting is availiable'))
    data_dict = logic.clean_dict(
        dict_fns.unflatten(
            logic.tuplize_dict(
                logic.parse_params(tk.request.files)
            )
        )
    )
    try:
        upload_info = tk.get_action('ckanext_pages_upload')(None, data_dict)
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to upload file %s') % id)

    return upload_info


def group_list_pages(id, group_type, group_dict=None):
    tk.c.pages_dict = tk.get_action('ckanext_pages_list')(
        context={}, data_dict={'org_id': tk.c.group_dict['id']}
    )
    return tk.render(
        'ckanext_pages/{}_page_list.html'.format(group_type),
        extra_vars={
            'group_type': group_type,
            'group_dict': group_dict
        })


def _template_setup_group(id, group_type):
    if not id:
        return
    context = {'for_view': True}
    action = 'organization_show' if group_type == 'organization' else 'group_show'
    try:
        tk.c.group_dict = tk.get_action(action)(context, {'id': id})
    except tk.ObjectNotFound:
        tk.abort(404, _('{} not found'.format(group_type.title())))
    except tk.NotAuthorized:
        tk.abort(401, _('Unauthorized to read {} {}'.format(group_type, id)))


def group_show(id, group_type, page=None):

    if page and page.startswith('/'):
        page = page[1:]

    _template_setup_group(id, group_type)

    context = {'for_view': True}

    action = 'organization_show' if group_type == 'organization' else 'group_show'

    group_dict = tk.get_action(action)(context, {'id': id})

    if not page:
        return group_list_pages(id, group_type, group_dict)

    _page = tk.get_action('ckanext_pages_show')(
        context={},
        data_dict={
            'org_id': tk.c.group_dict['id'], 'page': page}
    )
    if _page is None:
        return group_list_pages(id, group_type, group_dict)

    tk.c.page = _page

    return tk.render(
        'ckanext_pages/{}_page.html'.format(group_type),
        {
            'group_type': group_type,
            'group_dict': group_dict
        }
    )


def group_edit(id, group_type, page=None, data=None, errors=None, error_summary=None):

    _template_setup_group(id, group_type)

    page_dict = None
    if page:
        if page.startswith('/'):
            page = page[1:]
        page_dict = tk.get_action('ckanext_pages_show')(
            context={}, data_dict={'org_id': tk.c.group_dict['id'], 'page': page}
        )
    if page_dict is None:
        page_dict = {}

    if tk.request.method == 'POST' and not data:

        data = _parse_form_data(tk.request)

        page_dict.update(data)

        data = _parse_form_data(tk.request)
        page_dict['org_id'] = tk.c.group_dict['id']
        page_dict['page'] = page
        try:
            tk.get_action('ckanext_org_pages_update')(
                context={}, data_dict=page_dict
            )
        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return group_edit(id, group_type, page, data, errors, error_summary)

        endpoint = 'pages.{}_pages_show'.format(group_type)
        return tk.redirect_to(endpoint, id=id, page=page_dict['name'])

    if not data:
        data = page_dict

    errors = errors or {}
    error_summary = error_summary or {}

    context = {'for_view': True}

    action = 'organization_show' if group_type == 'organization' else 'group_show'
    group_dict = tk.get_action(action)(context, {'id': id})

    vars = {'data': data, 'errors': errors,
            'error_summary': error_summary, 'page': page,
            'group_type': group_type, 'group_dict': group_dict}

    return tk.render(
        'ckanext_pages/{}_page_edit.html'.format(group_type), extra_vars=vars)


def group_delete(id, group_type, page):

    _template_setup_group(id, group_type)

    if page.startswith('/'):
        page = page[1:]

    if 'cancel' in tk.request.args:
        return tk.redirect_to('pages.%s_edit' % group_type, id=tk.c.group_dict['name'], page=page)

    try:
        if tk.request.method == 'POST':
            action = 'ckanext_org_pages_delete' if group_type == 'organization' else 'ckanext_group_pages_delete'
            action = tk.get_action(action)
            action({}, {'org_id': tk.c.group_dict['id'], 'page': page})
            endpoint = 'pages.{}_pages_index'.format(group_type)
            return tk.redirect_to(endpoint, id=id)
        else:
            tk.abort(404, _('Page Not Found'))
    except tk.NotAuthorized:
        tk.abort(401, _('Unauthorized to delete page'))
    except tk.ObjectNotFound:
        tk.abort(404, _('{} not found'.format(group_type.title())))

    context = {'for_view': True}

    action = 'organization_show' if group_type == 'organization' else 'group_show'
    group_dict = tk.get_action(action)(context, {'id': id})

    return tk.render(
        'ckanext_pages/confirm_delete.html',
        {'page': page, 'group_type': group_type, 'group_dict': group_dict}
    )


# Water Family Community of Practice Functions
def water_family_main_page():
    """Main water family page showing all three content types"""
    
    # Get recent items from each category (only approved/public items)
    try:
        news_items = tk.get_action('ckanext_pages_list')(
            context={}, data_dict={
                'org_id': None, 
                'page_type': 'water-news',
                'order_publish_date': True,
                'private': False
            }
        )[:3]  # Latest 3 news items
    except:
        news_items = []
    
    try:
        events_items = tk.get_action('ckanext_pages_list')(
            context={}, data_dict={
                'org_id': None, 
                'page_type': 'water-events',
                'order_publish_date': True,
                'private': False
            }
        )[:3]  # Latest 3 events
    except:
        events_items = []
    
    try:
        publications_items = tk.get_action('ckanext_pages_list')(
            context={}, data_dict={
                'org_id': None, 
                'page_type': 'water-publications',
                'order_publish_date': True,
                'private': False
            }
        )[:3]  # Latest 3 publications
    except:
        publications_items = []
    
    return tk.render('ckanext_pages/water-family.html', extra_vars={
        'news_items': news_items,
        'events_items': events_items,
        'publications_items': publications_items
    })


def water_admin_dashboard():
    """Admin dashboard to approve/reject water family content"""
    
    try:
        tk.check_access('sysadmin', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to access admin dashboard'))
    
    # Get all pending items (private items that need approval)
    try:
        pending_news = tk.get_action('ckanext_pages_list')(
            context={}, data_dict={
                'org_id': None, 
                'page_type': 'water-news',
                'private': True,
                'order_publish_date': True
            }
        )
    except:
        pending_news = []
    
    try:
        pending_events = tk.get_action('ckanext_pages_list')(
            context={}, data_dict={
                'org_id': None, 
                'page_type': 'water-events',
                'private': True,
                'order_publish_date': True
            }
        )
    except:
        pending_events = []
    
    try:
        pending_publications = tk.get_action('ckanext_pages_list')(
            context={}, data_dict={
                'org_id': None, 
                'page_type': 'water-publications',
                'private': True,
                'order_publish_date': True
            }
        )
    except:
        pending_publications = []
    
    return tk.render('ckanext_pages/water-admin-dashboard.html', extra_vars={
        'pending_news': pending_news,
        'pending_events': pending_events,
        'pending_publications': pending_publications
    })


def water_admin_approve(page, page_type):
    """Approve a water family content item (make it public)"""
    
    try:
        tk.check_access('sysadmin', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to approve content'))
    
    if tk.request.method == 'POST':
        try:
            # Get the page first
            page_dict = tk.get_action('ckanext_pages_show')(
                context={}, data_dict={'org_id': None, 'page': page}
            )
            
            # Update to make it public
            page_dict['private'] = 'False'
            page_dict['page'] = page
            page_dict['page_type'] = page_type
            
            tk.get_action('ckanext_pages_update')(
                context={}, data_dict=page_dict
            )
            
            tk.h.flash_success(_('Content approved and published successfully'))
            
        except Exception as e:
            tk.h.flash_error(_('Error approving content: %s') % str(e))
    
    return tk.redirect_to('pages.water_admin_dashboard')


def water_admin_reject(page, page_type):
    """Reject a water family content item (delete it)"""
    
    try:
        tk.check_access('sysadmin', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to reject content'))
    
    if tk.request.method == 'POST':
        try:
            tk.get_action('ckanext_pages_delete')({}, {'page': page})
            tk.h.flash_success(_('Content rejected and deleted successfully'))
        except Exception as e:
            tk.h.flash_error(_('Error rejecting content: %s') % str(e))
    
    return tk.redirect_to('pages.water_admin_dashboard')
