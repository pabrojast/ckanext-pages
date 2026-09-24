"""Real CKAN actions, database, permissions and authenticated form round trips."""
import copy
import json
from html import unescape
import re

import pytest
from ckan.plugins import toolkit as tk
from ckan.tests import factories, helpers

from ckanext.pages import db
from ckanext.pages.rapid_response_story import story_for_page


@pytest.mark.usefixtures('with_plugins', 'clean_db')
@pytest.mark.ckan_config('ckan.plugins', 'pages')
@pytest.mark.ckan_config('ckanext.data_stories.enabled', False)
class TestRapidResponseStoryIntegration:
    def create(self, user):
        helpers.call_action('ckanext_pages_update', {'user': user['name']},
                            name='emergency-story', title='Emergency story',
                            page_type='rapid-response', private=False,
                            content='<p>Original context</p>',
                            impact_assessment='<p>Original impact</p>',
                            publish_date='2026-09-24', timeline_events='[]')
        return helpers.call_action('ckanext_pages_show', {}, page='emergency-story')

    def save(self, user, story):
        helpers.call_action('ckanext_pages_update', {'user': user['name']},
                            page='emergency-story', name='emergency-story',
                            title='Emergency story', page_type='rapid-response',
                            rapid_response_story=json.dumps(story), private=False)
        return helpers.call_action('ckanext_pages_show', {}, page='emergency-story')

    def test_document_action_roundtrip_revisions_and_legacy_api(self, app):
        user = factories.Sysadmin()
        original = self.create(user)
        story = story_for_page(original)
        saved = self.save(user, story)
        assert saved['rapid_response_story'] == story
        assert saved['impact_assessment'] == original['impact_assessment']
        page = db.Page.get(name='emergency-story')
        revision_id = next(key for key, revision in page.revisions.items() if revision.get('current'))
        full_revision = copy.deepcopy(page.revisions[revision_id])
        assert full_revision['rapid_response']['rapid_response_story'] == story
        self.save(user, dict(story, sections=[]))
        helpers.call_action('ckanext_pages_revision_restore', {'user': user['name']},
                            page='emergency-story', revision=revision_id)
        restored = helpers.call_action('ckanext_pages_show', {}, page='emergency-story')
        assert restored['rapid_response_story'] == story
        helpers.call_action('ckanext_pages_update', {'user': user['name']},
                            page='emergency-story', name='emergency-story', title='Emergency story',
                            content='<p>Updated through older client</p>')
        changed = helpers.call_action('ckanext_pages_show', {}, page='emergency-story')
        context_block = changed['rapid_response_story']['sections'][0]['blocks_metadata'][0]
        assert context_block['content'] == '<p>Updated through older client</p>'
        assert changed['rapid_response_story']['sections'][1] == story['sections'][1]

    def test_malformed_document_leaves_database_unchanged(self, app):
        user = factories.Sysadmin()
        original = self.create(user)
        story = story_for_page(original)
        story['sections'][1]['id'] = story['sections'][0]['id']
        with pytest.raises(tk.ValidationError):
            self.save(user, story)
        after = helpers.call_action('ckanext_pages_show', {}, page='emergency-story')
        assert after['content'] == original['content']
        assert 'rapid_response_story' not in after

    def test_linked_datasets_use_canonical_ids_and_reader_permissions(self, app):
        user = factories.Sysadmin()
        original = self.create(user)
        organization = factories.Organization(user=user)
        public = factories.Dataset(owner_org=organization['id'], user=user)
        private = factories.Dataset(owner_org=organization['id'], private=True, user=user)
        story = story_for_page(original)
        story['datasets'] = [{'id': public['name']}, {'id': private['name']}]
        saved = self.save(user, story)
        assert saved['rapid_response_story']['datasets'] == [{'id': public['id']}, {'id': private['id']}]
        from ckanext.pages.rapid_response_story import readable_datasets
        assert [d['id'] for d in readable_datasets(saved['rapid_response_story'], {'user': ''})] == [public['id']]

    def test_authenticated_form_save_reload_and_public_view_without_data_stories(self, app):
        user = factories.Sysadmin()
        original = self.create(user)
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get('/rapid-response_edit/emergency-story', extra_environ=env)
        assert response.status_code == 200
        html = response.body.decode() if isinstance(response.body, bytes) else response.body
        value = re.search(r'<textarea[^>]*id="rr-story-json"[^>]*>(.*?)</textarea>', html, re.S).group(1)
        story = json.loads(unescape(value))
        response = app.post('/rapid-response_edit/emergency-story', params={
            'name': 'emergency-story', 'title': 'Emergency story', 'publish_date': '2026-09-24',
            'private': 'false', 'rapid_response_story': json.dumps(story), 'save': '',
        }, extra_environ=env)
        assert response.status_code in (200, 302)
        saved = helpers.call_action('ckanext_pages_show', {}, page='emergency-story')
        assert saved['rapid_response_story'] == story
        assert saved['content'] == original['content']
        response = app.get('/rapid-response/emergency-story')
        assert response.status_code == 200
        html = response.body.decode() if isinstance(response.body, bytes) else response.body
        assert 'storymap-config' in html and 'Original impact' in html
        response = app.get('/rapid-response_edit/emergency-story', extra_environ=env)
        assert response.status_code == 200
