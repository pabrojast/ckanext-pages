"""
Database initialization and migration utilities for ckanext-pages
"""
import logging
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError
from ckan import model
from ckan.plugins import toolkit as tk

log = logging.getLogger(__name__)


def ensure_pages_table_exists():
    """
    Ensure that the ckanext_pages table exists with all required columns.
    This function can be called during plugin initialization to ensure
    the database is properly set up.
    """
    try:
        # Check if table exists
        engine = model.meta.engine
        inspector = sa.inspect(engine)
        
        if 'ckanext_pages' not in inspector.get_table_names():
            log.info("Creating ckanext_pages table...")
            create_pages_table()
        else:
            log.info("ckanext_pages table already exists")
            # Check if all required columns exist
            ensure_all_columns_exist()
            
    except Exception as e:
        log.error("Error ensuring pages table exists: %s", str(e))
        raise


def create_pages_table():
    """Create the ckanext_pages table with all required columns"""
    try:
        engine = model.meta.engine
        
        # Create the table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS ckanext_pages (
            id text PRIMARY KEY,
            title text DEFAULT '',
            name text DEFAULT '',
            content text DEFAULT '',
            lang text DEFAULT '',
            "order" text DEFAULT '',
            private boolean DEFAULT true,
            group_id text DEFAULT NULL,
            user_id text DEFAULT '',
            publish_date timestamp without time zone,
            page_type text,
            created timestamp without time zone,
            modified timestamp without time zone,
            extras text DEFAULT '{}',
            revisions jsonb
        );
        """
        
        with engine.connect() as conn:
            conn.execute(sa.text(create_table_sql))
            conn.commit()
            
        log.info("Successfully created ckanext_pages table")
        
    except Exception as e:
        log.error("Error creating ckanext_pages table: %s", str(e))
        raise


def ensure_all_columns_exist():
    """Ensure all required columns exist in the ckanext_pages table"""
    try:
        engine = model.meta.engine
        inspector = sa.inspect(engine)
        
        columns = [col['name'] for col in inspector.get_columns('ckanext_pages')]
        
        # Check for revisions column (added in later migration)
        if 'revisions' not in columns:
            log.info("Adding revisions column to ckanext_pages table...")
            add_revisions_column_sql = """
            ALTER TABLE ckanext_pages 
            ADD COLUMN revisions jsonb;
            """
            
            with engine.connect() as conn:
                conn.execute(sa.text(add_revisions_column_sql))
                conn.commit()
                
            log.info("Successfully added revisions column")
        
        # Check for new submission workflow columns
        new_columns = [
            'submission_status', 'ihp_organization', 'submitted_at',
            'reviewed_at', 'reviewed_by', 'featured'
        ]

        for col_name in new_columns:
            if col_name not in columns:
                log.info(f"Adding {col_name} column to ckanext_pages table...")
                add_missing_column(col_name)

        # Verify all required columns exist
        required_columns = [
            'id', 'title', 'name', 'content', 'lang', 'order', 'private',
            'group_id', 'user_id', 'publish_date', 'page_type', 'created',
            'modified', 'extras', 'revisions', 'submission_status',
            'ihp_organization', 'submitted_at', 'reviewed_at', 'reviewed_by',
            'featured'
        ]
        
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            log.warning("Missing columns in ckanext_pages table: %s", missing_columns)
            # Add missing columns with defaults
            for col in missing_columns:
                add_missing_column(col)
        else:
            log.info("All required columns exist in ckanext_pages table")
            
    except Exception as e:
        log.error("Error checking columns: %s", str(e))
        raise


def add_missing_column(column_name):
    """Add a missing column to the ckanext_pages table"""
    try:
        engine = model.meta.engine
        
        column_definitions = {
            'id': 'text PRIMARY KEY',
            'title': 'text DEFAULT \'\'',
            'name': 'text DEFAULT \'\'',
            'content': 'text DEFAULT \'\'',
            'lang': 'text DEFAULT \'\'',
            'order': 'text DEFAULT \'\'',
            'private': 'boolean DEFAULT true',
            'group_id': 'text DEFAULT NULL',
            'user_id': 'text DEFAULT \'\'',
            'publish_date': 'timestamp without time zone',
            'page_type': 'text',
            'created': 'timestamp without time zone',
            'modified': 'timestamp without time zone',
            'extras': 'text DEFAULT \'{}\'',
            'revisions': 'jsonb',
            # New fields for submission workflow
            'submission_status': 'text DEFAULT \'draft\'',
            'ihp_organization': 'text DEFAULT NULL',
            'submitted_at': 'timestamp without time zone DEFAULT NULL',
            'reviewed_at': 'timestamp without time zone DEFAULT NULL',
            'reviewed_by': 'text DEFAULT NULL',
            'featured': 'boolean NOT NULL DEFAULT false'
        }
        
        if column_name in column_definitions:
            alter_sql = f"""
            ALTER TABLE ckanext_pages 
            ADD COLUMN {column_name} {column_definitions[column_name]};
            """
            
            with engine.connect() as conn:
                conn.execute(sa.text(alter_sql))
                conn.commit()
                
            log.info(f"Successfully added column {column_name}")
        else:
            log.warning(f"Unknown column definition for {column_name}")
            
    except Exception as e:
        log.error(f"Error adding column {column_name}: {str(e)}")
        raise


def check_table_health():
    """Check if the ckanext_pages table is healthy and accessible"""
    try:
        from ckanext.pages.db import Page
        
        # First check basic connectivity
        engine = model.meta.engine
        with engine.connect() as conn:
            # Simple connectivity test
            conn.execute(sa.text("SELECT 1"))
        
        # Try to query the table
        query = model.Session.query(Page).limit(1)
        result = query.first()
        
        log.info("Table health check passed - can query ckanext_pages table")
        return True
        
    except Exception as e:
        error_str = str(e).lower()
        
        # Log different types of errors differently
        if any(keyword in error_str for keyword in [
            'server closed the connection',
            'connection unexpectedly',
            'nonetype',
            'cursor',
            'connection refused',
            'no connection to the server'
        ]):
            log.warning("Table health check failed due to database connection issue: %s", str(e))
        elif 'does not exist' in error_str or 'no such table' in error_str:
            log.warning("Table health check failed - table does not exist: %s", str(e))
        else:
            log.error("Table health check failed: %s", str(e))
            
        return False


def repair_table_if_needed():
    """Attempt to repair the table if there are issues"""
    try:
        # First, check if we have basic database connectivity
        try:
            engine = model.meta.engine
            with engine.connect() as conn:
                # Simple connectivity test
                conn.execute(sa.text("SELECT 1"))
        except Exception as conn_error:
            log.error("Database connection test failed: %s", str(conn_error))
            # If we can't connect to the database at all, don't attempt repair
            error_str = str(conn_error).lower()
            if any(keyword in error_str for keyword in [
                'server closed the connection',
                'connection unexpectedly',
                'nonetype',
                'cursor',
                'connection refused',
                'no connection to the server'
            ]):
                log.warning("Database connection issue detected. Cannot repair table while connection is unstable.")
                return False
            
        if not check_table_health():
            log.info("Attempting to repair ckanext_pages table...")
            ensure_pages_table_exists()
            
            # Test again
            if check_table_health():
                log.info("Table repair successful")
                return True
            else:
                log.error("Table repair failed")
                return False
        else:
            log.info("Table is healthy, no repair needed")
            return True
            
    except Exception as e:
        log.error("Error during table repair: %s", str(e))
        error_str = str(e).lower()
        
        # Don't attempt repair for connection issues
        if any(keyword in error_str for keyword in [
            'server closed the connection',
            'connection unexpectedly',
            'nonetype',
            'cursor',
            'connection refused'
        ]):
            log.warning("Skipping table repair due to database connection issues")
            return False
        return False 