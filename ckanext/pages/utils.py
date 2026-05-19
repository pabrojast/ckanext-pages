import datetime
import json
import logging
import six
from types import SimpleNamespace

import ckan.lib.navl.dictization_functions as dict_fns
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.logic as logic
import ckan.lib.helpers as helpers
import ckan.authz as authz
from ckan import model

from ckanext.pages.db import Page

_LOWERCASE_WORDS = {'of', 'and', 'the', 'de', 'da', 'du'}


def _format_member_state_name(name):
    """Convert a slug like 'united-states' to 'United States'."""
    if not name:
        return name
    words = name.split('-')
    result = []
    for i, word in enumerate(words):
        if i > 0 and word.lower() in _LOWERCASE_WORDS:
            result.append(word.lower())
        else:
            result.append(word.capitalize())
    return ' '.join(result)


# UNESCO region classification for member states (simplified)
_UNESCO_REGIONS = {
    'africa': {
        'algeria', 'angola', 'benin', 'botswana', 'burkina-faso', 'burundi',
        'cabo-verde', 'cape-verde', 'cameroon', 'central-african-republic',
        'chad', 'comoros', 'congo', 'democratic-republic-of-the-congo',
        'cote-d-ivoire', 'ivory-coast', 'djibouti', 'egypt', 'equatorial-guinea',
        'eritrea', 'eswatini', 'swaziland', 'ethiopia', 'gabon', 'gambia',
        'ghana', 'guinea', 'guinea-bissau', 'kenya', 'lesotho', 'liberia',
        'libya', 'madagascar', 'malawi', 'mali', 'mauritania', 'mauritius',
        'morocco', 'mozambique', 'namibia', 'niger', 'nigeria', 'rwanda',
        'sao-tome-and-principe', 'senegal', 'seychelles', 'sierra-leone',
        'somalia', 'south-africa', 'south-sudan', 'sudan', 'tanzania',
        'togo', 'tunisia', 'uganda', 'zambia', 'zimbabwe',
        'republic-of-the-congo', 'united-republic-of-tanzania',
    },
    'asia-pacific': {
        'afghanistan', 'australia', 'bangladesh', 'bhutan', 'brunei',
        'brunei-darussalam', 'cambodia', 'china', 'cook-islands', 'fiji',
        'india', 'indonesia', 'iran', 'japan', 'kazakhstan', 'kiribati',
        'korea', 'republic-of-korea', 'kyrgyzstan', 'lao', 'laos',
        'malaysia', 'maldives', 'marshall-islands', 'micronesia', 'mongolia',
        'myanmar', 'nauru', 'nepal', 'new-zealand', 'niue', 'pakistan',
        'palau', 'papua-new-guinea', 'philippines', 'samoa', 'singapore',
        'solomon-islands', 'sri-lanka', 'tajikistan', 'thailand',
        'timor-leste', 'tonga', 'turkmenistan', 'tuvalu', 'uzbekistan',
        'vanuatu', 'viet-nam', 'vietnam',
        'democratic-peoples-republic-of-korea',
    },
    'europe': {
        'albania', 'andorra', 'armenia', 'austria', 'azerbaijan', 'belarus',
        'belgium', 'bosnia-and-herzegovina', 'bulgaria', 'croatia', 'cyprus',
        'czechia', 'czech-republic', 'denmark', 'estonia', 'finland',
        'france', 'georgia', 'germany', 'greece', 'hungary', 'iceland',
        'ireland', 'israel', 'italy', 'latvia', 'lithuania', 'luxembourg',
        'malta', 'moldova', 'monaco', 'montenegro', 'netherlands',
        'north-macedonia', 'norway', 'poland', 'portugal', 'romania',
        'russian-federation', 'russia', 'san-marino', 'serbia', 'slovakia',
        'slovenia', 'spain', 'sweden', 'switzerland', 'turkey', 'turkiye',
        'ukraine', 'united-kingdom',
    },
    'lac': {
        'antigua-and-barbuda', 'argentina', 'bahamas', 'barbados', 'belize',
        'bolivia', 'brazil', 'chile', 'colombia', 'costa-rica', 'cuba',
        'dominica', 'dominican-republic', 'ecuador', 'el-salvador',
        'grenada', 'guatemala', 'guyana', 'haiti', 'honduras', 'jamaica',
        'mexico', 'nicaragua', 'panama', 'paraguay', 'peru',
        'saint-kitts-and-nevis', 'saint-lucia',
        'saint-vincent-and-the-grenadines', 'suriname',
        'trinidad-and-tobago', 'uruguay', 'venezuela',
    },
    'arab': {
        'algeria', 'bahrain', 'comoros', 'djibouti', 'egypt', 'iraq',
        'jordan', 'kuwait', 'lebanon', 'libya', 'mauritania', 'morocco',
        'oman', 'palestine', 'qatar', 'saudi-arabia', 'somalia', 'sudan',
        'syria', 'syrian-arab-republic', 'tunisia', 'united-arab-emirates',
        'yemen',
    },
}


def _get_unesco_region(slug):
    """Return the UNESCO region for a member-state slug, or empty string."""
    if not slug:
        return ''
    s = slug.lower().strip()
    for region, members in _UNESCO_REGIONS.items():
        if s in members:
            return region
    return ''


def _normalize_ckan_upload_url(image_url, upload_root):
    """Return a public URL for CKAN uploads while preserving external URLs."""
    if not image_url:
        return ''
    if not isinstance(image_url, six.string_types):
        image_url = str(image_url)
    if image_url.startswith(('http://', 'https://', '/', 'data:')):
        return image_url
    return '/uploads/{}/{}'.format(
        upload_root.strip('/'),
        image_url.lstrip('/'),
    )


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
    # Water family advanced filters (initiative, member_state)
    if page_type in ['water-news', 'water-events', 'water-publications']:
        for param in ['initiative', 'member_state']:
            if tk.request.args.get(param):
                data_dict[param] = tk.request.args.get(param)
    if tk.request.args.get('order_by'):
        data_dict['order_by'] = tk.request.args.get('order_by')
    else:
        # Default ordering for different page types
        if page_type in ['blog', 'rapid-response', 'water-news', 'water-events', 'water-publications', 'open-source-software', 'ai-water-tools']:
            data_dict['order_by'] = 'recent'  # Default to most recent first
    
    # Additional filters for rapid-response pages
    if page_type == 'rapid-response':
        filter_params = ['country', 'activity_status', 'severity', 'event_status']
        for param in filter_params:
            if tk.request.args.get(param):
                data_dict[param] = tk.request.args.get(param)
    
    # Additional filters for open-source-software and ai-water-tools
    if page_type in ['open-source-software', 'ai-water-tools']:
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
    if not authz.is_sysadmin(tk.g.user):
        # Regular users only see public items
        data_dict['private'] = False
        # For water family content and open-source-software, also consider submission status
        if page_type in ['water-news', 'water-events', 'water-publications', 'open-source-software', 'ai-water-tools']:
            # Only show approved content to regular users
            if page_type in ['open-source-software', 'ai-water-tools']:
                data_dict['submission_status'] = 'approved'
    
    tk.g.pages_dict = tk.get_action('ckanext_pages_list')(
        context={}, data_dict=data_dict
    )

    if page_type in ['water-news', 'water-events', 'water-publications']:
        pages_list = tk.g.pages_dict
        filters = {}

        if page_type == 'water-publications' and tk.request.args.get('publication_type'):
            filters['publication_type'] = tk.request.args.get('publication_type')

        if filters:
            pages_list = filter_water_family_list(pages_list, filters)

        # Source filter for water-events: ihp | community | (empty = all).
        # Counts are computed over the pre-filter list so the tabs reflect totals.
        if page_type == 'water-events':
            from ckanext.pages.plugin import is_ihp_event
            ihp_count = sum(1 for p in pages_list if is_ihp_event(p))
            tk.c.ihp_events_count = ihp_count
            tk.c.community_events_count = len(pages_list) - ihp_count
            source_filter = (tk.request.args.get('source') or '').strip().lower()
            if source_filter not in ('ihp', 'community'):
                source_filter = ''
            tk.c.events_source_filter = source_filter
            if source_filter == 'ihp':
                pages_list = [p for p in pages_list if is_ihp_event(p)]
            elif source_filter == 'community':
                pages_list = [p for p in pages_list if not is_ihp_event(p)]
            # Split featured out of the main list so the template can render
            # it in a dedicated, more prominent section.
            tk.c.featured_events = [p for p in pages_list if p.get('featured')]
            pages_list = [p for p in pages_list if not p.get('featured')]

        order_by = tk.request.args.get('order_by')
        custom_sorts = {'title', 'author', 'upcoming', 'location', 'relevance'}
        if order_by in custom_sorts:
            pages_list = sort_water_family_list(
                pages_list,
                sort_by=order_by,
                page_type=page_type,
                query=tk.request.args.get('q')
            )

        tk.g.pages_dict = pages_list

    
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

    if page_type == 'ai-water-tools':
        summary_counts = {
            'total': 0,
            'research': 0,
            'production': 0,
            'open_source': 0,
        }
        for item in tk.g.pages_dict or []:
            summary_counts['total'] += 1
            maturity_level = (item.get('maturity_level') or '').strip().lower()
            access_type = (item.get('access_type') or '').strip().lower()

            if maturity_level == 'research':
                summary_counts['research'] += 1
            if maturity_level == 'production':
                summary_counts['production'] += 1
            if access_type == 'open-source' or not access_type:
                summary_counts['open_source'] += 1

        tk.c.ai_water_summary_counts = summary_counts

    if page_type == 'water-events':
        tk.c.upcoming_count = sum(
            1 for page in tk.c.page.items if _is_water_family_event_upcoming(page)
        )

    # Load member states and initiatives for water-family filter dropdowns
    if page_type in ['water-news', 'water-events', 'water-publications']:
        _load_water_family_filter_options()

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
    elif page_type == 'ai-water-tools':
        return tk.render('ckanext_pages/ai-water-tools_list.html')
    return tk.render('ckanext_pages/pages_list.html')


