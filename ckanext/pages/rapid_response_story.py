"""Versioned Rapid Response narratives, independent of Data Stories tables.

The document is authoritative once saved. Legacy pages are adapted on read;
the adapter never writes, and unrecognised HTML/blocks are retained verbatim.
"""

import ast
import copy
import json
import re
import uuid
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse


SECTIONS = (
    ('overview', 'Context', 'content', None),
    ('impact', 'Impact Assessment', 'impact_assessment', 'impact_assessment_blocks_metadata'),
    ('response', 'Response Activities', 'response_activities', 'response_activities_blocks_metadata'),
    ('recovery', 'Recovery', 'recovery_phase', 'recovery_phase_blocks_metadata'),
    ('resilience', 'Resilience', 'resilience_phase', 'resilience_phase_blocks_metadata'),
    ('additional', 'Additional Information', 'map_stories', 'additional_info_blocks_metadata'),
)
ORIGINS = {item[0] for item in SECTIONS}
CONTENT_FIELDS = tuple(item[2] for item in SECTIONS)
METADATA_FIELDS = tuple(item[3] for item in SECTIONS if item[3])
SNAPSHOT_FIELDS = CONTENT_FIELDS + METADATA_FIELDS + (
    'rapid_response_story', 'spatial_blocks_metadata', 'header_image', 'excerpt',
    'uploaded_images', 'image_gallery', 'image_carousel', 'key_info',
    'timeline_events', 'key_event_start', 'key_activation',
    'key_world_heritage_sites', 'key_biosphere_reserves', 'key_geoparks',
    'key_people_affected', 'key_casualties', 'key_damage_usd', 'key_cities_affected',
)
ID_RE = re.compile(r'^[a-zA-Z0-9_-]{1,100}$')


def decode(value, legacy=False):
    """Accept native and older double-encoded JSON without evaluating code."""
    for _ in range(2):
        if not isinstance(value, str) or not value.strip():
            return value
        try:
            value = json.loads(value)
        except ValueError:
            if legacy:
                try:
                    return ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    pass
            return value
    return value


def _id(seed):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'rapid-response:' + seed))


def parse_story(value):
    """Strict on structure; keep extra block properties for forward compatibility."""
    story = copy.deepcopy(decode(value))
    if not isinstance(story, dict) or story.get('version') != 1:
        raise ValueError('Unsupported or invalid story document. Your content has not been replaced.')
    if not isinstance(story.get('sections'), list) or not isinstance(story.get('datasets'), list):
        raise ValueError('Story chapters and datasets must be lists.')
    ids = set()

    def identity(item):
        ident = item.get('id')
        if not isinstance(ident, str) or not ID_RE.fullmatch(ident) or ident in ids:
            raise ValueError('Every chapter and block must have a unique, stable ID.')
        ids.add(ident)

    for order, section in enumerate(story['sections']):
        if not isinstance(section, dict):
            raise ValueError('Invalid chapter.')
        identity(section)
        if section.get('origin') not in ORIGINS:
            raise ValueError('Invalid emergency chapter category.')
        if not isinstance(section.get('title'), str) or not section['title'].strip():
            raise ValueError('Every chapter needs a title.')
        blocks = section.get('blocks_metadata')
        if not isinstance(blocks, list):
            raise ValueError('Chapter blocks must be a list.')
        section['order_index'] = order
        for block in blocks:
            if not isinstance(block, dict) or not isinstance(block.get('type'), str):
                raise ValueError('Invalid story block.')
            identity(block)
            for key in ('content', 'url', 'title', 'alt', 'caption', 'width', 'height'):
                if key in block and not isinstance(block[key], str):
                    raise ValueError('Invalid %s in story block.' % key)
            if block['type'] == 'terria':
                tabs = block.get('tabs')
                if not isinstance(tabs, list):
                    raise ValueError('Map tabs must be a list.')
                source_ids = set()
                for tab in tabs:
                    if not isinstance(tab, dict) or not isinstance(tab.get('url'), str):
                        raise ValueError('Invalid map tab.')
                    source_id = tab.get('source_id')
                    if not isinstance(source_id, str) or not ID_RE.fullmatch(source_id) or source_id in source_ids:
                        raise ValueError('Every map source needs a unique ID.')
                    source_ids.add(source_id)
                    if tab['url'] and not _web_url(tab['url']):
                        raise ValueError('Map links must use HTTP or HTTPS.')
            if block['type'] in ('image', 'media') and block.get('url'):
                url = block['url'].strip()
                if not (block['type'] == 'media' and url.startswith('<')) and not _web_url(url):
                    raise ValueError('Image and media links must use HTTP or HTTPS, or a local path.')
    seen = set()
    for dataset in story['datasets']:
        if not isinstance(dataset, dict) or not isinstance(dataset.get('id'), str) or not dataset['id']:
            raise ValueError('Invalid dataset reference.')
        if dataset['id'] in seen:
            raise ValueError('A dataset cannot be linked twice.')
        seen.add(dataset['id'])
    return story


