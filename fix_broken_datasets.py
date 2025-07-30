#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to fix broken datasets in CKAN
This script identifies and repairs datasets with common issues like:
- Missing or invalid metadata
- Broken resource URLs
- Encoding problems
- Missing required fields
"""

import sys
import logging
import click
from sqlalchemy import create_engine, text
from datetime import datetime
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatasetFixer:
    def __init__(self, db_url):
        """Initialize the dataset fixer with database connection"""
        self.engine = create_engine(db_url)
        self.fixed_count = 0
        self.error_count = 0
        self.issues_found = []

    def find_broken_datasets(self):
        """Find datasets with potential issues"""
        logger.info("Searching for broken datasets...")
        
        queries = {
            'missing_title': """
                SELECT id, name FROM package 
                WHERE state = 'active' 
                AND (title IS NULL OR title = '')
            """,
            'missing_metadata': """
                SELECT id, name FROM package 
                WHERE state = 'active' 
                AND (
                    author IS NULL OR author = '' OR
                    maintainer IS NULL OR maintainer = '' OR
                    notes IS NULL OR notes = ''
                )
            """,
            'invalid_extras': """
                SELECT DISTINCT p.id, p.name 
                FROM package p
                JOIN package_extra pe ON p.id = pe.package_id
                WHERE p.state = 'active'
                AND pe.state = 'active'
                AND (
                    pe.value IS NULL OR 
                    pe.value = '' OR
                    pe.value = 'None'
                )
            """,
            'broken_resources': """
                SELECT DISTINCT p.id, p.name
                FROM package p
                JOIN resource r ON p.id = r.package_id
                WHERE p.state = 'active'
                AND r.state = 'active'
                AND (
                    r.url IS NULL OR 
                    r.url = '' OR
                    r.url NOT LIKE 'http%'
                )
            """,
            'encoding_issues': """
                SELECT id, name FROM package
                WHERE state = 'active'
                AND (
                    title LIKE '%�%' OR
                    notes LIKE '%�%' OR
                    author LIKE '%�%'
                )
            """
        }
        
        broken_datasets = {}
        
        with self.engine.connect() as conn:
            for issue_type, query in queries.items():
                result = conn.execute(text(query))
                datasets = result.fetchall()
                if datasets:
                    broken_datasets[issue_type] = [
                        {'id': row[0], 'name': row[1]} for row in datasets
                    ]
                    logger.info(f"Found {len(datasets)} datasets with {issue_type}")
        
        return broken_datasets

    def fix_dataset(self, dataset_id, dataset_name, issues):
        """Fix a single dataset based on identified issues"""
        logger.info(f"Fixing dataset: {dataset_name} (ID: {dataset_id})")
        
        try:
            with self.engine.connect() as conn:
                # Begin transaction
                trans = conn.begin()
                
                try:
                    # Fix missing title
                    if 'missing_title' in issues:
                        conn.execute(
                            text("UPDATE package SET title = :title WHERE id = :id"),
                            {'title': f'Dataset {dataset_name}', 'id': dataset_id}
                        )
                        logger.info(f"  - Fixed missing title for {dataset_name}")
                    
                    # Fix missing metadata
                    if 'missing_metadata' in issues:
                        updates = []
                        result = conn.execute(
                            text("SELECT author, maintainer, notes FROM package WHERE id = :id"),
                            {'id': dataset_id}
                        ).fetchone()
                        
                        if not result[0]:
                            updates.append("author = :author")
                        if not result[1]:
                            updates.append("maintainer = :maintainer")
                        if not result[2]:
                            updates.append("notes = :notes")
                        
                        if updates:
                            query = f"UPDATE package SET {', '.join(updates)}, metadata_modified = :modified WHERE id = :id"
                            conn.execute(
                                text(query),
                                {
                                    'author': 'Unknown',
                                    'maintainer': 'Unknown',
                                    'notes': 'No description available',
                                    'modified': datetime.utcnow(),
                                    'id': dataset_id
                                }
                            )
                            logger.info(f"  - Fixed missing metadata for {dataset_name}")
                    
                    # Fix invalid extras
                    if 'invalid_extras' in issues:
                        # Remove empty extras
                        conn.execute(
                            text("""
                                UPDATE package_extra 
                                SET state = 'deleted' 
                                WHERE package_id = :id 
                                AND (value IS NULL OR value = '' OR value = 'None')
                            """),
                            {'id': dataset_id}
                        )
                        logger.info(f"  - Removed invalid extras for {dataset_name}")
                    
                    # Fix broken resources
                    if 'broken_resources' in issues:
                        # Get broken resources
                        resources = conn.execute(
                            text("""
                                SELECT id, url, name 
                                FROM resource 
                                WHERE package_id = :id 
                                AND state = 'active'
                                AND (url IS NULL OR url = '' OR url NOT LIKE 'http%')
                            """),
                            {'id': dataset_id}
                        ).fetchall()
                        
                        for resource in resources:
                            if not resource[1] or not resource[1].startswith('http'):
                                # Mark resource as deleted if URL is completely broken
                                conn.execute(
                                    text("UPDATE resource SET state = 'deleted' WHERE id = :id"),
                                    {'id': resource[0]}
                                )
                                logger.info(f"  - Removed broken resource: {resource[2]}")
                    
                    # Fix encoding issues
                    if 'encoding_issues' in issues:
                        # Get current values
                        result = conn.execute(
                            text("SELECT title, notes, author FROM package WHERE id = :id"),
                            {'id': dataset_id}
                        ).fetchone()
                        
                        updates = []
                        params = {'id': dataset_id}
                        
                        if result[0] and '�' in result[0]:
                            fixed_title = result[0].encode('utf-8', 'ignore').decode('utf-8', 'ignore')
                            updates.append("title = :title")
                            params['title'] = fixed_title
                        
                        if result[1] and '�' in result[1]:
                            fixed_notes = result[1].encode('utf-8', 'ignore').decode('utf-8', 'ignore')
                            updates.append("notes = :notes")
                            params['notes'] = fixed_notes
                        
                        if result[2] and '�' in result[2]:
                            fixed_author = result[2].encode('utf-8', 'ignore').decode('utf-8', 'ignore')
                            updates.append("author = :author")
                            params['author'] = fixed_author
                        
                        if updates:
                            query = f"UPDATE package SET {', '.join(updates)} WHERE id = :id"
                            conn.execute(text(query), params)
                            logger.info(f"  - Fixed encoding issues for {dataset_name}")
                    
                    # Update search index flag
                    conn.execute(
                        text("UPDATE package SET metadata_modified = :modified WHERE id = :id"),
                        {'modified': datetime.utcnow(), 'id': dataset_id}
                    )
                    
                    trans.commit()
                    self.fixed_count += 1
                    logger.info(f"✓ Successfully fixed dataset: {dataset_name}")
                    
                except Exception as e:
                    trans.rollback()
                    raise e
                    
        except Exception as e:
            self.error_count += 1
            logger.error(f"✗ Error fixing dataset {dataset_name}: {str(e)}")
            self.issues_found.append({
                'dataset': dataset_name,
                'error': str(e)
            })

    def generate_report(self):
        """Generate a report of the fixing process"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_fixed': self.fixed_count,
            'total_errors': self.error_count,
            'issues': self.issues_found
        }
        
        # Save report to file
        report_file = f'dataset_fix_report_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to: {report_file}")
        return report


