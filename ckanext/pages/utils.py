import datetime
import logging
import six
from types import SimpleNamespace

import ckan.lib.navl.dictization_functions as dict_fns
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.logic as logic
import ckan.lib.helpers as helpers
from ckan import model

from ckanext.pages.db import Page


def _get_open_source_admin_organizations():
    """Return organization options and lookup mapping for admin dashboard."""
    try:
        org_query = model.Session.query(model.Group).filter(
            model.Group.type == 'organization',
            model.Group.state == 'active'
        )
        organizations = org_query.all()
    except Exception:
        organizations = []

    options = []
    lookup = {}

    for org in organizations:
        org_id = getattr(org, 'id', None) or getattr(org, 'name', None)
        if not org_id:
            continue

        label = getattr(org, 'title', None) or getattr(org, 'display_name', None) or getattr(org, 'name', None)
        if not label:
            label = org_id

        org_id_text = six.text_type(org_id)
        label_text = six.text_type(label)

        options.append(SimpleNamespace(id=org_id_text, label=label_text))
        lookup[org_id_text] = label_text

    options.sort(key=lambda item: item.label.lower())

    return options, lookup


def _build_user_display_lookup(pages):
    """Create a lookup mapping user ids to human-readable names."""
    lookup = {}

    user_ids = {
        six.text_type(getattr(page, 'user_id'))
        for page in pages
        if getattr(page, 'user_id', None)
    }

    if not user_ids:
        return lookup

    try:
        users = model.Session.query(model.User).filter(
            model.User.id.in_(user_ids)
        ).all()
    except Exception:
        users = []

    for user in users:
        display = user.fullname or getattr(user, 'display_name', None) or user.name or user.id
        user_id_text = six.text_type(user.id)
        lookup[user_id_text] = six.text_type(display)

    return lookup

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
    
    # Additional filters for rapid-response pages
    if page_type == 'rapid-response':
        filter_params = ['country', 'activity_status', 'severity', 'event_status']
        for param in filter_params:
            if tk.request.args.get(param):
                data_dict[param] = tk.request.args.get(param)
    
    # Additional filters for open-source-software
    if page_type == 'open-source-software':
        # Handle multiple values for category and language filters
        multi_value_params = ['category', 'language']
        single_value_params = ['access_type', 'license', 'platform', 'attribution']
        
        for param in multi_value_params:
            param_values = tk.request.args.getlist(param)
            if param_values and any(v.strip() for v in param_values):
                data_dict[param] = [v for v in param_values if v.strip()]
        
        for param in single_value_params:
            if tk.request.args.get(param):
                data_dict[param] = tk.request.args.get(param)
    
    # Filter content based on user permissions
    try:
        tk.check_access('sysadmin', {'user': tk.g.user})
        # Admin can see all items including private ones and pending submissions
    except tk.NotAuthorized:
        # Regular users only see public items
        data_dict['private'] = False
        # For water family content and open-source-software, also consider submission status
        if page_type in ['water-news', 'water-events', 'water-publications', 'open-source-software']:
            # Only show approved content to regular users
            if page_type == 'open-source-software':
                data_dict['submission_status'] = 'approved'
    
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

    def _slugify_title(value):
        import re
        value = (value or '').strip().lower()
        value = re.sub(r'[^a-z0-9\s_-]+', '', value)
        value = re.sub(r'\s+', '-', value)
        value = re.sub(r'-{2,}', '-', value)
        return value.strip('-')

    page_dict = None
    if page:
        if page.startswith('/'):
            page = page[1:]
        page_dict = tk.get_action('ckanext_pages_show')(
            context={}, data_dict={'org_id': None, 'page': page}
        )
    if page_dict is None:
        page_dict = {}

    # Check permissions based on page type
    permission_needed = 'ckanext_pages_update'
    if page_type in ['water-news', 'water-events', 'water-publications']:
        permission_needed = f'ckanext_{page_type.replace("-", "_")}_update'
    
    try:
        tk.check_access(permission_needed, {'user': tk.g.user, 'page': page})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to create or edit a page'))

    if tk.request.method == 'POST' and not data:
        data = _parse_form_data(tk.request)
        submission_action = data.pop('submission_action', None) or tk.request.form.get('submission_action')
        page_dict.update(data)

        page_dict['org_id'] = None
        page_dict['page'] = page
        page_dict['page_type'] = 'page' if page_type == 'pages' else page_type

        # Re-add submission_action to page_dict so it reaches actions.py
        if submission_action:
            page_dict['submission_action'] = submission_action

        if not page_dict.get('name') and page_dict.get('title'):
            generated_name = _slugify_title(page_dict['title'])
            if generated_name:
                page_dict['name'] = generated_name

        # For water family content, set as private by default for non-admin users
        if page_type in ['water-news', 'water-events', 'water-publications'] and not page:
            try:
                tk.check_access('sysadmin', {'user': tk.g.user})
                # Admin can choose public/private
            except tk.NotAuthorized:
                # Regular users create as private (pending approval)
                page_dict['private'] = 'True'

        if page_type in ['water-news', 'water-events', 'water-publications']:
            # Ensure we store the organization id of the submitter when missing
            if not page_dict.get('ihp_organization'):
                try:
                    orgs = tk.get_action('organization_list_for_user')(
                        {'user': tk.g.user} if tk.g.user else {},
                        {'permission': 'create_dataset'}
                    )
                    if orgs:
                        primary_org = orgs[0]
                        page_dict['ihp_organization'] = primary_org.get('id') or primary_org.get('name')
                        if not page_dict.get('organization'):
                            page_dict['organization'] = primary_org.get('title') or primary_org.get('display_name') or primary_org.get('name')
                except Exception:
                    pass

            if submission_action == 'draft':
                page_dict['private'] = 'True'
                page_dict['submission_status'] = 'draft'
            elif submission_action == 'submit':
                page_dict.setdefault('private', 'True')
                page_dict['submission_status'] = 'pending'
            elif submission_action == 'publish':
                page_dict['private'] = 'False'
                page_dict['submission_status'] = 'published'

        # Remove helper fields that should not hit the action layer
        if 'submission_action' in page_dict and page_type != 'open-source-software':
            page_dict.pop('submission_action')

        try:
            tk.get_action('ckanext_pages_update')(
                context={}, data_dict=page_dict
            )

            # If this is a Water Publication creation and dataset creation info was provided,
            # create a CKAN dataset of type 'documents' with an optional resource
            if page_type == 'water-publications' and not page:
                try:
                    _maybe_create_documents_dataset(page_dict)
                except Exception as e:
                    # Do not block page creation on dataset errors; show a warning
                    tk.h.flash_error(_('Dataset creation warning: %s') % str(e))

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

    if page_type in ['water-news', 'water-events', 'water-publications']:
        if not data.get('ihp_organization'):
            try:
                orgs = tk.get_action('organization_list_for_user')(
                    {'user': tk.g.user} if tk.g.user else {},
                    {'permission': 'create_dataset'}
                )
                if orgs:
                    primary_org = orgs[0]
                    data['ihp_organization'] = primary_org.get('id') or primary_org.get('name')
                    data.setdefault('organization', primary_org.get('title') or primary_org.get('display_name') or primary_org.get('name'))
            except Exception:
                pass

    errors = errors or {}
    error_summary = error_summary or {}

    form_snippet = config.get('ckanext.pages.form', 'ckanext_pages/base_form.html')

    # Create a simple object that allows attribute access for template compatibility
    class PageObject:
        def __init__(self, data_dict):
            for key, value in data_dict.items():
                setattr(self, key, value)
    
    # Pass both the page object (if editing) and page name for the template
    page_object = None
    if page and page_dict:
        page_object = PageObject(page_dict)
    
    vars = {'data': data, 'errors': errors,
            'error_summary': error_summary, 'page': page_object,
            'page_name': page or '',
            'form_snippet': form_snippet}

    return tk.render(
        'ckanext_pages/%s_edit.html' % page_type, extra_vars=vars)


