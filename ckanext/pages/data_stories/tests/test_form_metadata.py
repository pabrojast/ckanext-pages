import html
import json
import pytest
from flask import Flask
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import BadRequest
from ckanext.pages.data_stories.blueprint.routes import _parse_json_field, _extract_sections_form_data


@pytest.mark.parametrize('encode', [lambda value: value, html.escape, json.dumps])
def test_json_and_legacy_encoding_preserve_slide_entities(encode):
    blocks = [{'type':'terria_slide', 'title':'A', 'content':'<p>&quot;A&quot; &amp; B</p>',
               'share_data':{'initSources':[{'name':'Map &quot;A&quot;'}]}}]
    assert _parse_json_field(encode(json.dumps(blocks))) == blocks
    sections = _extract_sections_form_data(MultiDict({
        'sections[0][title]':'Test', 'sections[0][blocks_metadata]':encode(json.dumps(blocks))}))
    assert sections[0]['blocks_metadata'] == blocks


def test_invalid_blocks_are_rejected_instead_of_reconstructed_from_lossy_html():
    form = MultiDict({'sections[0][title]':'Test','sections[0][blocks_metadata]':'[{broken',
                      'sections[0][content]':'<p>Incomplete baked content</p>'})
    app = Flask(__name__)
    app.secret_key = 'isolated-test-key'
    with app.test_request_context('/data-stories/test/edit'):
        with pytest.raises(BadRequest):
            _extract_sections_form_data(form)
