# -*- coding: utf-8 -*-
"""Unit tests for the rapid-response edit-form JSON round-trip fix.

The edit form stores block/map builder state in hidden inputs as JSON
strings, but actions.py stores JSON-parseable extras as native lists/dicts,
so pages_edit must re-serialize them before rendering (otherwise Jinja emits
a Python repr and JSON.parse fails client-side, collapsing the blocks).
"""

import json

from ckanext.pages.utils import (
    RAPID_RESPONSE_JSON_FORM_FIELDS,
    _serialize_json_fields_for_form,
)
from ckanext.pages.commands.fix_rapid_response_blocks import (
    _coerce_to_list,
    _is_collapsed,
    _resplit_collapsed_html,
)


class TestSerializeJsonFieldsForForm(object):

    def test_native_list_becomes_json_string(self):
        blocks = [{'id': 'impact-block-1', 'type': 'text', 'content': '<p>Hi</p>'},
                  {'id': 'impact-block-2', 'type': 'iframe', 'title': 'Map',
                   'url': 'https://example.org', 'width': '100%', 'height': '600'}]
        data = {'impact_assessment_blocks_metadata': blocks}
        _serialize_json_fields_for_form(data, RAPID_RESPONSE_JSON_FORM_FIELDS)
        value = data['impact_assessment_blocks_metadata']
        assert isinstance(value, str)
        assert json.loads(value) == blocks

    def test_native_dict_becomes_json_string(self):
        data = {'timeline_events': {'a': 1}}
        _serialize_json_fields_for_form(data, RAPID_RESPONSE_JSON_FORM_FIELDS)
        assert data['timeline_events'] == '{"a": 1}'

    def test_legacy_json_string_untouched(self):
        legacy = '[{"id": "impact-block-1", "type": "text", "content": "x"}]'
        data = {'impact_assessment_blocks_metadata': legacy}
        _serialize_json_fields_for_form(data, RAPID_RESPONSE_JSON_FORM_FIELDS)
        assert data['impact_assessment_blocks_metadata'] is legacy

    def test_absent_and_empty_fields_untouched(self):
        data = {'uploaded_images': '', 'title': 'unrelated'}
        _serialize_json_fields_for_form(data, RAPID_RESPONSE_JSON_FORM_FIELDS)
        assert data == {'uploaded_images': '', 'title': 'unrelated'}

    def test_all_declared_fields_covered(self):
        data = {field: [] for field in RAPID_RESPONSE_JSON_FORM_FIELDS}
        _serialize_json_fields_for_form(data, RAPID_RESPONSE_JSON_FORM_FIELDS)
        assert all(value == '[]' for value in data.values())


class TestRepairHelpers(object):

    def test_coerce_native_list(self):
        assert _coerce_to_list([1]) == ([1], False)

    def test_coerce_json_string(self):
        assert _coerce_to_list('[{"a": 1}]') == ([{'a': 1}], False)

    def test_coerce_repr_string(self):
        blocks, was_repr = _coerce_to_list("[{'a': None}]")
        assert blocks == [{'a': None}]
        assert was_repr is True

    def test_coerce_garbage(self):
        assert _coerce_to_list('not json') == (None, False)
        assert _coerce_to_list('') == (None, False)
        assert _coerce_to_list(None) == (None, False)

    def test_collapsed_detection(self):
        collapsed = [{'id': 'x', 'type': 'text',
                      'content': '<p>a</p><iframe src="u"></iframe>'}]
        assert _is_collapsed(collapsed)
        assert not _is_collapsed([{'type': 'text', 'content': '<p>a</p>'}])
        assert not _is_collapsed(collapsed + [{'type': 'text', 'content': 'b'}])

    def test_resplit_text_iframe_text(self):
        html = ('<p>Intro</p>\n\n<h3>Flood Map</h3>\n'
                '<iframe src="https://example.org/map" width="100%" height="400" '
                'frameborder="0" allowfullscreen></iframe>\n\n<p>Outro</p>')
        blocks = _resplit_collapsed_html(html, 'impact')
        assert [b['type'] for b in blocks] == ['text', 'iframe', 'text']
        assert blocks[0]['content'] == '<p>Intro</p>'
        assert blocks[1]['title'] == 'Flood Map'
        assert blocks[1]['url'].startswith('<iframe src="https://example.org/map"')
        assert blocks[1]['width'] == '100%'
        assert blocks[1]['height'] == '400'
        assert blocks[2]['content'] == '<p>Outro</p>'
        assert [b['id'] for b in blocks] == [
            'impact-block-1', 'impact-block-2', 'impact-block-3']

    def test_resplit_iframe_only_without_title(self):
        html = '<iframe src="https://example.org"></iframe>'
        blocks = _resplit_collapsed_html(html, 'additional')
        assert len(blocks) == 1
        assert blocks[0]['type'] == 'iframe'
        assert blocks[0]['title'] == ''
        assert blocks[0]['width'] == '100%'
        assert blocks[0]['height'] == '600'
