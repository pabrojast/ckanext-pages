# encoding: utf-8
"""
Tests for data stories routes.
"""

import pytest

from ckan.plugins import toolkit
from ckan.tests import factories


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryRoutes:
    def test_import_route_is_available_for_sysadmins(self, app):
        sysadmin = factories.Sysadmin()
        env = {'REMOTE_USER': sysadmin['name'].encode('ascii')}

        url = toolkit.url_for('data_stories.import_story')
        response = app.get(url, status=200, extra_environ=env)

        assert 'name="import_file"' in response.body
