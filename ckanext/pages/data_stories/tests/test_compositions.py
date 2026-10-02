from ckanext.pages.data_stories.helpers.storymap import get_storymap_scenes, get_storymap_config
from ckanext.pages.data_stories.helpers.visuals import presentation_options
from ckanext.pages.rapid_response_story import parse_story

VIEW = '70441d68-3fa1-4e54-b7be-f87b6b27f515'


def test_composed_native_scene_retains_dashboard_references_and_media():
    composition = {'version': 1, 'layout': 'combined', 'text_side': 'right', 'text_width': 50, 'duration': 7,
                   'dashboards': [{'id': 'dashboard', 'view_id': VIEW}],
                   'references': [{'id': 'ref', 'dashboard_id': 'dashboard', 'on_enter': True}],
                   'media': [{'id': 'image', 'type': 'image', 'url': '/story-images/example', 'title': 'Image'}]}
    source = {'type': 'terria', 'tabs': [{'source_id': 'map', 'title': 'Map', 'url': 'https://example.test/terria/#share=example',
              'sequenced': True, 'snapshot': {'version': '8', 'initSources': []}}]}
    slide = {'type': 'terria_slide', 'source_id': 'map', 'slide_id': 'a:1', 'title': 'A', 'content': '<p>Text</p>',
             'share_data': {'version': '8', 'initSources': [{'workbench': ['cog-series']}]}, 'composition': composition}
    story = {'sections': [{'id': 'chapter', 'blocks_metadata': [source, slide]}]}
    scenes = get_storymap_scenes(story)
    composed = next(s for s in scenes if s.get('composed_step'))
    assert composed['composition']['duration'] == 7
    assert composed['references'][0]['dashboard_id'] == 'dashboard'
    assert composed['dashboards'][0]['view_id'] == VIEW
    assert composed['blocks'][-1]['url'] == '/story-images/example'
    assert get_storymap_config(story, scenes)['scenes'][-1]['composedStep']


def test_media_template_keeps_text_and_full_image_in_one_composition():
    scenes = get_storymap_scenes({'sections': [{'id': 'chapter', 'blocks_metadata': [
        {'type': 'presentation', 'layout': 'media'}, {'type': 'text', 'content': '<p>Text</p>'},
        {'type': 'image', 'url': '/image.png', 'display': 'full'}]}]})
    assert len(scenes) == 1
    assert [b['type'] for b in scenes[0]['blocks']] == ['text', 'image']


def test_rapid_response_roundtrip_retains_visual_blocks_and_reading_mode():
    story = {'version': 1, 'display_mode': 'slides', 'datasets': [], 'sections': [{
        'id': 'chapter', 'title': 'Emergency', 'origin': 'overview', 'blocks_metadata': [
            {'id': 'presentation', 'type': 'presentation', 'layout': 'combined', 'duration': 5},
            {'id': 'dashboard', 'type': 'dashboard', 'view_id': VIEW},
            {'id': 'text', 'type': 'text', 'content': '<p>Text</p>', 'references': [{'id': 'ref', 'dashboard_id': 'dashboard'}]}]}]}
    saved = parse_story(story)
    assert parse_story(saved) == saved
    assert saved['display_mode'] == 'slides'
    assert saved['sections'][0]['blocks_metadata'] == story['sections'][0]['blocks_metadata']


def test_presentation_rejects_unbounded_css_and_duration():
    assert presentation_options({'text_width': 'calc(1px)', 'text_side': 'other', 'duration': float('nan')}) == {
        'text_width': 35, 'text_side': 'left', 'duration': 10}


def test_linked_native_story_preserves_scene_references_without_import():
    from urllib.parse import quote
    import json
    share = {'version': '8', 'initSources': [{'stories': [
        {'id': 'a', 'title': 'A', 'text': '<a href="#story-ref-next">Next</a>',
         'composition': {'version': 1, 'layout': 'map', 'references': [{'id': 'next', 'scene_id': 'b'}]}},
        {'id': 'b', 'title': 'B', 'text': '<p>Second scene</p>'}]}]}
    story = {'sections': [{'id': 'chapter', 'blocks_metadata': [{'type': 'terria', 'tabs': [
        {'source_id': 'map', 'url': 'https://example.test/terria/#start=' + quote(json.dumps(share))}]}]}]}
    scenes = get_storymap_scenes(story)
    composed = next(s for s in scenes if s.get('composed_step'))
    assert composed['references'][0]['slide_id'] == 'b'
    assert composed['references'][0]['source_id'] == 'map'
    assert get_storymap_config(story, scenes)['scenes'][-1]['sources'][0]['slideIds'] == ['a', 'b']
