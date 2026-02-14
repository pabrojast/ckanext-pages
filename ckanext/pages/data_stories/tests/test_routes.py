# encoding: utf-8
"""
Tests for data stories routes.
"""

import pytest

from ckan.plugins import toolkit
from ckan.tests import factories, helpers


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryRoutes:
    def test_import_route_is_available_for_sysadmins(self, app):
        sysadmin = factories.Sysadmin()
        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}

        url = toolkit.url_for('data_stories.import_story')
        response = app.get(url, status=200, extra_environ=env)

        assert 'name="import_file"' in response.body

    def test_org_admin_can_access_pending_review_from_list(self, app):
        sysadmin = factories.Sysadmin()
        reviewer = factories.User()
        org = factories.Organization()

        helpers.call_action(
            'member_create',
            {'user': sysadmin['name']},
            id=org['id'],
            object=reviewer['id'],
            object_type='user',
            capacity='admin',
        )

        reviewer_env = {'REMOTE_USER': reviewer['name'].encode('ascii')}

        list_response = app.get(
            toolkit.url_for('data_stories.index'),
            status=200,
            extra_environ=reviewer_env,
        )
        assert toolkit.url_for('data_stories.pending_review') in list_response.body
        assert 'Pending Review' in list_response.body

        pending_response = app.get(
            toolkit.url_for('data_stories.pending_review'),
            status=200,
            extra_environ=reviewer_env,
        )
        assert 'Stories Pending Review' in pending_response.body
