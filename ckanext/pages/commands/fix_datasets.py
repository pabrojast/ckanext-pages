# -*- coding: utf-8 -*-
"""
CKAN command to fix broken datasets
Usage:
    ckan -c /etc/ckan/default/ckan.ini pages fix-datasets
    ckan -c /etc/ckan/default/ckan.ini pages fix-datasets --dry-run
    ckan -c /etc/ckan/default/ckan.ini pages fix-datasets --limit 10
    ckan -c /etc/ckan/default/ckan.ini pages fix-datasets --dataset my-dataset-name
"""

import click
import logging
from datetime import datetime

import ckan.model as model
import ckan.logic as logic
from ckan.common import config
from ckan.lib.cli import load_config

logger = logging.getLogger(__name__)


def get_broken_datasets():
    """Get all datasets with potential issues"""
    issues = {
        'missing_title': [],
        'missing_metadata': [],
        'broken_resources': [],
        'invalid_extras': [],
        'encoding_issues': []
    }
    
    # Get all active datasets
    datasets = model.Session.query(model.Package).filter(
        model.Package.state == 'active',
        model.Package.type == 'dataset'
    ).all()
    
    for dataset in datasets:
        # Check for missing title
        if not dataset.title or dataset.title.strip() == '':
            issues['missing_title'].append(dataset)
        
        # Check for missing metadata
        if (not dataset.author or dataset.author.strip() == '' or
            not dataset.maintainer or dataset.maintainer.strip() == '' or
            not dataset.notes or dataset.notes.strip() == ''):
            issues['missing_metadata'].append(dataset)
        
        # Check for broken resources
        for resource in dataset.resources:
            if resource.state == 'active':
                if not resource.url or not resource.url.startswith('http'):
                    if dataset not in issues['broken_resources']:
                        issues['broken_resources'].append(dataset)
                    break
        
        # Check for invalid extras
        for extra in dataset._extras:
            if extra.state == 'active':
                if not extra.value or extra.value in ['', 'None', 'null']:
                    if dataset not in issues['invalid_extras']:
                        issues['invalid_extras'].append(dataset)
                    break
        
        # Check for encoding issues
        if (dataset.title and '�' in dataset.title or
            dataset.notes and '�' in dataset.notes or
            dataset.author and '�' in dataset.author):
            issues['encoding_issues'].append(dataset)
    
    return issues


def fix_dataset(dataset, issues_list):
    """Fix issues in a dataset"""
    fixes_applied = []
    
    try:
        # Get context for API calls
        context = {
            'model': model,
            'session': model.Session,
            'user': 'admin',
            'ignore_auth': True
        }
        
        # Get current dataset data
        dataset_dict = logic.get_action('package_show')(
            context, {'id': dataset.id}
        )
        
        # Apply fixes based on issues
        if 'missing_title' in issues_list and (not dataset.title or dataset.title.strip() == ''):
            dataset_dict['title'] = f'Dataset {dataset.name}'
            fixes_applied.append('Added missing title')
        
        if 'missing_metadata' in issues_list:
            if not dataset_dict.get('author') or dataset_dict['author'].strip() == '':
                dataset_dict['author'] = 'Unknown'
                fixes_applied.append('Added missing author')
            
            if not dataset_dict.get('maintainer') or dataset_dict['maintainer'].strip() == '':
                dataset_dict['maintainer'] = 'Unknown'
                fixes_applied.append('Added missing maintainer')
            
            if not dataset_dict.get('notes') or dataset_dict['notes'].strip() == '':
                dataset_dict['notes'] = 'No description available'
                fixes_applied.append('Added missing description')
        
        if 'broken_resources' in issues_list:
            # Remove broken resources
            valid_resources = []
            removed_count = 0
            
            for resource in dataset_dict.get('resources', []):
                if resource.get('url') and resource['url'].startswith('http'):
                    valid_resources.append(resource)
                else:
                    removed_count += 1
            
            if removed_count > 0:
                dataset_dict['resources'] = valid_resources
                fixes_applied.append(f'Removed {removed_count} broken resources')
        
        if 'invalid_extras' in issues_list:
            # Clean up extras
            valid_extras = []
            removed_count = 0
            
            for extra in dataset_dict.get('extras', []):
                if extra.get('value') and extra['value'] not in ['', 'None', 'null']:
                    valid_extras.append(extra)
                else:
                    removed_count += 1
            
            if removed_count > 0:
                dataset_dict['extras'] = valid_extras
                fixes_applied.append(f'Removed {removed_count} invalid extras')
        
        if 'encoding_issues' in issues_list:
            # Fix encoding in text fields
            for field in ['title', 'notes', 'author', 'maintainer']:
                if dataset_dict.get(field) and '�' in dataset_dict[field]:
                    # Try to fix encoding
                    try:
                        fixed_text = dataset_dict[field].encode('utf-8', 'ignore').decode('utf-8', 'ignore')
                        dataset_dict[field] = fixed_text
                        fixes_applied.append(f'Fixed encoding in {field}')
                    except:
                        pass
        
        # Update dataset if any fixes were applied
        if fixes_applied:
            logic.get_action('package_update')(context, dataset_dict)
            return True, fixes_applied
        else:
            return False, []
            
    except Exception as e:
        logger.error(f"Error fixing dataset {dataset.name}: {str(e)}")
        return False, [f"Error: {str(e)}"]


