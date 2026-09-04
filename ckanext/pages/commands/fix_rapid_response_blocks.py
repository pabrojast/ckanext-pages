# -*- coding: utf-8 -*-
"""
CKAN command to repair rapid-response pages whose block/map metadata was
collapsed by the edit-form JSON regression (extras stored as native lists
since a954592 rendered as Python repr, JSON.parse failed, and the fallback
merged every section into a single text block on the next save).

Usage:
    ckan -c /etc/ckan/default/ckan.ini pages fix-rapid-response-blocks
    ckan -c /etc/ckan/default/ckan.ini pages fix-rapid-response-blocks --apply
    ckan -c /etc/ckan/default/ckan.ini pages fix-rapid-response-blocks --page my-page
"""

import ast
import json
import re

import click

import ckan.model as model

from ckanext.pages.db import Page

# blocks-metadata extras key -> JS block id prefix
BLOCK_METADATA_FIELDS = {
    'impact_assessment_blocks_metadata': 'impact',
    'response_activities_blocks_metadata': 'response',
    'recovery_phase_blocks_metadata': 'recovery',
    'resilience_phase_blocks_metadata': 'resilience',
    'additional_info_blocks_metadata': 'additional',
}

# Other JSON-bearing extras the broken re-save wiped to [] (unrecoverable:
# revisions snapshot only `content`). Reported, never modified.
WIPEABLE_JSON_FIELDS = (
    'timeline_events', 'uploaded_images', 'image_gallery', 'countries_affected',
)

IFRAME_RE = re.compile(r'<iframe\b.*?</iframe>', re.IGNORECASE | re.DOTALL)
H3_TAIL_RE = re.compile(r'<h3>(.*?)</h3>\s*$', re.IGNORECASE | re.DOTALL)


def _coerce_to_list(value):
    """Return (list_or_None, was_repr_string). Accepts native lists, JSON
    strings, and repr-corrupted strings (single quotes / None)."""
    if isinstance(value, list):
        return value, False
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return (parsed, False) if isinstance(parsed, list) else (None, False)
        except (ValueError, TypeError):
            pass
        try:
            parsed = ast.literal_eval(value)
            return (parsed, True) if isinstance(parsed, list) else (None, False)
        except (ValueError, SyntaxError):
            pass
    return None, False


def _is_collapsed(blocks):
    """The fallback signature: exactly one text block whose content swallowed
    the whole section HTML, iframe embeds included."""
    return (
        len(blocks) == 1
        and isinstance(blocks[0], dict)
        and blocks[0].get('type') == 'text'
        and '<iframe' in (blocks[0].get('content') or '')
    )


def _resplit_collapsed_html(html, prefix):
    """Best-effort split of collapsed section HTML back into alternating
    text / iframe blocks. The <h3> immediately before an iframe was generated
    from the iframe block's title, so it is recovered as the title (and
    removed from the text, since regeneration re-adds it)."""
    blocks = []
    counter = 0
    pos = 0

    def add(block):
        nonlocal counter
        counter += 1
        block['id'] = '%s-block-%d' % (prefix, counter)
        blocks.append(block)

    for m in IFRAME_RE.finditer(html):
        text = html[pos:m.start()]
        title = ''
        h3 = H3_TAIL_RE.search(text)
        if h3:
            title = h3.group(1).strip()
            text = text[:h3.start()]
        text = text.strip()
        if text:
            add({'type': 'text', 'content': text})
        iframe_html = m.group(0)
        width = re.search(r'width="([^"]*)"', iframe_html)
        height = re.search(r'height="([^"]*)"', iframe_html)
        add({
            'type': 'iframe',
            'title': title,
            # The edit form accepts full embed code in the URL field and
            # passes it through verbatim, so keeping the original iframe
            # HTML preserves every attribute.
            'url': iframe_html,
            'width': width.group(1) if width else '100%',
            'height': height.group(1) if height else '600',
        })
        pos = m.end()

    tail = html[pos:].strip()
    if tail:
        add({'type': 'text', 'content': tail})
    return blocks


@click.command(name='fix-rapid-response-blocks')
@click.option('--apply', 'do_apply', is_flag=True,
              help='Write repairs to the database (default is dry-run)')
@click.option('--page', 'page_name', help='Repair a single page by name')
def fix_rapid_response_blocks(do_apply, page_name):
    """Repair collapsed Maps/Blocks metadata on rapid-response pages."""
    query = model.Session.query(Page).filter(Page.page_type == 'rapid-response')
    if page_name:
        query = query.filter(Page.name == page_name)
    pages = query.all()
    if not pages:
        click.echo('No rapid-response pages found.')
        return

    repaired_pages = 0
    for page in pages:
        try:
            extras = json.loads(page.extras) if isinstance(page.extras, str) else page.extras
        except (ValueError, TypeError):
            click.echo('%s: extras is not valid JSON, skipping' % page.name)
            continue
        if not isinstance(extras, dict):
            continue

        changes = []
        for field, prefix in BLOCK_METADATA_FIELDS.items():
            blocks, was_repr = _coerce_to_list(extras.get(field))
            if blocks is None:
                continue
            if was_repr:
                extras[field] = blocks
                changes.append('%s: repaired repr-corrupted string' % field)
            if _is_collapsed(blocks):
                new_blocks = _resplit_collapsed_html(
                    blocks[0].get('content') or '', prefix)
                if len(new_blocks) > 1 or (
                        new_blocks and new_blocks[0]['type'] == 'iframe'):
                    extras[field] = new_blocks
                    changes.append('%s: re-split 1 collapsed block into %d '
                                   'blocks (%d iframe)' % (
                                       field, len(new_blocks),
                                       sum(1 for b in new_blocks
                                           if b['type'] == 'iframe')))

        if changes:
            repaired_pages += 1
            click.echo('%s:' % page.name)
            for change in changes:
                click.echo('  - %s' % change)
            # Fields the broken re-save may have wiped; flag for manual review.
            for field in WIPEABLE_JSON_FIELDS:
                value = extras.get(field)
                if value in ([], '[]'):
                    click.echo('  ! %s is empty - possibly wiped by the bug, '
                               'unrecoverable from extras' % field)
            if do_apply:
                page.extras = json.dumps(extras)
                model.Session.add(page)

    if repaired_pages and do_apply:
        model.Session.commit()
        click.echo('Applied repairs to %d page(s).' % repaired_pages)
    elif repaired_pages:
        click.echo('Dry-run: %d page(s) would be repaired. '
                   'Re-run with --apply to write.' % repaired_pages)
    else:
        click.echo('Checked %d page(s): no collapsed blocks metadata found.'
                   % len(pages))


def get_commands():
    return [fix_rapid_response_blocks]