def _maybe_create_documents_dataset(form_data):
    """Create a CKAN dataset of type 'documents' from publication form data
    if the user provided upload/link metadata. Runs only on create (not edit).

    Expected form fields (all optional, best-effort):
      - create_documents_dataset: 'on'|'true' (checkbox)
      - dataset_title: str
      - dataset_description: str
      - dataset_language: str (GeoDCAT language URI). Defaults to ENG
      - dataset_visibility: 'public'|'private'
      - organization_id: CKAN org id
      - contact_name, contact_email: if missing, auto from current user
      - graphic_overview: url
      - creation_date: YYYY-MM-DD (resource.created)
      - country_groups: JSON array of group names
      - initiative_groups: JSON array of group names
      - document_format: short code like PDF, DOCX, PNG (resource.format)
      - document_mimetype: optional mimetype (resource.mimetype)
      - dataset_url: external URL for resource (alternative to upload)
      - dataset_resource_title: optional resource title
    And request.files may include:
      - dataset_upload: uploaded file for the resource
    """
    req = tk.request

    create_flag = (form_data.get('create_documents_dataset') in ('on', 'true', '1', True))
    has_file = bool(getattr(req, 'files', None) and req.files.get('dataset_upload'))
    has_link = bool(form_data.get('dataset_url'))
    if not (create_flag or has_file or has_link):
        return  # nothing to do

    # Build package (dataset) payload
    dataset_title = (form_data.get('dataset_title') or form_data.get('title') or '').strip()
    if not dataset_title and has_file:
        # Try to use file name without extension
        filename = req.files.get('dataset_upload').filename or ''
        dataset_title = filename.rsplit('.', 1)[0]
    if not dataset_title and has_link:
        dataset_title = form_data.get('dataset_url').rstrip('/').rsplit('/', 1)[-1]
        dataset_title = dataset_title.rsplit('.', 1)[0]
    if not dataset_title:
        raise Exception(_('Dataset title is required to create the document'))

    def _slugify(text):
        import re
        value = (text or '').lower()
        value = re.sub(r'[^a-z0-9\-\_\s]+', '', value)
        value = re.sub(r'\s+', '-', value).strip('-')
        return value or 'document'

    base_name = 'document-' + _slugify(dataset_title)

    # Language default
    language = form_data.get('dataset_language') or \
        'http://publications.europa.eu/resource/authority/language/ENG'

    # Contact defaults from current user if missing
    contact_name = form_data.get('contact_name')
    contact_email = form_data.get('contact_email')
    if not (contact_name and contact_email):
        try:
            user = model.User.get(tk.g.user) if tk.g.user else None
            if user:
                contact_name = contact_name or (user.fullname or user.name)
                contact_email = contact_email or user.email
            else:
                # Fallback to site settings
                contact_name = contact_name or tk.config.get('ckan.site_title', 'contact')
                contact_email = contact_email or tk.config.get('email_to', '')
        except Exception:
            pass

    # Visibility and license
    visibility = (form_data.get('dataset_visibility') or 'public').lower()
    is_private = False if visibility == 'public' else True
    license_id = 'cc-by-sa' if not is_private else None

    # Owner org
    owner_org = form_data.get('organization_id') or None
    if not owner_org:
      try:
          orgs = tk.get_action('organization_list_for_user')(
              {'user': tk.g.user} if getattr(tk.g, 'user', None) else {},
              {'permission': 'create_dataset'}
          )
          if orgs:
              owner_org = orgs[0].get('id') or orgs[0].get('name')
      except Exception:
          pass

    # Notes/Abstract
    dataset_notes = (form_data.get('dataset_description') or form_data.get('content') or '').strip()

    # Groups (countries, initiatives)
    import json
    groups_payload = []
    for key in ('country_groups', 'initiative_groups'):
        raw = form_data.get(key)
        if not raw:
            continue
        try:
            arr = json.loads(raw)
            for g in arr:
                # accept dicts with name/id or plain names
                if isinstance(g, dict):
                    name = g.get('name') or g.get('id')
                else:
                    name = g
                if name:
                    groups_payload.append({'name': name})
        except Exception:
            # ignore parsing errors silently
            continue

    # Ensure unique dataset name before create
    unique_name = _generate_unique_dataset_name(base_name)

    package_dict = {
        'type': 'documents',
        'title_translated': {
            'en': dataset_title,
            'es': '',
            'fr': ''
        },
        'notes_translated': {
            'en': dataset_notes or '',
            'es': '',
            'fr': ''
        },
        'dataset_scope': 'non_spatial_dataset',
        'language': language,
        'identifier': unique_name,
        'name': unique_name,
        'private': is_private,
        'contact_name': contact_name,
        'contact_email': contact_email,
    }
    if license_id:
        package_dict['license_id'] = license_id
    if owner_org:
        package_dict['owner_org'] = owner_org
    graphic_overview = form_data.get('graphic_overview') or form_data.get('header_image')
    if graphic_overview:
        package_dict['graphic_overview'] = graphic_overview
    if groups_payload:
        package_dict['groups'] = groups_payload

    # Create package
    context = {'user': tk.g.user} if getattr(tk.g, 'user', None) else {}
    try:
        package = tk.get_action('package_create')(context, package_dict)
    except tk.ValidationError as e:
        # Handle name collision race conditions robustly
        if isinstance(getattr(e, 'error_dict', None), dict) and 'name' in e.error_dict:
            import uuid
            fallback_name = f"{base_name}-{str(uuid.uuid4())[:6]}"
            package_dict['name'] = fallback_name
            package_dict['identifier'] = fallback_name
            package = tk.get_action('package_create')(context, package_dict)
        else:
            raise

    # Create resource if provided
    resource_dict = {
        'package_id': package['id'],
    }

    # Title for resource
    resource_title = (form_data.get('dataset_resource_title') or dataset_title).strip()
    if resource_title:
        resource_dict['name'] = resource_title

    # Dates
    today = datetime.datetime.utcnow().date().isoformat()
    created_date = (form_data.get('creation_date') or today)
    resource_dict['created'] = created_date
    resource_dict['modified'] = today

    # Format/mimetype
    doc_format = (form_data.get('document_format') or '').strip()
    if doc_format:
        resource_dict['format'] = doc_format.upper()
    doc_mimetype = (form_data.get('document_mimetype') or '').strip()
    if doc_mimetype:
        resource_dict['mimetype'] = doc_mimetype

    # Availability/status optional defaults
    # resource_dict['availability'] = ''
    # resource_dict['status'] = ''

    upload_file = req.files.get('dataset_upload') if getattr(req, 'files', None) else None
    dataset_url = form_data.get('dataset_url')

    if upload_file and getattr(upload_file, 'filename', None):
        # File upload resource
        files_context = context.copy()
        files_context['allow_partial_update'] = False
        resource_dict['upload'] = upload_file
        tk.get_action('resource_create')(files_context, resource_dict)
    elif dataset_url:
        resource_dict['url'] = dataset_url
        # url_type left default; CKAN will set appropriately
        tk.get_action('resource_create')(context, resource_dict)

    # Optional: attempt DOI generation if an action is available
    try:
        if tk.get_action('package_doi_create'):
            tk.get_action('package_doi_create')(context, {'id': package['id']})
    except Exception:
        # ignore if action not available or fails
        pass


