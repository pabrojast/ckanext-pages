# encoding: utf-8
"""
Tests for Data Stories authorization.
"""

import pytest

from ckan import model
from ckan.tests import factories, helpers
from ckan.plugins import toolkit

from ckanext.pages.data_stories.db.utils import init_tables


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryAuth:
    """Tests for story authorization."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_anyone_can_create_story(self):
        """Test that any authenticated user can create a story."""
        user = factories.User()

        # Should succeed
        result = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='New Story',
        )

        assert result['author_id'] == user['id']

    def test_anonymous_cannot_create_story(self):
        """Test that anonymous users cannot create stories."""
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action(
                'data_story_create',
                context={'user': None},
                title='Anonymous Story',
            )

    def test_author_can_update_own_story(self):
        """Test that authors can update their own stories."""
        user = factories.User()

        # Create story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='My Story',
        )

        # Update should succeed
        updated = helpers.call_action(
            'data_story_update',
            context={'user': user['name']},
            id=story['id'],
            title='Updated Story',
        )

        assert updated['title'] == 'Updated Story'

    def test_other_user_cannot_update_story(self):
        """Test that other users cannot update someone else's story."""
        author = factories.User()
        other_user = factories.User()

        # Create story as author
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Authors Story',
        )

        # Try to update as other user (should fail)
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action(
                'data_story_update',
                context={'user': other_user['name']},
                id=story['id'],
                title='Hacked Story',
            )

    def test_sysadmin_can_update_any_story(self):
        """Test that sysadmins can update any story."""
        author = factories.User()
        sysadmin = factories.Sysadmin()

        # Create story as regular user
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='User Story',
        )

        # Sysadmin should be able to update
        updated = helpers.call_action(
            'data_story_update',
            context={'user': sysadmin['name']},
            id=story['id'],
            title='Sysadmin Updated',
        )

        assert updated['title'] == 'Sysadmin Updated'

    def test_author_can_delete_own_draft(self):
        """Test that authors can delete their own draft stories."""
        user = factories.User()

        # Create draft story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Draft to Delete',
        )

        # Delete should succeed
        helpers.call_action(
            'data_story_delete',
            context={'user': user['name']},
            id=story['id'],
        )

        # Verify deleted
        with pytest.raises(toolkit.ObjectNotFound):
            helpers.call_action('data_story_show', id=story['id'])

    def test_author_cannot_delete_published_story(self):
        """Test that authors cannot delete published stories."""
        user = factories.User()

        # Create and publish story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Published Story',
        )

        # Manually set to published
        from ckanext.pages.data_stories.db.models import DataStory
        story_obj = model.Session.query(DataStory).filter_by(id=story['id']).first()
        story_obj.status = 'published'
        model.Session.commit()

        # Try to delete (should fail)
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action(
                'data_story_delete',
                context={'user': user['name']},
                id=story['id'],
            )

    def test_author_can_submit_own_story(self):
        """Test that authors can submit their own stories."""
        user = factories.User()

        # Create story with required sections
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story to Submit',
        )

        # Add required sections
        for section_type in ['introduction', 'data_sources', 'methodology',
                            'spatial_analysis', 'conclusions']:
            helpers.call_action(
                'data_story_section_create',
                context={'user': user['name']},
                story_id=story['id'],
                section_type=section_type,
                content=f'Content for {section_type}',
            )

        # Submit should succeed
        updated = helpers.call_action(
            'data_story_submit',
            context={'user': user['name']},
            id=story['id'],
        )

        assert updated['status'] == 'submitted'

    def test_author_can_link_datasets(self):
        """Test that authors can link datasets to their stories."""
        user = factories.User()
        dataset = factories.Dataset(user=user)

        # Create story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story',
        )

        # Link dataset should succeed
        link = helpers.call_action(
            'data_story_dataset_link',
            context={'user': user['name']},
            story_id=story['id'],
            dataset_id=dataset['id'],
            relationship_type='primary',
        )

        assert link['dataset_id'] == dataset['id']

    def test_user_cannot_link_private_dataset(self):
        """Test that users cannot link datasets they don't have access to."""
        author = factories.User()
        other_user = factories.User()
        org = factories.Organization(users=[{'name': other_user['name'], 'capacity': 'editor'}])

        # Create private dataset owned by other user
        dataset = factories.Dataset(
            user=other_user,
            owner_org=org['id'],
            private=True,
        )

        # Create story
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Story',
        )

        # Try to link private dataset (should fail)
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action(
                'data_story_dataset_link',
                context={'user': author['name']},
                story_id=story['id'],
                dataset_id=dataset['id'],
                relationship_type='primary',
            )

    def test_anyone_can_view_published_story(self):
        """Test that anyone can view published stories."""
        author = factories.User()
        viewer = factories.User()

        # Create and publish story
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Public Story',
        )

        # Manually set to published
        from ckanext.pages.data_stories.db.models import DataStory
        story_obj = model.Session.query(DataStory).filter_by(id=story['id']).first()
        story_obj.status = 'published'
        model.Session.commit()

        # Any user should be able to view
        result = helpers.call_action(
            'data_story_show',
            context={'user': viewer['name']},
            id=story['id'],
        )

        assert result['id'] == story['id']

        # Even anonymous should be able to view
        result_anon = helpers.call_action(
            'data_story_show',
            context={'user': None},
            id=story['id'],
        )

        assert result_anon['id'] == story['id']

    def test_only_author_can_view_draft_story(self):
        """Test that only authors can view their draft stories."""
        author = factories.User()
        other_user = factories.User()

        # Create draft story
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Private Draft',
        )

        # Author should be able to view
        result = helpers.call_action(
            'data_story_show',
            context={'user': author['name']},
            id=story['id'],
        )

        assert result['id'] == story['id']

        # Other user should not be able to view
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action(
                'data_story_show',
                context={'user': other_user['name']},
                id=story['id'],
            )

    def test_users_can_comment_on_stories(self):
        """Test that users can comment on stories."""
        author = factories.User()
        commenter = factories.User()

        # Create and publish story
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Story',
        )

        # Any user should be able to comment
        comment = helpers.call_action(
            'data_story_comment_create',
            context={'user': commenter['name']},
            story_id=story['id'],
            comment_text='Great story!',
        )

        assert comment['user_id'] == commenter['id']

    def test_comment_author_can_edit_own_comment(self):
        """Test that comment authors can edit their own comments."""
        author = factories.User()
        commenter = factories.User()

        # Create story and comment
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Story',
        )

        comment = helpers.call_action(
            'data_story_comment_create',
            context={'user': commenter['name']},
            story_id=story['id'],
            comment_text='Original comment',
        )

        # Update comment should succeed
        updated = helpers.call_action(
            'data_story_comment_update',
            context={'user': commenter['name']},
            id=comment['id'],
            comment_text='Updated comment',
        )

        assert updated['comment_text'] == 'Updated comment'

    def test_user_cannot_edit_others_comment(self):
        """Test that users cannot edit other people's comments."""
        author = factories.User()
        commenter = factories.User()
        other_user = factories.User()

        # Create story and comment
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Story',
        )

        comment = helpers.call_action(
            'data_story_comment_create',
            context={'user': commenter['name']},
            story_id=story['id'],
            comment_text='Original comment',
        )

        # Try to update as other user (should fail)
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action(
                'data_story_comment_update',
                context={'user': other_user['name']},
                id=comment['id'],
                comment_text='Hacked comment',
            )


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestOrganizationAuth:
    """Tests for organization-based authorization."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_org_admin_can_update_org_stories(self):
        """Test that organization admins can update stories from their org."""
        org = factories.Organization()
        admin = factories.User()
        member = factories.User()

        # Add users to org
        helpers.call_action(
            'member_create',
            id=org['id'],
            object=admin['id'],
            object_type='user',
            capacity='admin',
        )

        helpers.call_action(
            'member_create',
            id=org['id'],
            object=member['id'],
            object_type='user',
            capacity='member',
        )

        # Member creates story
        story = helpers.call_action(
            'data_story_create',
            context={'user': member['name']},
            title='Org Story',
            organization_id=org['id'],
        )

        # Admin should be able to update
        updated = helpers.call_action(
            'data_story_update',
            context={'user': admin['name']},
            id=story['id'],
            title='Admin Updated',
        )

        assert updated['title'] == 'Admin Updated'

    def test_non_org_member_cannot_update_org_story(self):
        """Test that users outside org cannot update org stories."""
        org = factories.Organization()
        member = factories.User()
        outsider = factories.User()

        # Add member to org
        helpers.call_action(
            'member_create',
            id=org['id'],
            object=member['id'],
            object_type='user',
            capacity='member',
        )

        # Member creates org story
        story = helpers.call_action(
            'data_story_create',
            context={'user': member['name']},
            title='Org Story',
            organization_id=org['id'],
        )

        # Outsider should not be able to update
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action(
                'data_story_update',
                context={'user': outsider['name']},
                id=story['id'],
                title='Hacked',
            )
