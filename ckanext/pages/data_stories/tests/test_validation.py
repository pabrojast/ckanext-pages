# encoding: utf-8
"""
Tests for Data Stories validation logic.
"""

import pytest
import json

from ckanext.pages.data_stories.logic.validation import (
    validate_story_completeness,
    validate_terria_config,
    validate_slug,
    generate_slug,
    validate_section_type,
    validate_story_status,
    validate_contributor_role,
)


class TestValidationFunctions:
    """Tests for validation utility functions."""

    def test_generate_slug_from_title(self):
        """Test slug generation from title."""
        slug = generate_slug('This is a Test Title')
        assert slug == 'this-is-a-test-title'

    def test_generate_slug_removes_special_chars(self):
        """Test that special characters are removed."""
        slug = generate_slug('Title with @#$% Special!')
        assert slug == 'title-with-special'

    def test_generate_slug_handles_unicode(self):
        """Test handling of unicode characters."""
        slug = generate_slug('Título con acentós')
        # Should convert or remove accents
        assert 'titulo' in slug or 'con' in slug

    def test_generate_slug_empty_string(self):
        """Test generating slug from empty string."""
        slug = generate_slug('')
        assert slug == ''

    def test_validate_slug_valid(self):
        """Test validating a valid slug."""
        is_valid, error = validate_slug('valid-slug-123')
        assert is_valid is True
        assert error is None

    def test_validate_slug_invalid_characters(self):
        """Test validating slug with invalid characters."""
        is_valid, error = validate_slug('invalid slug!')
        assert is_valid is False
        assert 'lowercase' in error.lower() or 'hyphen' in error.lower()

    def test_validate_slug_uppercase(self):
        """Test that uppercase in slug is invalid."""
        is_valid, error = validate_slug('Invalid-Slug')
        assert is_valid is False

    def test_validate_section_type_valid(self):
        """Test validating valid section types."""
        valid_types = [
            'introduction', 'research_question', 'study_area',
            'data_sources', 'methodology', 'spatial_analysis',
            'results', 'discussion', 'conclusions',
            'references', 'acknowledgments', 'custom'
        ]

        for section_type in valid_types:
            is_valid, error = validate_section_type(section_type)
            assert is_valid is True, f"Failed for {section_type}"
            assert error is None

    def test_validate_section_type_invalid(self):
        """Test validating invalid section type."""
        is_valid, error = validate_section_type('invalid_type')
        assert is_valid is False
        assert error is not None

    def test_validate_story_status_valid(self):
        """Test validating valid story statuses."""
        valid_statuses = ['draft', 'submitted', 'under_review', 'published', 'archived']

        for status in valid_statuses:
            is_valid, error = validate_story_status(status)
            assert is_valid is True, f"Failed for {status}"
            assert error is None

    def test_validate_story_status_invalid(self):
        """Test validating invalid status."""
        is_valid, error = validate_story_status('invalid_status')
        assert is_valid is False
        assert error is not None

    def test_validate_contributor_role_valid(self):
        """Test validating valid contributor roles."""
        valid_roles = ['co-author', 'data-provider', 'reviewer', 'editor', 'translator']

        for role in valid_roles:
            is_valid, error = validate_contributor_role(role)
            assert is_valid is True, f"Failed for {role}"
            assert error is None

    def test_validate_contributor_role_invalid(self):
        """Test validating invalid role."""
        is_valid, error = validate_contributor_role('invalid_role')
        assert is_valid is False
        assert error is not None


class TestStoryCompletenessValidation:
    """Tests for story completeness validation."""

    def test_complete_story_passes(self):
        """Test that a complete story passes validation."""
        story_dict = {
            'title': 'Complete Story',
            'sections': [
                {'section_type': 'introduction', 'content': 'Intro'},
                {'section_type': 'data_sources', 'content': 'Data'},
                {'section_type': 'methodology', 'content': 'Methods'},
                {'section_type': 'spatial_analysis', 'content': 'Analysis'},
                {'section_type': 'conclusions', 'content': 'Conclusions'},
            ]
        }

        is_complete, errors = validate_story_completeness(story_dict)
        assert is_complete is True
        assert len(errors) == 0

    def test_incomplete_story_fails(self):
        """Test that incomplete story fails validation."""
        story_dict = {
            'title': 'Incomplete Story',
            'sections': [
                {'section_type': 'introduction', 'content': 'Intro'},
            ]
        }

        is_complete, errors = validate_story_completeness(story_dict)
        assert is_complete is False
        assert len(errors) > 0

    def test_identifies_missing_sections(self):
        """Test that missing required sections are identified."""
        story_dict = {
            'title': 'Story',
            'sections': [
                {'section_type': 'introduction', 'content': 'Intro'},
                {'section_type': 'methodology', 'content': 'Methods'},
            ]
        }

        is_complete, errors = validate_story_completeness(story_dict)
        assert is_complete is False
        # Should mention missing sections
        error_text = ' '.join(errors).lower()
        assert 'data_sources' in error_text or 'missing' in error_text

    def test_empty_sections_list(self):
        """Test validation with no sections."""
        story_dict = {
            'title': 'No Sections Story',
            'sections': []
        }

        is_complete, errors = validate_story_completeness(story_dict)
        assert is_complete is False
        assert len(errors) > 0

    def test_extra_sections_allowed(self):
        """Test that extra sections beyond required ones are allowed."""
        story_dict = {
            'title': 'Extended Story',
            'sections': [
                {'section_type': 'introduction', 'content': 'Intro'},
                {'section_type': 'data_sources', 'content': 'Data'},
                {'section_type': 'methodology', 'content': 'Methods'},
                {'section_type': 'spatial_analysis', 'content': 'Analysis'},
                {'section_type': 'conclusions', 'content': 'Conclusions'},
                {'section_type': 'references', 'content': 'References'},
                {'section_type': 'acknowledgments', 'content': 'Thanks'},
            ]
        }

        is_complete, errors = validate_story_completeness(story_dict)
        assert is_complete is True