def _web_url(url):
    parsed = urlparse(url)
    return (url.startswith('/') and not url.startswith('//')) or (
        parsed.scheme in ('http', 'https') and bool(parsed.netloc))


class _Iframe(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=False)
        self.attrs = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'iframe' and self.attrs is None:
            self.attrs = dict(attrs)


def legacy_blocks(content, metadata, seed):
    """Keep opaque legacy HTML intact; embeds never pass through Quill."""
    parsed = decode(metadata, legacy=True)
    if not isinstance(parsed, list) or not parsed:
        parsed = [{'type': 'text', 'content': content}] if content else []
    result = []
    for index, source in enumerate(parsed):
        if not isinstance(source, dict):
            # An invalid metadata list must not hide the rendered legacy HTML.
            return [{'id': _id(seed), 'type': 'legacy_html', 'content': content or '',
                     'legacy_metadata': copy.deepcopy(parsed)}]
        block = copy.deepcopy(source)
        block['id'] = _id('%s:%s' % (seed, index))
        for dimension in ('width', 'height'):
            if dimension in block:
                block[dimension] = str(block[dimension] or '')
        if block.get('type') == 'iframe':
            block['type'] = 'media'
        if block.get('type') == 'text' and re.search(
                r'<(?:iframe|embed|object|table|div|video|style|script)\b', block.get('content', ''), re.I):
            block['type'] = 'legacy_html'
        if block.get('type') == 'media':
            raw = block.get('url') or ''
            attrs = _Iframe(raw).attrs if '<iframe' in raw.lower() else None
            url = attrs.get('src', '') if attrs else raw
            if re.search(r'[#&](?:share|start)=', url):
                block['type'] = 'terria'
                block['legacy_embed'] = raw
                block['tabs'] = [{'source_id': _id(seed + ':source:' + str(index)),
                                  'url': url, 'title': block.get('title') or 'Map 1',
                                  'width': str(block.get('width') or '100%'),
                                  'height': str(block.get('height') or '600')}]
        if block.get('type') == 'terria':
            for tab_index, tab in enumerate(block.get('tabs') or []):
                tab.setdefault('source_id', _id('%s:%s:%s' % (seed, index, tab_index)))
        result.append(block)
    return result


def story_for_page(page, new=False):
    if page.get('rapid_response_story') not in (None, ''):
        return parse_story(page['rapid_response_story'])
    sections = []
    for origin, title, field, metadata in SECTIONS:
        raw = page.get(metadata) if metadata else None
        if origin == 'additional' and not raw:
            raw = page.get('spatial_blocks_metadata')
        seed = '%s:%s' % (page.get('name') or 'new', origin)
        blocks = legacy_blocks(page.get(field) or '', raw, seed)
        if blocks or (new and origin != 'additional'):
            sections.append({'id': _id(seed), 'origin': origin, 'section_type': origin,
                             'title': title, 'order_index': len(sections),
                             'blocks_metadata': blocks,
                             'legacy_content': page.get(field) or '',
                             'legacy_blocks': copy.deepcopy(blocks)})
    return {'version': 1, 'sections': sections, 'datasets': []}


def block_html(block):
    """Compatibility projection; the saved document remains the source of truth."""
    kind = block.get('type')
    if kind in ('text', 'legacy_html', 'terria_slide'):
        return block.get('content') or ''
    if kind == 'image':
        if not block.get('url'):
            return ''
        return '<figure><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (
            escape(block['url'], quote=True), escape(block.get('alt') or '', quote=True),
            escape(block.get('caption') or ''))
    if kind == 'terria':
        if block.get('legacy_embed'):
            return block['legacy_embed']
        return '\n'.join(block_html(dict(tab, type='media')) for tab in block.get('tabs', []))
    if kind in ('media', 'iframe'):
        from ckanext.pages.data_stories.helpers.storymap import _media_embed_html
        return _media_embed_html(block)
    return block.get('content') or ''


