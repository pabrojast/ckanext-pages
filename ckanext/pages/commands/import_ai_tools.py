# -*- coding: utf-8 -*-
"""
CKAN command to import AI water tools from UNESCO seed data.
Usage:
    ckan -c /etc/ckan/default/ckan.ini pages import-ai-tools
    ckan -c /etc/ckan/default/ckan.ini pages import-ai-tools --dry-run
    ckan -c /etc/ckan/default/ckan.ini pages import-ai-tools --update-existing
"""

import click
import json
import os
import logging

import ckan.logic as logic

logger = logging.getLogger(__name__)


def get_commands():
    return [import_ai_tools]


@click.command('import-ai-tools')
@click.option('--dry-run', is_flag=True,
              help='Show what would be imported without making changes')
@click.option('--update-existing', is_flag=True,
              help='Update tools that already exist')
def import_ai_tools(dry_run, update_existing):
    """Import AI water tools from UNESCO document seed data."""
    data_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'data'
    )
    seed_file = os.path.join(data_dir, 'ai_water_tools_seed.json')

    if not os.path.exists(seed_file):
        click.echo(f'Error: Seed file not found at {seed_file}', err=True)
        raise SystemExit(1)

    with open(seed_file, 'r', encoding='utf-8') as f:
        tools = json.load(f)

    click.echo(f'Found {len(tools)} tools to import')

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

    for tool in tools:
        name = tool['name']
        try:
            existing = None
            try:
                existing = logic.get_action('ckanext_pages_show')(
                    dict(context), {'page': name}
                )
            except logic.NotFound:
                pass
            except KeyError:
                pass

            if existing and not update_existing:
                if dry_run:
                    click.echo(f'  [SKIP] {name} (already exists)')
                skipped += 1
                continue

            if dry_run:
                action = 'UPDATE' if existing else 'CREATE'
                click.echo(
                    f'  [DRY-RUN {action}] {tool["title"]} ({name})'
                )
                if existing:
                    updated += 1
                else:
                    created += 1
                continue

            page_data = dict(tool)
            page_data['page'] = name
            page_data['publish_date'] = '2025-01-01'

            logic.get_action('ckanext_pages_update')(dict(context), page_data)

            if existing:
                updated += 1
                click.echo(f'  [UPDATED] {tool["title"]}')
            else:
                created += 1
                click.echo(f'  [CREATED] {tool["title"]}')

        except Exception as e:
            errors += 1
            click.echo(f'  [ERROR] {name}: {str(e)}', err=True)
            logger.exception(f'Error importing {name}')

    click.echo(
        f'\nResults: {created} created, {updated} updated, '
        f'{skipped} skipped, {errors} errors'
    )
