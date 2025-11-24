# encoding: utf-8
"""
Tests for Data Stories actions.
"""

import pytest

from ckan import model
from ckan.tests import factories, helpers
from ckan.plugins import toolkit

from ckanext.pages.data_stories.db.utils import init_tables


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryCreateActions:
    """Tests for story creation actions."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_data_story_create(self):
        """Test creating a data story."""
        user = factories.User()

        result = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Test Story',
            abstract='A test story about water data.',
            research_question='How does water flow?',
        )

        assert result['title'] == 'Test Story'
        assert result['abstract'] == 'A test story about water data.'
        assert result['author_id'] == user['id']
        assert result['status'] == 'draft'
        assert 'slug' in result

    def test_data_story_create_with_countries(self):
        """Test creating a story with countries metadata."""
        user = factories.User()

        countries = [
            {'name': 'France', 'display_name': 'France'},
            {'name': 'Spain', 'display_name': 'Spain'},
        ]

        result = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story With Countries',
            countries=countries,
        )

        assert result['countries'][0]['name'] == 'France'
        assert result['countries'][1]['display_name'] == 'Spain'

    def test_data_story_create_with_slug(self):
        """Test creating a story with explicit slug."""
        user = factories.User()

        result = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Custom Slug Story',
            slug='my-custom-slug',
        )

        assert result['slug'] == 'my-custom-slug'

    def test_data_story_create_auto_slug(self):
        """Test automatic slug generation."""
        user = factories.User()

        result = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='This is a Long Title',
        )

        assert result['slug'] == 'this-is-a-long-title'

    def test_data_story_create_requires_auth(self):
        """Test that creating a story requires authentication."""
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action(
                'data_story_create',
                context={'user': None},
                title='Unauthorized Story',
            )

    def test_data_story_section_create(self):
        """Test creating a section."""
        user = factories.User()

        # Create story first
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story with Sections',
        )

        # Create section
        section = helpers.call_action(
            'data_story_section_create',
            context={'user': user['name']},
            story_id=story['id'],
            section_type='introduction',
            title='Introduction',
            content='This is the introduction section.',
        )

        assert section['story_id'] == story['id']
        assert section['section_type'] == 'introduction'
        assert section['title'] == 'Introduction'
        assert section['content'] == 'This is the introduction section.'


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryReadActions:
    """Tests for story reading actions."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_data_story_show(self):
        """Test showing a single story."""
        user = factories.User()

        # Create story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Show Test Story',
        )

        # Retrieve story
        result = helpers.call_action(
            'data_story_show',
            id=story['id'],
        )

        assert result['id'] == story['id']
        assert result['title'] == 'Show Test Story'

    def test_data_story_show_by_slug(self):
        """Test showing a story by slug."""
        user = factories.User()

        # Create story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Slug Test',
            slug='slug-test',
        )

        # Retrieve by slug
        result = helpers.call_action(
            'data_story_show',
            slug='slug-test',
        )

        assert result['id'] == story['id']
        assert result['slug'] == 'slug-test'

    def test_data_story_list(self):
        """Test listing stories."""
        user = factories.User()

        # Create multiple stories
        for i in range(3):
            helpers.call_action(
                'data_story_create',
                context={'user': user['name']},
                title=f'Story {i}',
            )

        # List stories
        result = helpers.call_action('data_story_list')

        assert 'stories' in result
        assert len(result['stories']) >= 3

    def test_data_story_list_with_filters(self):
        """Test listing stories with filters."""
        user = factories.User()

        # Create stories with different statuses
        helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Draft Story',
        )

        published_story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Published Story',
        )
        # Manually set to published for test
        from ckanext.pages.data_stories.db.models import DataStory
        story_obj = model.Session.query(DataStory).filter_by(
            id=published_story['id']
        ).first()
        story_obj.status = 'published'
        model.Session.commit()

        # List only published
        result = helpers.call_action(
            'data_story_list',
            status='published',
        )

        assert len(result['stories']) >= 1
        for story in result['stories']:
            assert story['status'] == 'published'

    def test_data_story_list_pagination(self):
        """Test pagination in story list."""
        user = factories.User()

        # Create many stories
        for i in range(15):
            helpers.call_action(
                'data_story_create',
                context={'user': user['name']},
                title=f'Paginated Story {i}',
            )

        # Get first page
        result = helpers.call_action(
            'data_story_list',
            limit=10,
            offset=0,
        )

        assert len(result['stories']) == 10
        assert result['count'] >= 15


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryUpdateActions:
    """Tests for story update actions."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_data_story_update(self):
        """Test updating a story."""
        user = factories.User()

        # Create story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Original Title',
        )

        # Update story
        updated = helpers.call_action(
            'data_story_update',
            context={'user': user['name']},
            id=story['id'],
            title='Updated Title',
            abstract='Updated abstract',
            countries=[{'name': 'Germany', 'display_name': 'Germany'}],
        )

        assert updated['title'] == 'Updated Title'
        assert updated['abstract'] == 'Updated abstract'
        assert updated['countries'][0]['name'] == 'Germany'

    def test_data_story_update_requires_permission(self):
        """Test that updating requires permission."""
        author = factories.User()
        other_user = factories.User()

        # Create story as author
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Authors Story',
        )

        # Try to update as other user
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action(
                'data_story_update',
                context={'user': other_user['name']},
                id=story['id'],
                title='Hacked Title',
            )

    def test_data_story_section_update(self):
        """Test updating a section."""
        user = factories.User()

        # Create story and section
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story',
        )

        section = helpers.call_action(
            'data_story_section_create',
            context={'user': user['name']},
            story_id=story['id'],
            section_type='methodology',
            content='Original content',
        )

        # Update section
        updated = helpers.call_action(
            'data_story_section_update',
            context={'user': user['name']},
            id=section['id'],
            content='Updated content',
        )

        assert updated['content'] == 'Updated content'


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryDeleteActions:
    """Tests for story deletion actions."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_data_story_delete(self):
        """Test deleting a story."""
        user = factories.User()

        # Create story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story to Delete',
        )

        # Delete story
        helpers.call_action(
            'data_story_delete',
            context={'user': user['name']},
            id=story['id'],
        )

        # Verify deletion (should raise NotFound)
        with pytest.raises(toolkit.ObjectNotFound):
            helpers.call_action('data_story_show', id=story['id'])

    def test_data_story_delete_requires_permission(self):
        """Test that deleting requires permission."""
        author = factories.User()
        other_user = factories.User()

        # Create story
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Protected Story',
        )

        # Try to delete as other user
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action(
                'data_story_delete',
                context={'user': other_user['name']},
                id=story['id'],
            )


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryWorkflowActions:
    """Tests for story workflow actions."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_data_story_submit(self):
        """Test submitting a story for review."""
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

        # Submit story
        updated = helpers.call_action(
            'data_story_submit',
            context={'user': user['name']},
            id=story['id'],
        )

        assert updated['status'] == 'submitted'
        assert updated['submission_date'] is not None

    def test_data_story_submit_incomplete(self):
        """Test that submitting incomplete story fails."""
        user = factories.User()

        # Create story without required sections
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Incomplete Story',
        )

        # Try to submit (should fail validation)
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action(
                'data_story_submit',
                context={'user': user['name']},
                id=story['id'],
            )


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryDatasetActions:
    """Tests for dataset linking actions."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_data_story_dataset_link(self):
        """Test linking a dataset to a story."""
        user = factories.User()
        dataset = factories.Dataset(user=user)

        # Create story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story with Dataset',
        )

        # Link dataset
        link = helpers.call_action(
            'data_story_dataset_link',
            context={'user': user['name']},
            story_id=story['id'],
            dataset_id=dataset['id'],
            relationship_type='primary',
        )

        assert link['story_id'] == story['id']
        assert link['dataset_id'] == dataset['id']
        assert link['relationship_type'] == 'primary'

    def test_data_story_dataset_unlink(self):
        """Test unlinking a dataset."""
        user = factories.User()
        dataset = factories.Dataset(user=user)

        # Create story and link dataset
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story',
        )

        helpers.call_action(
            'data_story_dataset_link',
            context={'user': user['name']},
            story_id=story['id'],
            dataset_id=dataset['id'],
            relationship_type='primary',
        )

        # Unlink dataset
        helpers.call_action(
            'data_story_dataset_unlink',
            context={'user': user['name']},
            story_id=story['id'],
            dataset_id=dataset['id'],
        )

        # Verify unlinked
        datasets = helpers.call_action(
            'data_story_datasets_list',
            story_id=story['id'],
        )

        assert len(datasets) == 0


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryCommentActions:
    """Tests for comment actions."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_data_story_comment_create(self):
        """Test creating a comment."""
        author = factories.User()
        reviewer = factories.User()

        # Create story
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Story',
        )

        # Add comment
        comment = helpers.call_action(
            'data_story_comment_create',
            context={'user': reviewer['name']},
            story_id=story['id'],
            comment_text='Please add more details.',
            comment_type='suggestion',
        )

        assert comment['story_id'] == story['id']
        assert comment['user_id'] == reviewer['id']
        assert comment['comment_text'] == 'Please add more details.'

    def test_data_story_comment_reply(self):
        """Test replying to a comment."""
        author = factories.User()
        reviewer = factories.User()

        # Create story
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Story',
        )

        # Add parent comment
        parent = helpers.call_action(
            'data_story_comment_create',
            context={'user': reviewer['name']},
            story_id=story['id'],
            comment_text='Parent comment',
        )

        # Add reply
        reply = helpers.call_action(
            'data_story_comment_create',
            context={'user': author['name']},
            story_id=story['id'],
            comment_text='Reply to comment',
            parent_id=parent['id'],
        )

        assert reply['parent_id'] == parent['id']

    def test_data_story_comment_resolve(self):
        """Test resolving a comment."""
        author = factories.User()
        reviewer = factories.User()

        # Create story and comment
        story = helpers.call_action(
            'data_story_create',
            context={'user': author['name']},
            title='Story',
        )

        comment = helpers.call_action(
            'data_story_comment_create',
            context={'user': reviewer['name']},
            story_id=story['id'],
            comment_text='Fix this',
            comment_type='required_change',
        )

        # Resolve comment
        resolved = helpers.call_action(
            'data_story_comment_resolve',
            context={'user': author['name']},
            id=comment['id'],
        )

        assert resolved['is_resolved'] is True


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryStatsActions:
    """Tests for stats actions."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_data_story_increment_views(self):
        """Test incrementing view count."""
        user = factories.User()

        # Create story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story',
        )

        # Increment views
        helpers.call_action(
            'data_story_increment_views',
            id=story['id'],
        )

        # Check view count
        updated = helpers.call_action('data_story_show', id=story['id'])
        assert updated['view_count'] == 1

    def test_data_story_stats(self):
        """Test getting story statistics."""
        user = factories.User()

        # Create story
        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Story',
        )

        # Get stats
        stats = helpers.call_action(
            'data_story_stats',
            id=story['id'],
        )

        assert 'view_count' in stats
        assert 'section_count' in stats
        assert 'dataset_count' in stats
