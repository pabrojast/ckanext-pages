"""Narrative round trips and legacy compatibility (no database required)."""
import copy
import json

import pytest

from ckanext.pages import rapid_response_story as rr


def legacy_page():
    return {
        'name': 'melissa', 'content': '<p class="ql-align-center">Context &amp; facts</p>',
        'impact_assessment': '<p>Impact</p>\n<iframe src="https://example.org/map" height="700"></iframe>',
        'impact_assessment_blocks_metadata': [
            {'id': 'impact-block-1', 'type': 'text', 'content': '<p>Impact</p>'},
            {'id': 'impact-block-3', 'type': 'iframe', 'url': '<iframe src="https://example.org/map" height="700"></iframe>',
             'width': '100%', 'height': 700},
        ],
        'timeline_events': '[{"date":"2025-10-01","description":"Activation"}]',
    }


def test_legacy_adapter_is_read_only_and_repeatable():
    page = legacy_page()
    original = copy.deepcopy(page)
    first = rr.story_for_page(page)
    assert rr.story_for_page(page) == first
    assert page == original
    assert [s['origin'] for s in first['sections']] == ['overview', 'impact']
    assert first['sections'][1]['blocks_metadata'][1]['type'] == 'media'
    assert rr.parse_story(json.dumps(first)) == first
    projection = rr.project_story(first)
    assert projection['content'] == original['content']
    assert projection['impact_assessment'] == original['impact_assessment']


@pytest.mark.parametrize('encode', [lambda x: x, json.dumps, lambda x: json.dumps(json.dumps(x)), repr])
def test_older_metadata_encodings_preserve_blocks(encode):
    page = legacy_page()
    page['impact_assessment_blocks_metadata'] = encode(page['impact_assessment_blocks_metadata'])
    blocks = rr.story_for_page(page)['sections'][1]['blocks_metadata']
    assert [b['type'] for b in blocks] == ['text', 'media']
    assert 'height="700"' in blocks[1]['url']


@pytest.mark.parametrize('metadata', ['', 'not json', {}, [], [False]])
def test_opaque_html_is_never_sent_to_quill(metadata):
    html = '<div style="height:800px"><iframe src="https://example.org"></iframe></div>'
    page = {'name': 'old', 'impact_assessment': html, 'impact_assessment_blocks_metadata': metadata}
    blocks = rr.story_for_page(page)['sections'][0]['blocks_metadata']
    assert blocks[0]['type'] == 'legacy_html'
    assert blocks[0]['content'] == html


def test_terria_legacy_embed_keeps_attributes_and_becomes_a_map_source():
    raw = '<iframe src="https://example.org/terria/#share=g-1" width="87%" allow="fullscreen; geolocation"></iframe>'
    blocks = rr.legacy_blocks('', [{'type': 'iframe', 'url': raw}], 'map')
    assert blocks[0]['type'] == 'terria'
    assert blocks[0]['tabs'][0]['source_id']
    assert rr.block_html(blocks[0]) == raw


def test_new_template_and_empty_existing_event():
    assert rr.story_for_page({'name': 'idai'})['sections'] == []
    story = rr.story_for_page({}, new=True)
    assert [s['origin'] for s in story['sections']] == ['overview', 'impact', 'response', 'recovery', 'resilience']
    assert all(not s['blocks_metadata'] for s in story['sections'])


def test_explicit_empty_document_does_not_resurrect_old_html():
    page = legacy_page()
    page['rapid_response_story'] = {'version': 1, 'sections': [], 'datasets': []}
    assert rr.story_for_page(page)['sections'] == []
    assert not rr.project_story(page['rapid_response_story'])['impact_assessment']


def test_invalid_document_does_not_silently_fall_back():
    page = legacy_page()
    page['rapid_response_story'] = 'broken'
    with pytest.raises(ValueError):
        rr.story_for_page(page)


def test_reordering_and_renaming_keep_semantics_and_ids():
    story = rr.story_for_page(legacy_page())
    story['sections'].reverse()
    story['sections'][0]['title'] = 'Impacts & "observations"'
    story = rr.parse_story(story)
    assert story['sections'][0]['origin'] == 'impact'
    assert rr.project_story(story)['content'] == legacy_page()['content']
    restored = rr.parse_story(json.dumps(story))
    assert restored == story


def test_duplicate_ids_are_rejected_before_any_write():
    story = rr.story_for_page(legacy_page())
    blocks = story['sections'][1]['blocks_metadata']
    blocks[1]['id'] = blocks[0]['id']
    with pytest.raises(ValueError, match='unique'):
        rr.parse_story(story)


def test_unknown_block_properties_survive():
    story = rr.story_for_page(legacy_page())
    block = story['sections'][0]['blocks_metadata'][0]
    block.update(type='future_widget', content='<p>Kept</p>', vendor={'opaque': [1, 2]})
    assert rr.parse_story(story)['sections'][0]['blocks_metadata'][0] == block


def test_legacy_api_update_preserves_other_chapters_and_datasets():
    story = rr.story_for_page(legacy_page())
    story['datasets'] = [{'id': 'dataset-1'}]
    updated = rr.sync_legacy_submission(story, {'content': '<p>New context</p>'})
    assert updated['sections'][1] == story['sections'][1]
    assert updated['datasets'] == story['datasets']
    assert rr.project_story(updated)['content'] == '<p>New context</p>'


def test_full_revision_restores_deleted_chapters_and_media():
    page = legacy_page()
    page['rapid_response_story'] = rr.story_for_page(page)
    page['uploaded_images'] = [{'url': 'https://example.org/photo.png'}]
    revision = {'content': page['content'], 'rapid_response': rr.snapshot(page)}
    changed = dict(page, rapid_response_story={'version': 1, 'sections': [], 'datasets': []}, uploaded_images=[])
    restored = rr.restore_content(changed, revision)
    assert restored['rapid_response_story'] == page['rapid_response_story']
    assert restored['uploaded_images'] == page['uploaded_images']
    assert restored['timeline_events'] == page['timeline_events']


def test_old_revision_restores_only_overview_in_canonical_document():
    page = legacy_page()
    page['rapid_response_story'] = rr.story_for_page(page)
    restored = rr.restore_content(page, {'content': '<p>Older context</p>'})
    assert restored['content'] == '<p>Older context</p>'
    assert rr.project_story(restored['rapid_response_story'])['content'] == '<p>Older context</p>'
    assert restored['rapid_response_story']['sections'][1] == page['rapid_response_story']['sections'][1]


def test_dataset_display_checks_each_readers_permissions(monkeypatch):
    from ckan.plugins import toolkit as tk
    contexts = []

    def show(context, data):
        contexts.append(context)
        if data['id'] == 'private':
            raise tk.NotAuthorized('private')
        if data['id'] == 'deleted':
            raise tk.ObjectNotFound('deleted')
        return {'id': 'public', 'name': 'public', 'title': 'Public data'}

    monkeypatch.setattr(tk, 'get_action', lambda name: show)
    story = {'datasets': [{'id': id, 'title': 'Stored secret'} for id in ['private', 'deleted', 'public']]}
    assert rr.readable_datasets(story, {'user': ''}) == [{'id': 'public', 'name': 'public', 'title': 'Public data'}]
    assert contexts == [{'user': ''}] * 3