def _generate_unique_dataset_name(base_name):
    """Return a unique dataset name by testing candidates.
    Tries base, then appends -1..-20, then a short UUID suffix.
    """
    candidate = base_name
    context = {}
    # Try base and numeric suffixes
    for i in range(0, 21):
        if i > 0:
            candidate = f"{base_name}-{i}"
        try:
            tk.get_action('package_show')(context, {'id': candidate})
            # exists -> continue
            continue
        except tk.ObjectNotFound:
            return candidate
        except Exception:
            # On any other error, prefer returning candidate to avoid blocking
            return candidate
    # Fallback with short uuid
    import uuid
    return f"{base_name}-{str(uuid.uuid4())[:6]}"


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

    # Process file upload correctly
    data_dict = {}

    # Get the uploaded file from request
    if 'upload' in tk.request.files:
        data_dict['upload'] = tk.request.files['upload']

    # Also process form parameters if they exist
    if tk.request.form:
        form_data = logic.clean_dict(
            dict_fns.unflatten(
                logic.tuplize_dict(
                    logic.parse_params(tk.request.form)
                )
            )
        )
        data_dict.update(form_data)

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


def _filter_non_admin_pages(page_type):
    """Get private pages created by non-admin users for the specified page type"""
    from ckanext.pages.db import Page
    from ckan import model
    
    # Get all private pages of the specified type
    query = model.Session.query(Page).filter(
        Page.page_type == page_type,
        Page.private == True,
        Page.group_id == None
    ).order_by(Page.publish_date.desc())
    
    private_pages = query.all()
    
    filtered_pages = []
    for page in private_pages:
        if page.user_id:
            try:
                # Get the user object
                user = model.User.get(page.user_id)
                if user:
                    # Check if the page creator is a sysadmin
                    context = {'user': user.name}
                    tk.check_access('sysadmin', context, {})
                    # If no exception, user is admin - skip this page
                    continue
            except tk.NotAuthorized:
                # User is not admin - include this page for review
                pass
            except:
                # Any other error, include for review
                pass
        
        # Convert page object to dict format expected by template
        page_dict = {
            'title': page.title,
            'content': page.content,
            'name': page.name,
            'publish_date': page.publish_date.isoformat() if page.publish_date else None,
            'group_id': page.group_id,
            'page_type': page.page_type,
            'private': 'True',
            'created': page.created.isoformat() if page.created else None,
            'user_id': page.user_id
        }
        
        # Add extras if they exist
        if page.extras:
            try:
                import json
                extras = json.loads(page.extras)
                page_dict.update(extras)
            except:
                pass
        
        filtered_pages.append(page_dict)
    
    return filtered_pages