@click.command()
@click.option('--db-url', '-d', required=True, help='PostgreSQL database URL')
@click.option('--dry-run', is_flag=True, help='Show what would be fixed without making changes')
@click.option('--limit', '-l', type=int, help='Limit number of datasets to fix')
@click.option('--dataset', '-n', help='Fix specific dataset by name')
def main(db_url, dry_run, limit, dataset):
    """Fix broken datasets in CKAN"""
    
    logger.info("Starting CKAN Dataset Fixer")
    logger.info(f"Database: {db_url.split('@')[1] if '@' in db_url else 'local'}")
    
    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    
    fixer = DatasetFixer(db_url)
    
    # Find broken datasets
    broken_datasets = fixer.find_broken_datasets()
    
    if not broken_datasets:
        logger.info("No broken datasets found!")
        return
    
    # Count total broken datasets
    total_broken = sum(len(datasets) for datasets in broken_datasets.values())
    logger.info(f"Total broken datasets found: {total_broken}")
    
    if dry_run:
        # Just show what would be fixed
        logger.info("\nDatasets that would be fixed:")
        for issue_type, datasets in broken_datasets.items():
            logger.info(f"\n{issue_type.replace('_', ' ').title()}:")
            for ds in datasets[:10]:  # Show first 10
                logger.info(f"  - {ds['name']} (ID: {ds['id']})")
            if len(datasets) > 10:
                logger.info(f"  ... and {len(datasets) - 10} more")
        return
    
    # Build list of datasets to fix
    datasets_to_fix = {}
    
    if dataset:
        # Fix specific dataset
        found = False
        for issue_type, datasets in broken_datasets.items():
            for ds in datasets:
                if ds['name'] == dataset:
                    if ds['id'] not in datasets_to_fix:
                        datasets_to_fix[ds['id']] = {
                            'name': ds['name'],
                            'issues': [issue_type]
                        }
                    else:
                        datasets_to_fix[ds['id']]['issues'].append(issue_type)
                    found = True
        
        if not found:
            logger.error(f"Dataset '{dataset}' not found in broken datasets")
            return
    else:
        # Fix all broken datasets
        for issue_type, datasets in broken_datasets.items():
            for ds in datasets:
                if ds['id'] not in datasets_to_fix:
                    datasets_to_fix[ds['id']] = {
                        'name': ds['name'],
                        'issues': [issue_type]
                    }
                else:
                    datasets_to_fix[ds['id']]['issues'].append(issue_type)
    
    # Apply limit if specified
    if limit:
        datasets_to_fix = dict(list(datasets_to_fix.items())[:limit])
    
    # Fix datasets
    logger.info(f"\nFixing {len(datasets_to_fix)} datasets...")
    
    for dataset_id, info in datasets_to_fix.items():
        fixer.fix_dataset(dataset_id, info['name'], info['issues'])
    
    # Generate report
    report = fixer.generate_report()
    
    logger.info("\n" + "="*50)
    logger.info("SUMMARY")
    logger.info("="*50)
    logger.info(f"Total datasets processed: {len(datasets_to_fix)}")
    logger.info(f"Successfully fixed: {fixer.fixed_count}")
    logger.info(f"Errors encountered: {fixer.error_count}")
    
    if fixer.error_count > 0:
        logger.warning("\nDatasets with errors:")
        for issue in fixer.issues_found[:10]:
            logger.warning(f"  - {issue['dataset']}: {issue['error']}")
        if len(fixer.issues_found) > 10:
            logger.warning(f"  ... and {len(fixer.issues_found) - 10} more")


if __name__ == '__main__':
    main()