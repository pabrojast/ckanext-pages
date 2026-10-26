"""Width validation, form metadata and the actual reader templates (no DB)."""
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from jinja2 import ChoiceLoader, DictLoader, Environment, FileSystemLoader
from werkzeug.datastructures import MultiDict

from ckan.lib.jinja_extensions import SnippetExtension
from ckan.plugins import toolkit as tk
from ckanext.pages.data_stories.blueprint.routes import _extract_sections_form_data
from ckanext.pages.data_stories.helpers.section_width import (
    get_section_width, normalize_section_width, validate_story_section_widths,
)
from ckanext.pages.data_stories.helpers.storymap import get_storymap_scenes, get_storymap_config


WIDTHS = [None, {'mode': 'full'}, {'mode': 'custom', 'value': 80, 'unit': '%'},
          {'mode': 'custom', 'value': 900, 'unit': 'px'}]
INVALID = [{'mode': 'unknown'}, '80%', {'mode': 'custom'},
           *[{'mode': 'custom', 'value': value, 'unit': '%'}
             for value in (None, '', -1, 0, 101, True, float('nan'), float('inf'), '80')],
           {'mode': 'custom', 'value': 10, 'unit': 'vw'},
           {'mode': 'custom', 'value': 10 ** 400, 'unit': 'px'},
           {'mode': 'custom', 'value': '1; color:red', 'unit': 'px'}]


MEDIA_WIDTHS = [{'mode': 'full'}, {'mode': 'custom', 'value': 80, 'unit': '%'}]


def make_section(width, index=0, layout='full'):
    """``media`` sections use the Text + image / multimedia template with an in-card image."""
    presentation = {'type': 'presentation', 'version': 1, 'layout': layout}
    if width is not None:
        presentation['width'] = width
    content = '<p>Section narrative ' + ('content ' * 70) + '</p>'
    media = '<iframe title="Sized media" src="about:blank" width="600" height="250"></iframe>'
    blocks = [presentation, {'type': 'text', 'content': content},
              {'type': 'media', 'url': 'about:blank', 'width': '600', 'height': '250'}]
    if layout == 'media':
        blocks.append({'type': 'image', 'url': '/picture.png', 'alt': 'Picture', 'display': 'full'})
    prefix = 'width-media-' if layout == 'media' else 'width-'
    return {'id': prefix + str(index), 'section_type': 'introduction', 'title': 'Width %d' % index,
            'is_visible': True, 'order_index': index, 'content': content + media,
            'blocks_metadata': blocks}


@pytest.mark.parametrize('width', WIDTHS + [{'mode': 'normal'}])
def test_width_survives_form_and_scene_continuations(width):
    section = make_section(width)
    section['blocks_metadata'] += [
        {'type': 'image', 'url': '/picture.png', 'display': 'full'},
        {'type': 'text', 'content': '<p>Continued</p>'}]
    sections = _extract_sections_form_data(MultiDict({
        'sections[0][title]': section['title'],
        'sections[0][blocks_metadata]': json.dumps(section['blocks_metadata'])}))
    validate_story_section_widths(sections)
    assert sections[0]['blocks_metadata'] == section['blocks_metadata']
    scenes = get_storymap_scenes({'sections': sections})
    assert len(scenes) == 3
    assert all(scene['width'] == get_section_width(section) for scene in scenes)


@pytest.mark.parametrize('width', MEDIA_WIDTHS)
def test_media_template_keeps_its_media_in_the_card_with_explicit_widths(width):
    """The viewer stacks text and media with CSS, so the scene must stay one narrative card."""
    scenes = get_storymap_scenes({'sections': [make_section(width, 1, layout='media')]})
    assert len(scenes) == 1
    assert scenes[0]['presentation'] == 'media' and scenes[0]['layout'] == 'full'
    assert [block['type'] for block in scenes[0]['blocks']] == ['text', 'media', 'image']
    assert scenes[0]['width']['mode'] == width['mode'] and scenes[0]['width']['css']


@pytest.mark.parametrize('width', INVALID)
def test_invalid_width_is_rejected_and_historical_rendering_is_safe(width):
    with pytest.raises(ValueError):
        normalize_section_width(width)
    with pytest.raises(tk.ValidationError):
        validate_story_section_widths([make_section(width)])
    assert get_section_width(make_section(width)) == {'mode': 'normal', 'css': ''}