def project_story(story):
    fields = {}
    for origin, _, field, metadata in SECTIONS:
        sections = [s for s in story['sections'] if s['origin'] == origin]
        blocks = [b for s in sections for b in s['blocks_metadata']]
        fields[field] = '\n'.join(
            section['legacy_content'] if section.get('legacy_blocks') == section['blocks_metadata']
            and 'legacy_content' in section else '\n'.join(block_html(b) for b in section['blocks_metadata'])
            for section in sections)
        if metadata:
            fields[metadata] = copy.deepcopy(blocks)
    return fields


def sync_legacy_submission(story, submitted):
    """Older API clients can still update an explicitly supplied legacy field."""
    result = copy.deepcopy(story)
    projection = project_story(story)
    for origin, title, field, metadata in SECTIONS:
        if field not in submitted and (not metadata or metadata not in submitted):
            continue
        html = submitted.get(field, projection[field])
        raw = decode(submitted.get(metadata), legacy=True) if metadata in submitted else None
        if html == projection[field] and (metadata not in submitted or raw == projection.get(metadata)):
            continue
        existing = [s for s in result['sections'] if s['origin'] == origin]
        section = copy.deepcopy(existing[0]) if existing else {
            'id': _id(origin), 'title': title, 'origin': origin, 'section_type': origin}
        section['blocks_metadata'] = legacy_blocks(html, raw, section['id'])
        position = result['sections'].index(existing[0]) if existing else len(result['sections'])
        result['sections'] = [s for s in result['sections'] if s['origin'] != origin]
        result['sections'].insert(position, section)
    return parse_story(result)


def snapshot(page):
    return {key: copy.deepcopy(page.get(key)) for key in SNAPSHOT_FIELDS}


def restore_content(page, revision):
    """Old revisions restore the overview only, retaining all other chapters."""
    result = copy.deepcopy(page)
    if isinstance(revision.get('rapid_response'), dict):
        result.update(copy.deepcopy(revision['rapid_response']))
    else:
        result['content'] = revision.get('content') or ''
        if page.get('rapid_response_story'):
            result['rapid_response_story'] = sync_legacy_submission(
                parse_story(page['rapid_response_story']), {'content': result['content']})
    return result


def readable_datasets(story, context):
    from ckan.plugins import toolkit as tk
    datasets = []
    # Never render stored labels of private/deleted datasets to another reader.
    for reference in story.get('datasets', []):
        try:
            dataset = tk.get_action('package_show')(context, {'id': reference['id']})
        except (tk.ObjectNotFound, tk.NotAuthorized):
            continue
        datasets.append({'id': dataset['id'], 'name': dataset['name'],
                         'title': dataset.get('title') or dataset['name']})
    return datasets


def view_context(page, context):
    from ckan.plugins import toolkit as tk
    from ckanext.pages.data_stories.helpers.storymap import get_storymap_scenes, get_storymap_config
    from ckanext.pages.rapid_response_media import lazy_media_html
    story = story_for_page(page)
    view = copy.deepcopy(story)
    for section in view['sections']:
        for block in section['blocks_metadata']:
            if block['type'] in ('text', 'legacy_html') or block['type'] not in (
                    'terria', 'terria_slide', 'media', 'image'):
                block['type'] = 'text'
                block['content'] = lazy_media_html(tk.h.render_markdown(block.get('content') or '', allow_html=True))
    view['sections'] = [s for s in view['sections'] if any(block_html(b).strip() for b in s['blocks_metadata'])]
    view['uploaded_images'] = decode(page.get('uploaded_images') or '[]', legacy=True)
    scenes = get_storymap_scenes(view)
    config = get_storymap_config(view, scenes)
    config['mobileStackedMedia'] = True
    config['sceneResolveEndpoint'] = tk.url_for('pages.rapid_response_terria_scene', share_id='__ID__')
    return {'storymap_scenes': scenes, 'storymap_config': config,
            'rr_datasets': readable_datasets(story, context)}
