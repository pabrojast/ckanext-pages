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


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestDataStoryExportImportActions:
    """Tests for export/import actions including bulk operations."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def _create_story_with_sections(self, user, title, slug=None, num_sections=2):
        """Helper to create a story with sections."""
        create_kwargs = {
            'title': title,
            'abstract': f'Abstract for {title}',
            'research_question': 'Test question',
        }
        if slug:
            create_kwargs['slug'] = slug

        story = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            **create_kwargs,
        )

        for i in range(num_sections):
            helpers.call_action(
                'data_story_section_create',
                context={'user': user['name']},
                story_id=story['id'],
                section_type='text',
                title=f'Section {i}',
                content=f'Content for section {i}',
            )

        return story

    def test_single_export(self):
        """Test exporting a single story."""
        sysadmin = factories.Sysadmin()

        story = self._create_story_with_sections(sysadmin, 'Export Test', slug='export-test')

        result = helpers.call_action(
            'data_story_export',
            context={'user': sysadmin['name']},
            slug='export-test',
        )

        assert result['format_version'] == '1.0'
        assert result['story']['title'] == 'Export Test'
        assert result['story']['slug'] == 'export-test'
        assert len(result['story']['sections']) == 2
        assert 'export_metadata' in result

    def test_single_export_requires_sysadmin(self):
        """Test that export requires sysadmin."""
        user = factories.User()
        story = self._create_story_with_sections(user, 'Protected Story', slug='protected')

        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action(
                'data_story_export',
                context={'user': user['name'], 'ignore_auth': False},
                slug='protected',
            )

    def test_single_import(self):
        """Test importing a single story."""
        sysadmin = factories.Sysadmin()

        export_data = {
            'format_version': '1.0',
            'story': {
                'title': 'Imported Story',
                'slug': 'imported-story',
                'abstract': 'Imported abstract',
                'sections': [
                    {'section_type': 'text', 'title': 'Section 1', 'content': 'Content 1', 'order_index': 0},
                ],
                'contributors': [
                    {'name': 'John Doe', 'role': 'co-author', 'order_index': 0},
                ],
            },
        }

        result = helpers.call_action(
            'data_story_import',
            context={'user': sysadmin['name']},
            data=export_data,
        )

        assert result['title'] == 'Imported Story'
        assert result['slug'] == 'imported-story'
        assert result['status'] == 'draft'
        assert result['import_info']['sections_imported'] == 1
        assert result['import_info']['contributors_imported'] == 1

    def test_import_preserve_status(self):
        """Test importing with preserve_status flag."""
        sysadmin = factories.Sysadmin()

        export_data = {
            'format_version': '1.0',
            'story': {
                'title': 'Published Story',
                'slug': 'published-import',
                'status': 'published',
                'sections': [],
            },
        }

        result = helpers.call_action(
            'data_story_import',
            context={'user': sysadmin['name']},
            data=export_data,
            preserve_status=True,
        )

        assert result['status'] == 'published'
        assert result['is_public'] == True

    def test_import_preserve_dates(self):
        """Test importing with preserve_dates flag."""
        sysadmin = factories.Sysadmin()

        export_data = {
            'format_version': '1.0',
            'story': {
                'title': 'Old Story',
                'slug': 'old-story',
                'created_at': '2024-01-15T10:30:00',
                'published_at': '2024-02-20T14:00:00',
                'sections': [],
            },
        }

        result = helpers.call_action(
            'data_story_import',
            context={'user': sysadmin['name']},
            data=export_data,
            preserve_dates=True,
        )

        assert '2024-01-15' in result['created_at']
        assert '2024-02-20' in result['published_at']

    def test_import_slug_conflict_rename(self):
        """Test slug conflict with rename strategy."""
        sysadmin = factories.Sysadmin()

        # Create existing story
        self._create_story_with_sections(sysadmin, 'Existing', slug='conflict-slug', num_sections=0)

        export_data = {
            'format_version': '1.0',
            'story': {
                'title': 'Conflicting Story',
                'slug': 'conflict-slug',
                'sections': [],
            },
        }

        result = helpers.call_action(
            'data_story_import',
            context={'user': sysadmin['name']},
            data=export_data,
            slug_conflict='rename',
        )

        assert result['slug'] != 'conflict-slug'
        assert result['slug'].startswith('conflict-slug')

    def test_bulk_export(self):
        """Test bulk exporting all stories."""
        sysadmin = factories.Sysadmin()

        self._create_story_with_sections(sysadmin, 'Bulk Story 1', slug='bulk-1')
        self._create_story_with_sections(sysadmin, 'Bulk Story 2', slug='bulk-2')

        result = helpers.call_action(
            'data_story_bulk_export',
            context={'user': sysadmin['name']},
        )

        assert result['format_version'] == '1.0'
        assert isinstance(result['stories'], list)
        assert len(result['stories']) >= 2
        assert 'export_metadata' in result
        assert result['export_metadata']['total_stories'] >= 2

    def test_bulk_export_with_status_filter(self):
        """Test bulk export filtered by status."""
        sysadmin = factories.Sysadmin()

        story = self._create_story_with_sections(sysadmin, 'Published Bulk', slug='pub-bulk')

        # Set story to published
        from ckanext.pages.data_stories.db.models import DataStory
        story_obj = model.Session.query(DataStory).filter_by(id=story['id']).first()
        story_obj.status = 'published'
        model.Session.commit()

        result = helpers.call_action(
            'data_story_bulk_export',
            context={'user': sysadmin['name']},
            status='published',
        )

        for s in result['stories']:
            assert s['status'] == 'published'

    def test_bulk_export_requires_sysadmin(self):
        """Test that bulk export requires sysadmin."""
        user = factories.User()

        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action(
                'data_story_bulk_export',
                context={'user': user['name'], 'ignore_auth': False},
            )

    def test_bulk_import(self):
        """Test bulk importing multiple stories."""
        sysadmin = factories.Sysadmin()

        bulk_data = {
            'format_version': '1.0',
            'stories': [
                {
                    'title': 'Bulk Import 1',
                    'slug': 'bulk-import-1',
                    'sections': [
                        {'section_type': 'text', 'title': 'S1', 'content': 'C1', 'order_index': 0},
                    ],
                },
                {
                    'title': 'Bulk Import 2',
                    'slug': 'bulk-import-2',
                    'sections': [
                        {'section_type': 'text', 'title': 'S2', 'content': 'C2', 'order_index': 0},
                        {'section_type': 'text', 'title': 'S3', 'content': 'C3', 'order_index': 1},
                    ],
                },
            ],
        }

        result = helpers.call_action(
            'data_story_bulk_import',
            context={'user': sysadmin['name']},
            data=bulk_data,
        )

        assert result['total_imported'] == 2
        assert result['total_errors'] == 0
        assert len(result['imported']) == 2

    def test_bulk_import_with_preserve_status(self):
        """Test bulk import preserving original status."""
        sysadmin = factories.Sysadmin()

        bulk_data = {
            'format_version': '1.0',
            'stories': [
                {
                    'title': 'Published Bulk',
                    'slug': 'pub-bulk-import',
                    'status': 'published',
                    'sections': [],
                },
                {
                    'title': 'Draft Bulk',
                    'slug': 'draft-bulk-import',
                    'status': 'draft',
                    'sections': [],
                },
            ],
        }

        result = helpers.call_action(
            'data_story_bulk_import',
            context={'user': sysadmin['name']},
            data=bulk_data,
            preserve_status=True,
        )

        assert result['total_imported'] == 2

        # Verify statuses
        pub = helpers.call_action('data_story_show', slug='pub-bulk-import')
        assert pub['status'] == 'published'

        draft = helpers.call_action('data_story_show', slug='draft-bulk-import')
        assert draft['status'] == 'draft'

    def test_bulk_import_requires_sysadmin(self):
        """Test that bulk import requires sysadmin."""
        user = factories.User()

        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action(
                'data_story_bulk_import',
                context={'user': user['name'], 'ignore_auth': False},
                data={'format_version': '1.0', 'stories': []},
            )

    def test_roundtrip_export_import(self):
        """Test full roundtrip: create → export → import."""
        sysadmin = factories.Sysadmin()

        # Create stories with sections
        self._create_story_with_sections(sysadmin, 'Roundtrip 1', slug='roundtrip-1')
        self._create_story_with_sections(sysadmin, 'Roundtrip 2', slug='roundtrip-2', num_sections=3)

        # Bulk export
        export_result = helpers.call_action(
            'data_story_bulk_export',
            context={'user': sysadmin['name']},
        )

        # Delete originals
        for story_data in export_result['stories']:
            slug = story_data['slug']
            if slug.startswith('roundtrip-'):
                show = helpers.call_action('data_story_show', slug=slug)
                helpers.call_action(
                    'data_story_delete',
                    context={'user': sysadmin['name']},
                    id=show['id'],
                )

        # Bulk import with preserved status/dates
        import_result = helpers.call_action(
            'data_story_bulk_import',
            context={'user': sysadmin['name']},
            data=export_result,
            preserve_status=True,
            preserve_dates=True,
        )

        assert import_result['total_errors'] == 0
        # Verify roundtrip stories are imported (may also include other stories from test)
        roundtrip_imported = [i for i in import_result['imported'] if 'Roundtrip' in i['title']]
        assert len(roundtrip_imported) >= 2
