# Database Connection Fix for ckanext-pages

## Problem Summary

The CKAN logs show several database connection issues:
1. PostgreSQL connection pool exhaustion: "server closed the connection unexpectedly"
2. Invalid transaction states: "Can't reconnect until invalid transaction is rolled back"
3. Connection errors: "error with status PGRES_TUPLES_OK and no message from the libpq"

## Solution Implemented

### 1. Database Utilities Module (`db_utils.py`)
Created a new module with:
- **Retry decorator**: Automatically retries database operations on connection pool errors
- **Session validation**: Ensures database session is valid before operations
- **Proper rollback handling**: Safely handles rollback operations

### 2. Updated Database Models (`db.py`)
- Added retry decorator to `Page.get()` and `Page.pages()` methods
- Improved error handling with proper session rollback
- Added session validation before queries

### 3. Updated Actions (`actions.py`)
- Added try-catch blocks for database operations
- Graceful fallback to empty lists on errors
- Better error logging

## Configuration Recommendations

Add these settings to your CKAN configuration file (`production.ini` or `ckan.ini`):

```ini
# Database connection pool settings
sqlalchemy.pool_size = 10
sqlalchemy.pool_overflow = 20
sqlalchemy.pool_recycle = 3600
sqlalchemy.pool_pre_ping = true

# PostgreSQL specific settings
# Add to your PostgreSQL connection string:
# postgresql://user:pass@localhost/db?connect_timeout=10&options=-c%20statement_timeout=30000
```

## Deployment Instructions

1. **Restart CKAN** to apply the changes:
   ```bash
   sudo supervisorctl restart ckan-uwsgi:*
   ```

2. **Monitor the logs** for improvements:
   ```bash
   tail -f /var/log/ckan/ckan.log
   ```

3. **If issues persist**, check PostgreSQL connection limits:
   ```sql
   -- Check current connections
   SELECT count(*) FROM pg_stat_activity;
   
   -- Check max connections
   SHOW max_connections;
   
   -- Increase if needed (requires PostgreSQL restart)
   ALTER SYSTEM SET max_connections = 200;
   ```

## Testing the Fix

The solution includes automatic retry logic that:
- Retries failed queries up to 3 times
- Implements exponential backoff between retries
- Properly handles session cleanup on errors
- Provides graceful degradation (empty results instead of crashes)

## Additional Recommendations

1. **Database Connection Monitoring**: Set up monitoring for connection pool usage
2. **Regular Maintenance**: Schedule periodic PostgreSQL VACUUM and ANALYZE
3. **Connection Pooling**: Consider using pgBouncer for better connection management
4. **Resource Limits**: Review container/pod resource limits if running in Kubernetes

## Files Modified

- `/ckanext/pages/db.py` - Added retry logic and better error handling
- `/ckanext/pages/db_utils.py` - New utilities for connection management (created)
- `/ckanext/pages/actions.py` - Improved error handling in action functions
- `/DATABASE_CONNECTION_FIX.md` - This documentation file (created)