# encoding: utf-8
"""
Tests for data stories routes.
"""

import pytest

from ckan import model
from ckan.plugins import toolkit
from ckan.tests import factories, helpers

from ckanext.pages.data_stories.blueprint.routes import (
    _prepare_story_datasets,
    _sync_story_datasets,
)
from ckanext.pages.data_stories.db.models import DataStoryDataset
from ckanext.pages.data_stories.db.utils import init_tables


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


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestStoryDatasetFormSync:
    def test_prepares_canonical_dataset_metadata_and_deduplicates(self):
        user = factories.User()
        dataset = factories.Dataset(user=user, title='Canonical dataset')
        context = {'user': user['name']}

        prepared = _prepare_story_datasets(context, [
            {'name': dataset['name']},
            {'id': dataset['id']},
        ])

        assert len(prepared) == 1
        assert prepared[0]['id'] == dataset['id']
        assert prepared[0]['name'] == dataset['name']
        assert prepared[0]['title'] == 'Canonical dataset'
        assert prepared[0]['url'].endswith('/dataset/' + dataset['name'])

    def test_missing_dataset_is_a_form_validation_error(self):
        user = factories.User()

        with pytest.raises(toolkit.ValidationError) as error:
            _prepare_story_datasets(
                {'user': user['name']},
                [{'name': 'dataset-that-does-not-exist'}],
            )

        assert 'datasets_data' in error.value.error_dict

    def test_sync_reconciles_add_remove_and_order_in_one_commit(self):
        init_tables(model.meta.engine)
        user = factories.User()
        first = factories.Dataset(user=user, title='First')
        second = factories.Dataset(user=user, title='Second')
        context = {'user': user['name']}
        story = helpers.call_action(
            'data_story_create', context=context, title='Dataset sync story',
            slug='dataset-sync-story')

        prepared = _prepare_story_datasets(context, [
            {'id': first['id']}, {'id': second['id']},
        ])
        _sync_story_datasets(context, story['id'], prepared)
        links = model.Session.query(DataStoryDataset).filter_by(
            story_id=story['id']).order_by(DataStoryDataset.order_index).all()
        assert [link.dataset_id for link in links] == [first['id'], second['id']]

        prepared = _prepare_story_datasets(context, [{'id': second['id']}])
        _sync_story_datasets(context, story['id'], prepared)
        links = model.Session.query(DataStoryDataset).filter_by(
            story_id=story['id']).order_by(DataStoryDataset.order_index).all()
        assert [link.dataset_id for link in links] == [second['id']]
        assert links[0].order_index == 0
