# -*- coding: utf-8 -*-
"""
CKAN command to seed CRIDA case studies from data files.
Usage:
    ckan -c /etc/ckan/default/ckan.ini pages seed-crida
    ckan -c /etc/ckan/default/ckan.ini pages seed-crida --dry-run
    ckan -c /etc/ckan/default/ckan.ini pages seed-crida --update-existing
"""

import click
import json
import os
import re
import logging

import ckan.logic as logic

logger = logging.getLogger(__name__)

# Approximate coordinates from the UNESCO CRIDA case studies map
COORDINATES = {
    "cl-limari": (-30.60, -71.05, "Aprox (Limarí/Coquimbo)"),
    "zw-chimanimani": (-19.80, 32.87, "Aprox (Chimanimani)"),
    "zm-lusaka-iolanda": (-15.39, 28.32, "Aprox (Lusaka)"),
    "lk-colombo": (6.93, 79.86, "Aprox (Colombo)"),
    "th-bangkok": (13.76, 100.50, "Aprox (Bangkok)"),
    "ph-cebu": (14.60, 121.00, "Aprox (Filipinas; punto representativo)"),
    "th-udon-thani": (17.42, 102.79, "Aprox (Udon Thani)"),
    "co-magdalena": (4.70, -74.10, "Aprox (cuenca Magdalena)"),
    "mx-reserves": (19.43, -99.13, "Aprox (México)"),
    "ec-guayaquil": (-2.17, -79.92, "Aprox (Guayaquil)"),
    "se-municipality": (59.33, 18.07, "Aprox (Suecia)"),
    "nl-deltares-waas": (51.92, 4.48, "Aprox (zona delta Rin)"),
    "us-ca-great-lakes-glam": (44.50, -84.50, "Aprox (Grandes Lagos)"),
    "us-state-water-project": (38.58, -121.49, "Aprox (California)"),
    "us-great-lakes-resilience": (44.50, -84.50, "Aprox (Grandes Lagos)"),
    "pe-chancay-lambayeque": (-6.77, -79.84, "Aprox (Chancay-Lambayeque)"),
    "ga-ntoum": (0.39, 9.77, "Aprox (Gabon; Ntoum)"),
    "bt-thimphu": (27.47, 89.64, "Aprox (Thimphu)"),
    "za-biosphere": (-30.60, 22.90, "Aprox (Sudáfrica)"),
    "do-guayubin": (19.62, -71.33, "Aprox (Rep. Dominicana)"),
    "ke-nairobi": (-1.29, 36.82, "Aprox (Nairobi)"),
    "ar-atuel": (-34.62, -68.33, "Aprox (cuenca Atuel)"),
    "ua-tisza": (48.62, 22.30, "Aprox (zona Tisza)"),
    # Additional from crida.json matching
    "us-great-lakes": (44.50, -84.50, "Aprox (Grandes Lagos)"),
    "bd-dhaka": (23.81, 90.41, "Aprox (Dhaka)"),
}

# Map downloaded images to case study IDs
IMAGE_MAP = {
    "cl-limari": "/images/crida/limari-chile.jpg",
    "zw-chimanimani": "/images/crida/chimanimani-zimbabwe.jpg",
    "zm-lusaka-iolanda": "/images/crida/zambia-water-energy.jpg",
    "lk-colombo": "/images/crida/colombo-sri-lanka.jpg",
    "th-bangkok": "/images/crida/bangkok-thailand.jpg",
    "ph-cebu": "/images/crida/cebu-philippines.jpg",
    "th-udon-thani": "/images/crida/udon-thani-nbs.jpg",
    "co-magdalena-hydropower": "/images/crida/colombia-hydropower.jpg",
    "ec-guayaquil-flood-resilience": "/images/crida/ecuador-flood-resilience.jpg",
    "us-ca-tuolumne-merced": "/images/crida/california-tuolumne.jpg",
    "us-ca-article": "/images/crida/california-crida.jpg",
    "ca-us-glam": "/images/crida/great-lakes-glam.jpg",
    "ga-ntoum": "/images/crida/gabon-ntoum.jpg",
    "bt-nap": "/images/crida/bhutan-nap.jpg",
    "za-be-resilient-program-article": "/images/crida/south-africa-resilient.jpg",
    "za-luvuvhu": "/images/crida/south-africa-luvuvhu.jpg",
    "za-marico": "/images/crida/south-africa-marico.jpg",
    "za-eerste-cape-winelands": "/images/crida/south-africa-eerste.jpg",
    "za-k2c": "/images/crida/south-africa-kruger.jpg",
    "do-guayubin": "/images/crida/dominican-republic.jpg",
    "ar-atuel": "/images/crida/argentina-atuel.jpg",
    "mx-water-reserves": "/images/crida/mexico-water-reserves.jpg",
    "se-municipal-dapp": "/images/crida/sweden-dapp.jpg",
    "nl-waas-lower-rhine": "/images/crida/netherlands-waas.jpg",
    "pe-chancay-lambayeque": "/images/crida/peru-chancay.jpg",
    "ke-water-supply-demand": "/images/crida/kenya-nairobi.jpg",
    "ua-tisza": "/images/crida/ukraine-tisza.jpg",
}


