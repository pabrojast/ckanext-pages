"""Initiative associations through the real Water Family forms and readers."""

import json

import pytest
from bs4 import BeautifulSoup
from ckan import model
from ckan.plugins import toolkit
from ckan.tests import factories, helpers

from ckanext.pages.db import Page
from ckanext.pages.plugin import get_pages_by_initiative


@pytest.mark.usefixtures('with_plugins', 'clean_db')
@pytest.mark.ckan_config('ckan.plugins', 'pages')
@pytest.mark.ckan_config('ckanext.data_stories.enabled', False)
class TestWaterFamilyInitiatives:
    @pytest.mark.parametrize('kind', ['news', 'events'])
    @pytest.mark.parametrize('admin', [True, False])
    def test_form_associations_round_trip(self, app, kind, admin):
        user = factories.Sysadmin() if admin else factories.User()
        organization = factories.Organization(
            users=[{'name': user['id'], 'capacity': 'admin'}])
        first = factories.Group(name='be-resilient', title='Be Resilient')
        second = factories.Group(name='riverwatch', title='Riverwatch')
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        create_url = toolkit.url_for('pages.water_%s_new' % kind)

        response = app.get(create_url, extra_environ=env, status=200)
        soup = BeautifulSoup(response.body, 'html.parser')
        selector = soup.select_one('#initiative-select')
        assert len(soup.select('#initiative-select')) == 1
        assert len(soup.select('[name="initiative_groups"]')) == 1
        assert selector.find_parent(class_='row') == soup.select_one(
            '#field-ihp-organization').find_parent(class_='row')
        assert selector.find_parent('fieldset') == soup.select_one('fieldset')
        assert {o.get('value') for o in selector.select('option')} >= {
            first['name'], second['name']}

        slug = 'initiative-%s-%s' % (kind, 'admin' if admin else 'editor')
        payload = {
            'title': 'Initiative content', 'name': slug,
            'content': 'Content linked to initiatives.', 'excerpt': 'Summary',
            'publish_date': '2026-10-09',
            'ihp_organization': organization['id'],
            'private': 'False', 'submission_action': 'publish',
            'initiative_groups': json.dumps([
                {'name': first['name']}, {'name': second['name']}]),
        }
        app.post(create_url, params=payload, extra_environ=env, status=302,
                 follow_redirects=False)
        edit_url = toolkit.url_for('pages.water_%s_edit' % kind, page=slug)

        selections = ([first['name'], second['name']], [second['name']], [])
        for selected in selections:
            if len(selected) < 2:
                payload['initiative_groups'] = json.dumps([
                    {'name': name} for name in selected])
                app.post(edit_url, params=payload, extra_environ=env,
                         status=302, follow_redirects=False)
            response = app.get(edit_url, extra_environ=env, status=200)
            soup = BeautifulSoup(response.body, 'html.parser')
            stored = json.loads(soup.select_one('#initiative_groups')['value'])
            assert stored == [{'name': name} for name in selected]
            page = Page.get(name=slug)
            assert page.ihp_organization == organization['id']
            expected_status = 'approved' if admin else 'pending'
            assert page.submission_status == expected_status
            for initiative in (first['name'], second['name']):
                expected = [slug] if admin and initiative in selected else []
                result = get_pages_by_initiative(initiative, 'water-' + kind)
                assert [item['name'] for item in result] == expected
                api = helpers.call_action('ckanext_water_family_list', {},
                                          initiative=initiative,
                                          page_type='water-' + kind)
                assert [item['name'] for item in api['results']] == expected

    @pytest.mark.parametrize('kind', ['news', 'events'])
    def test_empty_catalog_is_optional(self, app, kind):
        user = factories.Sysadmin()
        response = app.get(toolkit.url_for('pages.water_%s_new' % kind),
                           extra_environ={'REMOTE_USER': user['name']},
                           status=200)
        soup = BeautifulSoup(response.body, 'html.parser')
        assert 'No initiatives available' in soup.select_one(
            '#initiative-select').text
        assert soup.select_one('#initiative_groups')['value'] == '[]'
        assert not soup.select_one('#initiative-select').has_attr('required')

    @pytest.mark.parametrize('kind', ['news', 'events', 'publications'])
    def test_reader_legacy_json_and_publication_status(self, app, kind):
        representations = [
            [{'name': 'be-resilient'}],
            ['be-resilient'],
            [{'id': 'be-resilient'}],
            json.dumps([{'name': 'be-resilient'}]),
            json.dumps(json.dumps([{'name': 'be-resilient'}])),
        ]
        for index, association in enumerate(representations):
            model.Session.add(Page(
                revisions={},
                name='legacy-%s' % index, title='Legacy content',
                page_type='water-' + kind, private=False,
                submission_status='approved',
                extras=json.dumps({'initiative_groups': association})))
        for status, private in [('approved', True), ('draft', False),
                                ('pending', False), ('rejected', False)]:
            model.Session.add(Page(
                revisions={},
                name='hidden-%s' % status, page_type='water-' + kind,
                private=private, submission_status=status,
                extras=json.dumps({'initiative_groups': representations[0]})))
        for index, extras in enumerate([
            'invalid JSON', '[]',
            json.dumps({'initiative_groups': {'name': 'be-resilient'}}),
            json.dumps({'initiative_groups': ['be-resilient-other']}),
            json.dumps({'country_groups': [{'name': 'be-resilient'}]}),
        ]):
            model.Session.add(Page(
                revisions={},
                name='unrelated-%s' % index, page_type='water-' + kind,
                private=False, submission_status='approved', extras=extras))
        model.Session.commit()

        result = get_pages_by_initiative('BE-RESILIENT', 'water-' + kind)
        assert {item['name'] for item in result} == {
            'legacy-%s' % i for i in range(len(representations))}
        assert [item['created'] for item in result] == sorted(
            [item['created'] for item in result], reverse=True)
        assert get_pages_by_initiative(' ', 'water-' + kind) == []
        assert get_pages_by_initiative('be-resilient', 'other-type') == []