def water_admin_dashboard():
    """Admin dashboard to approve/reject water family content"""
    
    try:
        tk.check_access('sysadmin', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to access admin dashboard'))
    
    # Get pending items created by non-admin users
    try:
        pending_news = _filter_non_admin_pages('water-news')
    except:
        pending_news = []
    
    try:
        pending_events = _filter_non_admin_pages('water-events')
    except:
        pending_events = []
    
    try:
        pending_publications = _filter_non_admin_pages('water-publications')
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
    """Reject water family content (admin only)"""
    # Check admin access
    try:
        tk.check_access('sysadmin', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to reject content'))
    
    if tk.request.method == 'POST':
        try:
            # Get the page first
            page_dict = tk.get_action('ckanext_pages_show')(
                context={}, data_dict={'org_id': None, 'page': page}
            )
            
            if not page_dict:
                tk.h.flash_error(_('Content not found'))
                return tk.redirect_to('pages.water_admin_dashboard')
            
            # Delete the rejected content
            tk.get_action('ckanext_pages_delete')(
                context={}, data_dict={'org_id': None, 'page': page}
            )
            
            tk.h.flash_success(_('Content rejected and deleted successfully'))
            
        except Exception as e:
            tk.h.flash_error(_('Error rejecting content: %s') % str(e))
        
        return tk.redirect_to('pages.water_admin_dashboard')
    
    # GET request - should not happen normally
    return tk.redirect_to('pages.water_admin_dashboard')


def open_source_admin_dashboard():
    """Admin dashboard to approve/reject open source software submissions"""
    
    try:
        tk.check_access('sysadmin', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to access admin dashboard'))
    
    # Get pending open source software submissions
    try:
        pending_software = _filter_pending_open_source_software()
    except:
        pending_software = []

    org_options, org_lookup = _get_open_source_admin_organizations()
    user_lookup = _build_user_display_lookup(pending_software)

    return tk.render('ckanext_pages/open-source-admin-dashboard.html', extra_vars={
        'pending_software': pending_software,
        'organization_options': org_options,
        'organization_lookup': org_lookup,
        'user_lookup': user_lookup,
    })


def open_source_admin_approve(page):
    """Approve an open source software submission (make it public)"""

    log = logging.getLogger(__name__)

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

            if not page_dict:
                tk.h.flash_error(_('Entry not found.'))
                return tk.redirect_to('pages.open_source_admin_dashboard')

            # Check if organization was changed during approval
            new_organization = tk.request.form.get('new_organization')

            # Log current state
            log.info(f"[APPROVE] Before approval - page: {page}, submission_status: {page_dict.get('submission_status')}, private: {page_dict.get('private')}, current_org: {page_dict.get('ihp_organization')}, new_org: {new_organization}")

            page_dict['page'] = page
            page_dict['org_id'] = None
            page_dict['page_type'] = page_dict.get('page_type') or 'open-source-software'

            # Update submission metadata and make entry public
            now = datetime.datetime.utcnow()
            page_dict['submission_status'] = 'approved'
            page_dict['private'] = False
            page_dict['reviewed_at'] = now.isoformat()
            page_dict['reviewed_by'] = tk.g.user
            page_dict['submitted_at'] = page_dict.get('submitted_at') or now.isoformat()
            if not page_dict.get('publish_date'):
                page_dict['publish_date'] = now.isoformat()

            # Update organization if provided
            if new_organization:
                page_dict['ihp_organization'] = new_organization
                log.info(f"[APPROVE] Organization will be updated to: {new_organization}")

            log.info(f"[APPROVE] Attempting to update - submission_status: {page_dict['submission_status']}, private: {page_dict['private']}, ihp_organization: {page_dict.get('ihp_organization')}")

            tk.get_action('ckanext_pages_update')(
                context={
                    'ignore_auth': True,
                    'user': tk.g.user,
                    'model': model,
                    'session': model.Session,
                },
                data_dict=page_dict
            )
            
            # Force session flush and commit to ensure database write
            model.Session.flush()
            model.Session.commit()
            
            # Verify the update was successful
            verified_page = tk.get_action('ckanext_pages_show')(
                context={}, data_dict={'org_id': None, 'page': page}
            )
            verified_status = verified_page.get('submission_status')
            verified_private = verified_page.get('private')
            verified_org = verified_page.get('ihp_organization')
            log.info(f"[APPROVE] After approval - submission_status: {verified_status} (type: {type(verified_status)}), private: {verified_private} (type: {type(verified_private)}), ihp_organization: {verified_org}")

            # Check if values are correct (handle both bool and string values)
            status_ok = verified_status == 'approved'
            private_ok = verified_private in (False, 'False', '0', 0)
            org_ok = True
            if new_organization:
                org_ok = verified_org == new_organization
                if not org_ok:
                    log.error(f"[APPROVE] Organization not updated! Expected: {new_organization}, Got: {verified_org}")

            if not status_ok or not private_ok or not org_ok:
                log.error(f"[APPROVE] Verification failed - entry not properly approved! status_ok: {status_ok}, private_ok: {private_ok}, org_ok: {org_ok}")
                tk.h.flash_error(_('Entry approval may have failed. Please verify the entry status.'))
            else:
                success_msg = _('Open source software entry approved and published successfully.')
                if new_organization:
                    # Get organization name for message
                    org = model.Group.get(new_organization)
                    org_name = org.title or org.display_name or org.name if org else new_organization
                    success_msg += ' ' + _('Organization set to "{0}".').format(org_name)
                tk.h.flash_success(success_msg)
                
        except Exception as e:
            log.error(f"[APPROVE] Error approving entry: {str(e)}", exc_info=True)
            model.Session.rollback()
            tk.h.flash_error(_('Error approving entry: {0}').format(str(e)))
    
    return tk.redirect_to('pages.open_source_admin_dashboard')


def open_source_admin_reject(page):
    """Reject an open source software submission"""
    
    try:
        tk.check_access('sysadmin', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to reject content'))
    
    if tk.request.method == 'POST':
        try:
            # Get the page first
            page_dict = tk.get_action('ckanext_pages_show')(
                context={}, data_dict={'org_id': None, 'page': page}
            )

            if not page_dict:
                tk.h.flash_error(_('Entry not found.'))
                return tk.redirect_to('pages.open_source_admin_dashboard')

            page_dict['page'] = page
            page_dict['org_id'] = None
            page_dict['page_type'] = page_dict.get('page_type') or 'open-source-software'

            # Update submission status to rejected
            now = datetime.datetime.utcnow()
            page_dict['submission_status'] = 'rejected'
            page_dict['reviewed_at'] = now.isoformat()
            page_dict['reviewed_by'] = tk.g.user

            tk.get_action('ckanext_pages_update')(
                context={
                    'ignore_auth': True,
                    'user': tk.g.user,
                    'model': model,
                    'session': model.Session,
                },
                data_dict=page_dict
            )
            
            tk.h.flash_success(_('Open source software entry rejected.'))
        except Exception as e:
            tk.h.flash_error(_('Error rejecting entry: {0}').format(str(e)))
    
    return tk.redirect_to('pages.open_source_admin_dashboard')


def _filter_pending_open_source_software():
    """Get pending open source software submissions for admin review"""
    from ckanext.pages.db import Page
    from ckan import model
    
    # Get all pending open-source-software submissions
    query = model.Session.query(Page).filter(
        Page.page_type == 'open-source-software',
        Page.submission_status == 'pending',
        Page.group_id == None
    ).order_by(Page.submitted_at.desc())
    
    return query.all()


def open_source_admin_change_org(page):
    """Change the organization of an open source software entry"""

    import ckan.model as model
    log = logging.getLogger(__name__)

    try:
        tk.check_access('sysadmin', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to change organization'))
    
    if tk.request.method == 'POST':
        try:
            new_organization = tk.request.form.get('new_organization')
            
            if not new_organization:
                tk.h.flash_error(_('Please select an organization'))
                return tk.redirect_to('pages.open_source_admin_dashboard')
            
            # Get the page first
            page_dict = tk.get_action('ckanext_pages_show')(
                context={}, data_dict={'org_id': None, 'page': page}
            )

            if not page_dict:
                tk.h.flash_error(_('Entry not found.'))
                return tk.redirect_to('pages.open_source_admin_dashboard')

            # Log current state
            current_submission_status = page_dict.get('submission_status')
            current_private = page_dict.get('private')
            log.info(f"[CHANGE_ORG] Before change - page: {page}, current_org: {page_dict.get('ihp_organization')}, new_org: {new_organization}, submission_status: {current_submission_status}, private: {current_private}")

            page_dict['page'] = page
            page_dict['org_id'] = None
            page_dict['page_type'] = page_dict.get('page_type') or 'open-source-software'

            # Update organization - PRESERVE submission_status and private
            page_dict['ihp_organization'] = new_organization
            page_dict['modified'] = datetime.datetime.utcnow().isoformat()

            # Explicitly preserve submission_status and private status when changing organization
            if current_submission_status:
                page_dict['submission_status'] = current_submission_status
            if current_private is not None:
                page_dict['private'] = current_private

            log.info(f"[CHANGE_ORG] Attempting to update - ihp_organization: {new_organization}, preserving submission_status: {page_dict.get('submission_status')}, private: {page_dict.get('private')}")

            tk.get_action('ckanext_pages_update')(
                context={
                    'ignore_auth': True,
                    'user': tk.g.user,
                    'model': model,
                    'session': model.Session,
                },
                data_dict=page_dict
            )
            
            # Force session flush and commit to ensure database write
            model.Session.flush()
            model.Session.commit()
            
            # Verify the update was successful
            verified_page = tk.get_action('ckanext_pages_show')(
                context={}, data_dict={'org_id': None, 'page': page}
            )
            log.info(f"[CHANGE_ORG] After change - ihp_organization: {verified_page.get('ihp_organization')}, submission_status: {verified_page.get('submission_status')}, private: {verified_page.get('private')}")

            # Get organization name for message
            org = model.Group.get(new_organization)
            org_name = org.title or org.display_name or org.name if org else new_organization
            
            if verified_page.get('ihp_organization') != new_organization:
                log.error(f"[CHANGE_ORG] Verification failed - organization not changed! Expected: {new_organization}, Got: {verified_page.get('ihp_organization')}")
                tk.h.flash_error(_('Organization change may have failed. Please verify the entry.'))
            else:
                tk.h.flash_success(_('Organization changed to "{0}" successfully.').format(org_name))
            
        except Exception as e:
            log.error(f"[CHANGE_ORG] Error changing organization: {str(e)}", exc_info=True)
            model.Session.rollback()
            tk.h.flash_error(_('Error changing organization: {0}').format(str(e)))
    
    return tk.redirect_to('pages.open_source_admin_dashboard')


# Event Types Management Functions

def event_types_admin():
    """Admin page for managing event types (sysadmin only)"""
    try:
        tk.check_access('ckanext_event_types_list', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to access event types administration'))
    
    # Check if user is sysadmin for edit/delete actions
    try:
        tk.check_access('sysadmin', {'user': tk.g.user})
        tk.c.is_sysadmin = True
    except tk.NotAuthorized:
        tk.c.is_sysadmin = False
    
    # Get all event types
    try:
        event_types = tk.get_action('ckanext_event_types_list')(
            context={}, data_dict={'active_only': False}
        )
        tk.c.event_types = event_types
    except Exception as e:
        tk.h.flash_error(_('Error loading event types: %s') % str(e))
        tk.c.event_types = []
    
    return tk.render('ckanext_pages/admin/event_types_admin.html')


def event_types_edit(event_type_id=None, data=None, errors=None, error_summary=None):
    """Create or edit event type (sysadmin only)"""
    # Check access
    if event_type_id:
        try:
            tk.check_access('ckanext_event_types_update', {'user': tk.g.user})
        except tk.NotAuthorized:
            return tk.abort(401, _('Unauthorized to edit event types'))
    else:
        try:
            tk.check_access('ckanext_event_types_create', {'user': tk.g.user})
        except tk.NotAuthorized:
            return tk.abort(401, _('Unauthorized to create event types'))
    
    # Get existing event type if editing
    event_type_dict = {}
    if event_type_id:
        try:
            event_type_dict = tk.get_action('ckanext_event_types_show')(
                context={}, data_dict={'id': event_type_id}
            )
        except tk.ObjectNotFound:
            tk.h.flash_error(_('Event type not found'))
            return tk.redirect_to('pages.event_types_admin')
        except Exception as e:
            tk.h.flash_error(_('Error loading event type: %s') % str(e))
            return tk.redirect_to('pages.event_types_admin')
    
    if tk.request.method == 'POST' and not data:
        data = _parse_form_data(tk.request)
        
        # Prepare data for action
        data_dict = event_type_dict.copy()
        data_dict.update(data)
        
        if event_type_id:
            data_dict['id'] = event_type_id
        
        try:
            if event_type_id:
                result = tk.get_action('ckanext_event_types_update')(
                    context={}, data_dict=data_dict
                )
                tk.h.flash_success(_('Event type updated successfully'))
            else:
                result = tk.get_action('ckanext_event_types_create')(
                    context={}, data_dict=data_dict
                )
                tk.h.flash_success(_('Event type created successfully'))
            
            return tk.redirect_to('pages.event_types_admin')
            
        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            tk.h.flash_error(error_summary)
            return event_types_edit(event_type_id, data, errors, error_summary)
        except Exception as e:
            tk.h.flash_error(_('Error saving event type: %s') % str(e))
            return event_types_edit(event_type_id, data, errors, error_summary)
    
    if not data:
        data = event_type_dict
    
    errors = errors or {}
    error_summary = error_summary or {}
    
    vars = {
        'data': data, 
        'errors': errors,
        'error_summary': error_summary, 
        'event_type_id': event_type_id,
        'is_edit': bool(event_type_id)
    }
    
    return tk.render('ckanext_pages/admin/event_types_edit.html', extra_vars=vars)


def event_types_delete(event_type_id):
    """Delete event type (sysadmin only)"""
    try:
        tk.check_access('ckanext_event_types_delete', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to delete event types'))
    
    # Get event type info for confirmation
    try:
        event_type_dict = tk.get_action('ckanext_event_types_show')(
            context={}, data_dict={'id': event_type_id}
        )
    except tk.ObjectNotFound:
        tk.h.flash_error(_('Event type not found'))
        return tk.redirect_to('pages.event_types_admin')
    except Exception as e:
        tk.h.flash_error(_('Error loading event type: %s') % str(e))
        return tk.redirect_to('pages.event_types_admin')
    
    if 'cancel' in tk.request.args:
        return tk.redirect_to('pages.event_types_admin')
    
    if tk.request.method == 'POST':
        try:
            tk.get_action('ckanext_event_types_delete')(
                context={}, data_dict={'id': event_type_id}
            )
            tk.h.flash_success(_('Event type "%s" deleted successfully') % event_type_dict.get('title', event_type_id))
            
        except tk.ValidationError as e:
            # Handle business logic errors (like "cannot delete because in use")
            for field, messages in e.error_dict.items():
                for message in messages:
                    tk.h.flash_error(message)
        except Exception as e:
            tk.h.flash_error(_('Error deleting event type: %s') % str(e))
        
        return tk.redirect_to('pages.event_types_admin')
    else:
        # GET request - show confirmation page
        return tk.render('ckanext_pages/admin/event_types_delete.html', extra_vars={
            'event_type': event_type_dict,
            'event_type_id': event_type_id,
            'delete_url': tk.h.url_for('pages.event_types_delete', event_type_id=event_type_id)
        })