class TestTerriaConfigValidation:
    """Tests for Terria configuration validation."""

    def test_valid_terria_config(self):
        """Test validating valid Terria configuration."""
        config = {
            'initSources': [
                {
                    'type': 'wms',
                    'url': 'https://example.com/wms',
                    'name': 'Test Layer'
                }
            ]
        }

        is_valid, error = validate_terria_config(json.dumps(config))
        assert is_valid is True
        assert error is None

    def test_valid_terria_config_dict(self):
        """Test validating Terria config passed as dict."""
        config = {
            'initSources': [],
            'viewerMode': '3d'
        }

        is_valid, error = validate_terria_config(config)
        assert is_valid is True
        assert error is None

    def test_invalid_json(self):
        """Test validating invalid JSON."""
        invalid_json = '{"initSources": [invalid]}'

        is_valid, error = validate_terria_config(invalid_json)
        assert is_valid is False
        assert 'json' in error.lower()

    def test_empty_config(self):
        """Test validating empty configuration."""
        is_valid, error = validate_terria_config('')
        assert is_valid is False

    def test_config_without_content(self):
        """Test config without required content."""
        config = {'random': 'field'}

        is_valid, error = validate_terria_config(config)
        assert is_valid is False
        assert 'initSources' in error or 'content' in error.lower()

    def test_config_with_workbench(self):
        """Test config with workbench instead of initSources."""
        config = {
            'workbench': ['item1', 'item2']
        }

        is_valid, error = validate_terria_config(config)
        assert is_valid is True

    def test_config_with_catalog(self):
        """Test config with catalog."""
        config = {
            'catalog': [
                {
                    'name': 'Group',
                    'items': []
                }
            ]
        }

        is_valid, error = validate_terria_config(config)
        assert is_valid is True

    def test_config_with_stories(self):
        """Test config with Terria stories."""
        config = {
            'stories': [
                {
                    'title': 'Story 1',
                    'text': 'Content'
                }
            ]
        }

        is_valid, error = validate_terria_config(config)
        assert is_valid is True

    def test_initsources_must_be_array(self):
        """Test that initSources must be an array."""
        config = {
            'initSources': 'not an array'
        }

        is_valid, error = validate_terria_config(config)
        assert is_valid is False
        assert 'array' in error.lower()

    def test_workbench_must_be_array(self):
        """Test that workbench must be an array."""
        config = {
            'workbench': {'not': 'array'}
        }

        is_valid, error = validate_terria_config(config)
        assert is_valid is False
        assert 'array' in error.lower()


class TestSlugValidation:
    """Additional slug validation tests."""

    def test_slug_too_short(self):
        """Test that very short slugs might be invalid."""
        is_valid, error = validate_slug('a')
        # Depending on implementation, might be valid or not
        # Just testing the function works
        assert isinstance(is_valid, bool)

    def test_slug_too_long(self):
        """Test very long slugs."""
        long_slug = 'a' * 300
        is_valid, error = validate_slug(long_slug)
        # Should handle long slugs gracefully
        assert isinstance(is_valid, bool)

    def test_slug_with_consecutive_hyphens(self):
        """Test slug with multiple consecutive hyphens."""
        is_valid, error = validate_slug('slug--with---hyphens')
        # Might be invalid depending on rules
        assert isinstance(is_valid, bool)

    def test_slug_starting_with_hyphen(self):
        """Test slug starting with hyphen."""
        is_valid, error = validate_slug('-invalid-slug')
        assert is_valid is False

    def test_slug_ending_with_hyphen(self):
        """Test slug ending with hyphen."""
        is_valid, error = validate_slug('invalid-slug-')
        assert is_valid is False

    def test_slug_numbers_only(self):
        """Test slug with only numbers."""
        is_valid, error = validate_slug('12345')
        # Should be valid
        assert is_valid is True

    def test_slug_with_underscore(self):
        """Test slug with underscore."""
        is_valid, error = validate_slug('slug_with_underscore')
        # Typically invalid (should use hyphens)
        assert is_valid is False
