# encoding: utf-8

try:
    from unittest import mock
except ImportError:
    import mock
import pytest
from collections import OrderedDict
import datetime
import json
import re

from ckan.plugins import toolkit
from ckan.tests import factories, helpers

from ckanext.pages.logic import schema

ckan_29_or_higher = toolkit.check_ckan_version(u'2.9')


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "pages")
class TestPages():

    def test_create_page(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        page = 'test_page'
        response = app.post(
            url=toolkit.url_for('pages_edit', page=page),
            params={
                'title': 'Page Title',
                'name': 'page_name',
                'private': False,
            },
            extra_environ=env,
        )
        assert '<h1 class="page-heading">Page Title</h1>' in response.body

    @pytest.mark.ckan_config('ckanext.pages.allow_html', 'True')
    def test_rendering_with_html_allowed(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        page = 'test_html_page'
        response = app.post(
            url=toolkit.url_for('pages_edit', page=page),
            params={
                'title': 'Allowed',
                'name': 'page_html_allowed',
                'content': '<a href="/test">Test Link</a>',
                'private': False,
            },
            extra_environ=env,
        )
        assert '<h1 class="page-heading">Allowed</h1>' in response.body
        assert 'Test Link' in response.body

    @pytest.mark.ckan_config('ckanext.pages.allow_html', False)
    def test_rendering_with_html_disallowed(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        page = 'test_html_page'
        response = app.post(
            url=toolkit.url_for('pages_edit', page=page),
            params={
                'title': 'Disallowed',
                'name': 'page_html_disallowed',
                'content': '<a href="/test">Test Link</a>',
                'private': False,
            },
            extra_environ=env,
        )
        assert '<h1 class="page-heading">Disallowed</h1>' in response.body
        assert 'Test Link' in response.body
        assert '<a href="/test">Test Link</a>' not in response.body

    @pytest.mark.ckan_config('ckanext.pages.allow_html', False)
    def test_rendering_no_p_tags_added_with_html_disallowed(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        page = 'test_html_page_p'
        response = app.post(
            url=toolkit.url_for('pages_edit', page=page),
            params={
                'title': 'Disallowed',
                'name': 'page_html_disallowed_p',
                'content': 'Hi there **you**',
                'private': False,
            },
            extra_environ=env,
        )
        assert '<p>Hi there <strong>you</strong></p>' in response.body

    @pytest.mark.ckan_config('ckanext.pages.allow_html', True)
    def test_rendering_no_div_tags_added_with_html_allowed(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        page = 'test_html_page_div'
        response = app.post(
            url=toolkit.url_for('pages_edit', page=page),
            params={
                'title': 'Disallowed',
                'name': 'page_html_allowed_div',
                'content': '<p>Hi there</p>',
                'private': False,
            },
            extra_environ=env,
        )
        assert '<p>Hi there</p>' in response.body
        assert '<div><p>Hi there</p></div>' not in response.body

    def test_pages_index(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('pages.pages_index')
        response = app.get(url, status=200, extra_environ=env)
        assert '<h1 class="page-heading page-list-header">Pages</h1>' in response.body
        assert 'Add page</a>' in response.body

    def test_blog_index(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        endpoint = 'pages.blog_index'
        url = toolkit.url_for(endpoint)
        response = app.get(url, status=200, extra_environ=env)
        assert '<h1 class="page-heading page-list-header">Blog</h1>' in response.body
        assert 'Add Article</a>' in response.body

    def test_organization_pages_index(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        org = factories.Organization()

        endpoint = 'pages.organization_pages_index'
        url = toolkit.url_for(endpoint, id=org['id'])
        response = app.get(url, status=200, extra_environ=env)
        assert '<h1 class="page-heading page-list-header">Pages</h1>' in response.body
        assert 'Add page</a>' in response.body

    def test_group_pages_index(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        group = factories.Group()
        endpoint = 'pages.group_pages_index'
        url = toolkit.url_for(endpoint, id=group['id'])
        response = app.get(url, status=200, extra_environ=env)
        assert '<h1 class="page-heading page-list-header">Pages</h1>' in response.body
        assert 'Add page</a>' in response.body

    def test_open_source_submission_appears_in_pending_list(self, app):
        submitter = factories.User()
        env = {'REMOTE_USER': submitter['name'].encode('ascii')}
        slug = 'pending-tool'

        app.post(
            toolkit.url_for('pages.open_source_software_new'),
            params={
                'title': 'Pending Tool',
                'name': slug,
                'content': 'Useful open source entry awaiting review.',
                'submission_action': 'submit',
            },
            extra_environ=env,
            status=302,
        )

        page = helpers.call_action(
            'ckanext_pages_show', {'user': submitter['name']}, page=slug
        )
        assert page['submission_status'] == 'pending'

        admin = factories.Sysadmin()
        pending_entries = helpers.call_action(
            'ckanext_pages_list',
            {'user': admin['name']},
            page_type='open-source-software',
            submission_status='pending',
        )
        pending_names = [item['name'] for item in pending_entries]
        assert slug in pending_names

    def test_ai_water_tools_summary_counts_use_full_filtered_result_set(self, app):
        admin = factories.Sysadmin()
        env = {'REMOTE_USER': admin['name'].encode('ascii')}

        for idx in range(22):
            helpers.call_action(
                'ckanext_pages_update',
                {'user': admin['name']},
                name='ai-tool-{0}'.format(idx),
                page='ai-tool-{0}'.format(idx),
                title='AI Tool {0}'.format(idx),
                content='AI tool content {0}'.format(idx),
                page_type='ai-water-tools',
                private=False,
                submission_status='approved',
                maturity_level='research' if idx < 7 else 'production',
                access_type='open-source' if idx < 8 else 'proprietary',
            )

        response = app.get(
            toolkit.url_for('pages.ai_water_tools_index') + '?page=2',
            status=200,
            extra_environ=env,
        )

        assert 'AI Tool 21' in response.body
        assert re.search(
            r'<div class="metric-number">\s*22\s*</div>\s*<div class="metric-label">Total Tools</div>',
            response.body,
        )
        assert re.search(
            r'<div class="metric-number">\s*7\s*</div>\s*<div class="metric-label">Research Stage</div>',
            response.body,
        )
        assert re.search(
            r'<div class="metric-number">\s*15\s*</div>\s*<div class="metric-label">Production Stage</div>',
            response.body,
        )
        assert re.search(
            r'<div class="metric-number">\s*8\s*</div>\s*<div class="metric-label">Open Source</div>',
            response.body,
        )

    def test_non_admin_publish_request_is_converted_to_pending_for_water_news(self, app):
        submitter = factories.User()
        env = {'REMOTE_USER': submitter['name'].encode('ascii')}
        slug = 'pending-water-news'

        app.post(
            toolkit.url_for('pages.water_news_new'),
            params={
                'title': 'Pending Water News',
                'name': slug,
                'content': 'Water news content awaiting review.',
                'excerpt': 'Short summary',
                'publish_date': '2025-01-01',
                'submission_action': 'publish',
            },
            extra_environ=env,
            status=302,
        )

        page = helpers.call_action(
            'ckanext_pages_show', {'user': submitter['name']}, page=slug
        )
        assert page['submission_status'] == 'pending'
        assert page['private'] in (True, 'True', 'true', 1)

    def test_water_news_show_renders_uploaded_gallery_and_associations(self, app):
        admin = factories.Sysadmin()
        env = {'REMOTE_USER': admin['name'].encode('ascii')}
        slug = 'water-news-gallery'

        app.post(
            toolkit.url_for('pages.water_news_new'),
            params={
                'title': 'Water News Gallery',
                'name': slug,
                'content': 'Water news content with gallery.',
                'excerpt': 'Short summary',
                'publish_date': '2025-01-01',
                'submission_action': 'publish',
                'uploaded_images': json.dumps([
                    {
                        'url': 'https://example.com/gallery-image.jpg',
                        'alt': 'Gallery image',
                        'caption': 'Gallery caption'
                    }
                ]),
                'country_groups': json.dumps([{'name': 'chile'}]),
                'initiative_groups': json.dumps([{'name': 'crida'}]),
            },
            extra_environ=env,
            status=302,
        )

        response = app.get(
            toolkit.url_for('pages.water_news_show', page=slug),
            extra_environ=env,
            status=200,
        )

        assert 'https://example.com/gallery-image.jpg' in response.body
        assert 'Gallery caption' in response.body
        assert 'Member States &amp; Initiatives' in response.body
        assert 'Chile' in response.body
        assert 'Crida' in response.body
        assert '/memberstates/chile' in response.body
        assert '/initiatives/crida' in response.body

    def test_water_events_show_renders_uploaded_gallery_and_associations(self, app):
        admin = factories.Sysadmin()
        env = {'REMOTE_USER': admin['name'].encode('ascii')}
        slug = 'water-events-gallery'

        app.post(
            toolkit.url_for('pages.water_events_new'),
            params={
                'title': 'Water Events Gallery',
                'name': slug,
                'content': 'Water event content with gallery.',
                'publish_date': '2025-01-01',
                'submission_action': 'publish',
                'uploaded_images': json.dumps([
                    {
                        'url': 'https://example.com/event-gallery-image.jpg',
                        'alt': 'Event gallery image',
                        'caption': 'Event gallery caption'
                    }
                ]),
                'country_groups': json.dumps([{'name': 'chile'}]),
                'initiative_groups': json.dumps([{'name': 'crida'}]),
            },
            extra_environ=env,
            status=302,
        )

        response = app.get(
            toolkit.url_for('pages.water_events_show', page=slug),
            extra_environ=env,
            status=200,
        )

        assert 'https://example.com/event-gallery-image.jpg' in response.body
        assert 'Event gallery caption' in response.body
        assert 'Member States &amp; Initiatives' in response.body
        assert 'Chile' in response.body
        assert 'Crida' in response.body
        assert '/memberstates/chile' in response.body
        assert '/initiatives/crida' in response.body

    def test_water_events_agenda_upload_validation_accepts_images(self):
        from ckanext.pages import actions

        class DummyUpload(object):
            filename = 'agenda-flyer.png'

        result = actions._validate_water_file(
            {'upload': DummyUpload(), 'asset_role': 'agenda_document'},
            'water-events',
            'image',
            asset_role='agenda_document',
        )

        assert result['valid'] is True
        assert result['max_size_mb'] == 20
        assert 'pdf' in result['allowed_extensions']
        assert 'png' in result['allowed_extensions']

    def test_water_publications_show_renders_image_preview_and_dataset_link(self, app):
        admin = factories.Sysadmin()
        slug = 'water-publication-image-preview'

        helpers.call_action(
            'ckanext_pages_update',
            {'user': admin['name']},
            name=slug,
            page=slug,
            title='Water Publication Image Preview',
            content='Publication content with image resource.',
            page_type='water-publications',
            download_url='https://example.com/resources/publication-preview.png',
            document_format='png',
            document_mimetype='image/png',
            dataset_title='Publication Dataset',
            associated_dataset_url='https://example.com/dataset/publication-dataset',
            private=False,
            submission_status='approved',
        )

        env = {'REMOTE_USER': admin['name'].encode('ascii')}
        response = app.get(
            toolkit.url_for('pages.water_publications_show', page=slug),
            extra_environ=env,
            status=200,
        )

        assert 'https://example.com/resources/publication-preview.png' in response.body
        assert 'https://example.com/dataset/publication-dataset' in response.body
        assert 'Publication Dataset' in response.body

    def test_water_publications_show_recovers_dataset_links_when_download_url_is_blank(self, app):
        admin = factories.Sysadmin()
        slug = 'water-publication-recovered-links'

        dataset = helpers.call_action(
            'package_create',
            {'user': admin['name']},
            name='document-recovered-publication',
            title='Recovered Publication',
        )

        helpers.call_action(
            'resource_create',
            {'user': admin['name']},
            package_id=dataset['id'],
            url='https://example.com/resources/recovered-publication.pdf',
            format='PDF',
            name='Recovered publication PDF',
        )

        helpers.call_action(
            'ckanext_pages_update',
            {'user': admin['name']},
            name=slug,
            page=slug,
            title='Recovered Publication',
            content='Publication content with recovered dataset links.',
            page_type='water-publications',
            download_url='',
            publication_url='',
            dataset_url='',
            associated_dataset_url='',
            dataset_title='Recovered Publication',
            document_format='pdf',
            document_mimetype='application/pdf',
            private=False,
            submission_status='approved',
        )

        env = {'REMOTE_USER': admin['name'].encode('ascii')}
        response = app.get(
            toolkit.url_for('pages.water_publications_show', page=slug),
            extra_environ=env,
            status=200,
        )

        assert 'https://example.com/resources/recovered-publication.pdf' in response.body
        assert '/dataset/document-recovered-publication' in response.body

    def test_open_source_admin_dashboard_shows_organization_labels(self, app):
        sysadmin = factories.Sysadmin()
        org = factories.Organization()

        helpers.call_action(
            'ckanext_pages_update',
            {'user': sysadmin['name']},
            name='pending-admin-view',
            page='pending-admin-view',
            title='Pending Admin Entry',
            content='Pending content awaiting approval.',
            page_type='open-source-software',
            submission_status='pending',
            private=True,
            ihp_organization=org['id'],
            submitted_at=datetime.datetime.utcnow().isoformat(),
        )

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        response = app.get(
            toolkit.url_for('pages.open_source_admin_dashboard'),
            status=200,
            extra_environ=env,
        )

        assert org['title'] in response.body
        assert f'value="{org["id"]}"' in response.body

        sysadmin_data = helpers.call_action('user_show', {'ignore_auth': True}, id=sysadmin['name'])
        expected_display = sysadmin_data.get('fullname') or sysadmin_data.get('display_name') or sysadmin_data['name']

        assert expected_display in response.body
        assert sysadmin_data['id'] not in response.body

    def test_water_admin_approve_route_sets_workflow_metadata(self, app):
        sysadmin = factories.Sysadmin()
        slug = 'pending-water-approve'

        helpers.call_action(
            'ckanext_pages_update',
            {'user': sysadmin['name']},
            name=slug,
            page=slug,
            title='Pending Water Entry',
            content='Pending water content.',
            page_type='water-news',
            submission_status='pending',
            private=True,
            submitted_at=datetime.datetime.utcnow().isoformat(),
        )

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        response = app.post(
            toolkit.url_for('pages.water_admin_approve', page_type='water-news', page=slug),
            status=302,
            extra_environ=env,
        )
        assert response.status_code == 302

        page = helpers.call_action('ckanext_pages_show', {}, page=slug)
        assert page['submission_status'] == 'approved'
        assert page['private'] is False
        assert page['reviewed_by'] == sysadmin['name']
        assert page['reviewed_at'] is not None
        assert page['submitted_at'] is not None

    def test_open_source_admin_approve_route_publishes_entry(self, app):
        sysadmin = factories.Sysadmin()

        helpers.call_action(
            'ckanext_pages_update',
            {'user': sysadmin['name']},
            name='approve-route-tool',
            page='approve-route-tool',
            title='Pending Admin Route',
            content='Pending entry for route test.',
            page_type='open-source-software',
            submission_status='pending',
            private=True,
            ihp_organization=None,
            submitted_at=datetime.datetime.utcnow().isoformat(),
        )

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}

        response = app.post(
            toolkit.url_for('pages.open_source_admin_approve', page='approve-route-tool'),
            status=302,
            extra_environ=env,
        )
        assert response.status_code == 302

        page = helpers.call_action('ckanext_pages_show', {}, page='approve-route-tool')
        assert page['submission_status'] == 'approved'
        assert page['private'] is False
        assert page['reviewed_by'] == sysadmin['name']

        pending_entries = helpers.call_action(
            'ckanext_pages_list',
            {'user': sysadmin['name']},
            page_type='open-source-software',
            submission_status='pending',
        )
        names = [item['name'] for item in pending_entries]
        assert 'approve-route-tool' not in names

        public_entries = helpers.call_action(
            'ckanext_pages_list',
            {},
            page_type='open-source-software',
            submission_status='approved',
            private=False,
        )
        public_names = [item['name'] for item in public_entries]
        assert 'approve-route-tool' in public_names

    def test_open_source_admin_change_org_updates_page(self, app):
        sysadmin = factories.Sysadmin()
        original_org = factories.Organization()
        replacement_org = factories.Organization()
        slug = 'change-org-tool'

        helpers.call_action(
            'ckanext_pages_update',
            {'user': sysadmin['name']},
            name=slug,
            page=slug,
            title='Change Org Entry',
            content='Entry awaiting organization change.',
            page_type='open-source-software',
            submission_status='approved',
            private=False,
            ihp_organization=original_org['id'],
            submitted_at=datetime.datetime.utcnow().isoformat(),
        )

        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}
        response = app.post(
            toolkit.url_for('pages.open_source_admin_change_org', page=slug),
            params={'new_organization': replacement_org['id']},
            status=302,
            extra_environ=env,
        )
        assert response.status_code == 302

        page = helpers.call_action(
            'ckanext_pages_show', {'ignore_auth': True}, page=slug
        )
        assert page['ihp_organization'] == replacement_org['id']

    def test_unicode(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        page = 'test_html_page_div'
        response = app.post(
            url=toolkit.url_for('pages_edit', page=page),
            params={
                'title': u'Tïtlé'.encode('utf-8'),
                'name': 'page_unicode',
                'content': u'Çöñtéñt'.encode('utf-8'),
                'order': 1,
                'private': False,
            },
            extra_environ=env,
        )

        assert u'<p>Çöñtéñt</p>' in response.get_data(as_text=True)
        assert u'<title>Tïtlé - CKAN</title>' in response.get_data(as_text=True)
        assert u'<a href="/pages/page_unicode">Tïtlé</a>' in response.get_data(as_text=True)
        assert u'<h1 class="page-heading">Tïtlé</h1>' in response.get_data(as_text=True)

    def test_pages_saves_custom_schema_fields(self, app):
        user = factories.Sysadmin()
        context = {'user': user['name']}

        mock_schema = schema.default_pages_schema()
        mock_schema.update({
            'new_field': [toolkit.get_validator('ignore_missing')],
        })

        with mock.patch('ckanext.pages.actions.update_pages_schema', return_value=mock_schema):
            helpers.call_action(
                'ckanext_pages_update',
                context=context,
                title='Page Title',
                name='page_name',
                page='page_name',
                new_field='new_field_value',
                content='test',
            )

        pages = helpers.call_action('ckanext_pages_list', context)
        assert pages[0]['new_field'] == 'new_field_value'

    def test_water_publication_dataset_fields_in_schema(self):
        dataset_fields = [
            'dataset_title',
            'dataset_visibility',
            'dataset_url',
            'associated_dataset_url',
            'document_format',
            'document_mimetype',
            'contact_name',
            'contact_email',
            'dataset_description',
            'graphic_overview',
            'dataset_language',
            'creation_date',
            'country_groups',
        ]

        schema_dict = schema.default_pages_schema()
        missing = [field for field in dataset_fields if field not in schema_dict]

        assert not missing, f"Missing dataset fields in schema: {missing}"

    def test_water_publication_create_retries_use_latest_title_for_slug(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}

        helpers.call_action(
            'ckanext_pages_update',
            {'user': user['name']},
            name='duplicate-publication',
            page='duplicate-publication',
            title='Existing Publication',
            content='Existing content',
            page_type='water-publications',
            publication_url='https://example.com/existing.pdf',
            private=False,
            submission_status='approved',
        )

        response = app.post(
            toolkit.url_for('pages.water_publications_quick'),
            params={
                'title': 'Fresh Publication Title',
                'dataset_title': 'Fresh Publication Title',
                'name': 'duplicate-publication',
                'dataset_url': 'https://example.com/fresh.pdf',
                'publication_url': 'https://example.com/fresh.pdf',
                'submission_action': 'publish',
            },
            extra_environ=env,
            status=302,
        )

        assert 'fresh-publication-title' in response.location

        page = helpers.call_action(
            'ckanext_pages_show', {}, page='fresh-publication-title'
        )

        assert page['name'] == 'fresh-publication-title'
        assert page['title'] == 'Fresh Publication Title'
        assert page['publication_url'] == 'https://example.com/fresh.pdf'

    def test_cannot_create_page_with_same_name(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        page = 'test_page'
        response = app.post(
            url=toolkit.url_for('pages.new', page=page),
            params={
                'title': 'Page Title',
                'name': 'page_name',
                'private': False,
            },
            extra_environ=env,
        )
        assert '<h1 class="page-heading">Page Title</h1>' in response.body

        response = app.post(
            url=toolkit.url_for('pages.new', page=page),
            params={
                'title': 'Page Title',
                'name': 'page_name',
                'private': False,
            },
            extra_environ=env,
        )

        assert '<div class="flash-messages">' in response.body
        assert 'Page name already exists' in response.body

    def test_revisions_page(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}

        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            name="page_name",
            title="New Page",
            content="This is a test content",
        )

        response = app.get(
            toolkit.url_for('pages.pages_revisions', page="page_name"),
            status=200, extra_environ=env)

        assert '<span class="badge badge-inverse">Active Revision</span>' in response.body

        response = app.get(
            toolkit.url_for('pages.pages_revisions', page="page_name1"),
            status=404, extra_environ=env)

        assert '404 Not Found' in response.body

        if toolkit.check_ckan_version(min_version="2.10.0"):
            response = app.get(
                toolkit.url_for('pages.pages_revisions', page="page_name"),
                status=401)

            assert '<h1>401 Unauthorized</h1>' in response.body
        else:
            response = app.get(
                toolkit.url_for('pages.pages_revisions', page="page_name")
            )
            assert '<h1 class="page-heading">Login</h1>' in response.body

    def test_revision_preview_page(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}

        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            name="page_name",
            title="New Page",
            content="This is a test content",
        )

        page = helpers.call_action("ckanext_pages_show", {}, page="page_name")

        revision_id = [i for i in page['revisions']][0]

        response = app.get(
            toolkit.url_for(
                'pages.pages_revisions_preview',
                page="page_name",
                revision=revision_id),
            status=200, extra_environ=env)

        assert '<p>This is a test content</p>' in response.body

        response = app.get(
            toolkit.url_for(
                'pages.pages_revisions_preview',
                page="page_name",
                revision=revision_id + '1'),
            status=404, extra_environ=env)

        assert '404 Not Found' in response.body

        if toolkit.check_ckan_version(min_version="2.10.0"):
            response = app.get(
                toolkit.url_for(
                    'pages.pages_revisions_preview',
                    page="page_name",
                    revision=revision_id),
                status=401)

            assert '<h1>401 Unauthorized</h1>' in response.body
        else:
            response = app.get(
                toolkit.url_for(
                    'pages.pages_revisions_preview',
                    page="page_name",
                    revision=revision_id),
            )
            assert '<h1 class="page-heading">Login</h1>' in response.body

    def test_revision_restore_page(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}

        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            name="page_name",
            title="New Page",
            content="This is a test content",
        )

        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            name="page_name",
            title="New Page Updated",
            content="This is a test content updated",
            page="page_name",
        )

        page = helpers.call_action("ckanext_pages_show", {}, page="page_name")

        assert page['content'] == 'This is a test content updated'

        revisions = page['revisions']

        sorted_revisions = OrderedDict(reversed(sorted(
                revisions.items(),
                key=lambda x: datetime.datetime.timestamp(
                    datetime.datetime.fromisoformat(x[1]['created'])
                    )
        )))

        last_revision = sorted_revisions.popitem()
        response = app.get(
            toolkit.url_for(
                'pages.pages_revision_restore',
                page="page_name",
                revision=last_revision[0]),
            status=200, extra_environ=env)

        assert 'Content from revision created on' in response.body

        response = app.get(
            toolkit.url_for(
                'pages.pages_revision_restore',
                page="page_name",
                revision=last_revision[0] + '1'),
            status=200, extra_environ=env)

        assert 'Bad values, please make sure that provided values exist' in response.body

        if toolkit.check_ckan_version(min_version="2.10.0"):
            response = app.get(
                toolkit.url_for(
                    'pages.pages_revision_restore',
                    page="page_name",
                    revision=last_revision[0]),
                status=401)

            assert '<h1>401 Unauthorized</h1>' in response.body
        else:
            response = app.get(
                toolkit.url_for(
                    'pages.pages_revision_restore',
                    page="page_name",
                    revision=last_revision[0]),
            )

            assert '<h1 class="page-heading">Login</h1>' in response.body

    def test_revisions_blog(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}

        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            name="blog_name",
            title="New Blog",
            content="This is a test content",
            page_type="blog",
            publish_date="2024-10-15"
        )

        response = app.get(
            toolkit.url_for('pages.blog_revisions', page="blog_name"),
            status=200, extra_environ=env)

        assert '<span class="badge badge-inverse">Active Revision</span>' in response.body

        response = app.get(
            toolkit.url_for('pages.blog_revisions', page="blog_name1"),
            status=404, extra_environ=env)

        assert '404 Not Found' in response.body

        if toolkit.check_ckan_version(min_version="2.10.0"):
            response = app.get(
                toolkit.url_for('pages.blog_revisions', page="blog_name"),
                status=401)

            assert '<h1>401 Unauthorized</h1>' in response.body
        else:
            response = app.get(
                toolkit.url_for('pages.blog_revisions', page="blog_name"),
            )

            assert '<h1 class="page-heading">Login</h1>' in response.body

    def test_revision_preview_blog(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}

        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            name="blog_name",
            title="New Blog",
            content="This is a test content",
            page_type="blog",
            publish_date="2024-10-15"
        )

        page = helpers.call_action("ckanext_pages_show", {}, page="blog_name")

        revision_id = [i for i in page['revisions']][0]

        response = app.get(
            toolkit.url_for(
                'pages.blog_revisions_preview',
                page="blog_name",
                revision=revision_id),
            status=200, extra_environ=env)

        assert '<p>This is a test content</p>' in response.body

        response = app.get(
            toolkit.url_for(
                'pages.blog_revisions_preview',
                page="blog_name",
                revision=revision_id + '1'),
            status=404, extra_environ=env)

        assert '404 Not Found' in response.body

        if toolkit.check_ckan_version(min_version="2.10.0"):
            response = app.get(
                toolkit.url_for(
                    'pages.blog_revisions_preview',
                    page="blog_name",
                    revision=revision_id),
                status=401)

            assert '<h1>401 Unauthorized</h1>' in response.body
        else:
            response = app.get(
                toolkit.url_for(
                    'pages.blog_revisions_preview',
                    page="blog_name",
                    revision=revision_id),
            )
            assert '<h1 class="page-heading">Login</h1>' in response.body

    def test_revision_restore_blog(self, app):
        user = factories.Sysadmin()
        env = {'REMOTE_USER': user['name'].encode('ascii')}

        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            name="blog_name",
            title="New Blog",
            content="This is a test content",
            page_type="blog",
            publish_date="2024-10-15"
        )

        helpers.call_action(
            "ckanext_pages_update",
            {"user": user["name"]},
            name="blog_name",
            title="New Blog Updated",
            content="This is a test content updated",
            page="blog_name",
            page_type="blog",
            publish_date="2024-10-15"
        )

        page = helpers.call_action("ckanext_pages_show", {}, page="blog_name")

        assert page['content'] == 'This is a test content updated'

        revisions = page['revisions']

        sorted_revisions = OrderedDict(reversed(sorted(
                revisions.items(),
                key=lambda x: datetime.datetime.timestamp(
                    datetime.datetime.fromisoformat(x[1]['created'])
                    )
        )))

        last_revision = sorted_revisions.popitem()

        response = app.get(
            toolkit.url_for(
                'pages.blog_revision_restore',
                page="blog_name",
                revision=last_revision[0]),
            status=200, extra_environ=env)

        assert 'Content from revision created on' in response.body

        response = app.get(
            toolkit.url_for(
                'pages.blog_revision_restore',
                page="blog_name",
                revision=last_revision[0] + '1'),
            status=200, extra_environ=env)

        assert 'Bad values, please make sure that provided values exist' in response.body

        if toolkit.check_ckan_version(min_version="2.10.0"):
            response = app.get(
                toolkit.url_for(
                    'pages.blog_revision_restore',
                    page="blog_name",
                    revision=last_revision[0]),
                status=401)

            assert '<h1>401 Unauthorized</h1>' in response.body
        else:
            response = app.get(
                toolkit.url_for(
                    'pages.blog_revision_restore',
                    page="blog_name",
                    revision=last_revision[0]),
            )

            assert '<h1 class="page-heading">Login</h1>' in response.body
