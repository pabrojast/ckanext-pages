import pytest

from ckanext.pages.data_stories.helpers.storymap import get_storymap_scenes, get_storymap_config
from ckanext.pages.data_stories.helpers.visuals import dashboard_block, dashboard_state, references

VIEW = '70441d68-3fa1-4e54-b7be-f87b6b27f515'


def test_dashboard_only_section_is_a_visual_scene():
    story = {'sections': [{'id': 'chapter', 'blocks_metadata': [
        {'type': 'dashboard', 'view_id': VIEW, 'id': 'dashboard-1'},
        {'type': 'text', 'content': '<p>Observations</p>', 'id': 'text-1',
         'references': [{'id': 'ref-1', 'dashboard_id': 'dashboard-1', 'on_enter': True,
                         'state': {'filters': [{'field': 'country', 'op': 'eq', 'value': 'Chile'}]}}]},
    ]}]}
    scenes = get_storymap_scenes(story)
    assert scenes[0]['layout'] == 'split'
    assert scenes[0]['sources'] == []
    config = get_storymap_config(story, scenes)
    assert config['hasMedia']
    assert config['scenes'][0]['dashboards'][0]['url'] == '/dashboard/%s/embed' % VIEW
    assert config['scenes'][0]['references'][0]['state']['filters'][0]['value'] == 'Chile'


def test_full_width_keeps_saved_visuals_without_activating_them():
    story = {'sections': [{'id': 'full', 'blocks_metadata': [
        {'type': 'presentation', 'layout': 'full'}, {'type': 'dashboard', 'view_id': VIEW},
        {'type': 'text', 'content': '<p>Text</p>'}]}]}
    scene = get_storymap_scenes(story)[0]
    assert scene['layout'] == 'full'
    assert scene['dashboards'][0]['view_id'] == VIEW


def test_dashboard_urls_cannot_be_injected():
    assert dashboard_block({'view_id': 'https://external.test/x'})['type'] == 'visual_error'
    assert dashboard_block({'view_id': VIEW, 'url': 'javascript:alert(1)'})['url'].startswith('/dashboard/')


@pytest.mark.parametrize('filters', [[{'field': 'a', 'op': 'sql', 'value': 'x'}],
    [{'field': 'a', 'op': 'between', 'value': [1]}], [{'field': 'a', 'op': 'eq', 'value': {}}]])
def test_invalid_filters_are_rejected(filters):
    with pytest.raises(ValueError):
        dashboard_state({'filters': filters})


def test_invalid_references_do_not_break_the_story():
    assert references({'references': [{'id': '<script>'}]}) == []
