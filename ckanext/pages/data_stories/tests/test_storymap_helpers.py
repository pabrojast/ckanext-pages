# encoding: utf-8
"""
Tests for story map (scrollytelling) helpers.
"""

import json

from ckanext.pages.data_stories.helpers.storymap import (
    build_terria_scene_url,
    get_storymap_scenes,
    get_storymap_config,
    _media_embed_html,
    _strip_terria_tab_markup,
)


SHARE = 'https://ihp-wins.unesco.org/terria/#share=g-abc123'


class TestBuildTerriaSceneUrl:

    def test_adds_embed_flags_to_fragment(self):
        url = build_terria_scene_url(SHARE)
        assert url == ('https://ihp-wins.unesco.org/terria/'
                       '#share=g-abc123&hideWorkbench=1&hideExplorerPanel=1')

    def test_does_not_duplicate_existing_flags(self):
        url = build_terria_scene_url(SHARE + '&hideWorkbench=1')
        assert url.count('hideWorkbench=1') == 1
        assert 'hideExplorerPanel=1' in url

    def test_start_fragment_passes_through(self):
        url = build_terria_scene_url(
            'https://terria.example.org/#start=%7B%22version%22%3A%228%22%7D')
        assert url.startswith('https://terria.example.org/#start=')
        assert 'hideWorkbench=1' in url

    def test_rejects_links_without_share_or_start(self):
        assert build_terria_scene_url('https://example.org/') is None
        assert build_terria_scene_url('https://example.org/#map=2d') is None

    def test_rejects_invalid_input(self):
        assert build_terria_scene_url(None) is None
        assert build_terria_scene_url('') is None
        assert build_terria_scene_url('not a url') is None
        assert build_terria_scene_url(123) is None


class TestGetStorymapScenes:

    def _story(self, sections):
        return {'sections': sections}

    def test_blocks_metadata_section(self):
        story = self._story([{
            'id': 'sec-1',
            'title': 'Chapter 1',
            'section_type': 'introduction',
            'order_index': 0,
            'is_visible': True,
            'blocks_metadata': [
                {'type': 'text', 'content': '<p>Hello</p>'},
                {'type': 'terria', 'tabs': [
                    {'title': 'Map A', 'url': SHARE},
                    {'title': 'Map B',
                     'url': 'https://ihp-wins.unesco.org/terria/#share=g-b'},
                ]},
            ],
        }])

        scenes = get_storymap_scenes(story)
        assert len(scenes) == 1
        scene = scenes[0]
        assert scene['section_id'] == 'sec-1'
        assert scene['blocks'][0] == {'type': 'text',
                                      'content': '<p>Hello</p>'}
        tabs = scene['blocks'][1]['tabs']
        assert len(tabs) == 2
        assert tabs[0]['title'] == 'Map A'
        assert 'hideWorkbench=1' in tabs[0]['scene_url']
        # The first tab becomes the card's scene
        assert scene['scene_url'] == tabs[0]['scene_url']
        assert scene['share_url'] == SHARE

    def test_blocks_metadata_as_json_string(self):
        blocks = [{'type': 'terria', 'tabs': [{'title': 'M', 'url': SHARE}]}]
        story = self._story([{
            'id': 'sec-1', 'order_index': 0,
            'blocks_metadata': json.dumps(blocks),
        }])

        scenes = get_storymap_scenes(story)
        assert scenes[0]['scene_url'] is not None

    def test_narrative_only_section_has_no_scene(self):
        story = self._story([{
            'id': 'sec-1', 'order_index': 0,
            'blocks_metadata': [{'type': 'text', 'content': '<p>Hi</p>'}],
        }])

        scenes = get_storymap_scenes(story)
        assert scenes[0]['scene_url'] is None

    def test_legacy_section_strips_terria_markup(self):
        content = (
            '<p>Before</p>\n'
            '<div class="terria-tabs-display">\n'
            '<ul class="terria-tabs-nav-display"><li>Tab</li></ul>\n'
            '<div class="terria-tabs-panels-display">\n'
            '  <div class="terria-tab-display active" data-tab="0">\n'
            '    <iframe src="%s"></iframe>\n'
            '  </div>\n'
            '</div>\n'
            '</div>\n'
            '<p>After</p>' % SHARE)
        story = self._story([{
            'id': 'sec-1', 'order_index': 0,
            'content': content,
            'terria_share_link': SHARE,
            'blocks_metadata': None,
        }])

        scenes = get_storymap_scenes(story)
        block_html = scenes[0]['blocks'][0]['content']
        assert 'Before' in block_html
        assert 'After' in block_html
        assert 'terria-tabs-display' not in block_html
        assert '<iframe' not in block_html
        assert 'hideWorkbench=1' in scenes[0]['scene_url']

    def test_hidden_sections_are_skipped(self):
        story = self._story([
            {'id': 'a', 'order_index': 0, 'is_visible': False,
             'blocks_metadata': [{'type': 'text', 'content': 'x'}]},
            {'id': 'b', 'order_index': 1, 'is_visible': True,
             'blocks_metadata': [{'type': 'text', 'content': 'y'}]},
        ])

        scenes = get_storymap_scenes(story)
        assert [s['section_id'] for s in scenes] == ['b']

    def test_sections_sorted_by_order_index(self):
        story = self._story([
            {'id': 'b', 'order_index': 2, 'blocks_metadata': []},
            {'id': 'a', 'order_index': 1, 'blocks_metadata': []},
        ])

        scenes = get_storymap_scenes(story)
        assert [s['section_id'] for s in scenes] == ['a', 'b']

    def test_empty_story(self):
        assert get_storymap_scenes({}) == []
        assert get_storymap_scenes(None) == []


