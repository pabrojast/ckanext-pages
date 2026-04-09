# -*- coding: utf-8 -*-
"""
CKAN commands for Data Stories export/import.

Usage:
    ckan -c /etc/ckan/default/ckan.ini pages data-stories-export
    ckan -c /etc/ckan/default/ckan.ini pages data-stories-export --output /tmp/stories.json
    ckan -c /etc/ckan/default/ckan.ini pages data-stories-export --status published

    ckan -c /etc/ckan/default/ckan.ini pages data-stories-import /tmp/stories.json
    ckan -c /etc/ckan/default/ckan.ini pages data-stories-import /tmp/stories.json --preserve-status --preserve-dates
    ckan -c /etc/ckan/default/ckan.ini pages data-stories-import /tmp/stories.json --slug-conflict overwrite --dry-run
"""

import json
import logging
import sys

import click

import ckan.plugins.toolkit as tk
from ckan import model

logger = logging.getLogger(__name__)


def get_commands():
    return [data_stories_export, data_stories_import]


@click.command('data-stories-export')
@click.option('--output', '-o', type=click.Path(), default=None,
              help='Output file path. Prints to stdout if omitted.')
@click.option('--status', type=click.Choice(['draft', 'submitted', 'under_review', 'published', 'archived']),
              default=None, help='Filter by status (exports all if omitted)')
@click.option('--pretty/--compact', default=True,
              help='Pretty-print JSON output (default: pretty)')
def data_stories_export(output, status, pretty):
    """Export all data stories as JSON for migration."""
    flask_app = tk.config.get('flask_app') or tk.config.get('pylons.app')

    site_user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {
        'user': site_user['name'],
        'ignore_auth': True,
        'model': model,
        'session': model.Session,
    }

    data_dict = {'include_metadata': True}
    if status:
        data_dict['status'] = status

    try:
        result = tk.get_action('data_story_bulk_export')(context, data_dict)
    except Exception as e:
        click.echo(f'Error: {str(e)}', err=True)
        raise SystemExit(1)

    total = len(result.get('stories', []))
    indent = 2 if pretty else None
    json_str = json.dumps(result, indent=indent, ensure_ascii=False)

    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(json_str)
        click.echo(f'Exported {total} stories to {output}')
    else:
        click.echo(json_str)
        click.echo(f'\n# Exported {total} stories', err=True)


@click.command('data-stories-import')
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--slug-conflict', type=click.Choice(['rename', 'overwrite', 'error']),
              default='rename', help='Action on slug conflict (default: rename)')
@click.option('--preserve-status', is_flag=True, default=False,
              help='Keep original publication status')
@click.option('--preserve-dates', is_flag=True, default=False,
              help='Keep original created_at/published_at timestamps')
@click.option('--status', type=click.Choice(['draft', 'published']),
              default='draft', help='Status for imported stories (default: draft, ignored with --preserve-status)')
@click.option('--dry-run', is_flag=True, default=False,
              help='Show what would be imported without making changes')
def data_stories_import(filepath, slug_conflict, preserve_status, preserve_dates, status, dry_run):
    """Import data stories from a JSON export file."""
    site_user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {
        'user': site_user['name'],
        'ignore_auth': True,
        'model': model,
        'session': model.Session,
    }

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
    except json.JSONDecodeError as e:
        click.echo(f'Error: Invalid JSON file: {str(e)}', err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f'Error reading file: {str(e)}', err=True)
        raise SystemExit(1)

    is_bulk = 'stories' in export_data and isinstance(export_data.get('stories'), list)
    is_single = 'story' in export_data and isinstance(export_data.get('story'), dict)

    if not is_bulk and not is_single:
        click.echo('Error: JSON file must contain either "stories" (bulk) or "story" (single) key.', err=True)
        raise SystemExit(1)

    if dry_run:
        click.echo('=== DRY RUN (no changes will be made) ===\n')

        if is_bulk:
            stories = export_data['stories']
            click.echo(f'Bulk import: {len(stories)} stories found\n')
            for idx, s in enumerate(stories, 1):
                click.echo(f'  {idx}. "{s.get("title", "Untitled")}" (slug: {s.get("slug", "N/A")}, status: {s.get("status", "N/A")})')
        else:
            s = export_data['story']
            click.echo(f'Single import: "{s.get("title", "Untitled")}" (slug: {s.get("slug", "N/A")}, status: {s.get("status", "N/A")})')
            sections = s.get('sections', [])
            click.echo(f'  Sections: {len(sections)}')
            contributors = s.get('contributors', [])
            click.echo(f'  Contributors: {len(contributors)}')

        click.echo(f'\nOptions: slug_conflict={slug_conflict}, preserve_status={preserve_status}, preserve_dates={preserve_dates}, status={status}')
        return

    try:
        if is_bulk:
            result = tk.get_action('data_story_bulk_import')(context, {
                'data': export_data,
                'slug_conflict': slug_conflict,
                'preserve_status': preserve_status,
                'preserve_dates': preserve_dates,
                'status': status,
            })

            click.echo(f'Bulk import complete:')
            click.echo(f'  Imported: {result["total_imported"]}')
            click.echo(f'  Errors:   {result["total_errors"]}')

            if result.get('imported'):
                click.echo('\nImported stories:')
                for item in result['imported']:
                    click.echo(f'  ✓ "{item["title"]}" → slug: {item["slug"]}')

            if result.get('errors'):
                click.echo('\nErrors:')
                for item in result['errors']:
                    click.echo(f'  ✗ "{item["title"]}" (slug: {item["slug"]}): {item["error"]}')

        else:
            result = tk.get_action('data_story_import')(context, {
                'data': export_data,
                'slug_conflict': slug_conflict,
                'preserve_status': preserve_status,
                'preserve_dates': preserve_dates,
                'status': status,
            })

            info = result.get('import_info', {})
            click.echo(f'Story imported successfully!')
            click.echo(f'  Title: {result.get("title", "N/A")}')
            click.echo(f'  Slug:  {info.get("final_slug", result.get("slug", "N/A"))}')
            click.echo(f'  Sections: {info.get("sections_imported", 0)}')
            click.echo(f'  Contributors: {info.get("contributors_imported", 0)}')

    except Exception as e:
        click.echo(f'Error: {str(e)}', err=True)
        raise SystemExit(1)
