"""Secuencias guardadas: orden, mapas congelados y compatibilidad editorial."""
from ckanext.pages.data_stories.helpers.storymap import get_storymap_scenes, get_storymap_config


def story(blocks):
    return {'sections': [{'id': 'section', 'title': 'Chapter', 'blocks_metadata': blocks}]}


def source():
    return {'type': 'terria', 'tabs': [{
        'url': 'https://terria.example.org/#share=frozen', 'title': 'Map',
        'source_id': 'map', 'sequenced': True,
        'snapshot': {'version': '8', 'initSources': [{'baseMapName': 'Satellite'}]},
    }]}


def slide(name):
    return {'type': 'terria_slide', 'source_id': 'map', 'slide_id': name,
            'title': name, 'content': '<p>' + name + '</p>',
            'share_data': {'version': '8', 'initSources': [{'name': name}]}}


def no_network(*args):
    raise AssertionError('Saved sequences must not fetch live shares')


def test_interleaved_order_and_frozen_map_data():
    scenes = get_storymap_scenes(story([source(), slide('A'),
        {'type': 'image', 'url': '/image.png', 'display': 'map'},
        {'type': 'text', 'content': 'Between'}, slide('B')]), resolve_share=no_network)
    assert len(scenes) == 1
    assert [b['type'] for b in scenes[0]['blocks']] == ['scene_tabs', 'step', 'image', 'text', 'step']
    config = get_storymap_config({}, scenes)
    stories = config['scenes'][0]['sources'][0]['startData']['initSources'][-1]['stories']
    assert [s['shareData']['initSources'][0]['name'] for s in stories] == ['A', 'B']
    assert config['scenes'][0]['sources'][0]['shareId'] is None


def test_full_image_is_separate_stop_and_next_slide_resumes_correct_map():
    scenes = get_storymap_scenes(story([source(), slide('A'),
        {'type': 'image', 'url': '/image.png', 'display': 'full'}, slide('B')]), resolve_share=no_network)
    assert [s['layout'] for s in scenes] == ['split', 'full', 'split']
    assert len({s['section_id'] for s in scenes}) == 3
    assert scenes[1]['sources'] == []
    assert scenes[2]['initial_step'] == {'sourceIndex': 0, 'stepIndex': 1}
    assert scenes[2]['continuation']


def test_old_image_keeps_map_panel_presentation():
    scenes = get_storymap_scenes(story([source(), {'type': 'image', 'url': '/old.png'}, slide('A')]), resolve_share=no_network)
    assert len(scenes) == 1
    assert scenes[0]['blocks'][1]['display'] == 'map'


def test_retained_removed_slide_is_still_renderable():
    removed = dict(slide('Removed'), orphaned=True)
    scenes = get_storymap_scenes(story([source(), removed]), resolve_share=no_network)
    assert scenes[0]['blocks'][-1]['title'] == 'Removed'


def test_missing_source_keeps_slide_text_without_fetch_or_crash():
    scenes = get_storymap_scenes(story([slide('Saved')]), resolve_share=no_network)
    assert scenes[0]['layout'] == 'full'
    assert 'Saved' in scenes[0]['blocks'][0]['content']


def test_runtime_can_use_dev_without_changing_share_origin(monkeypatch):
    from ckan.plugins import toolkit
    monkeypatch.setitem(toolkit.config, 'ckanext.data_stories.terria_runtime_url', 'https://dev.example.org/terria/')
    scenes = get_storymap_scenes(story([source(), slide('A')]), resolve_share=no_network)
    config = get_storymap_config({}, scenes)
    assert config['embedBaseUrl'].startswith('https://dev.example.org/terria/#')
    assert config['terriaOrigin'] == 'https://dev.example.org'
    assert config['scenes'][0]['sources'][0]['sceneUrl'].startswith('https://terria.example.org/')