@pytest.mark.parametrize('action_name', ['create', 'update', 'import'])
def test_api_rejects_width_before_database_access(monkeypatch, action_name):
    from ckanext.pages.data_stories.actions.create import data_story_section_create
    from ckanext.pages.data_stories.actions.update import data_story_section_update
    from ckanext.pages.data_stories.actions.import_export import data_story_import
    monkeypatch.setattr(tk, 'check_access', lambda *args: True)
    invalid = make_section({'mode': 'custom', 'value': 101, 'unit': '%'})
    actions = {'create': data_story_section_create, 'update': data_story_section_update,
               'import': data_story_import}
    data = ({'data': {'format_version': '1.0', 'story': {'sections': [invalid]}}}
            if action_name == 'import' else invalid)
    with pytest.raises(tk.ValidationError, match='Section width'):
        actions[action_name]({}, data)


class NoBreadcrumbSnippet(SnippetExtension):
    """The classic template only includes the unrelated site breadcrumb."""
    @classmethod
    def _call(cls, args, kwargs):
        assert args == ['snippets/breadcrumb_home.html']
        return ''


def render_fixtures():
    templates = Path(__file__).resolve().parents[2] / 'theme/templates_main'
    env = Environment(autoescape=True, extensions=[NoBreadcrumbSnippet], loader=ChoiceLoader([
        DictLoader({'page.html': '<!doctype html><html><body>{% block content %}{% endblock %}</body></html>'}),
        FileSystemLoader(str(templates)),
    ]))
    env.globals.update(_=lambda value: value, get_flashed_messages=lambda **kw: [],
                       request=SimpleNamespace(url='https://stories.test/classic'),
                       h=SimpleNamespace(get_section_width=get_section_width,
                                         get_section_icon=lambda kind: 'fa-book',
                                         url_for=lambda *a, **kw: '/', check_access=lambda *a: False,
                                         is_sysadmin=lambda: False,
                                         render_datetime=lambda *a, **kw: '2026-10-01'))
    sections = [make_section(width, index) for index, width in enumerate(WIDTHS)]
    sections += [make_section(width, index, layout='media') for index, width in enumerate(MEDIA_WIDTHS, 1)]
    for order, section in enumerate(sections):
        section['order_index'] = order
    story = {'title': 'Section widths', 'slug': 'widths', 'status': 'published', 'sections': sections}
    result = {'classic': env.get_template('data_stories/show.html').render(story=story)}
    scenes = get_storymap_scenes(story)
    for mode in ('storymap', 'slides'):
        config = get_storymap_config(story, scenes)
        config['displayMode'] = mode
        result[mode] = env.get_template('data_stories/components/storymap_viewer.html').render(
            storymap_scenes=scenes, storymap_config=config)
    modes = ''.join('<option value="%s">%s</option>' % (mode, mode)
                    for mode in ('classic', 'storymap', 'slides'))
    editors = ''.join(
        env.get_template('data_stories/components/section_edit.html').render(section=section, section_index=index)
        for index, section in enumerate(story['sections']))
    result['editor'] = ('<form class="data-stories-form"><select id="display_mode">' + modes
                        + '</select><div id="sections-container">' + editors + '</div></form>')
    return result


def test_rendered_templates_use_the_same_safe_widths():
    fixtures = render_fixtures()
    for mode in ('classic', 'storymap', 'slides'):
        assert fixtures[mode].count('data-section-width="normal"') == 1
        assert fixtures[mode].count('data-section-width="full"') == 2
        assert fixtures[mode].count('--ds-section-width: 80%;') == 2
        assert fixtures[mode].count('--ds-section-width: 900px;') == 1
    for mode in ('storymap', 'slides'):
        assert fixtures[mode].count('data-presentation="media"') == 2
        for section_id, width_mode in (('width-media-1', 'full'), ('width-media-2', 'custom')):
            assert re.search(r'id="scene-%s"[^>]*data-presentation="media"[^>]*data-section-width="%s"'
                             % (section_id, width_mode), fixtures[mode])


if __name__ == '__main__':
    print(json.dumps(render_fixtures()))
