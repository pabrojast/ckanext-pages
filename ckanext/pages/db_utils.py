"""
Database utilities for handling connection pool issues and session management
"""
import logging
import time
from functools import wraps
from sqlalchemy.exc import DBAPIError, InvalidRequestError, OperationalError
from ckan import model

log = logging.getLogger(__name__)


def with_db_retry(max_retries=3, delay=0.5):
    """
    Decorator to retry database operations on connection pool errors.
    
    :param max_retries: Maximum number of retry attempts
    :param delay: Delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (DBAPIError, InvalidRequestError, OperationalError) as e:
                    last_exception = e
                    error_msg = str(e)
                    
                    # Handle specific connection pool errors
                    if any(msg in error_msg for msg in [
                        "server closed the connection unexpectedly",
                        "connection pool exhausted",
                        "Can't reconnect until invalid transaction is rolled back",
                        "error with status PGRES_TUPLES_OK"
                    ]):
                        log.warning(f"Database connection error on attempt {attempt + 1}/{max_retries}: {error_msg}")
                        
                        # Try to recover the session
                        try:
                            model.Session.rollback()
                            model.Session.remove()
                            model.Session.configure(bind=model.meta.engine)
                        except:
                            pass
                        
                        # Wait before retrying
                        if attempt < max_retries - 1:
                            time.sleep(delay * (attempt + 1))
                            continue
                    
                    # Re-raise if not a connection pool error
                    raise
                except Exception as e:
                    # Log unexpected errors but don't retry
                    log.error(f"Unexpected error in {func.__name__}: {str(e)}")
                    raise
            
            # If all retries failed, raise the last exception
            if last_exception:
                log.error(f"All {max_retries} database retry attempts failed for {func.__name__}")
                raise last_exception
                
        return wrapper
    return decorator


def ensure_valid_session():
    """
    Ensure the current database session is in a valid state.
    This should be called before critical database operations.
    """
    try:
        # Test the connection with a simple query
        model.Session.execute("SELECT 1")
        model.Session.commit()
    except Exception as e:
        log.warning(f"Invalid session detected: {str(e)}")
        try:
            model.Session.rollback()
            model.Session.remove()
            model.Session.configure(bind=model.meta.engine)
        except:
            pass


def safe_commit():
    """
    Safely commit the current transaction with error handling
    """
    try:
        model.Session.commit()
    except Exception as e:
        log.error(f"Error during commit: {str(e)}")
        try:
            model.Session.rollback()
        except:
            pass
        raise


def safe_rollback():
    """
    Safely rollback the current transaction
    """
    try:
        model.Session.rollback()
    except Exception as e:
        log.warning(f"Error during rollback: {str(e)}")
        # Force remove the session if rollback fails
        try:
            model.Session.remove()
        except:
            pass