def get_commands():
    return [seed_crida]


def _slugify(text):
    """Create a URL-safe slug from text."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:100].strip('-')


def _load_data():
    """Load and merge data from all data files (lat_lon, crida.json,
    enriched content scraped from UNESCO pages)."""
    data_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'data'
    )

    # Load crida_lat_lon (richer data with 27 items)
    lat_lon_file = os.path.join(data_dir, 'crida_lat_lon')
    items_by_id = {}
    if os.path.exists(lat_lon_file):
        with open(lat_lon_file, 'r', encoding='utf-8') as f:
            lat_lon_data = json.load(f)
        for item in lat_lon_data.get('items', []):
            items_by_id[item['id']] = item

    # Load crida.json (18 items with context/actions/outcomes)
    crida_file = os.path.join(data_dir, 'crida.json')
    crida_items = []
    if os.path.exists(crida_file):
        with open(crida_file, 'r', encoding='utf-8') as f:
            crida_items = json.load(f)

    # Load enriched content (scraped from UNESCO pages)
    enriched_file = os.path.join(data_dir, 'crida_enriched.json')
    enriched = {}
    if os.path.exists(enriched_file):
        with open(enriched_file, 'r', encoding='utf-8') as f:
            enriched = json.load(f)

    # Merge crida.json into lat_lon items by matching title
    title_map = {}
    for item_id, item in items_by_id.items():
        title_map[item['title'].lower().strip()] = item_id

    def _find_match(title):
        """Find matching item by exact title or fuzzy word overlap."""
        t = title.lower().strip()
        if t in title_map:
            return title_map[t]
        # Fuzzy match by word overlap (threshold 40%)
        words = set(t.split())
        best_id, best_score = None, 0
        for llt, lid in title_map.items():
            llt_words = set(llt.split())
            union = len(words | llt_words)
            if union == 0:
                continue
            score = len(words & llt_words) / union
            if score > best_score:
                best_id, best_score = lid, score
        return best_id if best_score >= 0.4 else None

    for cj in crida_items:
        matched_id = _find_match(cj['title'])

        if matched_id:
            # Merge extra fields from crida.json
            item = items_by_id[matched_id]
            if cj.get('context'):
                item['context'] = cj['context']
            if cj.get('actions'):
                item['actions'] = cj['actions']
            if cj.get('outcomes'):
                item['outcomes'] = cj['outcomes']
            if cj.get('image_credit'):
                item['image_credit'] = cj['image_credit']
            if cj.get('summary') and not item.get('summary'):
                item['summary'] = cj['summary']
        else:
            # New item from crida.json not in lat_lon
            new_id = _slugify(cj['title'])[:40]
            items_by_id[new_id] = {
                'id': new_id,
                'country': cj.get('country', ''),
                'title': cj['title'],
                'status': cj.get('status', 'Finished'),
                'themes': cj.get('themes', []),
                'partners': cj.get('partners', []),
                'url_original': cj.get('url', ''),
                'url_unesco': '',
                'image_url': cj.get('image_url', ''),
                'summary': cj.get('summary', ''),
                'highlights': [],
                'context': cj.get('context', ''),
                'actions': cj.get('actions', ''),
                'outcomes': cj.get('outcomes', ''),
                'image_credit': cj.get('image_credit', ''),
            }

    # Merge enriched content from UNESCO scraping (highest priority)
    for item_id, enr in enriched.items():
        if item_id not in items_by_id:
            continue
        item = items_by_id[item_id]
        # Enriched overview becomes the summary if richer
        if enr.get('overview') and (
            not item.get('summary')
            or len(enr['overview']) > len(item.get('summary', ''))
        ):
            item['summary'] = enr['overview']
        # Enriched context/actions/outcomes replace if richer
        if enr.get('context') and (
            not item.get('context')
            or len(enr['context']) > len(item.get('context', ''))
        ):
            item['context'] = enr['context']
        if enr.get('actions') and (
            not item.get('actions')
            or len(enr['actions']) > len(item.get('actions', ''))
        ):
            item['actions'] = enr['actions']
        if enr.get('outcomes') and (
            not item.get('outcomes')
            or len(enr['outcomes']) > len(item.get('outcomes', ''))
        ):
            item['outcomes'] = enr['outcomes']
        # Enriched highlights supplement existing ones
        if enr.get('highlights'):
            existing_hl = item.get('highlights', [])
            if not existing_hl or len(enr['highlights']) > len(existing_hl):
                item['highlights'] = enr['highlights']

    return items_by_id


@click.command('seed-crida')
@click.option('--dry-run', is_flag=True,
              help='Show what would be imported without making changes')
@click.option('--update-existing', is_flag=True,
              help='Update case studies that already exist')
def seed_crida(dry_run, update_existing):
    """Seed CRIDA case studies from data files."""
    items = _load_data()
    click.echo(f'Found {len(items)} CRIDA case studies to import')

    if dry_run:
        click.echo('DRY RUN - no changes will be made\n')

    site_user = logic.get_action('get_site_user')(
        {'ignore_auth': True}, {}
    )
    context = {
        'user': site_user['name'],
        'ignore_auth': True,
    }

    created = 0
    updated = 0
    skipped = 0
    errors = 0

    for item_id, item in items.items():
        name = _slugify(item['title'])[:80] or item_id
        try:
            existing = None
            try:
                existing = logic.get_action('ckanext_pages_show')(
                    dict(context), {'page': name}
                )
            except (logic.NotFound, KeyError):
                pass

            if existing and not update_existing:
                if dry_run:
                    click.echo(f'  [SKIP] {name} (already exists)')
                skipped += 1
                continue

            # Get coordinates
            coords = COORDINATES.get(item_id, (None, None, ''))
            lat, lon, coord_note = (
                coords if len(coords) == 3
                else (coords[0], coords[1], '')
            )

            # Get local image
            header_image = IMAGE_MAP.get(item_id, '')

            page_data = {
                'page': name,
                'name': name,
                'title': item['title'],
                'page_type': 'crida-case-study',
                'content': item.get('summary', ''),
                'excerpt': (item.get('summary', '')[:300]
                            if item.get('summary') else ''),
                'country': item.get('country', ''),
                'crida_status': item.get('status', 'Finished'),
                'themes': json.dumps(item.get('themes', [])),
                'partners': json.dumps(item.get('partners', [])),
                'highlights': json.dumps(item.get('highlights', [])),
                'case_study_url': item.get('url_unesco', ''),
                'external_link': item.get('url_original', ''),
                'crida_context': item.get('context', ''),
                'crida_actions': item.get('actions', ''),
                'crida_outcomes': item.get('outcomes', ''),
                'image_credit': item.get('image_credit', ''),
                'header_image': header_image,
                'publish_date': '2025-01-01',
                'submission_action': 'publish',
            }

            if lat is not None:
                page_data['latitude'] = str(lat)
            if lon is not None:
                page_data['longitude'] = str(lon)
            if coord_note:
                page_data['coord_note'] = coord_note

            if dry_run:
                action = 'UPDATE' if existing else 'CREATE'
                loc = f" ({lat}, {lon})" if lat else " (no coords)"
                click.echo(
                    f'  [DRY-RUN {action}] {item["title"]}{loc}'
                )
                if existing:
                    updated += 1
                else:
                    created += 1
                continue

            logic.get_action('ckanext_pages_update')(
                dict(context), page_data
            )

            if existing:
                updated += 1
                click.echo(f'  [UPDATED] {item["title"]}')
            else:
                created += 1
                click.echo(f'  [CREATED] {item["title"]}')

        except Exception as e:
            errors += 1
            click.echo(f'  [ERROR] {name}: {str(e)}', err=True)
            logger.exception(f'Error importing CRIDA case study: {name}')

    click.echo(
        f'\nResults: {created} created, {updated} updated, '
        f'{skipped} skipped, {errors} errors'
    )
