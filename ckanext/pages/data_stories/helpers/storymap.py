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
from urllib.parse import urlparse

from ckanext.pages.data_stories.helpers.terria import get_terria_base_url

log = logging.getLogger(__name__)

# Hash parameters that put Terria in fullscreen-map mode (no workbench or
# explorer panel). They must live in the URL fragment, not the query string:
# Terria parses the fragment as user properties (ViewState.ts).
STORYMAP_EMBED_FLAGS = ('hideWorkbench=1', 'hideExplorerPanel=1')

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


def resolve_terria_share(share_id, timeout=5):
    """
    Resolve a Terria share id to its share JSON via the configured Terria
    instance ('{terria_base}/api/v1/share/<id>'), with an in-process cache.

    Returns the parsed dict, or None on any failure (network, bad id, bad
    JSON) — callers must degrade gracefully.
    """
    import time
    import requests

    if not share_id or not _SHARE_ID_VALID_RE.match(share_id):
        return None

    now = time.time()
    cached = _SHARE_CACHE.get(share_id)
    if cached and now - cached[0] < _SHARE_CACHE_TTL:
        return cached[1]

    resolve_url = '%s/api/v1/share/%s' % (
        get_terria_base_url().rstrip('/'), share_id)
    try:
        resp = requests.get(resolve_url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        log.warning('[STORYMAP] Could not resolve Terria share %s: %s',
                    share_id, e)
        return None

    if not isinstance(data, dict):
        return None

    if len(_SHARE_CACHE) >= _SHARE_CACHE_MAX:
        oldest = min(_SHARE_CACHE, key=lambda k: _SHARE_CACHE[k][0])
        del _SHARE_CACHE[oldest]
    _SHARE_CACHE[share_id] = (now, data)
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


def build_terria_scene_url(share_link):
    """
    Normalize a Terria share link into an embeddable scene URL.

    Keeps the original origin/path and the '#share=' (or '#start=') payload,
    and ensures the fullscreen-embed flags are present in the fragment:

        https://host/terria/#share=g-XXX&hideWorkbench=1&hideExplorerPanel=1

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
                {'type': 'scene_tabs', 'tabs': [{'title', 'scene_url',
                                                 'share_url'}]},
            ],
            'scene_url': str or None,   # map scene shown when card is reached
            'share_url': str or None,   # original share link (open-in-Terria)
            'share_id': str or None,    # Terria share id ('g-xxx')
            'steps': [{'title', 'text'}, ...],  # Terria story scenes inside
                                                # the share (multi-scene only)
        }

    When the section's share contains a multi-scene Terria story, each story
    scene becomes a scroll 'step': the card shows the scene's title and text
    and the viewer applies that scene's shareData as the reader reaches it.

    Sections without a Terria block become narrative-only cards (the map
    keeps the previous scene). Legacy sections without blocks_metadata fall
    back to their baked 'content' HTML with embedded Terria tab markup
    stripped out.

    'resolve_share' lets tests inject a stub resolver; the default fetches
    (and caches) the share JSON from the configured Terria instance.
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
        scene_url = None
        share_url = None

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
                elif block_type == 'terria':
                    tabs = []
                    for tab in block.get('tabs') or []:
                        if not isinstance(tab, dict):
                            continue
                        url = build_terria_scene_url(tab.get('url'))
                        if not url:
                            continue
                        tabs.append({
                            'title': tab.get('title') or
                            'Map %d' % (len(tabs) + 1),
                            'scene_url': url,
                            'share_url': tab.get('url'),
                        })
                    if tabs:
                        blocks.append({'type': 'scene_tabs', 'tabs': tabs})
                        if scene_url is None:
                            scene_url = tabs[0]['scene_url']
                            share_url = tabs[0]['share_url']
        else:
            # Legacy section: baked HTML only. Strip embedded Terria tab
            # markup (the storymap renders the map separately) and fall back
            # to the section-level share link.
            content = _strip_terria_tab_markup(section.get('content') or '')
            if content.strip():
                blocks.append({'type': 'text', 'content': content})
            scene_url = build_terria_scene_url(
                section.get('terria_share_link'))
            if scene_url:
                share_url = section.get('terria_share_link')

        if scene_url is None and section.get('terria_share_link'):
            scene_url = build_terria_scene_url(section['terria_share_link'])
            share_url = section['terria_share_link']

        # Expand multi-scene Terria stories embedded in the share into
        # scroll steps (the card walks through them instead of Terria's
        # native story panel).
        share_id = share_id_from_url(share_url)
        steps = []
        if share_id:
            try:
                stories = _extract_share_stories(resolve_share(share_id))
            except Exception as e:
                log.warning('[STORYMAP] Step expansion failed for share '
                            '%s: %s', share_id, e)
                stories = []
            if len(stories) >= 2:
                steps = [{
                    'title': s.get('title') or 'Scene %d' % (i + 1),
                    'text': s.get('text') or '',
                } for i, s in enumerate(stories)]

        scenes.append({
            'section_id': section.get('id'),
            'title': section.get('title') or '',
            'section_type': section.get('section_type') or '',
            'blocks': blocks,
            'scene_url': scene_url,
            'share_url': share_url,
            'share_id': share_id,
            'steps': steps,
        })

    return scenes


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
                'sceneUrl': s.get('scene_url'),
                'shareId': s.get('share_id'),
                'steps': len(s.get('steps') or []),
            }
            for s in scenes
        ],
        'terriaOrigin': terria_origin,
        'embedBaseUrl': embed_base_url,
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
