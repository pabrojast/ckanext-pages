"""Width validation, form metadata and the actual reader templates (no DB)."""
import json
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


def make_section(width, index=0):
    presentation = {'type': 'presentation', 'version': 1, 'layout': 'full'}
    if width is not None:
        presentation['width'] = width
    content = '<p>Section narrative ' + ('content ' * 70) + '</p>'
    media = '<iframe title="Sized media" src="about:blank" width="600" height="250"></iframe>'
    return {'id': 'width-%d' % index, 'section_type': 'introduction', 'title': 'Width %d' % index,
            'is_visible': True, 'order_index': index, 'content': content + media,
            'blocks_metadata': [presentation, {'type': 'text', 'content': content},
                                {'type': 'media', 'url': 'about:blank', 'width': '600', 'height': '250'}]}


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
    story = {'title': 'Section widths', 'slug': 'widths', 'status': 'published',
             'sections': [make_section(width, index) for index, width in enumerate(WIDTHS)]}
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
        assert fixtures[mode].count('data-section-width="full"') == 1
        assert '--ds-section-width: 80%;' in fixtures[mode]
        assert '--ds-section-width: 900px;' in fixtures[mode]


if __name__ == '__main__':
    print(json.dumps(render_fixtures()))
