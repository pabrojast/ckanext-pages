#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple script to fix broken datasets in CKAN
Run with: python fix_broken_datasets_simple.py postgresql://user:pass@localhost/ckan
"""

import sys
import psycopg2
from datetime import datetime
import json

def fix_broken_datasets(db_url):
    """Fix broken datasets in CKAN database"""
    
    print("Connecting to database...")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    fixed_count = 0
    error_count = 0
    
    try:
        # Find datasets with issues
        print("\nFinding broken datasets...")
        
        # 1. Fix missing titles
        print("\n1. Fixing missing titles...")
        cur.execute("""
            UPDATE package 
            SET title = 'Dataset ' || name,
                metadata_modified = NOW()
            WHERE state = 'active' 
            AND type = 'dataset'
            AND (title IS NULL OR title = '')
            RETURNING id, name
        """)
        fixed_titles = cur.fetchall()
        if fixed_titles:
            print(f"   Fixed {len(fixed_titles)} missing titles")
            fixed_count += len(fixed_titles)
        
        # 2. Fix missing metadata
        print("\n2. Fixing missing metadata...")
        cur.execute("""
            UPDATE package 
            SET author = COALESCE(NULLIF(author, ''), 'Unknown'),
                maintainer = COALESCE(NULLIF(maintainer, ''), 'Unknown'),
                maintainer_email = COALESCE(NULLIF(maintainer_email, ''), 'no-email@example.com'),
                notes = COALESCE(NULLIF(notes, ''), 'No description available'),
                metadata_modified = NOW()
            WHERE state = 'active' 
            AND type = 'dataset'
            AND (
                author IS NULL OR author = '' OR
                maintainer IS NULL OR maintainer = '' OR
                notes IS NULL OR notes = ''
            )
            RETURNING id, name
        """)
        fixed_metadata = cur.fetchall()
        if fixed_metadata:
            print(f"   Fixed {len(fixed_metadata)} datasets with missing metadata")
            fixed_count += len(fixed_metadata)
        
        # 3. Remove invalid extras
        print("\n3. Removing invalid extras...")
        cur.execute("""
            UPDATE package_extra 
            SET state = 'deleted'
            WHERE state = 'active'
            AND (
                value IS NULL OR 
                value = '' OR 
                value = 'None' OR
                value = 'null'
            )
            RETURNING package_id
        """)
        fixed_extras = cur.fetchall()
        if fixed_extras:
            print(f"   Removed {len(fixed_extras)} invalid extras")
        
        # 4. Fix or remove broken resources
        print("\n4. Fixing broken resources...")
        # First, try to fix resources with relative URLs
        cur.execute("""
            UPDATE resource 
            SET url = 'http://placeholder.invalid/' || url
            WHERE state = 'active'
            AND url NOT LIKE 'http%'
            AND url != ''
            RETURNING id, package_id
        """)
        fixed_resources = cur.fetchall()
        if fixed_resources:
            print(f"   Fixed {len(fixed_resources)} resources with relative URLs")
        
        # Remove completely broken resources
        cur.execute("""
            UPDATE resource 
            SET state = 'deleted'
            WHERE state = 'active'
            AND (url IS NULL OR url = '')
            RETURNING id, package_id
        """)
        deleted_resources = cur.fetchall()
        if deleted_resources:
            print(f"   Removed {len(deleted_resources)} resources with empty URLs")
        
        # 5. Fix encoding issues
        print("\n5. Fixing encoding issues...")
        # This is tricky in pure SQL, so we'll do it row by row
        cur.execute("""
            SELECT id, name, title, notes, author
            FROM package
            WHERE state = 'active'
            AND type = 'dataset'
            AND (
                title LIKE '%�%' OR
                notes LIKE '%�%' OR
                author LIKE '%�%'
            )
        """)
        
        encoding_issues = cur.fetchall()
        for row in encoding_issues:
            pkg_id, name, title, notes, author = row
            updates = []
            params = []
            
            if title and '�' in title:
                updates.append("title = %s")
                params.append(title.encode('utf-8', 'ignore').decode('utf-8', 'ignore'))
            
            if notes and '�' in notes:
                updates.append("notes = %s")
                params.append(notes.encode('utf-8', 'ignore').decode('utf-8', 'ignore'))
            
            if author and '�' in author:
                updates.append("author = %s")
                params.append(author.encode('utf-8', 'ignore').decode('utf-8', 'ignore'))
            
            if updates:
                updates.append("metadata_modified = NOW()")
                params.append(pkg_id)
                
                query = f"UPDATE package SET {', '.join(updates)} WHERE id = %s"
                cur.execute(query, params)
                fixed_count += 1
        
        if encoding_issues:
            print(f"   Fixed {len(encoding_issues)} datasets with encoding issues")
        
        # 6. Update metadata_modified for all affected packages
        print("\n6. Updating metadata timestamps...")
        cur.execute("""
            UPDATE package 
            SET metadata_modified = NOW()
            WHERE id IN (
                SELECT DISTINCT package_id 
                FROM resource 
                WHERE state = 'deleted' 
                AND metadata_modified > NOW() - INTERVAL '5 minutes'
            )
        """)
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "="*50)
        print("DATASET REPAIR COMPLETE")
        print("="*50)
        print(f"Total datasets fixed: {fixed_count}")
        print(f"Total errors: {error_count}")
        
        # Generate summary report
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE state = 'active') as active_datasets,
                COUNT(*) FILTER (WHERE state = 'active' AND (title IS NULL OR title = '')) as missing_titles,
                COUNT(*) FILTER (WHERE state = 'active' AND (notes IS NULL OR notes = '')) as missing_descriptions
            FROM package
            WHERE type = 'dataset'
        """)
        stats = cur.fetchone()
        
        print(f"\nCurrent database statistics:")
        print(f"  Active datasets: {stats[0]}")
        print(f"  Missing titles: {stats[1]}")
        print(f"  Missing descriptions: {stats[2]}")
        
        if stats[1] > 0 or stats[2] > 0:
            print("\nWarning: Some issues remain. You may need to run this script again.")
        
    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {str(e)}")
        error_count += 1
    finally:
        cur.close()
        conn.close()
    
    return fixed_count, error_count


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fix_broken_datasets_simple.py <database_url>")
        print("Example: python fix_broken_datasets_simple.py postgresql://user:pass@localhost/ckan")
        sys.exit(1)
    
    db_url = sys.argv[1]
    
    # Add timestamp
    print(f"Starting dataset repair at {datetime.now()}")
    
    try:
        fixed, errors = fix_broken_datasets(db_url)
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'database': db_url.split('@')[1] if '@' in db_url else 'unknown',
            'fixed_count': fixed,
            'error_count': errors
        }
        
        report_file = f'dataset_fix_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved to: {report_file}")
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)