@click.command(name='fix-datasets')
@click.option('--dry-run', is_flag=True, help='Show what would be fixed without making changes')
@click.option('--limit', '-l', type=int, help='Limit number of datasets to fix')
@click.option('--dataset', '-d', help='Fix specific dataset by name')
@click.pass_context
def fix_datasets(ctx, dry_run, limit, dataset):
    """Fix broken datasets with missing or invalid metadata"""
    
    load_config(ctx.obj['config'])
    
    logger.info("Starting dataset repair process...")
    
    # Find datasets with issues
    issues = get_broken_datasets()
    
    # Count total issues
    total_issues = sum(len(datasets) for datasets in issues.values())
    
    if total_issues == 0:
        click.echo("No broken datasets found!")
        return
    
    # Display summary
    click.echo(f"\nFound {total_issues} datasets with issues:")
    for issue_type, datasets in issues.items():
        if datasets:
            click.echo(f"  - {issue_type.replace('_', ' ').title()}: {len(datasets)} datasets")
    
    if dry_run:
        click.echo("\nDRY RUN - Showing datasets that would be fixed:")
        count = 0
        for issue_type, datasets in issues.items():
            if datasets:
                click.echo(f"\n{issue_type.replace('_', ' ').title()}:")
                for ds in datasets[:5]:
                    click.echo(f"  - {ds.name} (ID: {ds.id})")
                    count += 1
                    if limit and count >= limit:
                        break
                if len(datasets) > 5 and (not limit or count < limit):
                    click.echo(f"  ... and {len(datasets) - 5} more")
            if limit and count >= limit:
                break
        return
    
    # Build list of datasets to fix
    datasets_to_fix = {}
    
    if dataset:
        # Fix specific dataset
        found = False
        for issue_type, datasets in issues.items():
            for ds in datasets:
                if ds.name == dataset:
                    if ds.id not in datasets_to_fix:
                        datasets_to_fix[ds.id] = {
                            'dataset': ds,
                            'issues': [issue_type]
                        }
                    else:
                        datasets_to_fix[ds.id]['issues'].append(issue_type)
                    found = True
        
        if not found:
            click.echo(f"Dataset '{dataset}' not found in broken datasets")
            return
    else:
        # Fix all datasets
        for issue_type, datasets in issues.items():
            for ds in datasets:
                if ds.id not in datasets_to_fix:
                    datasets_to_fix[ds.id] = {
                        'dataset': ds,
                        'issues': [issue_type]
                    }
                else:
                    datasets_to_fix[ds.id]['issues'].append(issue_type)
    
    # Apply limit
    if limit:
        datasets_to_fix = dict(list(datasets_to_fix.items())[:limit])
    
    # Fix datasets
    click.echo(f"\nFixing {len(datasets_to_fix)} datasets...")
    
    fixed_count = 0
    error_count = 0
    
    with click.progressbar(datasets_to_fix.items(), label='Fixing datasets') as items:
        for dataset_id, info in items:
            success, fixes = fix_dataset(info['dataset'], info['issues'])
            if success:
                fixed_count += 1
                if fixes:
                    logger.info(f"Fixed {info['dataset'].name}: {', '.join(fixes)}")
            else:
                error_count += 1
    
    # Summary
    click.echo(f"\n{'='*50}")
    click.echo("SUMMARY")
    click.echo(f"{'='*50}")
    click.echo(f"Total datasets processed: {len(datasets_to_fix)}")
    click.echo(f"Successfully fixed: {fixed_count}")
    click.echo(f"Errors encountered: {error_count}")
    
    # Rebuild search index
    if fixed_count > 0:
        click.echo("\nRebuilding search index...")
        try:
            from ckan.lib.search import rebuild
            rebuild()
            click.echo("Search index rebuilt successfully")
        except Exception as e:
            click.echo(f"Warning: Could not rebuild search index: {str(e)}")
            click.echo("You may need to run: ckan search-index rebuild")


def get_commands():
    return [fix_datasets]