class TestGetStorymapConfig:

    def test_scene_list_and_origin(self):
        story = {
            'sections': [{
                'id': 'sec-1', 'order_index': 0,
                'blocks_metadata': [
                    {'type': 'terria', 'tabs': [{'title': 'M', 'url': SHARE}]}
                ],
            }],
            'uploaded_images': [
                {'url': 'https://cdn.example.org/a.png', 'featured': False},
                {'url': 'https://cdn.example.org/b.png', 'featured': True},
            ],
        }

        config = get_storymap_config(story)
        assert config['terriaOrigin'] == 'https://ihp-wins.unesco.org'
        assert config['scenes'][0]['id'] == 'sec-1'
        assert config['scenes'][0]['sceneUrl'].startswith(
            'https://ihp-wins.unesco.org/terria/#share=g-abc123')
        assert config['placeholderImage'] == 'https://cdn.example.org/b.png'
        assert config['usePostMessage'] is False


class TestMediaEmbedHtml:

    def test_youtube_url_becomes_embed(self):
        html = _media_embed_html({
            'url': 'https://www.youtube.com/watch?v=AesqQqAzaPM',
            'title': 'Video', 'width': '100%', 'height': '400',
        })
        assert 'youtube.com/embed/AesqQqAzaPM' in html
        assert '<h3>Video</h3>' in html

    def test_plain_url_becomes_iframe(self):
        html = _media_embed_html({'url': 'https://example.org/embed'})
        assert html.startswith('<iframe src="https://example.org/embed"')

    def test_raw_embed_code_passes_through(self):
        code = '<iframe src="https://example.org/x"></iframe>'
        assert _media_embed_html({'url': code}) == code

    def test_attributes_are_escaped(self):
        html = _media_embed_html(
            {'url': 'https://example.org/"><script>x</script>'})
        assert '<script>' not in html


class TestStripTerriaTabMarkup:

    def test_no_marker_returns_unchanged(self):
        assert _strip_terria_tab_markup('<p>plain</p>') == '<p>plain</p>'

    def test_strips_multiple_blocks(self):
        block = ('<div class="terria-tabs-display"><div>'
                 '<div><iframe></iframe></div></div></div>')
        content = '<p>a</p>%s<p>b</p>%s<p>c</p>' % (block, block)
        result = _strip_terria_tab_markup(content)
        assert result == '<p>a</p><p>b</p><p>c</p>'

    def test_unbalanced_markup_truncates_safely(self):
        content = '<p>a</p><div class="terria-tabs-display"><div>broken'
        assert _strip_terria_tab_markup(content) == '<p>a</p>'