def pages_edit(page=None, data=None, errors=None, error_summary=None, page_type='pages',
               quick_mode=False):

    def _slugify_title(value):
        import re
        value = (value or '').strip().lower()
        value = re.sub(r'[^a-z0-9\s_-]+', '', value)
        value = re.sub(r'\s+', '-', value)
        value = re.sub(r'-{2,}', '-', value)
        return value.strip('-')

    def _normalize_submission_action(value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in ['draft', 'submit', 'publish']:
                return normalized
        return None

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
    _page_type = 'page' if page_type == 'pages' else page_type
    permission_needed = 'ckanext_pages_update'
    if page_type in ['water-news', 'water-events', 'water-publications']:
        permission_needed = f'ckanext_{page_type.replace("-", "_")}_update'
    
    try:
        tk.check_access(permission_needed, {'user': tk.g.user}, {'page': page, 'page_type': _page_type})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to create or edit a page'))

    is_sysadmin = authz.is_sysadmin(tk.g.user)

    if tk.request.method == 'POST' and not data:
        data = _parse_form_data(tk.request)
        submission_action = _normalize_submission_action(
            data.pop('submission_action', None) or tk.request.form.get('submission_action')
        )
        page_dict.update(data)

        page_dict['org_id'] = None
        page_dict['page'] = page
        page_dict['page_type'] = 'page' if page_type == 'pages' else page_type

        # Never allow non-admin users to publish directly via crafted form payloads.
        workflow_page_types = ['water-news', 'water-events', 'water-publications', 'open-source-software', 'ai-water-tools']
        if submission_action == 'publish' and not is_sysadmin and page_type in workflow_page_types:
            log = logging.getLogger(__name__)
            log.warning(
                "User '%s' attempted to publish %s content directly. Downgrading to submit.",
                getattr(tk.g, 'user', 'unknown'), page_type
            )
            tk.h.flash_notice(_('Content has been submitted for review instead of published directly.'))
            submission_action = 'submit'

        # Re-add submission_action to page_dict so it reaches actions.py
        if submission_action:
            page_dict['submission_action'] = submission_action

        should_regenerate_name = (
            page_type == 'water-publications' and not page and page_dict.get('title')
        )
        if should_regenerate_name or (
            (not page_dict.get('name') or len(page_dict.get('name', '')) < 2) and page_dict.get('title')
        ):
            generated_name = _slugify_title(page_dict['title'])
            if generated_name and len(generated_name) >= 2:
                page_dict['name'] = generated_name
            elif not page_dict.get('name'):
                # Fallback: use 'document' prefix if slug is too short
                page_dict['name'] = 'document'

        # For water family content, set as private by default for non-admin users
        if page_type in ['water-news', 'water-events', 'water-publications', 'ai-water-tools'] and not page:
            if not is_sysadmin:
                # Regular users create as private (pending approval)
                page_dict['private'] = True

        if page_type in ['water-news', 'water-events', 'water-publications', 'ai-water-tools']:
            # Map organization_id (from dropdown) to ihp_organization (model column)
            if page_dict.get('organization_id') and not page_dict.get('ihp_organization'):
                page_dict['ihp_organization'] = page_dict['organization_id']
                # Resolve org display name for the organization text field
                try:
                    org_obj = tk.get_action('organization_show')(
                        {'ignore_auth': True},
                        {'id': page_dict['organization_id']}
                    )
                    if org_obj:
                        page_dict['organization'] = (
                            org_obj.get('title') or org_obj.get('display_name') or org_obj.get('name')
                        )
                except Exception:
                    pass

            # Fallback: auto-set from user's primary org when no org provided
            if not page_dict.get('ihp_organization'):
                try:
                    orgs = tk.get_action('organization_list_for_user')(
                        {'user': tk.g.user} if tk.g.user else {},
                        {'permission': 'read'}
                    )
                    if orgs:
                        primary_org = orgs[0]
                        page_dict['ihp_organization'] = primary_org.get('id') or primary_org.get('name')
                        if not page_dict.get('organization'):
                            page_dict['organization'] = primary_org.get('title') or primary_org.get('display_name') or primary_org.get('name')
                except Exception:
                    pass

            if submission_action == 'draft':
                page_dict['private'] = True
                page_dict['submission_status'] = 'draft'
            elif submission_action == 'submit':
                page_dict.setdefault('private', True)
                page_dict['submission_status'] = 'pending'
            elif submission_action == 'publish':
                page_dict['private'] = False
                page_dict['submission_status'] = 'approved'
            else:
                # No submission_action provided - check if admin is publishing directly
                if is_sysadmin:
                    # Admin publishing directly without submission workflow
                    if page_dict.get('private') in [False, 'False', 'false']:
                        page_dict['submission_status'] = 'approved'
                    elif not page_dict.get('submission_status'):
                        # Default to draft if no status set
                        page_dict['submission_status'] = 'draft'
                else:
                    # Non-admin without submission_action - treat as draft
                    if not page_dict.get('submission_status'):
                        page_dict['submission_status'] = 'draft'
                        page_dict['private'] = True

        # Remove helper fields that should not hit the action layer
        # Keep submission_action for water-family and open-source-software so actions.py can process it
        water_family_types = ['water-news', 'water-events', 'water-publications', 'open-source-software', 'ai-water-tools']
        if 'submission_action' in page_dict and page_type not in water_family_types:
            page_dict.pop('submission_action')

        try:
            tk.get_action('ckanext_pages_update')(
                context={'user': tk.g.user}, data_dict=page_dict
            )

            # For Water Publications, run the dataset/upload flow on BOTH create and
            # edit. Originally this was create-only, which meant that if the first
            # save's dataset creation failed silently (e.g. validation error caught
            # below), the user had no way to fix it from the edit form — uploading
            # a new file or pasting a link did nothing. `_maybe_create_documents_dataset`
            # is itself a no-op when the form has no upload, link or create flag,
            # so it's safe to call on every save.
            if page_type == 'water-publications':
                dataset_attach_error = None
                try:
                    dataset_result = _maybe_create_documents_dataset(page_dict)
                    if isinstance(dataset_result, dict):
                        if dataset_result.get('resource_url'):
                            # Save the resource URL back to the page so the display
                            # template can show the document viewer / image preview.
                            page_dict['download_url'] = dataset_result.get('resource_url')
                        if dataset_result.get('dataset_page_url'):
                            page_dict['associated_dataset_url'] = dataset_result.get('dataset_page_url')
                    else:
                        if dataset_result:
                            page_dict['download_url'] = dataset_result
                except Exception as e:
                    # Do not block page save on dataset errors; surface a warning
                    # AND log it so silent failures (the original bug here) can be
                    # diagnosed from server logs.
                    log = logging.getLogger(__name__)
                    log.warning(
                        "Water Publication dataset attach failed for page '%s': %s",
                        page_dict.get('name') or page, e, exc_info=True
                    )
                    dataset_attach_error = e
                    # CKAN's `ValidationError.__str__` is `{'field': ['msg']}` —
                    # readable but ugly. When the error has an `error_dict`,
                    # flatten it into "field: msg" so the user can see exactly
                    # which scheming field rejected the documents-dataset
                    # payload (e.g. `notes_translated: Required language "en"
                    # missing`) instead of a wall of bracketed quotes.
                    error_detail = str(e)
                    error_dict = getattr(e, 'error_dict', None)
                    if isinstance(error_dict, dict) and error_dict:
                        parts = []
                        for field_name, msgs in error_dict.items():
                            if isinstance(msgs, (list, tuple)):
                                msg = '; '.join(str(m) for m in msgs)
                            else:
                                msg = str(msgs)
                            parts.append('{0}: {1}'.format(field_name, msg))
                        error_detail = ' | '.join(parts)
                    tk.h.flash_error(_('Dataset creation warning: %s') % error_detail)

                # When the documents-dataset flow failed but the user did
                # supply a file, try a plain page-images upload so the file
                # is at least preserved on this CKAN and the publication
                # show page can display it. Without this fallback the user
                # sees "no file attached" right after a successful upload —
                # exactly the silent-loss bug the user reported.
                if dataset_attach_error is not None and not page_dict.get('download_url'):
                    fallback_url = _fallback_upload_publication_file()
                    if fallback_url:
                        page_dict['download_url'] = fallback_url
                        tk.h.flash_notice(
                            _('We could not create the documents dataset, but your file was '
                              'uploaded and attached to the publication. Ask an admin to '
                              'register it as a dataset later.')
                        )

                try:
                    _recover_water_publication_dataset_links(page_dict)
                    update_page_dict = dict(page_dict)
                    update_page_dict['page'] = (
                        update_page_dict.get('page')
                        or page
                        or update_page_dict.get('name')
                    )
                    resource_url = page_dict.get('download_url')
                    dataset_page_url = page_dict.get('associated_dataset_url')

                    if resource_url or dataset_page_url:
                        tk.get_action('ckanext_pages_update')(
                            context={'user': tk.g.user}, data_dict=update_page_dict
                        )
                except Exception as e:
                    log = logging.getLogger(__name__)
                    log.warning(
                        "Water Publication post-upload page update failed for '%s': %s",
                        page_dict.get('name') or page, e, exc_info=True
                    )

            # Show different messages based on user type and page status
            if page_type in ['water-news', 'water-events', 'water-publications', 'ai-water-tools']:
                status = page_dict.get('submission_status')
                is_private = page_dict.get('private') in [True, 'True', 'true', 1]
                page_title = page_dict.get('title', page_dict.get('name', ''))
                if status == 'approved' and not is_private:
                    tk.h.flash_success(
                        _('✅ "%s" has been published successfully and is now visible to everyone.') % page_title
                    )
                elif status == 'pending':
                    tk.h.flash_success(
                        _('📤 "%s" has been submitted for review. An administrator will review and approve it.') % page_title
                    )
                elif status == 'draft' or is_private:
                    tk.h.flash_success(
                        _('📝 "%s" has been saved as a draft. Only you can see it. You can edit it anytime.') % page_title
                    )
                elif is_sysadmin:
                    tk.h.flash_success(
                        _('✅ "%s" has been updated successfully.') % page_title
                    )
                else:
                    tk.h.flash_success(
                        _('📤 "%s" has been submitted for review.') % page_title
                    )

        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            tk.h.flash_error(error_summary)
            return pages_edit(
                page, data, errors, error_summary, page_type=page_type,
                quick_mode=quick_mode)

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
        elif page_type == 'ai-water-tools':
            endpoint = 'ai_water_tools_show'
        
        return tk.redirect_to('pages.%s' % endpoint, page=page_dict['name'])

    if not data:
        data = page_dict

    if page_type == 'water-publications':
        _recover_water_publication_dataset_links(page_dict)
        if data is page_dict:
            data = page_dict

    if page_type in ['water-news', 'water-events', 'water-publications', 'ai-water-tools']:
        if not data.get('ihp_organization'):
            try:
                orgs = tk.get_action('organization_list_for_user')(
                    {'user': tk.g.user} if tk.g.user else {},
                    {'permission': 'read'}
                )
                if orgs:
                    primary_org = orgs[0]
                    data['ihp_organization'] = primary_org.get('id') or primary_org.get('name')
                    data.setdefault('organization', primary_org.get('title') or primary_org.get('display_name') or primary_org.get('name'))
            except Exception:
                pass
        # Ensure organization_id is set for the edit form dropdown
        if data.get('ihp_organization') and not data.get('organization_id'):
            data['organization_id'] = data['ihp_organization']

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

    # Load organizations server-side for page types that need them
    if page_type in ['open-source-software', 'ai-water-tools', 'water-news', 'water-events', 'water-publications']:
        try:
            context = {'user': tk.g.user}
            if is_sysadmin:
                # Sysadmin sees all orgs — use direct query to avoid N+1
                try:
                    org_rows = (
                        model.Session.query(
                            model.Group.id, model.Group.name, model.Group.title,
                            model.Group.image_url, model.Group.state,
                        )
                        .filter(model.Group.type == 'organization',
                                model.Group.state == 'active')
                        .order_by(model.Group.title)
                        .all()
                    )
                    org_list = [
                        {'id': o.id, 'name': o.name, 'title': o.title or o.name,
                         'display_name': o.title or o.name,
                         'image_url': o.image_url or '', 'state': o.state}
                        for o in org_rows
                    ]
                except Exception:
                    org_list = tk.get_action('organization_list')(
                        context, {'all_fields': True, 'include_extras': False}
                    )
            else:
                # Non-sysadmin: respect membership — DO NOT replace this call
                org_list = tk.get_action('organization_list_for_user')(
                    context, {'permission': 'read'}
                )
            vars['organization_list'] = [
                o for o in org_list if o.get('state') == 'active'
            ]
        except Exception:
            vars['organization_list'] = []

    # Load member states server-side
    if page_type in ['open-source-software', 'ai-water-tools',
                      'water-publications', 'water-news', 'water-events']:
        try:
            # Direct DB query to avoid N+1 from group_show(include_groups=True)
            ms_group = model.Group.get('member-states')
            if ms_group:
                members = (
                    model.Session.query(model.Group.name, model.Group.title)
                    .join(model.Member, model.Member.table_id == model.Group.id)
                    .filter(
                        model.Member.group_id == ms_group.id,
                        model.Member.state == 'active',
                        model.Member.table_name == 'group',
                        model.Group.state == 'active',
                    )
                    .all()
                )
                groups = [
                    {'name': g.name, 'title': g.title or g.name,
                     'display_name': g.title or g.name}
                    for g in members if g.name
                ]
            else:
                groups = []
            for g in groups:
                g['formatted_name'] = _format_member_state_name(
                    g.get('name', '')
                )
                g['region'] = _get_unesco_region(g.get('name', ''))
            vars['member_states_list'] = sorted(
                groups, key=lambda g: g.get('formatted_name', '')
            )
        except Exception:
            vars['member_states_list'] = []

    # Load initiatives server-side for water family content types
    if page_type in ('water-publications', 'water-news', 'water-events'):
        try:
            # Query member-state children directly from DB
            member_state_names = {'member-states'}
            ms_group = model.Group.get('member-states')
            if ms_group:
                ms_members = (
                    model.Session.query(model.Group.name)
                    .join(model.Member,
                          model.Member.table_id == model.Group.id)
                    .filter(
                        model.Member.group_id == ms_group.id,
                        model.Member.state == 'active',
                        model.Member.table_name == 'group',
                        model.Group.state == 'active',
                    )
                    .all()
                )
                member_state_names.update(
                    g.name for g in ms_members if g.name
                )
            # Direct DB query to avoid N+1 from group_list(all_fields=True)
            group_rows = (
                model.Session.query(model.Group.name, model.Group.title,
                                    model.Group.state)
                .filter(
                    model.Group.type == 'group',
                    model.Group.state == 'active',
                    ~model.Group.name.in_(member_state_names)
                    if member_state_names else True,
                )
                .order_by(model.Group.title)
                .all()
            )
            initiatives = [
                {'name': g.name, 'title': g.title or g.name,
                 'display_name': g.title or g.name, 'state': g.state}
                for g in group_rows if g.name
            ]
            for g in initiatives:
                g['formatted_name'] = g.get('title') or \
                    _format_member_state_name(g.get('name', ''))
            vars['initiatives_list'] = sorted(
                initiatives, key=lambda g: g.get('formatted_name', '')
            )
        except Exception:
            vars['initiatives_list'] = []

    template_name = 'ckanext_pages/%s_edit.html' % page_type
    if quick_mode and page_type == 'water-publications' and not page:
        template_name = 'ckanext_pages/water-publications_quick.html'

    return tk.render(template_name, extra_vars=vars)


def _resolve_documents_dataset_type():
    """Resolve the dataset type used for documents.

    Preference order:
      1) Explicit config override: ckanext.pages.documents_dataset_type
      2) Known dataset types from helpers (documents -> document)
      3) Scheming schema presence (documents -> document)
      4) Fallback to 'documents' for backward compatibility
    """
    override = (
        tk.config.get('ckanext.pages.documents_dataset_type')
        or tk.config.get('ckanext.pages.document_dataset_type')
    )
    if override:
        return str(override).strip()

    candidates = ['documents', 'document']

    # Try CKAN helpers for available dataset types
    dataset_types = []
    for helper_name in ('get_dataset_types', 'package_types'):
        getter = getattr(tk.h, helper_name, None)
        if getter is None:
            continue
        try:
            if callable(getter):
                dataset_types = list(getter())
            else:
                dataset_types = list(getter)
        except Exception:
            continue
        if dataset_types:
            break

    if dataset_types:
        available = {str(t).strip().lower() for t in dataset_types if t}
        for candidate in candidates:
            if candidate in available:
                return candidate

    # Try scheming action if available
    try:
        schema_action = tk.get_action('scheming_dataset_schema_show')
    except Exception:
        schema_action = None
    if schema_action:
        for candidate in candidates:
            try:
                schema_action({}, {'type': candidate})
                return candidate
            except tk.ObjectNotFound:
                continue
            except tk.NotAuthorized:
                # Assume schema exists but current user lacks permission
                return candidate
            except Exception:
                continue

    return 'documents'


def _slugify_documents_dataset_title(text):
    import re

    value = (text or '').lower()
    value = re.sub(r'[^a-z0-9\-\_\s]+', '', value)
    value = re.sub(r'\s+', '-', value).strip('-')
    return value or 'document'


def _build_dataset_page_url(package_name):
    package_name = (package_name or '').strip()
    if not package_name:
        return ''

    site_url = (tk.config.get('ckan.site_url') or '').rstrip('/')
    try:
        return helpers.url_for('dataset.read', id=package_name, qualified=True)
    except Exception:
        dataset_path = '/dataset/{0}'.format(
            six.moves.urllib.parse.quote(str(package_name))
        )
        return '{0}{1}'.format(site_url, dataset_path) if site_url else dataset_path


def _build_resource_download_url(package_name, resource, original_filename=''):
    if isinstance(resource, dict):
        resource_id = resource.get('id')
        raw_url = resource.get('url', '') or ''
        resource_name = resource.get('name', '') or ''
    else:
        resource_id = getattr(resource, 'id', None)
        raw_url = getattr(resource, 'url', '') or ''
        resource_name = getattr(resource, 'name', '') or ''

    if raw_url.startswith(('http://', 'https://')):
        return raw_url
    if raw_url.startswith('/'):
        site_url = (tk.config.get('ckan.site_url') or '').rstrip('/')
        return '{0}{1}'.format(site_url, raw_url) if site_url else raw_url
    if not (package_name and resource_id):
        return raw_url

    filename = (original_filename or '').strip()
    if not filename:
        filename = raw_url.split('?')[0].split('#')[0].rstrip('/').rsplit('/', 1)[-1]
    if not filename:
        filename = resource_name or str(resource_id)

    base_dataset_url = _build_dataset_page_url(package_name)
    safe_filename = six.moves.urllib.parse.quote(str(filename))
    return '{0}/resource/{1}/download/{2}'.format(
        base_dataset_url.rstrip('/'),
        resource_id,
        safe_filename
    )


def is_ckan_download_url(url, site_url=None):
    """Public Jinja-helper alias for `_is_ckan_download_url`.

    Templates use this to decide whether a `doc_url` is safe to embed in an
    inline viewer (PDF.js / image preview). External links are excluded so we
    don't ask PDF.js to fetch HTML wrapper pages cross-origin and surface
    `Invalid PDF structure` in the console.
    """
    return _is_ckan_download_url(url, site_url=site_url)


def _fallback_upload_publication_file():
    """Upload `dataset_upload` via the page-images uploader.

    Used when the documents-dataset creation path fails — typically because
    the user lacks `create_dataset` on any org, or the documents schema
    rejects the payload — but the user has already provided a file. Without
    this fallback the file is silently dropped and the publication shows up
    with no attachment, which the user reads as "the upload didn't happen."

    Returns a fully-qualified URL (so it stays a valid `download_url` after
    `url_validator`) or `''` on failure.
    """
    log = logging.getLogger(__name__)
    try:
        request = tk.request
    except Exception:
        return ''

    upload_file = None
    try:
        if getattr(request, 'files', None):
            upload_file = request.files.get('dataset_upload')
    except Exception:
        return ''

    if not upload_file or not getattr(upload_file, 'filename', None):
        return ''

    try:
        result = tk.get_action('ckanext_water_family_upload')(
            {'user': tk.g.user} if getattr(tk.g, 'user', None) else {},
            {
                'upload': upload_file,
                'water_content_type': 'water-publications',
                'file_type': 'document',
            }
        )
    except Exception as e:
        log.warning(
            "Fallback page-images upload failed for water publication: %s",
            e, exc_info=True
        )
        return ''

    if not isinstance(result, dict) or result.get('uploaded') != 1:
        return ''

    file_url = result.get('url') or ''
    if not file_url:
        return ''

    # `water_family_upload` already returns a qualified URL via
    # `url_for_static(..., qualified=True)`, but be defensive.
    if file_url.startswith('/'):
        site_url = (tk.config.get('ckan.site_url') or '').rstrip('/')
        if site_url:
            file_url = '{0}{1}'.format(site_url, file_url)

    return file_url


def _add_origin(origins, raw):
    """Push `scheme://host[:port]` of `raw` into `origins`, ignoring failures."""
    if not raw:
        return
    try:
        parts = six.moves.urllib.parse.urlsplit(str(raw).strip())
    except Exception:
        return
    if parts.scheme and parts.netloc:
        origins.add('{0}://{1}'.format(parts.scheme, parts.netloc))


def _trusted_storage_origins():
    """Origins (`scheme://host[:port]`) we treat as same-site for inline preview.

    Always includes `ckan.site_url`. If the deployment serves uploads from
    a remote bucket (Azure blob, S3, a CDN), the bucket's origin is added
    too — those uploads were written by us, so PDF.js / `<img>` can embed
    them safely without bumping into the cross-origin HTML-wrapper trap
    that breaks viewers on arbitrary external links.

    Sources, in order, all best-effort:
      1. `ckan.site_url`.
      2. The `ckanext-asset-storage` configured backend (where uploads go
         via `Upload(object_type='page_images')`). For the Azure backend
         this is `_svc_client.url` (`https://<account>.blob.core.windows.net`);
         for Google Cloud it's the `https://storage.googleapis.com/<bucket>`
         endpoint — both are introspected via duck-typing so we don't hard-
         require asset-storage to be installed.
      3. `helpers.url_for_static('uploads/page_images/_probe', qualified=True)`.
         Only useful for backends that override the static URL helper
         (e.g. local storage with a CDN proxy); plain CKAN returns the
         site URL, which is already in the set.
      4. Manual override via `ckanext.pages.trusted_storage_hosts` (CSV of
         `scheme://host` values), for deployments where none of the above
         can resolve the origin (custom plugin, in-test config, etc.).
    """
    origins = set()
    _add_origin(origins, tk.config.get('ckan.site_url') or '')

    try:
        from ckanext.asset_storage.uploader import get_configured_storage
        storage = get_configured_storage()
    except Exception:
        storage = None

    if storage is not None:
        # Azure: `_svc_client` is a `BlobServiceClient` whose `.url` ends in
        # `https://<account>.blob.core.windows.net`. Container name shows
        # up only in derived URLs, not in `.url`, so the origin alone is
        # what we want.
        for attr in ('_svc_client', '_client', '_service_client'):
            obj = getattr(storage, attr, None)
            obj_url = getattr(obj, 'url', None)
            if obj_url:
                _add_origin(origins, obj_url)

        # Google Cloud / other backends sometimes expose `_bucket` with
        # `.client.api_endpoint` or similar. Probe a couple of common
        # property paths without hard-coding any single SDK.
        for attr_path in (
            ('_bucket', 'client', 'api_endpoint'),
            ('_bucket', 'client', '_base_url'),
        ):
            obj = storage
            for step in attr_path:
                obj = getattr(obj, step, None)
                if obj is None:
                    break
            if obj:
                _add_origin(origins, obj)

    try:
        probe = helpers.url_for_static(
            'uploads/page_images/_probe', qualified=True
        )
        _add_origin(origins, probe)
    except Exception:
        pass

    for raw in (tk.config.get('ckanext.pages.trusted_storage_hosts') or '').split(','):
        candidate = raw.strip().rstrip('/')
        if candidate:
            _add_origin(origins, candidate)

    return origins


def _is_ckan_download_url(url, site_url=None):
    """True if `url` is a CKAN-managed download we can embed in PDF.js / `<img>`.

    We accept three shapes:

      - dataset resource download: `/dataset/<id|name>/resource/<id>/download/<filename>`
      - page-images uploads (fallback path): `/uploads/page_images/<filename>`
      - the same files served through a configured object store (Azure blob,
        S3, etc.). When `ckan.storage_path` lives on a remote bucket,
        `url_for_static('uploads/page_images/...', qualified=True)` is
        rewritten to e.g.
        `https://<account>.blob.core.windows.net/<container>/static/page_images/<filename>`,
        but the bytes are still ours and CORS/public-read is configured for
        them. The origin must match a trusted storage host (derived from the
        site URL or from a `url_for_static` probe) so an editor can't
        smuggle an arbitrary `https://evil.com/page_images/foo.pdf` past us.
    """
    if not url:
        return False
    candidate = url.strip()
    if not candidate:
        return False
    if site_url is None:
        site_url = (tk.config.get('ckan.site_url') or '').rstrip('/')
    site_url = (site_url or '').rstrip('/')

    if site_url and candidate.startswith(site_url):
        path = candidate[len(site_url):]
    elif candidate.startswith('/'):
        path = candidate
    elif candidate.startswith(('http://', 'https://')):
        try:
            parts = six.moves.urllib.parse.urlsplit(candidate)
        except Exception:
            return False
        if not (parts.scheme and parts.netloc):
            return False
        origin = '{0}://{1}'.format(parts.scheme, parts.netloc)
        if origin not in _trusted_storage_origins():
            return False
        path = parts.path or ''
    else:
        return False

    path = path.split('?', 1)[0].split('#', 1)[0]
    if path.startswith('/dataset/') and '/resource/' in path and '/download/' in path:
        return True
    # Page-images upload (water-family fallback path or rewritten by an
    # object-storage adapter). The trailing segment `/page_images/<file>`
    # is what `Upload(object_type='page_images')` writes; we own it.
    if '/page_images/' in path:
        last = path.rsplit('/page_images/', 1)[-1]
        if last and '/' not in last:
            return True
    return False


def _recover_water_publication_dataset_links(page_data):
    """Recover/refresh document links from a matching CKAN dataset.

    Beyond filling missing fields, this also re-points an *external*
    `download_url` to a same-origin CKAN download endpoint when the
    associated dataset has an uploaded resource. That handles publications
    where the user only provided an external link in the form but the PDF
    was later uploaded directly into the CKAN dataset.
    """
    if not isinstance(page_data, dict):
        return {}

    dataset_title = (page_data.get('dataset_title') or page_data.get('title') or '').strip()
    if not dataset_title:
        return {}

    site_url = (tk.config.get('ckan.site_url') or '').rstrip('/')
    current_download = (page_data.get('download_url') or '').strip()
    current_dataset_page = (page_data.get('associated_dataset_url') or '').strip()
    current_publication_type = (page_data.get('publication_type') or '').strip()

    download_is_external = bool(current_download) and not _is_ckan_download_url(current_download, site_url)
    needs_download = (not current_download) or download_is_external
    needs_dataset_page = not current_dataset_page
    needs_publication_type = not current_publication_type

    if not needs_download and not needs_dataset_page and not needs_publication_type:
        return {}

    plain_name = _slugify_documents_dataset_title(dataset_title)
    base_name = 'document-' + plain_name
    documents_type = _resolve_documents_dataset_type()

    # Only auto-recover datasets created by `_maybe_create_documents_dataset`
    # (which prefixes every name with `document-`). Earlier versions also fell
    # back to `name == plain_name` and `title == dataset_title`, but those
    # lookups produced false positives against unrelated datasets that happened
    # to share the publication's slug — e.g. a publication titled "test" would
    # silently inherit the resource of any pre-existing `/dataset/test`,
    # including private ones the viewer can't even open. If users want to link
    # an external dataset they should populate `dataset_url` /
    # `associated_dataset_url` explicitly via the form.
    try:
        packages = (
            model.Session.query(model.Package)
            .filter(
                model.Package.state == 'active',
                model.Package.name.like(base_name + '%')
            )
            .all()
        )
    except Exception:
        packages = []

    if not packages:
        return {}

    desired_title = dataset_title.lower()

    def _package_sort_key(pkg):
        pkg_title = (getattr(pkg, 'title', '') or '').strip().lower()
        pkg_name = (getattr(pkg, 'name', '') or '').strip()
        pkg_type = (getattr(pkg, 'type', '') or '').strip().lower()
        return (
            1 if pkg_type == documents_type else 0,
            1 if pkg_title == desired_title else 0,
            1 if pkg_name == base_name else 0,
            1 if pkg_name == plain_name else 0,
        )

    package = sorted(packages, key=_package_sort_key, reverse=True)[0]
    recovered = {}

    if needs_dataset_page:
        dataset_page_url = _build_dataset_page_url(package.name)
        if dataset_page_url:
            recovered['associated_dataset_url'] = dataset_page_url

    # Pull the documents dataset's `document_type` (a scheming extra) back
    # onto the publication. This keeps the page label aligned with the
    # dataset for entries created before the form exposed the field.
    if needs_publication_type:
        try:
            extras_pairs = getattr(package, 'extras', None)
            if extras_pairs is None and hasattr(package, 'extras_dict'):
                extras_pairs = package.extras_dict
            extras_lookup = {}
            if isinstance(extras_pairs, dict):
                extras_lookup = extras_pairs
            elif extras_pairs:
                # SQLAlchemy returns a list of PackageExtra rows.
                for extra in extras_pairs:
                    if isinstance(extra, dict):
                        key = extra.get('key')
                        if key:
                            extras_lookup[key] = extra.get('value')
                    else:
                        key = getattr(extra, 'key', None)
                        if key:
                            extras_lookup[key] = getattr(extra, 'value', None)
            doc_type = (extras_lookup.get('document_type') or '').strip()
            if doc_type:
                recovered['publication_type'] = doc_type
        except Exception:
            # Recovery is best-effort; never block on metadata read errors.
            pass

    if needs_download:
        try:
            resources = (
                model.Session.query(model.Resource)
                .filter(
                    model.Resource.package_id == package.id,
                    model.Resource.state == 'active'
                )
                .all()
            )
        except Exception:
            resources = []

        if resources:
            desired_format = (page_data.get('document_format') or '').strip().lower()

            def _resource_sort_key(resource):
                resource_format = (getattr(resource, 'format', '') or '').strip().lower()
                resource_url = (getattr(resource, 'url', '') or '').strip()
                resource_url_type = (getattr(resource, 'url_type', '') or '').strip().lower()
                return (
                    1 if resource_url_type == 'upload' else 0,
                    1 if desired_format and resource_format == desired_format else 0,
                    1 if resource_url else 0,
                )

            resource = sorted(resources, key=_resource_sort_key, reverse=True)[0]
            resource_url_type = (getattr(resource, 'url_type', '') or '').strip().lower()

            # Don't replace a working external link with another external link.
            # Only override when we found a real same-origin upload, or when
            # there was no `download_url` at all.
            if not (download_is_external and resource_url_type != 'upload'):
                download_url = _build_resource_download_url(package.name, resource)
                if download_url and download_url != current_download:
                    recovered['download_url'] = download_url
                if not page_data.get('document_format') and getattr(resource, 'format', None):
                    recovered['document_format'] = str(resource.format).lower()
                if not page_data.get('document_mimetype') and getattr(resource, 'mimetype', None):
                    recovered['document_mimetype'] = resource.mimetype

    if recovered:
        page_data.update(recovered)

    return recovered


def _maybe_create_documents_dataset(form_data):
    """Create a CKAN documents dataset from publication form data
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

    base_name = 'document-' + _slugify_documents_dataset_title(dataset_title)

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

    documents_type = _resolve_documents_dataset_type()

    # `notes_translated.en` is REQUIRED on the documents schema (preset
    # `schemingdcat_fluent_notes_translated`, `required: True`). The fluent
    # validator rejects empty strings on required languages, so when the
    # publication form leaves the description blank we'd silently fail
    # `package_create` and end up with an attached PDF that goes nowhere.
    # Fall back to the title so the dataset always has *something* in the
    # required language; the user can always polish it later from /documents.
    effective_notes = dataset_notes or dataset_title

    package_dict = {
        'type': documents_type,
        'title': dataset_title,
        'notes': effective_notes,
        'title_translated': {
            'en': dataset_title,
            'es': '',
            'fr': ''
        },
        'notes_translated': {
            'en': effective_notes,
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
    # CKAN's `package_create` validation rejects datasets without `owner_org`
    # for non-sysadmin callers (`{'owner_org': ['An organization must be
    # provided']}`), so the documents-dataset creation must include it from
    # the start — creating "unowned and assigning later" looked safer against
    # the schemingdcat after_dataset_create hook race, but it instead made
    # every water-publications upload fail validation and silently fall back
    # to a page_images upload (no dataset on `/documents`). The two real
    # races we *do* still need to dodge — ckanext-doi's in-hook DOI insert
    # and chained `package_show` filters — are already handled below by
    # `_skip_doi_create` and `return_id_only`.
    if owner_org:
        package_dict['owner_org'] = owner_org
    graphic_overview = form_data.get('graphic_overview') or form_data.get('header_image')
    if graphic_overview:
        package_dict['graphic_overview'] = graphic_overview
    if groups_payload:
        package_dict['groups'] = groups_payload

    # Carry the publication's `publication_type` over to the documents
    # dataset's `document_type` field (same vocabulary in
    # schemingdcat/unesco/documents.yaml). This keeps the page and the
    # dataset aligned so the documents listing reflects the right kind.
    publication_type = (form_data.get('publication_type') or '').strip()
    if publication_type:
        package_dict['document_type'] = publication_type

    # Create package.
    # Skip ckanext-doi's in-hook DOI insert: it fires before CKAN's own
    # `model.repo.commit()` and races the package row, surfacing as
    # `doi_package_id_fkey` violations. We mint the DOI explicitly below,
    # after package_create has fully committed.
    #
    # Also ask CKAN to return only the new package id. In production,
    # `package_create`'s built-in trailing `package_show` can be chained by
    # other plugins and fail with `NotFound` even after the insert/commit
    # succeeded, which makes water-publications think dataset creation failed
    # and leaves `/documents` empty for that upload.
    context = {'user': tk.g.user} if getattr(tk.g, 'user', None) else {}
    context['_skip_doi_create'] = True
    context['return_id_only'] = True

    package_create_context = context
    package_create_dict = dict(package_dict)

    try:
        package_create_result = tk.get_action('package_create')(
            package_create_context, package_create_dict
        )
    except tk.ValidationError as e:
        # Handle name collision race conditions robustly
        if isinstance(getattr(e, 'error_dict', None), dict) and 'name' in e.error_dict:
            import uuid
            fallback_name = f"{base_name}-{str(uuid.uuid4())[:6]}"
            package_dict['name'] = fallback_name
            package_dict['identifier'] = fallback_name
            package_create_dict['name'] = fallback_name
            package_create_dict['identifier'] = fallback_name
            package_create_result = tk.get_action('package_create')(
                package_create_context, package_create_dict
            )
        else:
            raise

    package = {}
    package_id = None
    package_name = package_dict.get('name') or ''
    if isinstance(package_create_result, dict):
        # Older/customized CKAN actions may ignore `return_id_only`.
        package = package_create_result
        package_id = package.get('id')
        package_name = package.get('name') or package_name
    else:
        package_id = package_create_result
        try:
            package = tk.get_action('package_show')(
                {'ignore_auth': True},
                {
                    'id': package_id,
                    'include_plugin_data': False,
                    'strip_resource_extras': False,
                }
            )
            package_name = package.get('name') or package_name
        except Exception:
            # Resource creation only needs the package id. If a chained
            # `package_show` filter still interferes here, keep going with the
            # deterministic dataset name we just created.
            package = {
                'id': package_id,
                'name': package_name,
                'title': dataset_title,
            }

    # Create resource if provided
    resource_dict = {
        'package_id': package_id,
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

    resource_url = None
    dataset_page_url = _build_dataset_page_url(package_name)

    if upload_file and getattr(upload_file, 'filename', None):
        # File upload resource
        files_context = context.copy()
        files_context.pop('return_id_only', None)
        files_context['allow_partial_update'] = False
        resource_dict['upload'] = upload_file
        created_resource = tk.get_action('resource_create')(files_context, resource_dict)
        resource_url = _build_resource_download_url(
            package_name,
            created_resource,
            getattr(upload_file, 'filename', '')
        )
    elif dataset_url:
        resource_dict['url'] = dataset_url
        # url_type left default; CKAN will set appropriately
        resource_context = context.copy()
        resource_context.pop('return_id_only', None)
        created_resource = tk.get_action('resource_create')(resource_context, resource_dict)
        resource_url = created_resource.get('url', '') or dataset_url

    # Mint the DOI now that the package has been committed.
    # We deferred this from ckanext-doi's `after_dataset_create` hook (via
    # `_skip_doi_create=True`) to avoid the FK race when both rows are
    # flushed in the same transaction.
    try:
        from ckanext.doi.model.crud import DOIQuery
        DOIQuery.read_package(package_id, create_if_none=True)
    except ImportError:
        pass
    except Exception as e:
        logging.getLogger(__name__).warning(
            'Could not mint DOI for documents dataset %s: %s',
            package_name or package_id,
            e,
        )

    return {
        'resource_url': resource_url,
        'dataset_page_url': dataset_page_url,
        'dataset_title': package.get('title') or dataset_title,
    }


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


def _enrich_publication_display(_page):
    """Resolve org, member-state and initiative slugs into full objects
    for rich card display on water-family detail pages."""
    from ckan import model
    result = {
        'org_details': None,
        'member_state_details': [],
        'initiative_details': [],
    }

    # --- Organization details ---
    org_id = (_page.get('organization_id') or _page.get('ihp_organization')
              or '').strip()
    if org_id:
        try:
            org = tk.get_action('organization_show')(
                {'ignore_auth': True},
                {'id': org_id, 'include_datasets': False}
            )
            result['org_details'] = org
        except Exception:
            pass

    # --- Resolve groups (member states + initiatives) ---
    def _parse_group_list(raw):
        if not raw:
            return []
        if isinstance(raw, str):
            try:
                import json
                raw = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                return []
        if not isinstance(raw, list):
            return []
        names = []
        for item in raw:
            if isinstance(item, dict):
                names.append(item.get('name', ''))
            elif isinstance(item, str):
                names.append(item)
        return [n for n in names if n]

    ms_slugs = _parse_group_list(_page.get('country_groups'))
    ini_slugs = _parse_group_list(_page.get('initiative_groups'))

    all_slugs = list(set(ms_slugs + ini_slugs))
    if all_slugs:
        try:
            groups = (
                model.Session.query(
                    model.Group.name,
                    model.Group.title,
                    model.Group.image_url,
                    model.Group.description,
                )
                .filter(
                    model.Group.name.in_(all_slugs),
                    model.Group.state == 'active',
                )
                .all()
            )
            group_map = {}
            for g in groups:
                img_url = _normalize_ckan_upload_url(
                    g.image_url or '',
                    'group',
                )
                group_map[g.name] = {
                    'name': g.name,
                    'title': g.title or g.name,
                    'display_name': g.title or
                    _format_member_state_name(g.name),
                    'image_display_url': img_url,
                    'description': g.description or '',
                }
        except Exception:
            group_map = {}

        result['member_state_details'] = [
            group_map.get(s, {
                'name': s,
                'display_name': _format_member_state_name(s),
                'title': _format_member_state_name(s),
                'image_display_url': '',
                'description': '',
            })
            for s in ms_slugs
        ]
        result['initiative_details'] = [
            group_map.get(s, {
                'name': s,
                'display_name': s,
                'title': s,
                'image_display_url': '',
                'description': '',
            })
            for s in ini_slugs
        ]

    return result


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

    # Check privacy: non-admin users cannot view private/pending content
    if _page.get('private') in [True, 'True', 'true']:
        is_viewer_admin = authz.is_sysadmin(tk.g.user)

        if not is_viewer_admin:
            is_author = False
            if hasattr(tk, 'g') and tk.g.user and _page.get('user_id'):
                try:
                    from ckan import model as ckan_model
                    user_obj = ckan_model.User.get(tk.g.user)
                    if user_obj and _page.get('user_id') == user_obj.id:
                        is_author = True
                except Exception:
                    pass
            if not is_author:
                return tk.abort(403, _('Not authorized to view this content'))

    tk.c.page = _page
    _inject_views_into_page(_page)

    extra_vars = {}

    # Enrich water-family detail pages with org/group details for card displays
    if page_type in ('water-publications', 'water-news', 'water-events'):
        if page_type == 'water-publications':
            _recover_water_publication_dataset_links(_page)
        extra_vars.update(_enrich_publication_display(_page))

    return tk.render('ckanext_pages/%s.html' % page_type,
                     extra_vars=extra_vars)


def pages_revisions(page, page_type='page'):
    permission_needed = 'ckanext_pages_update'
    if page_type in ['water-news', 'water-events', 'water-publications']:
        permission_needed = 'ckanext_%s_update' % page_type.replace('-', '_')
    try:
        tk.check_access(permission_needed, {'user': tk.g.user}, {'page': page, 'page_type': page_type})
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
    permission_needed = 'ckanext_pages_update'
    if page_type in ['water-news', 'water-events', 'water-publications']:
        permission_needed = 'ckanext_%s_update' % page_type.replace('-', '_')
    try:
        tk.check_access(permission_needed, {'user': tk.g.user}, {'page': page, 'page_type': page_type})
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
    permission_needed = 'ckanext_pages_update'
    if page_type in ['water-news', 'water-events', 'water-publications']:
        permission_needed = 'ckanext_%s_update' % page_type.replace('-', '_')
    try:
        tk.check_access(permission_needed, {'user': tk.g.user}, {'page': page, 'page_type': page_type})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to view this page'))

    try:
        tk.get_action('ckanext_pages_revision_restore')(
            context={}, data_dict={"page": page, "revision": revision}
        )
        _page = Page.get(name=page)
        timestamp = helpers.render_datetime(_page.revisions[revision]["created"], with_hours=True)
        tk.h.flash_success(tk._("Content from revision created on %(timestamp)s set.") % {'timestamp': timestamp})
    except TypeError:
        tk.h.flash_error(
            """Bad values, please make sure that provided values exist:
                Page name - '{name}', Revision version - '{rev}'""".format(name=page, rev=revision))

    endpoint = 'show' if page_type in ('pages', 'page') else '%s_show' % page_type
    if page_type == 'rapid-response':
        endpoint = 'rapid_response_show'
    elif page_type == 'open-source-software':
        endpoint = 'open_source_software_show'
    elif page_type == 'ai-water-tools':
        endpoint = 'ai_water_tools_show'
    elif page_type == 'water-news':
        endpoint = 'water_news_show'
    elif page_type == 'water-events':
        endpoint = 'water_events_show'
    elif page_type == 'water-publications':
        endpoint = 'water_publications_show'
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
        elif page_type == 'ai-water-tools':
            return tk.redirect_to('pages.ai_water_tools_edit', page=page)
        else:
            return tk.redirect_to('pages.edit', page=page)

    delete_permission = 'ckanext_pages_delete'
    if page_type in ['water-news', 'water-events', 'water-publications']:
        delete_permission = 'ckanext_%s_delete' % page_type.replace('-', '_')
    try:
        tk.check_access(delete_permission, {'user': tk.g.user})
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
            elif page_type == 'ai-water-tools':
                endpoint = 'ai_water_tools_index'
                tk.h.flash_success(_('AI tool entry deleted successfully'))
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
        elif page_type == 'ai-water-tools':
            delete_url = tk.h.url_for('pages.ai_water_tools_delete', page=page)
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
    else:
        return {'uploaded': 0, 'error': {'message': 'No file provided'}}

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
        upload_info = tk.get_action('ckanext_pages_upload')(
            {'user': tk.g.user if hasattr(tk.g, 'user') else None},
            data_dict
        )
    except tk.NotAuthorized:
        return {'uploaded': 0, 'error': {'message': 'Not authorized to upload files'}}
    except tk.ValidationError as e:
        return {'uploaded': 0, 'error': {'message': str(e)}}
    except Exception as e:
        return {'uploaded': 0, 'error': {'message': f'Upload failed: {str(e)}'}}

    return upload_info


def water_family_upload():
    """Handle file uploads for water-family content types.

    This function processes uploads for water-news, water-events, and water-publications
    with specific validation and metadata handling for each content type.

    Supports:
    - Images (header images, gallery images)
    - Documents (PDFs, DOC files for attachments and agendas)

    Returns:
        dict: Upload response with url, fileName, uploaded status, and metadata
    """
    if not tk.request.method == 'POST':
        tk.abort(409, _('Only POST requests are allowed'))

    # Process file upload correctly
    data_dict = {}

    # Get the uploaded file from request
    if 'upload' in tk.request.files:
        data_dict['upload'] = tk.request.files['upload']
    else:
        return {'uploaded': 0, 'error': {'message': 'No file provided'}}

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

    # Ensure water_content_type is provided
    if 'water_content_type' not in data_dict:
        return {'uploaded': 0, 'error': {'message': 'water_content_type parameter is required'}}

    # Validate water_content_type
    valid_types = ['water-news', 'water-events', 'water-publications']
    if data_dict['water_content_type'] not in valid_types:
        return {
            'uploaded': 0,
            'error': {'message': f'Invalid water_content_type. Must be one of: {", ".join(valid_types)}'}
        }

    try:
        # Call the water_family_upload action
        upload_info = tk.get_action('ckanext_water_family_upload')(
            {'user': tk.g.user if hasattr(tk.g, 'user') else None},
            data_dict
        )
    except tk.NotAuthorized:
        return tk.abort(401, _('Not authorized to upload files for water-family content'))
    except tk.ValidationError as e:
        return {'uploaded': 0, 'error': {'message': str(e)}}
    except Exception as e:
        return {'uploaded': 0, 'error': {'message': f'Upload failed: {str(e)}'}}

    return upload_info


def get_water_family_data(page, page_type):
    """Retrieve water-family content data with specific processing.

    This function fetches water-family content (news, events, publications) and
    processes it with type-specific enhancements like parsing JSON fields,
    validating dates, and enriching organization information.

    Args:
        page (str): Page name/slug to retrieve
        page_type (str): Type of water content (water-news, water-events, water-publications)

    Returns:
        dict: Processed page data with enhanced fields, or None if not found

    Raises:
        tk.ObjectNotFound: If page doesn't exist
        tk.NotAuthorized: If user not authorized to view
    """
    import json

    # Validate page_type
    valid_types = ['water-news', 'water-events', 'water-publications']
    if page_type not in valid_types:
        raise ValueError(f'Invalid page_type. Must be one of: {", ".join(valid_types)}')

    # Fetch the page data
    try:
        page_dict = tk.get_action('ckanext_pages_show')(
            context={'user': tk.g.user if hasattr(tk.g, 'user') else None},
            data_dict={'org_id': None, 'page': page}
        )
    except tk.ObjectNotFound:
        return None

    if not page_dict:
        return None

    # Verify page_type matches
    if page_dict.get('page_type') != page_type:
        return None

    # Process water-family specific fields
    _process_water_family_json_fields(page_dict)

    # Enrich organization information
    if page_dict.get('ihp_organization'):
        try:
            org = tk.get_action('organization_show')(
                context={},
                data_dict={'id': page_dict['ihp_organization']}
            )
            page_dict['ihp_organization_details'] = {
                'id': org.get('id'),
                'name': org.get('name'),
                'title': org.get('title') or org.get('display_name'),
                'image_url': org.get('image_url')
            }
        except (tk.ObjectNotFound, tk.NotAuthorized):
            pass

    # Add computed fields
    page_dict['is_draft'] = page_dict.get('private') == 'True' or page_dict.get('private') is True
    page_dict['is_pending'] = page_dict.get('submission_status') == 'pending'
    page_dict['is_approved'] = page_dict.get('submission_status') == 'approved'

    return page_dict


def validate_water_family(data_dict, page_type):
    """Validate water-family content before submission.

    Performs validation checks specific to water-family content types beyond
    the standard schema validation. This includes checking required fields,
    validating URLs, and ensuring data consistency.

    Args:
        data_dict (dict): Data to validate
        page_type (str): Type of water content (water-news, water-events, water-publications)

    Returns:
        dict: Validation result with structure:
            {
                'valid': bool,
                'errors': dict,  # Field-level errors
                'warnings': list  # Non-blocking warnings
            }
    """
    errors = {}
    warnings = []

    # Common validation for all water-family content
    if not data_dict.get('title'):
        errors['title'] = [tk._('Title is required')]

    if not data_dict.get('content'):
        warnings.append('Content field is empty. Consider adding a description.')

    # Water type validation (if provided)
    if data_dict.get('water_type'):
        valid_water_types = [
            'groundwater', 'surface_water', 'coastal_water', 'wastewater',
            'transboundary', 'urban_water', 'agricultural_water', 'industrial_water',
            'water_quality', 'water_governance', 'climate_water', 'ecosystem', 'other'
        ]
        if data_dict['water_type'] not in valid_water_types:
            errors['water_type'] = [f'Invalid water type. Must be one of: {", ".join(valid_water_types)}']

    # Type-specific validation
    if page_type == 'water-news':
        _validate_water_news(data_dict, errors, warnings)
    elif page_type == 'water-events':
        _validate_water_events(data_dict, errors, warnings)
    elif page_type == 'water-publications':
        _validate_water_publications(data_dict, errors, warnings)

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def process_water_family_metadata(data_dict, page_type):
    """Process and normalize water-family metadata.

    Handles processing of JSON fields, file metadata, and type-specific data
    normalization for water-family content. This includes parsing uploaded_images,
    attachments, and other metadata fields.

    Args:
        data_dict (dict): Page data to process
        page_type (str): Type of water content

    Returns:
        dict: Processed data_dict with normalized metadata
    """
    import json
    from datetime import datetime

    # Process JSON fields safely
    json_fields = ['uploaded_images', 'attachments', 'water_metadata', 'timeline_events', 'country_groups', 'initiative_groups']

    for field in json_fields:
        if field in data_dict and isinstance(data_dict[field], str):
            try:
                data_dict[field] = json.loads(data_dict[field])
            except (json.JSONDecodeError, ValueError):
                data_dict[field] = [] if field in ['uploaded_images', 'attachments', 'timeline_events'] else {}

    # Normalize water_category (can be list or comma-separated string)
    if 'water_category' in data_dict:
        if isinstance(data_dict['water_category'], list):
            data_dict['water_category'] = ','.join(data_dict['water_category'])
        elif isinstance(data_dict['water_category'], str):
            # Clean up spacing
            categories = [c.strip() for c in data_dict['water_category'].split(',') if c.strip()]
            data_dict['water_category'] = ','.join(categories)

    # Add processing timestamp
    if 'water_metadata' not in data_dict:
        data_dict['water_metadata'] = {}

    if isinstance(data_dict.get('water_metadata'), dict):
        data_dict['water_metadata']['processed_at'] = datetime.utcnow().isoformat()
        data_dict['water_metadata']['content_type'] = page_type

    # Type-specific processing
    if page_type == 'water-events':
        _process_water_events_metadata(data_dict)
    elif page_type == 'water-publications':
        _process_water_publications_metadata(data_dict)

    return data_dict


def _load_water_family_filter_options():
    """Load member states and initiatives lists for water-family filter dropdowns."""
    from ckan import model

    ms_members = []
    member_state_names = {'member-states'}

    # Load member states
    try:
        ms_group = model.Group.get('member-states')
        if ms_group:
            ms_members = (
                model.Session.query(model.Group.name, model.Group.title)
                .join(model.Member,
                      model.Member.table_id == model.Group.id)
                .filter(
                    model.Member.group_id == ms_group.id,
                    model.Member.state == 'active',
                    model.Member.table_name == 'group',
                    model.Group.state == 'active',
                )
                .order_by(model.Group.title)
                .all()
            )
            tk.c.member_states_list = [
                {'name': g.name, 'title': g.title or g.name}
                for g in ms_members
            ]
            member_state_names.update(g.name for g in ms_members)
        else:
            tk.c.member_states_list = []
    except Exception:
        tk.c.member_states_list = []

    # Load initiatives (groups that are not member states)
    try:
        group_rows = (
            model.Session.query(model.Group.name, model.Group.title)
            .filter(
                model.Group.type == 'group',
                model.Group.state == 'active',
                ~model.Group.name.in_(member_state_names)
                if member_state_names else True,
            )
            .order_by(model.Group.title)
            .all()
        )
        tk.c.initiatives_list = [
            {'name': g.name, 'title': g.title or g.name}
            for g in group_rows
        ]
    except Exception:
        tk.c.initiatives_list = []


def _is_water_family_event_upcoming(page):
    if not page.get('publish_date'):
        return False
    try:
        event_date = datetime.datetime.fromisoformat(
            str(page['publish_date']).replace('Z', '+00:00')
        )
        if event_date.tzinfo is None:
            event_date = event_date.replace(tzinfo=datetime.timezone.utc)
        return event_date > datetime.datetime.now(datetime.timezone.utc)
    except (ValueError, AttributeError):
        return False


def _process_water_family_json_fields(page_dict):
    """Helper to safely parse JSON fields in water-family data."""
    import json

    json_fields = ['uploaded_images', 'attachments', 'water_metadata', 'timeline_events', 'country_groups', 'initiative_groups']

    for field in json_fields:
        if field in page_dict and isinstance(page_dict[field], str):
            try:
                page_dict[field] = json.loads(page_dict[field])
            except (json.JSONDecodeError, ValueError):
                page_dict[field] = [] if field != 'water_metadata' else {}


def _validate_water_news(data_dict, errors, warnings):
    """Validate water-news specific fields."""
    # Source URL validation (optional but recommended)
    if not data_dict.get('source') and not data_dict.get('external_links'):
        warnings.append('Consider adding a source URL or external links for credibility.')

    # Author validation
    if not data_dict.get('author'):
        warnings.append('Author/source name is recommended for news articles.')


def _validate_water_events(data_dict, errors, warnings):
    """Validate water-events specific fields."""
    import re
    from datetime import datetime

    # Event date validation
    if data_dict.get('publish_date'):
        try:
            event_date = datetime.fromisoformat(str(data_dict['publish_date']).replace('Z', '+00:00'))
            # Warn if event is in the past
            if event_date < datetime.now():
                warnings.append('Event date is in the past. Consider updating if this is an upcoming event.')
        except (ValueError, AttributeError):
            errors['publish_date'] = ['Invalid date format']

    # Location validation
    if not data_dict.get('location'):
        warnings.append('Event location is recommended.')

    # Registration URL validation
    if data_dict.get('registration_url'):
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not url_pattern.match(data_dict['registration_url']):
            errors['registration_url'] = ['Invalid URL format']


def _validate_water_publications(data_dict, errors, warnings):
    """Validate water-publications specific fields."""
    import re
    from datetime import datetime

    # At least one URL required
    if not data_dict.get('publication_url') and not data_dict.get('download_url'):
        errors['publication_url'] = [tk._('Either publication URL or download URL is required')]

    # Year validation
    if data_dict.get('year'):
        try:
            year = int(data_dict['year'])
            current_year = datetime.now().year
            if year < 1900 or year > current_year + 1:
                errors['year'] = [f'Year must be between 1900 and {current_year + 1}']
        except (ValueError, TypeError):
            errors['year'] = ['Year must be a valid number']

    # Authors validation
    if not data_dict.get('authors') and not data_dict.get('author'):
        warnings.append('Author information is recommended for publications.')

    # DOI format validation (if provided)
    if data_dict.get('doi'):
        doi_pattern = re.compile(r'^10\.\d{4,}/[\S]+$')
        if not doi_pattern.match(data_dict['doi']):
            warnings.append('DOI format may be incorrect. Expected format: 10.xxxx/xxxxx')


def _process_water_events_metadata(data_dict):
    """Process water-events specific metadata."""
    from datetime import datetime

    # Parse event date for easier display
    if data_dict.get('publish_date'):
        try:
            event_date = datetime.fromisoformat(str(data_dict['publish_date']).replace('Z', '+00:00'))
            if 'water_metadata' not in data_dict:
                data_dict['water_metadata'] = {}

            if isinstance(data_dict['water_metadata'], dict):
                data_dict['water_metadata']['event_date_formatted'] = event_date.strftime('%B %d, %Y')
                data_dict['water_metadata']['is_upcoming'] = event_date > datetime.now()
        except (ValueError, AttributeError):
            pass


def _process_water_publications_metadata(data_dict):
    """Process water-publications specific metadata."""
    # Build citation string if not provided
    if not data_dict.get('publication_details'):
        citation_parts = []

        if data_dict.get('authors'):
            citation_parts.append(data_dict['authors'])

        if data_dict.get('year'):
            citation_parts.append(f"({data_dict['year']})")

        if data_dict.get('title'):
            citation_parts.append(f'"{data_dict["title"]}"')

        if data_dict.get('journal'):
            citation_parts.append(data_dict['journal'])
        elif data_dict.get('conference'):
            citation_parts.append(data_dict['conference'])

        if data_dict.get('volume') or data_dict.get('issue') or data_dict.get('pages'):
            vol_info = []
            if data_dict.get('volume'):
                vol_info.append(f"Vol. {data_dict['volume']}")
            if data_dict.get('issue'):
                vol_info.append(f"No. {data_dict['issue']}")
            if data_dict.get('pages'):
                vol_info.append(f"pp. {data_dict['pages']}")
            citation_parts.append(', '.join(vol_info))

        if citation_parts:
            if 'water_metadata' not in data_dict:
                data_dict['water_metadata'] = {}

            if isinstance(data_dict['water_metadata'], dict):
                data_dict['water_metadata']['generated_citation'] = '. '.join(citation_parts)


def filter_water_family_list(pages_list, filters):
    """Filter water-family content list based on various criteria.

    Args:
        pages_list (list): List of page dictionaries to filter
        filters (dict): Filter criteria:
            - water_type: Filter by water type
            - water_category: Filter by category (comma-separated)
            - organization: Filter by IHP organization
            - date_from: Filter by date (ISO format)
            - date_to: Filter by date (ISO format)
            - is_upcoming: For events, filter upcoming (bool)
            - publication_type: Filter by publication type

    Returns:
        list: Filtered list of pages
    """
    if not filters:
        return pages_list

    filtered = pages_list

    # Filter by water_type
    if filters.get('water_type'):
        filtered = [p for p in filtered if p.get('water_type') == filters['water_type']]

    # Filter by water_category
    if filters.get('water_category'):
        filter_cats = set(filters['water_category'].split(','))
        filtered = [p for p in filtered
                    if p.get('water_category') and
                    any(cat in filter_cats for cat in p.get('water_category', '').split(','))]

    # Filter by organization
    if filters.get('organization'):
        filtered = [p for p in filtered if p.get('ihp_organization') == filters['organization']]

    # Filter by date range
    if filters.get('date_from') or filters.get('date_to'):
        date_from = datetime.fromisoformat(filters['date_from']) if filters.get('date_from') else None
        date_to = datetime.fromisoformat(filters['date_to']) if filters.get('date_to') else None

        def in_date_range(page):
            if not page.get('publish_date'):
                return False
            try:
                page_date = datetime.fromisoformat(str(page['publish_date']).replace('Z', '+00:00'))
                if date_from and page_date < date_from:
                    return False
                if date_to and page_date > date_to:
                    return False
                return True
            except (ValueError, AttributeError):
                return False

        filtered = [p for p in filtered if in_date_range(p)]

    # Filter upcoming events
    if filters.get('is_upcoming') is not None:
        is_upcoming = filters['is_upcoming']
        if is_upcoming:
            filtered = [p for p in filtered if _is_water_family_event_upcoming(p)]
        else:
            filtered = [p for p in filtered if not _is_water_family_event_upcoming(p)]

    # Filter by publication type
    if filters.get('publication_type'):
        publication_type = filters['publication_type'].lower()
        filtered = [
            p for p in filtered
            if (p.get('publication_type') or '').lower() == publication_type
        ]

    return filtered


def sort_water_family_list(pages_list, sort_by='recent', page_type=None, query=None):
    """Sort water-family content list by various criteria.

    Args:
        pages_list (list): List of page dictionaries to sort
        sort_by (str): Sort criteria:
            - recent: Most recent first (by publish_date)
            - oldest: Oldest first (by publish_date)
            - title: Alphabetical by title
            - author: Alphabetical by author
            - upcoming: For events, upcoming first
            - location: For events, alphabetical by location
            - relevance: Order by relevance to query
        page_type (str): Optional page type for type-specific sorting
        query (str): Search query for relevance sorting

    Returns:
        list: Sorted list of pages
    """
    from datetime import datetime

    if not pages_list:
        return pages_list

    if sort_by == 'recent':
        return sorted(pages_list, key=lambda p: p.get('publish_date') or '', reverse=True)

    elif sort_by == 'oldest':
        return sorted(pages_list, key=lambda p: p.get('publish_date') or '')

    elif sort_by == 'title':
        return sorted(pages_list, key=lambda p: (p.get('title') or '').lower())

    elif sort_by == 'author':
        return sorted(pages_list, key=lambda p: (p.get('author') or p.get('authors') or '').lower())

    elif sort_by == 'upcoming' and page_type == 'water-events':
        # Sort events by date, with upcoming events first
        def event_sort_key(page):
            if not page.get('publish_date'):
                return (1, '')  # Put events without dates last
            try:
                event_date = datetime.fromisoformat(str(page['publish_date']).replace('Z', '+00:00'))
                is_upcoming = event_date > datetime.now()
                return (0 if is_upcoming else 1, event_date.isoformat())
            except (ValueError, AttributeError):
                return (1, '')

        return sorted(pages_list, key=event_sort_key)

    elif sort_by == 'location' and page_type == 'water-events':
        return sorted(pages_list, key=lambda p: (p.get('location') or '').lower())

    elif sort_by == 'relevance' and query:
        terms = [term for term in query.lower().split() if term]
        if not terms:
            return pages_list

        def score_text(text):
            value = (text or '').lower()
            return sum(value.count(term) for term in terms)

        def score_page(page):
            title = page.get('title')
            excerpt = page.get('excerpt')
            content = page.get('content')
            return (score_text(title) * 3) + (score_text(excerpt) * 2) + score_text(content)

        return sorted(
            pages_list,
            key=lambda p: (score_page(p), p.get('publish_date') or ''),
            reverse=True
        )

    return pages_list


def get_water_family_statistics(page_type=None):
    """Get statistics about water-family content.

    Args:
        page_type (str): Optional filter by specific type (water-news, water-events, water-publications)

    Returns:
        dict: Statistics including counts, recent activity, etc.
    """
    stats = {
        'total': 0,
        'by_type': {},
        'by_water_type': {},
        'by_category': {},
        'by_organization': {},
        'published': 0,
        'pending': 0,
        'draft': 0
    }

    # Get all water-family pages
    types_to_query = [page_type] if page_type else ['water-news', 'water-events', 'water-publications']

    for ptype in types_to_query:
        try:
            pages = tk.get_action('ckanext_pages_list')(
                context={},
                data_dict={'org_id': None, 'page_type': ptype}
            )

            stats['by_type'][ptype] = len(pages)
            stats['total'] += len(pages)

            for page in pages:
                # Count by status
                is_private = page.get('private') in [True, 'True', 'true', 1]
                if is_private:
                    if page.get('submission_status') == 'pending':
                        stats['pending'] += 1
                    else:
                        stats['draft'] += 1
                else:
                    stats['published'] += 1

                # Count by water_type
                if page.get('water_type'):
                    wtype = page['water_type']
                    stats['by_water_type'][wtype] = stats['by_water_type'].get(wtype, 0) + 1

                # Count by category
                if page.get('water_category'):
                    for cat in page['water_category'].split(','):
                        cat = cat.strip()
                        if cat:
                            stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1

                # Count by organization
                if page.get('ihp_organization'):
                    org = page['ihp_organization']
                    stats['by_organization'][org] = stats['by_organization'].get(org, 0) + 1

        except Exception:
            pass

    return stats


def slugify_water_family_title(title):
    """Generate a URL-safe slug from a title for water-family content.

    This is a convenience wrapper around the internal _slugify_title function
    used in pages_edit, made available for external use.

    Args:
        title (str): Title to slugify

    Returns:
        str: URL-safe slug
    """
    import re
    value = (title or '').strip().lower()
    value = re.sub(r'[^a-z0-9\s_-]+', '', value)
    value = re.sub(r'\s+', '-', value)
    value = re.sub(r'-{2,}', '-', value)
    return value.strip('-')


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
    except Exception:
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
    except Exception:
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
    except Exception:
        publications_items = []

    pending_counts = {'news': 0, 'events': 0, 'publications': 0}
    is_admin = authz.is_sysadmin(tk.g.user)

    if is_admin:
        try:
            pending_counts['news'] = len(_filter_non_admin_pages('water-news'))
        except Exception:
            pass
        try:
            pending_counts['events'] = len(_filter_non_admin_pages('water-events'))
        except Exception:
            pass
        try:
            pending_counts['publications'] = len(_filter_non_admin_pages('water-publications'))
        except Exception:
            pass

    return tk.render('ckanext_pages/water-family.html', extra_vars={
        'news_items': news_items,
        'events_items': events_items,
        'publications_items': publications_items,
        'pending_counts': pending_counts
    })


def _filter_non_admin_pages(page_type):
    """Get pending private pages created by non-admin users for the specified page type."""
    from ckanext.pages.db import Page
    from ckan import model
    
    # Only moderation queue items (pending) should appear here.
    query = model.Session.query(Page).filter(
        Page.page_type == page_type,
        Page.private == True,
        Page.submission_status == 'pending',
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
                    if authz.is_sysadmin(user.name):
                        # User is admin - skip this page
                        continue
            except Exception:
                # Any error, include for review
                pass
        
        # Convert page object to dict format expected by template
        page_dict = {
            'title': page.title,
            'content': page.content,
            'name': page.name,
            'publish_date': page.publish_date.isoformat() if page.publish_date else None,
            'group_id': page.group_id,
            'page_type': page.page_type,
            'private': True,
            'submission_status': page.submission_status,
            'created': page.created.isoformat() if page.created else None,
            'user_id': page.user_id
        }
        
        # Add extras if they exist
        if page.extras:
            try:
                import json
                extras = json.loads(page.extras)
                page_dict.update(extras)
            except (ValueError, TypeError):
                pass
        
        filtered_pages.append(page_dict)
    
    return filtered_pages


def water_admin_dashboard():
    """Admin dashboard to approve/reject water family content"""
    
    if not authz.is_sysadmin(tk.g.user):
        return tk.abort(401, _('Unauthorized to access admin dashboard'))
    
    # Get pending items created by non-admin users
    try:
        pending_news = _filter_non_admin_pages('water-news')
    except Exception:
        pending_news = []

    try:
        pending_events = _filter_non_admin_pages('water-events')
    except Exception:
        pending_events = []

    try:
        pending_publications = _filter_non_admin_pages('water-publications')
    except Exception:
        pending_publications = []
    
    return tk.render('ckanext_pages/water-admin-dashboard.html', extra_vars={
        'pending_news': pending_news,
        'pending_events': pending_events,
        'pending_publications': pending_publications
    })


def water_admin_approve(page, page_type):
    """Approve a water family content item (make it public)"""
    
    if not authz.is_sysadmin(tk.g.user):
        return tk.abort(401, _('Unauthorized to approve content'))
    
    if tk.request.method == 'POST':
        try:
            # Get the page first
            page_dict = tk.get_action('ckanext_pages_show')(
                context={}, data_dict={'org_id': None, 'page': page}
            )

            if not page_dict:
                tk.h.flash_error(_('Content not found'))
                return tk.redirect_to('pages.water_admin_dashboard')
            
            page_dict['page'] = page
            page_dict['org_id'] = None
            page_dict['page_type'] = page_dict.get('page_type') or page_type

            # Update moderation workflow metadata and publish
            now = datetime.datetime.utcnow()
            page_dict['private'] = False
            page_dict['submission_status'] = 'approved'
            page_dict['reviewed_at'] = now.isoformat()
            page_dict['reviewed_by'] = tk.g.user
            page_dict['submitted_at'] = page_dict.get('submitted_at') or now.isoformat()
            if not page_dict.get('publish_date'):
                page_dict['publish_date'] = now.isoformat()
            
            tk.get_action('ckanext_pages_update')(
                context={}, data_dict=page_dict
            )
            
            tk.h.flash_success(_('Content approved and published successfully'))
            
        except Exception as e:
            tk.h.flash_error(_('Error approving content: %s') % str(e))
    
    return tk.redirect_to('pages.water_admin_dashboard')


def water_admin_reject(page, page_type):
    """Reject water family content (admin only) - sets status to rejected instead of deleting"""
    # Check admin access
    if not authz.is_sysadmin(tk.g.user):
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

            # Set rejected status instead of deleting
            now = datetime.datetime.utcnow()
            page_dict['page'] = page
            page_dict['org_id'] = None
            page_dict['submission_status'] = 'rejected'
            page_dict['private'] = True
            page_dict['reviewed_at'] = now.isoformat()
            page_dict['reviewed_by'] = tk.g.user

            tk.get_action('ckanext_pages_update')(
                context={}, data_dict=page_dict
            )

            tk.h.flash_success(_('Content has been rejected. The author can edit and resubmit it.'))

        except Exception as e:
            tk.h.flash_error(_('Error rejecting content: %s') % str(e))

        return tk.redirect_to('pages.water_admin_dashboard')

    # GET request - should not happen normally
    return tk.redirect_to('pages.water_admin_dashboard')


def water_events_toggle_featured(page):
    """Toggle the ``featured`` flag on a water-events page (admin only).

    Designed as an idempotent action: an explicit ``featured`` form value
    of '1'/'true' or '0'/'false' wins; otherwise the current value is
    flipped. Always redirects back to the referrer or the events list.
    """
    if not authz.is_sysadmin(tk.g.user):
        return tk.abort(401, _('Unauthorized to feature events'))

    if tk.request.method != 'POST':
        return tk.redirect_to('pages.water_events_index')

    from ckanext.pages.db import Page
    page_obj = Page.get(group_id=None, name=page, page_type='water-events')
    if not page_obj:
        tk.h.flash_error(_('Event not found'))
        return tk.redirect_to('pages.water_events_index')

    requested = (tk.request.form.get('featured') or '').strip().lower()
    if requested in ('1', 'true', 'yes', 'on'):
        new_value = True
    elif requested in ('0', 'false', 'no', 'off'):
        new_value = False
    else:
        new_value = not bool(page_obj.featured)

    try:
        page_obj.featured = new_value
        page_obj.modified = datetime.datetime.utcnow()
        model.Session.add(page_obj)
        model.Session.commit()
        if new_value:
            tk.h.flash_success(_('Event marked as featured'))
        else:
            tk.h.flash_success(_('Event removed from featured'))
    except Exception as exc:
        model.Session.rollback()
        tk.h.flash_error(_('Could not update featured state: %s') % str(exc))

    redirect_to = tk.request.form.get('next') or tk.request.referrer
    if redirect_to:
        return tk.redirect_to(redirect_to)
    return tk.redirect_to('pages.water_events_index')


def water_events_calendar():
    """Render the calendar view for water-events.

    The calendar reuses the data exposed by ``ckanext_pages_list`` and is
    rendered client-side with FullCalendar (loaded via CDN in the template).
    Source/initiative/member-state filters are honoured so the calendar
    stays in sync with the list view.
    """
    data_dict = {'org_id': None, 'page_type': 'water-events'}
    if not authz.is_sysadmin(tk.g.user):
        data_dict['private'] = False

    for param in ('q', 'event_type', 'initiative', 'member_state'):
        if tk.request.args.get(param):
            data_dict[param] = tk.request.args.get(param)

    try:
        events = tk.get_action('ckanext_pages_list')(context={}, data_dict=data_dict)
    except Exception:
        events = []

    source_filter = (tk.request.args.get('source') or '').strip().lower()
    if source_filter not in ('ihp', 'community'):
        source_filter = ''

    from ckanext.pages.plugin import is_ihp_event

    if source_filter == 'ihp':
        events = [p for p in events if is_ihp_event(p)]
    elif source_filter == 'community':
        events = [p for p in events if not is_ihp_event(p)]

    calendar_events = []
    for ev in events:
        start = ev.get('publish_date')
        if not start:
            continue
        end = ev.get('event_end_date') or start
        is_ihp = is_ihp_event(ev)
        calendar_events.append({
            'id': ev.get('name'),
            'title': ev.get('title') or ev.get('name'),
            'start': start,
            'end': end,
            'allDay': True,
            'url': tk.h.url_for('pages.water_events_show', page=ev.get('name')),
            'extendedProps': {
                'location': ev.get('location') or '',
                'event_format': ev.get('event_format') or '',
                'organization': ev.get('organization') or '',
                'source': 'ihp' if is_ihp else 'community',
                'featured': bool(ev.get('featured')),
            },
            'classNames': [
                'wf-cal-event',
                'wf-cal-event--ihp' if is_ihp else 'wf-cal-event--community',
            ] + (['wf-cal-event--featured'] if ev.get('featured') else []),
        })

    tk.c.calendar_events = calendar_events
    tk.c.events_source_filter = source_filter
    tk.c.calendar_total = len(calendar_events)

    _load_water_family_filter_options()

    return tk.render('ckanext_pages/water-events_calendar.html')


def open_source_admin_dashboard():
    """Admin dashboard to approve/reject open source software submissions"""
    
    if not authz.is_sysadmin(tk.g.user):
        return tk.abort(401, _('Unauthorized to access admin dashboard'))
    
    # Get pending open source software submissions
    try:
        pending_software = _filter_pending_open_source_software()
    except Exception:
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

    if not authz.is_sysadmin(tk.g.user):
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
    
    if not authz.is_sysadmin(tk.g.user):
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

    if not authz.is_sysadmin(tk.g.user):
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
    tk.c.is_sysadmin = authz.is_sysadmin(tk.g.user)
    
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


def disaster_types_admin():
    """Admin page for managing disaster types (sysadmin only)"""
    try:
        tk.check_access('ckanext_disaster_types_list', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to access disaster types administration'))

    tk.c.is_sysadmin = authz.is_sysadmin(tk.g.user)

    try:
        disaster_types = tk.get_action('ckanext_disaster_types_list')(
            context={}, data_dict={'active_only': False}
        )
        tk.c.disaster_types = disaster_types
    except Exception as e:
        tk.h.flash_error(_('Error loading disaster types: %s') % str(e))
        tk.c.disaster_types = []

    return tk.render('ckanext_pages/admin/disaster_types_admin.html')


def disaster_types_edit(disaster_type_id=None, data=None, errors=None, error_summary=None):
    """Create or edit disaster type (sysadmin only)"""
    if disaster_type_id:
        try:
            tk.check_access('ckanext_disaster_types_update', {'user': tk.g.user})
        except tk.NotAuthorized:
            return tk.abort(401, _('Unauthorized to edit disaster types'))
    else:
        try:
            tk.check_access('ckanext_disaster_types_create', {'user': tk.g.user})
        except tk.NotAuthorized:
            return tk.abort(401, _('Unauthorized to create disaster types'))

    disaster_type_dict = {}
    if disaster_type_id:
        try:
            disaster_type_dict = tk.get_action('ckanext_disaster_types_show')(
                context={}, data_dict={'id': disaster_type_id}
            )
        except tk.ObjectNotFound:
            tk.h.flash_error(_('Disaster type not found'))
            return tk.redirect_to('pages.disaster_types_admin')
        except Exception as e:
            tk.h.flash_error(_('Error loading disaster type: %s') % str(e))
            return tk.redirect_to('pages.disaster_types_admin')

    if tk.request.method == 'POST' and not data:
        data = _parse_form_data(tk.request)

        data_dict = disaster_type_dict.copy()
        data_dict.update(data)

        if disaster_type_id:
            data_dict['id'] = disaster_type_id

        try:
            if disaster_type_id:
                result = tk.get_action('ckanext_disaster_types_update')(
                    context={}, data_dict=data_dict
                )
                tk.h.flash_success(_('Disaster type updated successfully'))
            else:
                result = tk.get_action('ckanext_disaster_types_create')(
                    context={}, data_dict=data_dict
                )
                tk.h.flash_success(_('Disaster type created successfully'))

            return tk.redirect_to('pages.disaster_types_admin')

        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            tk.h.flash_error(error_summary)
            return disaster_types_edit(disaster_type_id, data, errors, error_summary)
        except Exception as e:
            tk.h.flash_error(_('Error saving disaster type: %s') % str(e))
            return disaster_types_edit(disaster_type_id, data, errors, error_summary)

    if not data:
        data = disaster_type_dict

    errors = errors or {}
    error_summary = error_summary or {}

    vars = {
        'data': data,
        'errors': errors,
        'error_summary': error_summary,
        'disaster_type_id': disaster_type_id,
        'is_edit': bool(disaster_type_id)
    }

    return tk.render('ckanext_pages/admin/disaster_types_edit.html', extra_vars=vars)


def disaster_types_delete(disaster_type_id):
    """Delete disaster type (sysadmin only)"""
    try:
        tk.check_access('ckanext_disaster_types_delete', {'user': tk.g.user})
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to delete disaster types'))

    try:
        disaster_type_dict = tk.get_action('ckanext_disaster_types_show')(
            context={}, data_dict={'id': disaster_type_id}
        )
    except tk.ObjectNotFound:
        tk.h.flash_error(_('Disaster type not found'))
        return tk.redirect_to('pages.disaster_types_admin')
    except Exception as e:
        tk.h.flash_error(_('Error loading disaster type: %s') % str(e))
        return tk.redirect_to('pages.disaster_types_admin')

    if 'cancel' in tk.request.args:
        return tk.redirect_to('pages.disaster_types_admin')

    if tk.request.method == 'POST':
        try:
            tk.get_action('ckanext_disaster_types_delete')(
                context={}, data_dict={'id': disaster_type_id}
            )
            tk.h.flash_success(_('Disaster type "%s" deleted successfully') % disaster_type_dict.get('title', disaster_type_id))

        except tk.ValidationError as e:
            for field, messages in e.error_dict.items():
                for message in messages:
                    tk.h.flash_error(message)
        except Exception as e:
            tk.h.flash_error(_('Error deleting disaster type: %s') % str(e))

        return tk.redirect_to('pages.disaster_types_admin')
    else:
        return tk.render('ckanext_pages/admin/disaster_types_delete.html', extra_vars={
            'disaster_type': disaster_type_dict,
            'disaster_type_id': disaster_type_id,
            'delete_url': tk.h.url_for('pages.disaster_types_delete', disaster_type_id=disaster_type_id)
        })


# AI Water Tools Admin Functions

def _filter_pending_ai_water_tools():
    """Get pending AI water tools submissions for admin review"""
    from ckanext.pages.db import Page

    query = model.Session.query(Page).filter(
        Page.page_type == 'ai-water-tools',
        Page.submission_status == 'pending',
        Page.group_id == None
    ).order_by(Page.submitted_at.desc())

    return query.all()


def ai_water_admin_dashboard():
    """Admin dashboard to approve/reject AI water tools submissions"""

    if not authz.is_sysadmin(tk.g.user):
        return tk.abort(401, _('Unauthorized to access admin dashboard'))

    try:
        pending_tools = _filter_pending_ai_water_tools()
    except Exception:
        pending_tools = []

    org_options, org_lookup = _get_open_source_admin_organizations()
    user_lookup = _build_user_display_lookup(pending_tools)

    return tk.render('ckanext_pages/ai-water-admin-dashboard.html', extra_vars={
        'pending_tools': pending_tools,
        'organization_options': org_options,
        'organization_lookup': org_lookup,
        'user_lookup': user_lookup,
    })


def ai_water_admin_approve(page):
    """Approve an AI water tools submission"""

    log = logging.getLogger(__name__)

    if not authz.is_sysadmin(tk.g.user):
        return tk.abort(401, _('Unauthorized to approve content'))

    if tk.request.method == 'POST':
        try:
            page_dict = tk.get_action('ckanext_pages_show')(
                context={}, data_dict={'org_id': None, 'page': page}
            )

            if not page_dict:
                tk.h.flash_error(_('Entry not found.'))
                return tk.redirect_to('pages.ai_water_admin_dashboard')

            new_organization = tk.request.form.get('new_organization')

            page_dict['page'] = page
            page_dict['org_id'] = None
            page_dict['page_type'] = page_dict.get('page_type') or 'ai-water-tools'

            now = datetime.datetime.utcnow()
            page_dict['submission_status'] = 'approved'
            page_dict['private'] = False
            page_dict['reviewed_at'] = now.isoformat()
            page_dict['reviewed_by'] = tk.g.user
            page_dict['submitted_at'] = page_dict.get('submitted_at') or now.isoformat()
            if not page_dict.get('publish_date'):
                page_dict['publish_date'] = now.isoformat()

            if new_organization:
                page_dict['ihp_organization'] = new_organization

            tk.get_action('ckanext_pages_update')(
                context={
                    'ignore_auth': True,
                    'user': tk.g.user,
                    'model': model,
                    'session': model.Session,
                },
                data_dict=page_dict
            )

            model.Session.flush()
            model.Session.commit()

            tk.h.flash_success(_('AI water tool entry approved and published successfully.'))

        except Exception as e:
            log.error('Error approving AI water tool entry: %s', str(e), exc_info=True)
            model.Session.rollback()
            tk.h.flash_error(_('Error approving entry: {0}').format(str(e)))

    return tk.redirect_to('pages.ai_water_admin_dashboard')


def ai_water_admin_reject(page):
    """Reject an AI water tools submission"""

    if not authz.is_sysadmin(tk.g.user):
        return tk.abort(401, _('Unauthorized to reject content'))

    if tk.request.method == 'POST':
        try:
            page_dict = tk.get_action('ckanext_pages_show')(
                context={}, data_dict={'org_id': None, 'page': page}
            )

            if not page_dict:
                tk.h.flash_error(_('Entry not found.'))
                return tk.redirect_to('pages.ai_water_admin_dashboard')

            page_dict['page'] = page
            page_dict['org_id'] = None
            page_dict['page_type'] = page_dict.get('page_type') or 'ai-water-tools'

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

            tk.h.flash_success(_('AI water tool entry rejected.'))
        except Exception as e:
            tk.h.flash_error(_('Error rejecting entry: {0}').format(str(e)))

    return tk.redirect_to('pages.ai_water_admin_dashboard')


def ai_water_admin_change_org(page):
    """Change the organization of an AI water tools entry"""

    log = logging.getLogger(__name__)

    if not authz.is_sysadmin(tk.g.user):
        return tk.abort(401, _('Unauthorized to change organization'))

    if tk.request.method == 'POST':
        try:
            new_organization = tk.request.form.get('new_organization')

            if not new_organization:
                tk.h.flash_error(_('Please select an organization'))
                return tk.redirect_to('pages.ai_water_admin_dashboard')

            page_dict = tk.get_action('ckanext_pages_show')(
                context={}, data_dict={'org_id': None, 'page': page}
            )

            if not page_dict:
                tk.h.flash_error(_('Entry not found.'))
                return tk.redirect_to('pages.ai_water_admin_dashboard')

            current_submission_status = page_dict.get('submission_status')
            current_private = page_dict.get('private')

            page_dict['page'] = page
            page_dict['org_id'] = None
            page_dict['page_type'] = page_dict.get('page_type') or 'ai-water-tools'
            page_dict['ihp_organization'] = new_organization
            page_dict['modified'] = datetime.datetime.utcnow().isoformat()

            if current_submission_status:
                page_dict['submission_status'] = current_submission_status
            if current_private is not None:
                page_dict['private'] = current_private

            tk.get_action('ckanext_pages_update')(
                context={
                    'ignore_auth': True,
                    'user': tk.g.user,
                    'model': model,
                    'session': model.Session,
                },
                data_dict=page_dict
            )

            model.Session.flush()
            model.Session.commit()

            org = model.Group.get(new_organization)
            org_name = org.title or org.display_name or org.name if org else new_organization
            tk.h.flash_success(_('Organization changed to "{0}" successfully.').format(org_name))

        except Exception as e:
            log.error('Error changing organization for AI water tool: %s', str(e), exc_info=True)
            model.Session.rollback()
            tk.h.flash_error(_('Error changing organization: {0}').format(str(e)))

    return tk.redirect_to('pages.ai_water_admin_dashboard')


# ============================================================
# CRIDA Case Study Utils
# ============================================================


def _auto_seed_crida_if_empty():
    """Automatically seed CRIDA case studies from data files if none exist."""
    import json as json_module
    import logging
    logger = logging.getLogger(__name__)

    try:
        from ckanext.pages.commands.seed_crida import (
            _load_data, _slugify, COORDINATES, IMAGE_MAP, CATEGORY_MAP
        )
        import ckan.logic as logic

        items = _load_data()
        if not items:
            return

        site_user = logic.get_action('get_site_user')(
            {'ignore_auth': True}, {}
        )
        context = {
            'user': site_user['name'],
            'ignore_auth': True,
        }

        created = 0
        for item_id, item in items.items():
            name = _slugify(item['title'])[:80] or item_id
            try:
                existing = None
                try:
                    existing = logic.get_action('ckanext_pages_show')(
                        dict(context), {'page': name}
                    )
                except (logic.NotFound, KeyError):
                    pass

                if existing:
                    continue

                coords = COORDINATES.get(item_id, (None, None, ''))
                lat, lon, coord_note = (
                    coords if len(coords) == 3
                    else (coords[0], coords[1], '')
                )
                header_image = IMAGE_MAP.get(item_id, '')

                page_data = {
                    'page': name,
                    'name': name,
                    'title': item['title'],
                    'page_type': 'crida-case-study',
                    'content': item.get('summary', ''),
                    'excerpt': (item.get('summary', '')[:300]
                                if item.get('summary') else ''),
                    'country': item.get('country', ''),
                    'crida_status': item.get('status', 'Finished'),
                    'themes': json_module.dumps(
                        item.get('themes', [])),
                    'partners': json_module.dumps(
                        item.get('partners', [])),
                    'highlights': json_module.dumps(
                        item.get('highlights', [])),
                    'case_study_url': item.get('url_unesco', ''),
                    'external_link': item.get('url_original', ''),
                    'crida_context': item.get('context', ''),
                    'crida_actions': item.get('actions', ''),
                    'crida_outcomes': item.get('outcomes', ''),
                    'image_credit': item.get('image_credit', ''),
                    'header_image': header_image,
                    'publish_date': '2025-01-01',
                    'submission_action': 'publish',
                }

                # Add category classification if available
                cats = CATEGORY_MAP.get(item_id, {})
                if cats:
                    page_data['sector'] = json_module.dumps(
                        cats.get('sector', []))
                    page_data['crida_stage'] = cats.get(
                        'crida_stage', '')
                    page_data['region'] = cats.get('region', '')
                    page_data['scale'] = cats.get('scale', '')
                    page_data['climate_challenge'] = json_module.dumps(
                        cats.get('climate_challenge', []))
                    page_data['solution_type'] = json_module.dumps(
                        cats.get('solution_type', []))

                if lat is not None:
                    page_data['latitude'] = str(lat)
                if lon is not None:
                    page_data['longitude'] = str(lon)
                if coord_note:
                    page_data['coord_note'] = coord_note

                logic.get_action('ckanext_pages_update')(
                    dict(context), page_data
                )
                created += 1

            except Exception as e:
                logger.warning(
                    'Auto-seed CRIDA: error importing %s: %s',
                    name, str(e)
                )

        if created > 0:
            logger.info(
                'Auto-seeded %d CRIDA case studies from data files',
                created
            )

    except Exception as e:
        logger.warning('Auto-seed CRIDA failed: %s', str(e))


def crida_main_page():
    """CRIDA initiative hub — aggregates all content related to the CRIDA group."""
    from ckanext.pages.plugin import get_pages_by_initiative

    # ── 1. CKAN Group data (datasets & members) ────────────────────
    group_dict = {}
    group_datasets = []
    group_members = []
    try:
        group_dict = tk.get_action('group_show')(
            context={'ignore_auth': True},
            data_dict={
                'id': 'crida',
                'include_datasets': True,
                'include_extras': True,
            }
        )
        group_datasets = group_dict.get('packages', [])[:6]
    except Exception:
        pass

    try:
        raw_members = tk.get_action('member_list')(
            context={'ignore_auth': True},
            data_dict={'id': 'crida', 'object_type': 'user'}
        )
        for member_id, _obj_type, capacity in (raw_members or []):
            try:
                user = tk.get_action('user_show')(
                    context={'ignore_auth': True},
                    data_dict={'id': member_id}
                )
                group_members.append({
                    'id': user.get('id', ''),
                    'name': user.get('name', ''),
                    'display_name': user.get('display_name') or user.get('fullname') or user.get('name', ''),
                    'email_hash': user.get('email_hash', ''),
                    'image_url': _normalize_ckan_upload_url(
                        user.get('image_url', ''),
                        'user',
                    ),
                    'capacity': capacity,
                    'about': user.get('about', ''),
                })
            except Exception:
                pass
    except Exception:
        pass

    # ── 4. Initiative pages (news, events, publications) ───────────
    try:
        crida_news = get_pages_by_initiative('crida', 'water-news')[:3]
    except Exception:
        crida_news = []

    try:
        crida_events = get_pages_by_initiative('crida', 'water-events')[:3]
    except Exception:
        crida_events = []

    try:
        crida_publications = get_pages_by_initiative('crida', 'water-publications')[:3]
    except Exception:
        crida_publications = []

    # ── 5. Compute stats ───────────────────────────────────────────
    all_datasets_count = len(group_dict.get('packages', []))

    stats = {
        'datasets': all_datasets_count,
        'news': len(get_pages_by_initiative('crida', 'water-news')),
        'events': len(get_pages_by_initiative('crida', 'water-events')),
        'publications': len(get_pages_by_initiative('crida', 'water-publications')),
        'members': len(group_members),
    }

    return tk.render('ckanext_pages/crida.html', extra_vars={
        'stats': stats,
        'group_dict': group_dict,
        'group_datasets': group_datasets,
        'group_members': group_members,
        'crida_news': crida_news,
        'crida_events': crida_events,
        'crida_publications': crida_publications,
    })


def _compute_crida_category_counts(case_studies):
    """Compute case study counts per category dimension for the explorer."""
    import json as json_module
    counts = {
        'sector': {},
        'crida_stage': {},
        'region': {},
        'scale': {},
        'climate_challenge': {},
        'solution_type': {},
    }
    for cs in case_studies:
        for dim in counts:
            try:
                raw = cs.get(dim, '[]')
                vals = json_module.loads(raw) if isinstance(raw, str) else raw
                if isinstance(vals, list):
                    for v in vals:
                        counts[dim][v] = counts[dim].get(v, 0) + 1
                elif vals and isinstance(vals, str) and vals != '[]':
                    counts[dim][vals] = counts[dim].get(vals, 0) + 1
            except Exception:
                pass
    return counts


def crida_admin_dashboard():
    """Admin dashboard for approving/rejecting CRIDA case studies."""
    if not authz.is_sysadmin(tk.g.user):
        return tk.abort(401, _('Unauthorized to access admin dashboard'))

    try:
        pending_cases = _filter_non_admin_pages('crida-case-study')
    except Exception:
        pending_cases = []

    return tk.render('ckanext_pages/crida-admin-dashboard.html', extra_vars={
        'pending_cases': pending_cases,
    })


def crida_admin_approve(page):
    """Approve a CRIDA case study (make it public)."""
    if not authz.is_sysadmin(tk.g.user):
        return tk.abort(401, _('Unauthorized to approve content'))

    if tk.request.method == 'POST':
        try:
            page_dict = tk.get_action('ckanext_pages_show')(
                context={}, data_dict={'org_id': None, 'page': page}
            )

            if not page_dict:
                tk.h.flash_error(_('Content not found'))
                return tk.redirect_to('pages.crida_admin_dashboard')

            page_dict['page'] = page
            page_dict['org_id'] = None
            page_dict['page_type'] = page_dict.get('page_type') or 'crida-case-study'

            now = datetime.datetime.utcnow()
            page_dict['private'] = False
            page_dict['submission_status'] = 'approved'
            page_dict['reviewed_at'] = now.isoformat()
            page_dict['reviewed_by'] = tk.g.user
            page_dict['submitted_at'] = page_dict.get('submitted_at') or now.isoformat()
            if not page_dict.get('publish_date'):
                page_dict['publish_date'] = now.isoformat()

            tk.get_action('ckanext_pages_update')(
                context={}, data_dict=page_dict
            )

            tk.h.flash_success(_('CRIDA case study approved and published successfully'))

        except Exception as e:
            tk.h.flash_error(_('Error approving content: %s') % str(e))

    return tk.redirect_to('pages.crida_admin_dashboard')


def crida_admin_reject(page):
    """Reject a CRIDA case study."""
    if not authz.is_sysadmin(tk.g.user):
        return tk.abort(401, _('Unauthorized to reject content'))

    if tk.request.method == 'POST':
        try:
            page_dict = tk.get_action('ckanext_pages_show')(
                context={}, data_dict={'org_id': None, 'page': page}
            )

            if not page_dict:
                tk.h.flash_error(_('Content not found'))
                return tk.redirect_to('pages.crida_admin_dashboard')

            now = datetime.datetime.utcnow()
            page_dict['page'] = page
            page_dict['org_id'] = None
            page_dict['submission_status'] = 'rejected'
            page_dict['private'] = True
            page_dict['reviewed_at'] = now.isoformat()
            page_dict['reviewed_by'] = tk.g.user

            tk.get_action('ckanext_pages_update')(
                context={}, data_dict=page_dict
            )

            tk.h.flash_success(_('Case study has been rejected. The author can edit and resubmit it.'))

        except Exception as e:
            tk.h.flash_error(_('Error rejecting content: %s') % str(e))

        return tk.redirect_to('pages.crida_admin_dashboard')

    return tk.redirect_to('pages.crida_admin_dashboard')


def crida_admin_reseed():
    """Force re-seed all CRIDA case studies from data files."""
    if not authz.is_sysadmin(tk.g.user):
        return tk.abort(401, _('Unauthorized'))

    import json as json_module
    import logging
    logger = logging.getLogger(__name__)

    try:
        from ckanext.pages.commands.seed_crida import (
            _load_data, _slugify, COORDINATES, IMAGE_MAP, CATEGORY_MAP
        )
        import ckan.logic as logic

        items = _load_data()
        if not items:
            tk.h.flash_error(_('No data files found to seed.'))
            return tk.redirect_to('pages.crida_admin_dashboard')

        site_user = logic.get_action('get_site_user')(
            {'ignore_auth': True}, {}
        )
        context = {
            'user': site_user['name'],
            'ignore_auth': True,
        }

        created = 0
        updated = 0
        errors = 0

        for item_id, item in items.items():
            name = _slugify(item['title'])[:80] or item_id
            try:
                coords = COORDINATES.get(item_id, (None, None, ''))
                lat, lon, coord_note = (
                    coords if len(coords) == 3
                    else (coords[0], coords[1], '')
                )
                header_image = IMAGE_MAP.get(item_id, '')

                existing = None
                try:
                    existing = logic.get_action('ckanext_pages_show')(
                        dict(context), {'page': name}
                    )
                except (logic.NotFound, KeyError):
                    pass

                page_data = {
                    'page': name,
                    'name': name,
                    'title': item['title'],
                    'page_type': 'crida-case-study',
                    'content': item.get('summary', ''),
                    'excerpt': (
                        item.get('summary', '')[:300]
                        if item.get('summary') else ''
                    ),
                    'country': item.get('country', ''),
                    'crida_status': item.get('status', 'Finished'),
                    'themes': json_module.dumps(
                        item.get('themes', [])
                    ),
                    'partners': json_module.dumps(
                        item.get('partners', [])
                    ),
                    'highlights': json_module.dumps(
                        item.get('highlights', [])
                    ),
                    'case_study_url': item.get('url_unesco', ''),
                    'external_link': item.get(
                        'url_original', ''
                    ),
                    'crida_context': item.get('context', ''),
                    'crida_actions': item.get('actions', ''),
                    'crida_outcomes': item.get('outcomes', ''),
                    'image_credit': item.get(
                        'image_credit', ''
                    ),
                    'header_image': header_image,
                    'publish_date': '2025-01-01',
                    'submission_action': 'publish',
                }

                # Add category classification if available
                cats = CATEGORY_MAP.get(item_id, {})
                if cats:
                    page_data['sector'] = json_module.dumps(
                        cats.get('sector', []))
                    page_data['crida_stage'] = cats.get(
                        'crida_stage', '')
                    page_data['region'] = cats.get('region', '')
                    page_data['scale'] = cats.get('scale', '')
                    page_data['climate_challenge'] = json_module.dumps(
                        cats.get('climate_challenge', []))
                    page_data['solution_type'] = json_module.dumps(
                        cats.get('solution_type', []))

                if lat is not None:
                    page_data['latitude'] = str(lat)
                if lon is not None:
                    page_data['longitude'] = str(lon)
                if coord_note:
                    page_data['coord_note'] = coord_note

                logic.get_action('ckanext_pages_update')(
                    dict(context), page_data
                )

                if existing:
                    updated += 1
                else:
                    created += 1

            except Exception:
                errors += 1
                logger.exception(
                    'Error re-seeding CRIDA: %s', name
                )

        tk.h.flash_success(
            _('Re-seed complete: %d created, %d updated, '
              '%d errors') % (created, updated, errors)
        )

    except Exception as e:
        logger.exception('Error during CRIDA re-seed')
        tk.h.flash_error(
            _('Error during re-seed: %s') % str(e)
        )

    return tk.redirect_to('pages.crida_admin_dashboard')


def crida_case_studies_api():
    """API endpoint returning paginated case studies as JSON with category filters."""
    import json as json_module
    from flask import Response

    try:
        offset = int(tk.request.args.get('offset', 0))
    except (ValueError, TypeError):
        offset = 0
    try:
        limit = int(tk.request.args.get('limit', 6))
    except (ValueError, TypeError):
        limit = 6

    limit = max(1, min(limit, 50))
    offset = max(0, offset)

    # Category filter parameters
    filter_sector = tk.request.args.get('sector', '').strip()
    filter_stage = tk.request.args.get('crida_stage', '').strip()
    filter_region = tk.request.args.get('region', '').strip()
    filter_scale = tk.request.args.get('scale', '').strip()
    filter_challenge = tk.request.args.get('climate_challenge', '').strip()
    filter_solution = tk.request.args.get('solution_type', '').strip()

    try:
        all_case_studies = tk.get_action('ckanext_pages_list')(
            context={}, data_dict={
                'org_id': None,
                'page_type': 'crida-case-study',
                'order_publish_date': True,
                'private': False
            }
        )
    except Exception:
        all_case_studies = []

    # Apply category filters
    category_filters = {
        'sector': filter_sector,
        'crida_stage': filter_stage,
        'region': filter_region,
        'scale': filter_scale,
        'climate_challenge': filter_challenge,
        'solution_type': filter_solution,
    }
    active_filters = {k: v for k, v in category_filters.items() if v}

    if active_filters:
        filtered = []
        for cs in all_case_studies:
            match = True
            for dim, val in active_filters.items():
                try:
                    raw = cs.get(dim, '[]')
                    vals = json_module.loads(raw) if isinstance(raw, str) else raw
                    if isinstance(vals, list):
                        if val not in vals:
                            match = False
                            break
                    elif vals != val:
                        match = False
                        break
                except Exception:
                    match = False
                    break
            if match:
                filtered.append(cs)
        all_case_studies = filtered

    total = len(all_case_studies)
    page_items = all_case_studies[offset:offset + limit]

    results = []
    for cs in page_items:
        themes = []
        try:
            raw = cs.get('themes', '[]')
            themes = json_module.loads(raw) if isinstance(raw, str) else (raw or [])
        except Exception:
            pass
        results.append({
            'name': cs.get('name', ''),
            'title': cs.get('title', ''),
            'country': cs.get('country', ''),
            'crida_status': cs.get('crida_status', ''),
            'header_image': cs.get('header_image', ''),
            'excerpt': cs.get('excerpt', ''),
            'content': (cs.get('content') or '')[:180],
            'themes': themes,
            'sector': cs.get('sector', '[]'),
            'solution_type': cs.get('solution_type', '[]'),
            'region': cs.get('region', ''),
            'scale': cs.get('scale', ''),
            'url': tk.url_for('pages.crida_case_study_show', page=cs.get('name', '')),
        })

    payload = {
        'results': results,
        'total': total,
        'offset': offset,
        'limit': limit,
        'has_more': (offset + limit) < total,
    }

    return Response(
        json_module.dumps(payload),
        mimetype='application/json',
        headers={'Cache-Control': 'public, max-age=60'},
    )


def crida_geojson_api():
    """API endpoint returning GeoJSON for Terria map integration."""
    import json as json_module
    from flask import Response

    try:
        geojson_data = tk.get_action('ckanext_crida_geojson')(
            context={}, data_dict=dict(tk.request.args)
        )
    except Exception:
        geojson_data = {"type": "FeatureCollection", "features": []}

    return Response(
        json_module.dumps(geojson_data),
        mimetype='application/json',
        headers={
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'public, max-age=300',
        }
    )


def crida_admin_reseed():
    """Re-seed CRIDA case studies from data files (admin only)."""
    if not authz.is_sysadmin(tk.g.user):
        return tk.abort(401, _('Unauthorized'))

    from ckanext.pages.commands.seed_crida import _load_data, _slugify
    from ckanext.pages.commands.seed_crida import COORDINATES, IMAGE_MAP
    import json as json_module

    items = _load_data()
    created = 0
    updated = 0
    errors_list = []

    site_user = logic.get_action('get_site_user')(
        {'ignore_auth': True}, {}
    )
    context = {
        'user': site_user['name'],
        'ignore_auth': True,
    }

    for item_id, item in items.items():
        name = _slugify(item['title'])[:80] or item_id
        try:
            existing = None
            try:
                existing = logic.get_action('ckanext_pages_show')(
                    dict(context), {'page': name}
                )
            except (logic.NotFound, KeyError):
                pass

            coords = COORDINATES.get(item_id, (None, None, ''))
            lat, lon, coord_note = (
                coords if len(coords) == 3
                else (coords[0], coords[1], '')
            )

            header_image = IMAGE_MAP.get(item_id, '')

            page_data = {
                'page': name,
                'name': name,
                'title': item['title'],
                'page_type': 'crida-case-study',
                'content': item.get('summary', ''),
                'excerpt': (item.get('summary', '')[:300]
                            if item.get('summary') else ''),
                'country': item.get('country', ''),
                'crida_status': item.get('status', 'Finished'),
                'themes': json_module.dumps(item.get('themes', [])),
                'partners': json_module.dumps(item.get('partners', [])),
                'highlights': json_module.dumps(item.get('highlights', [])),
                'crida_context': item.get('context', ''),
                'crida_actions': item.get('actions', ''),
                'crida_outcomes': item.get('outcomes', ''),
                'image_credit': item.get('image_credit', ''),
                'header_image': header_image,
                'publish_date': '2025-01-01',
                'submission_action': 'publish',
            }

            if item.get('url_unesco'):
                page_data['case_study_url'] = item['url_unesco']
            if item.get('url_original'):
                page_data['external_link'] = item['url_original']

            if lat is not None:
                page_data['latitude'] = str(lat)
            if lon is not None:
                page_data['longitude'] = str(lon)
            if coord_note:
                page_data['coord_note'] = coord_note

            logic.get_action('ckanext_pages_update')(
                dict(context), page_data
            )

            if existing:
                updated += 1
            else:
                created += 1

        except Exception as e:
            log = logging.getLogger(__name__)
            log.error('Error re-seeding CRIDA: %s', name, exc_info=True)
            errors_list.append(f'{name}: {e}')

    if errors_list:
        tk.h.flash_error(
            _('Re-seed completed with %d errors') % len(errors_list)
        )
    else:
        tk.h.flash_success(
            _('Re-seed complete: %d created, %d updated') % (created, updated)
        )

    return tk.redirect_to('pages.crida_admin_dashboard')
