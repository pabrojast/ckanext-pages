# encoding: utf-8
"""
Story map (scrollytelling) helpers for data stories.

Builds the scene/card structure consumed by the 'storymap' display mode:
a single sticky Terria iframe whose scene changes as the reader scrolls
through narrative cards. Scenes come from the Terria share links that
authors paste into section blocks (blocks_metadata).
"""

import json
import logging
import re
from html import escape
from urllib.parse import parse_qs, urlparse

from ckanext.pages.data_stories.helpers.terria import get_terria_base_url

log = logging.getLogger(__name__)

# Hash parameters that put Terria in fullscreen-map mode (no workbench or
# explorer panel), keep its native story panel shut ('hideStory=1' — the
# storymap narrates the story itself; stock Terria builds ignore the flag)
# and skip the first-visit welcome modal ('hideWelcomeMessage', honored by
# stock terriajs via interpretHash). They must live in the URL fragment,
# not the query string: Terria parses the fragment as user properties.
STORYMAP_EMBED_FLAGS = ('hideWorkbench=1', 'hideExplorerPanel=1',
                        'hideStory=1', 'hideWelcomeMessage=1')

_YOUTUBE_RE = re.compile(
    r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]+)')

_SHARE_ID_RE = re.compile(r'[#&]share=([A-Za-z0-9_-]{1,128})')
_SHARE_ID_VALID_RE = re.compile(r'^[A-Za-z0-9_-]{1,128}$')

# In-process cache for resolved Terria share JSON: share_id -> (ts, dict)
_SHARE_CACHE = {}
_SHARE_CACHE_TTL = 3600  # seconds
_SHARE_CACHE_MAX = 200


def share_id_from_url(share_link):
    """Extract the share id ('g-xxx') from a Terria share link, or None."""
    if not share_link or not isinstance(share_link, str):
        return None
    match = _SHARE_ID_RE.search(share_link)
    return match.group(1) if match else None


