# encoding: utf-8
"""Tests for the Water Family public API endpoints."""

import json
import datetime
import pytest

from ckan.tests import factories, helpers

from ckanext.pages.actions import html_to_plain_text


def _create_water_page(user, name, page_type='water-news', private=False,
                       submission_status='approved', extras=None, **kwargs):
    """Helper to create a water family page via the action API."""
    params = {
        'name': name,
        'page': name,
        'title': kwargs.get('title', 'Test %s' % name),
        'content': kwargs.get('content', 'Content for %s' % name),
        'page_type': page_type,
        'private': private,
        'submission_status': submission_status,
        'publish_date': kwargs.get(
            'publish_date', datetime.datetime.utcnow().isoformat()
        ),
    }
    if kwargs.get('ihp_organization'):
        params['ihp_organization'] = kwargs['ihp_organization']
    if extras:
        for k, v in extras.items():
            params[k] = v if isinstance(v, str) else json.dumps(v)

    helpers.call_action(
        'ckanext_pages_update',
        {'user': user['name']},
        **params
    )


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "pages")
class TestWaterFamilyList:
    """Tests for the ckanext_water_family_list action."""

    def test_list_returns_public_approved_only(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(sysadmin, 'wf-public', private=False,
                           submission_status='approved')
        _create_water_page(sysadmin, 'wf-private', private=True,
                           submission_status='approved')
        _create_water_page(sysadmin, 'wf-draft', private=True,
                           submission_status='draft')

        result = helpers.call_action('ckanext_water_family_list', {})
        names = [r['name'] for r in result['results']]

        assert 'wf-public' in names
        assert 'wf-private' not in names
        assert 'wf-draft' not in names

    def test_list_no_auth_required(self, app):
        """Verify anonymous users can call the API."""
        sysadmin = factories.Sysadmin()
        _create_water_page(sysadmin, 'wf-anon-test')

        result = helpers.call_action(
            'ckanext_water_family_list', {'ignore_auth': False}
        )
        assert result['count'] >= 1

    def test_list_filter_by_page_type(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(sysadmin, 'wf-news-1', page_type='water-news')
        _create_water_page(sysadmin, 'wf-event-1', page_type='water-events')
        _create_water_page(sysadmin, 'wf-pub-1',
                           page_type='water-publications',
                           extras={'publication_url': 'https://example.com/pub'})

        result = helpers.call_action(
            'ckanext_water_family_list', {},
            page_type='water-news'
        )
        types = {r['page_type'] for r in result['results']}
        assert types == {'water-news'}

    def test_list_invalid_page_type_raises(self, app):
        with pytest.raises(Exception):
            helpers.call_action(
                'ckanext_water_family_list', {},
                page_type='blog'
            )

    def test_list_all_types_without_filter(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(sysadmin, 'wf-all-news', page_type='water-news')
        _create_water_page(sysadmin, 'wf-all-event', page_type='water-events')

        result = helpers.call_action('ckanext_water_family_list', {})
        types = {r['page_type'] for r in result['results']}

        assert 'water-news' in types
        assert 'water-events' in types

    def test_list_excludes_non_water_family_types(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(sysadmin, 'wf-news-only', page_type='water-news')
        # Create a regular page (not water family)
        helpers.call_action(
            'ckanext_pages_update',
            {'user': sysadmin['name']},
            name='regular-page', page='regular-page',
            title='Regular', content='Not water family',
            page_type='page', private=False,
            submission_status='approved',
        )

        result = helpers.call_action('ckanext_water_family_list', {})
        types = {r['page_type'] for r in result['results']}

        assert 'page' not in types

    def test_list_filter_by_initiative(self, app):
        sysadmin = factories.Sysadmin()
        initiative_data = [{'name': 'IslandWatch', 'title': 'Island Watch'}]
        _create_water_page(
            sysadmin, 'wf-initiative-yes',
            extras={'initiative_groups': initiative_data}
        )
        _create_water_page(sysadmin, 'wf-initiative-no')

        result = helpers.call_action(
            'ckanext_water_family_list', {},
            initiative='IslandWatch'
        )
        names = [r['name'] for r in result['results']]

        assert 'wf-initiative-yes' in names
        assert 'wf-initiative-no' not in names

    def test_list_filter_by_hyphenated_initiative_with_page_type(self, app):
        sysadmin = factories.Sysadmin()
        nested_initiative_data = json.dumps([{'name': 'be-resilient'}])

        _create_water_page(
            sysadmin, 'wf-be-resilient-news',
            page_type='water-news',
            extras={'initiative_groups': json.dumps(nested_initiative_data)}
        )
        _create_water_page(
            sysadmin, 'wf-be-resilient-event',
            page_type='water-events',
            extras={'initiative_groups': [{'name': 'be-resilient'}]}
        )
        _create_water_page(
            sysadmin, 'wf-other-initiative-news',
            page_type='water-news',
            extras={'initiative_groups': [{'name': 'riverwatch'}]}
        )

        result = helpers.call_action(
            'ckanext_water_family_list', {},
            page_type='water-news',
            initiative='be-resilient'
        )
        names = [r['name'] for r in result['results']]

        assert names == ['wf-be-resilient-news']
        assert result['count'] == 1

    def test_list_filter_by_member_state(self, app):
        sysadmin = factories.Sysadmin()
        country_data = [{'name': 'France', 'id': 'fr'}]
        _create_water_page(
            sysadmin, 'wf-ms-france',
            extras={'country_groups': country_data}
        )
        _create_water_page(sysadmin, 'wf-ms-none')

        result = helpers.call_action(
            'ckanext_water_family_list', {},
            member_state='France'
        )
        names = [r['name'] for r in result['results']]

        assert 'wf-ms-france' in names
        assert 'wf-ms-none' not in names

    def test_list_filter_by_organization(self, app):
        sysadmin = factories.Sysadmin()
        org = factories.Organization()

        _create_water_page(
            sysadmin, 'wf-org-yes', ihp_organization=org['id']
        )
        _create_water_page(sysadmin, 'wf-org-no')

        result = helpers.call_action(
            'ckanext_water_family_list', {},
            organization=org['id']
        )
        names = [r['name'] for r in result['results']]

        assert 'wf-org-yes' in names
        assert 'wf-org-no' not in names

    def test_list_filter_by_water_type(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(
            sysadmin, 'wf-ground',
            extras={'water_type': 'groundwater'}
        )
        _create_water_page(
            sysadmin, 'wf-surface',
            extras={'water_type': 'surface_water'}
        )

        result = helpers.call_action(
            'ckanext_water_family_list', {},
            water_type='groundwater'
        )
        names = [r['name'] for r in result['results']]

        assert 'wf-ground' in names
        assert 'wf-surface' not in names

    def test_list_search_by_q(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(
            sysadmin, 'wf-search-match',
            title='Drought in Sahel Region'
        )
        _create_water_page(
            sysadmin, 'wf-search-miss',
            title='Ocean Monitoring Update'
        )

        result = helpers.call_action(
            'ckanext_water_family_list', {},
            q='Sahel'
        )
        names = [r['name'] for r in result['results']]

        assert 'wf-search-match' in names
        assert 'wf-search-miss' not in names

    def test_list_pagination_limit(self, app):
        sysadmin = factories.Sysadmin()
        for i in range(5):
            _create_water_page(sysadmin, 'wf-page-%d' % i)

        result = helpers.call_action(
            'ckanext_water_family_list', {},
            limit=2
        )
        assert len(result['results']) == 2
        assert result['count'] == 5

    def test_list_pagination_offset(self, app):
        sysadmin = factories.Sysadmin()
        for i in range(5):
            _create_water_page(sysadmin, 'wf-off-%d' % i)

        all_result = helpers.call_action(
            'ckanext_water_family_list', {},
            limit=100
        )
        offset_result = helpers.call_action(
            'ckanext_water_family_list', {},
            limit=100, offset=2
        )

        assert len(offset_result['results']) == len(all_result['results']) - 2

    def test_list_returns_count(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(sysadmin, 'wf-count-1')
        _create_water_page(sysadmin, 'wf-count-2')

        result = helpers.call_action('ckanext_water_family_list', {})
        assert 'count' in result
        assert 'results' in result
        assert result['count'] >= 2

    def test_list_returns_expected_fields(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(
            sysadmin, 'wf-fields-test',
            extras={'water_type': 'groundwater', 'excerpt': 'Short summary'}
        )

        result = helpers.call_action('ckanext_water_family_list', {})
        page = next(r for r in result['results'] if r['name'] == 'wf-fields-test')

        assert 'title' in page
        assert 'name' in page
        assert 'content' in page
        assert 'publish_date' in page
        assert 'page_type' in page
        assert page['water_type'] == 'groundwater'


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "pages")
class TestWaterFamilyShow:
    """Tests for the ckanext_water_family_show action."""

    def test_show_public_approved_page(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(sysadmin, 'wf-show-ok')

        result = helpers.call_action(
            'ckanext_water_family_show', {},
            page='wf-show-ok'
        )
        assert result is not None
        assert result['name'] == 'wf-show-ok'

    def test_show_private_page_returns_none(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(sysadmin, 'wf-show-private', private=True)

        result = helpers.call_action(
            'ckanext_water_family_show', {},
            page='wf-show-private'
        )
        assert result is None

    def test_show_draft_page_returns_none(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(sysadmin, 'wf-show-draft',
                           private=True, submission_status='draft')

        result = helpers.call_action(
            'ckanext_water_family_show', {},
            page='wf-show-draft'
        )
        assert result is None

    def test_show_pending_page_returns_none(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(sysadmin, 'wf-show-pending',
                           private=True, submission_status='pending')

        result = helpers.call_action(
            'ckanext_water_family_show', {},
            page='wf-show-pending'
        )
        assert result is None

    def test_show_non_water_type_returns_none(self, app):
        sysadmin = factories.Sysadmin()
        helpers.call_action(
            'ckanext_pages_update',
            {'user': sysadmin['name']},
            name='wf-show-blog', page='wf-show-blog',
            title='Blog', content='Blog content',
            page_type='blog', private=False,
            submission_status='approved',
        )

        result = helpers.call_action(
            'ckanext_water_family_show', {},
            page='wf-show-blog'
        )
        assert result is None

    def test_show_nonexistent_returns_none(self, app):
        result = helpers.call_action(
            'ckanext_water_family_show', {},
            page='does-not-exist'
        )
        assert result is None

    def test_show_missing_page_param_raises(self, app):
        with pytest.raises(Exception):
            helpers.call_action('ckanext_water_family_show', {})

    def test_show_no_auth_required(self, app):
        """Verify anonymous users can call show."""
        sysadmin = factories.Sysadmin()
        _create_water_page(sysadmin, 'wf-show-anon')

        result = helpers.call_action(
            'ckanext_water_family_show', {'ignore_auth': False},
            page='wf-show-anon'
        )
        assert result is not None


class TestHtmlToPlainText:
    """Unit tests for the html_to_plain_text helper."""

    def test_none_and_empty_inputs(self):
        assert html_to_plain_text(None) == ''
        assert html_to_plain_text('') == ''

    def test_strips_tags_and_decodes_entities(self):
        html = '<p>Hello&nbsp;<strong>world</strong> &amp; friends</p>'
        # The non-breaking space decodes to U+00A0; assert on the words.
        text = html_to_plain_text(html)
        assert 'Hello' in text
        assert 'world' in text
        assert 'friends' in text
        assert '<' not in text and '>' not in text
        assert '&amp;' not in text

    def test_drops_script_and_style_bodies(self):
        html = (
            '<style>.x{color:red}</style>'
            '<script>alert(1)</script>'
            '<p>Visible</p>'
        )
        text = html_to_plain_text(html)
        assert text.strip() == 'Visible'

    def test_block_tags_become_paragraph_breaks(self):
        html = '<p>One</p><p>Two</p><p>Three</p>'
        text = html_to_plain_text(html)
        assert text == 'One\n\nTwo\n\nThree'

    def test_br_becomes_single_newline(self):
        html = 'Line one<br/>Line two'
        text = html_to_plain_text(html)
        assert text == 'Line one\nLine two'

    def test_collapses_whitespace(self):
        html = '<p>  too   many\t\tspaces  </p>'
        assert html_to_plain_text(html) == 'too many spaces'

    def test_malformed_html_does_not_raise(self):
        # Unclosed tag — should still extract the visible text.
        assert 'safe' in html_to_plain_text('<p>safe<p')


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "pages")
class TestWaterFamilyCleanContent:
    """Tests for plain-text fields and the strip_html flag."""

    _HTML_BODY = (
        '<p>Hello <strong>world</strong></p>'
        '<script>alert(1)</script>'
        '<p>Second paragraph</p>'
    )
    _HTML_EXCERPT = '<p>Short <em>summary</em></p>'

    def test_list_always_includes_content_plain(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(
            sysadmin, 'wf-plain-1',
            content=self._HTML_BODY,
            extras={'excerpt': self._HTML_EXCERPT},
        )

        result = helpers.call_action('ckanext_water_family_list', {})
        page = next(r for r in result['results'] if r['name'] == 'wf-plain-1')

        assert 'content_plain' in page
        assert page['content'] == self._HTML_BODY
        assert '<' not in page['content_plain']
        assert 'Hello world' in page['content_plain']
        assert 'Second paragraph' in page['content_plain']
        # script body must not leak into plain text
        assert 'alert(1)' not in page['content_plain']

        assert 'excerpt_plain' in page
        assert page['excerpt'] == self._HTML_EXCERPT
        assert page['excerpt_plain'] == 'Short summary'

    def test_list_strip_html_replaces_html_fields(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(
            sysadmin, 'wf-plain-2',
            content=self._HTML_BODY,
            extras={'excerpt': self._HTML_EXCERPT},
        )

        result = helpers.call_action(
            'ckanext_water_family_list', {},
            strip_html=True,
        )
        page = next(r for r in result['results'] if r['name'] == 'wf-plain-2')

        assert '<' not in page['content']
        assert page['content'] == page['content_plain']
        assert page['excerpt'] == 'Short summary'
        assert page['excerpt'] == page['excerpt_plain']

    def test_show_always_includes_content_plain(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(
            sysadmin, 'wf-plain-show',
            content=self._HTML_BODY,
            extras={'excerpt': self._HTML_EXCERPT},
        )

        page = helpers.call_action(
            'ckanext_water_family_show', {},
            page='wf-plain-show',
        )

        assert page is not None
        assert page['content'] == self._HTML_BODY
        assert 'Hello world' in page['content_plain']
        assert 'alert(1)' not in page['content_plain']
        assert page['excerpt_plain'] == 'Short summary'

    def test_show_strip_html_replaces_html_fields(self, app):
        sysadmin = factories.Sysadmin()
        _create_water_page(
            sysadmin, 'wf-plain-show-2',
            content=self._HTML_BODY,
            extras={'excerpt': self._HTML_EXCERPT},
        )

        page = helpers.call_action(
            'ckanext_water_family_show', {},
            page='wf-plain-show-2',
            strip_html='true',
        )

        assert page is not None
        assert '<' not in page['content']
        assert page['content'] == page['content_plain']
        assert page['excerpt'] == 'Short summary'