def start_data_from_url(share_link):
    """Decode a Terria ``#start=`` payload, or return ``None``."""
    if not share_link or not isinstance(share_link, str):
        return None
    try:
        fragment = urlparse(share_link.strip()).fragment
        start_value = parse_qs(fragment).get('start', [None])[0]
        if not start_value:
            return None
        data = json.loads(start_value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None

    if not isinstance(data, dict):
        return None
    init_sources = data.get('initSources')
    if init_sources is not None and not isinstance(init_sources, list):
        return None
    return data


def share_api_base_from_url(share_link):
    """
    Derive the Terria share-resolution API base from a share link:

        https://host/terria/#share=g-x  ->  https://host/terria/api/v1/share/

    This keeps share resolution working regardless of what
    'ckanext.pages.terria_base_url' is set to — the share lives on whatever
    instance the author copied the link from.
    """
    if not share_link or not isinstance(share_link, str):
        return None
    try:
        parsed = urlparse(share_link.strip())
    except ValueError:
        return None
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        return None
    base = '%s://%s%s' % (parsed.scheme, parsed.netloc, parsed.path)
    return base.rstrip('/') + '/api/v1/share/'


def _default_share_api_base():
    return get_terria_base_url().rstrip('/') + '/api/v1/share/'


def resolve_terria_share(share_id, api_base=None, timeout=5):
    """
    Resolve a Terria share id to its share JSON, with an in-process cache.

    'api_base' is the share API prefix (see share_api_base_from_url);
    it defaults to the configured Terria instance. Returns the parsed dict,
    or None on any failure (network, bad id, bad JSON) — callers must
    degrade gracefully.
    """
    import time
    import requests

    if not share_id or not _SHARE_ID_VALID_RE.match(share_id):
        return None

    if not api_base:
        api_base = _default_share_api_base()

    cache_key = api_base + share_id
    now = time.time()
    cached = _SHARE_CACHE.get(cache_key)
    if cached and now - cached[0] < _SHARE_CACHE_TTL:
        return cached[1]

    try:
        resp = requests.get(api_base + share_id, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        log.warning('[STORYMAP] Could not resolve Terria share %s at %s: %s',
                    share_id, api_base, e)
        return None

    if not isinstance(data, dict):
        return None

    if len(_SHARE_CACHE) >= _SHARE_CACHE_MAX:
        oldest = min(_SHARE_CACHE, key=lambda k: _SHARE_CACHE[k][0])
        del _SHARE_CACHE[oldest]
    _SHARE_CACHE[cache_key] = (now, data)
    return data


def _extract_share_stories(share_json):
    """
    Return the Terria story scenes embedded in a share JSON
    (initSources[].stories), or an empty list.
    """
    if not isinstance(share_json, dict):
        return []
    for init_source in share_json.get('initSources') or []:
        if isinstance(init_source, dict):
            stories = init_source.get('stories')
            if isinstance(stories, list) and stories:
                return [s for s in stories if isinstance(s, dict)]
    return []


def _story_steps(share_json):
    """Return renderable metadata for every native Terria Story Slide."""
    stories = _extract_share_stories(share_json)
    return [{
        'title': story.get('title') or 'Scene %d' % (index + 1),
        'text': story.get('text') or '',
    } for index, story in enumerate(stories)]


def _scene_source(tab):
    """Normalize one editor tab into a share- or start-backed source."""
    if not isinstance(tab, dict):
        return None

    share_url = tab.get('url')
    scene_url = build_terria_scene_url(share_url)
    if not scene_url:
        return None

    share_id = share_id_from_url(share_url)
    start_data = None if share_id else start_data_from_url(share_url)
    if not share_id and start_data is None:
        return None

    return {
        'title': tab.get('title') or '',
        'scene_url': scene_url,
        'share_url': share_url,
        'share_id': share_id,
        'start_data': start_data,
        'steps': _story_steps(start_data),
    }


def build_terria_scene_url(share_link):
    """
    Normalize a Terria share link into an embeddable scene URL.

    Keeps the original origin/path and the '#share=' (or '#start=') payload,
    and ensures the fullscreen-embed flags are present in the fragment:

        https://host/terria/#share=g-XXX&hideWorkbench=1&hideExplorerPanel=1&hideStory=1

    Returns None if the link has no share/start fragment.
    """
    if not share_link or not isinstance(share_link, str):
        return None

    try:
        parsed = urlparse(share_link.strip())
    except ValueError:
        return None

    if not parsed.scheme or not parsed.netloc or not parsed.fragment:
        return None

    fragment = parsed.fragment
    if not (fragment.startswith('share=') or fragment.startswith('start=')
            or '&share=' in fragment or '&start=' in fragment):
        return None

    for flag in STORYMAP_EMBED_FLAGS:
        name = flag.split('=')[0]
        if name + '=' not in fragment:
            fragment += '&' + flag

    base = '%s://%s%s' % (parsed.scheme, parsed.netloc, parsed.path)
    if parsed.query:
        base += '?' + parsed.query
    return base + '#' + fragment


def get_storymap_scenes(story, resolve_share=None):
    """
    Build the ordered list of storymap chapters (one per visible section).

    Each entry:
        {
            'section_id': str,
            'title': str,
            'section_type': str,
            'blocks': [
                {'type': 'text', 'content': html},
                {'type': 'media', 'embed_html': html},
                {'type': 'image', 'url': url, 'alt': str, 'caption': str},
                {'type': 'scene_tabs', 'tabs': [{'title', 'scene_url',
                                                 'share_url'}]},
            ],
            'sources': [{...}],         # normalized map tabs for the chapter
            'scene_url': str or None,   # default map scene
            'share_url': str or None,   # default original share link
            'share_id': str or None,    # default Terria share id ('g-xxx')
            'start_data': dict or None, # default decoded #start payload
            'steps': [{'title', 'text'}, ...],  # native Terria Story Slides
            'layout': 'split' or 'full',
        }

    When the section's source contains Terria Story Slides, every slide becomes
    a scroll step: the card shows its title and text and the viewer applies its
    shareData as the reader reaches it.

    Sections without a valid Terria source become full-width chapters. Legacy
    sections without blocks_metadata fall back to their baked 'content' HTML
    with embedded Terria tab markup stripped out.

    'resolve_share' lets tests inject a stub resolver (called with
    (share_id, api_base)); the default fetches (and caches) the share JSON
    from the instance the share link points at.
    """
    if resolve_share is None:
        resolve_share = resolve_terria_share

    scenes = []
    sections = sorted(
        (s for s in (story or {}).get('sections', [])
         if s.get('is_visible') is not False),
        key=lambda s: s.get('order_index') or 0)

    for section in sections:
        blocks_raw = section.get('blocks_metadata')
        if isinstance(blocks_raw, str) and blocks_raw.strip():
            try:
                blocks_raw = json.loads(blocks_raw)
            except (TypeError, ValueError):
                log.warning('[STORYMAP] Invalid blocks_metadata JSON in '
                            'section %s', section.get('id'))
                blocks_raw = None

        blocks = []
        sources = []

        if isinstance(blocks_raw, list) and blocks_raw:
            for block in blocks_raw:
                if not isinstance(block, dict):
                    continue
                block_type = block.get('type')
                if block_type == 'text' and block.get('content'):
                    blocks.append({'type': 'text',
                                   'content': block['content']})
                elif block_type == 'media' and block.get('url'):
                    blocks.append({
                        'type': 'media',
                        'embed_html': _media_embed_html(block),
                    })
                elif block_type == 'image' and block.get('url'):
                    # Rendered as a thumbnail trigger in the card; while it
                    # is the active scroll stop the sticky panel shows the
                    # image full-bleed over the map (ArcGIS-style slide).
                    blocks.append({
                        'type': 'image',
                        'url': block['url'],
                        'alt': block.get('alt') or '',
                        'caption': block.get('caption') or '',
                    })
                elif block_type == 'terria':
                    tabs = []
                    for tab in block.get('tabs') or []:
                        source = _scene_source(tab)
                        if not source:
                            continue
                        source['title'] = (
                            source.get('title') or
                            'Map %d' % (len(tabs) + 1)
                        )
                        source['source_index'] = len(sources)
                        sources.append(source)
                        tabs.append({
                            'title': source['title'],
                            'scene_url': source['scene_url'],
                            'share_url': source['share_url'],
                            'source_index': source['source_index'],
                        })
                    if tabs:
                        blocks.append({'type': 'scene_tabs', 'tabs': tabs})
        else:
            # Legacy section: baked HTML only. Strip embedded Terria tab
            # markup (the storymap renders the map separately) and fall back
            # to the section-level share link.
            content = _strip_terria_tab_markup(section.get('content') or '')
            if content.strip():
                blocks.append({'type': 'text', 'content': content})
            legacy_source = _scene_source({
                'title': 'Map 1',
                'url': section.get('terria_share_link'),
            })
            if legacy_source:
                legacy_source['source_index'] = 0
                sources.append(legacy_source)

        # Section-level share-link fallback, scoped to sections where the
        # link is still the only map signal: legacy rows (no usable
        # blocks_metadata) or a terria block whose tabs failed to parse.
        # When blocks_metadata exists and simply has no terria block the
        # author removed the map — a stale link must NOT resurrect it
        # (older editor JS never cleared the hidden field on delete).
        has_terria_block = isinstance(blocks_raw, list) and any(
            isinstance(b, dict) and b.get('type') == 'terria'
            for b in blocks_raw)
        link_is_map_signal = (
            not isinstance(blocks_raw, list) or not blocks_raw or
            has_terria_block)
        if (not sources and section.get('terria_share_link') and
                link_is_map_signal):
            fallback_source = _scene_source({
                'title': 'Map 1',
                'url': section['terria_share_link'],
            })
            if fallback_source:
                fallback_source['source_index'] = 0
                sources.append(fallback_source)

        default_source = sources[0] if sources else {}

        scenes.append({
            'section_id': section.get('id'),
            'title': section.get('title') or '',
            'section_type': section.get('section_type') or '',
            'blocks': blocks,
            'sources': sources,
            'scene_url': default_source.get('scene_url'),
            'share_url': default_source.get('share_url'),
            'share_id': default_source.get('share_id'),
            'start_data': default_source.get('start_data'),
            'layout': 'split' if sources else 'full',
        })

    # Story Slides live in the share JSON: resolve them for EVERY source
    # (not just the default one) so slides authored on any map tab render,
    # then lay each chapter's steps out in source order.
    _resolve_source_steps(
        [source for scene in scenes for source in scene['sources']],
        resolve_share)
    for scene in scenes:
        scene['steps'] = _flatten_scene_steps(scene['sources'])

    return scenes


def _resolve_source_steps(sources, resolve_share):
    """
    Fill source['steps'] from each source's share JSON.

    Sources built from a '#start=' link already carry their steps; the
    rest need one share fetch each (5s timeout, 1h in-process cache in
    the default resolver). Multiple pending shares resolve on a small
    thread pool so a cold cache costs one round-trip, not one per share;
    the single-source path stays synchronous so tests that count resolver
    calls behave deterministically. Failures are logged (share id
    included) and NOT cached, so a transient Terria outage heals on the
    next page load.
    """
    pending = [s for s in sources if s.get('share_id') and not s.get('steps')]
    if not pending:
        return

    def _worker(source):
        share_id = source['share_id']
        try:
            share_data = resolve_share(
                share_id,
                share_api_base_from_url(source.get('share_url')),
            )
        except Exception as e:
            log.warning('[STORYMAP] Story Slide expansion failed for share '
                        '%s: %s', share_id, e)
            share_data = None
        if share_data is None:
            log.warning('[STORYMAP] Steps unavailable for share %s — share '
                        'resolution failed; its Story Slides will not render '
                        'in the storymap', share_id)
        source['steps'] = _story_steps(share_data)

    if len(pending) == 1:
        _worker(pending[0])
        return

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(4, len(pending))) as pool:
        list(pool.map(_worker, pending))


def _flatten_scene_steps(sources):
    """
    Order every source's Story Slides into one scroll-step list.

    Each step keeps its LOCAL index within its source (that is what maps
    to extractStories(share)[stepIndex] in the viewer) plus the source it
    belongs to, so scrolling can switch the map to the right tab.
    """
    steps = []
    for source in sources:
        src_steps = source.get('steps') or []
        for idx, step in enumerate(src_steps):
            steps.append({
                'title': step.get('title') or '',
                'text': step.get('text') or '',
                'source_index': source.get('source_index', 0),
                'step_index': idx,
                'step_total': len(src_steps),
                'source_title': source.get('title') or '',
            })
    return steps


def get_storymap_config(story, scenes=None):
    """
    Build the JSON-serializable config consumed by data-stories-storymap.js.
    """
    from ckan.plugins import toolkit as tk

    if scenes is None:
        scenes = get_storymap_scenes(story)

    first_scene = next(
        (s['scene_url'] for s in scenes if s.get('scene_url')), None)
    terria_origin = None
    if first_scene:
        parsed = urlparse(first_scene)
        terria_origin = '%s://%s' % (parsed.scheme, parsed.netloc)
    else:
        parsed = urlparse(get_terria_base_url())
        if parsed.scheme and parsed.netloc:
            terria_origin = '%s://%s' % (parsed.scheme, parsed.netloc)

    # Bare Terria URL (no share in the hash): used by the postMessage path
    # so the share's embedded stories never load inside the iframe — that is
    # what pops Terria's native (and misplaced) story panel.
    embed_base_url = None
    if first_scene:
        embed_base_url = '%s#%s' % (first_scene.split('#', 1)[0],
                                    '&'.join(STORYMAP_EMBED_FLAGS))

    placeholder_image = None
    for image in (story or {}).get('uploaded_images') or []:
        if isinstance(image, dict) and image.get('url'):
            if placeholder_image is None or image.get('featured'):
                placeholder_image = image['url']
            if image.get('featured'):
                break

    config = {
        'scenes': [
            {
                'id': s.get('section_id'),
                'layout': s.get('layout') or (
                    'split' if s.get('scene_url') else 'full'),
                'sceneUrl': s.get('scene_url'),
                'shareId': s.get('share_id'),
                'startData': s.get('start_data'),
                # Flattened total across all sources; per-source counts
                # below drive the scroll-driven source sequencing.
                'steps': len(s.get('steps') or []),
                'sources': [
                    {
                        'sceneUrl': source.get('scene_url'),
                        'shareId': source.get('share_id'),
                        'startData': source.get('start_data'),
                        'title': source.get('title'),
                        'steps': len(source.get('steps') or []),
                    }
                    for source in (s.get('sources') or [])
                ],
            }
            for s in scenes
        ],
        'terriaOrigin': terria_origin,
        'embedBaseUrl': embed_base_url,
        'hasMedia': bool(first_scene),
        'placeholderImage': placeholder_image,
    }

    try:
        config['sceneResolveEndpoint'] = tk.url_for(
            'data_stories.terria_scene', share_id='__ID__')
    except Exception:
        config['sceneResolveEndpoint'] = None

    return config


def _media_embed_html(block):
    """
    Server-side equivalent of the editor's processContentForEmbed():
    raw embed code passes through, YouTube URLs become embed iframes,
    anything else becomes a plain iframe.
    """
    url = (block.get('url') or '').strip()
    if not url:
        return ''

    title = (block.get('title') or '').strip()
    width = (block.get('width') or '100%').strip()
    height = (block.get('height') or '400').strip()

    heading = '<h3>%s</h3>\n' % escape(title) if title else ''

    if '<iframe' in url or '<embed' in url:
        return heading + url

    youtube = _YOUTUBE_RE.search(url)
    if youtube:
        src = 'https://www.youtube.com/embed/%s' % youtube.group(1)
    else:
        src = url

    return ('%s<iframe src="%s" width="%s" height="%s" frameborder="0" '
            'allowfullscreen></iframe>'
            % (heading, escape(src, quote=True),
               escape(width, quote=True), escape(height, quote=True)))


def _strip_terria_tab_markup(content):
    """
    Remove '<div class="terria-tabs-display">...</div>' blocks (including
    their nested divs) from baked section HTML.
    """
    marker = '<div class="terria-tabs-display">'
    result = content
    while True:
        start = result.find(marker)
        if start == -1:
            return result

        depth = 0
        end = None
        for match in re.finditer(r'<div\b|</div\s*>', result[start:]):
            if match.group().startswith('</'):
                depth -= 1
            else:
                depth += 1
            if depth == 0:
                end = start + match.end()
                break

        if end is None:
            # Unbalanced markup: drop everything from the marker onwards.
            return result[:start]
        result = result[:start] + result[end:]
