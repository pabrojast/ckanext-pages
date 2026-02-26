import datetime
import uuid
import json
import logging

from collections import OrderedDict
from six import text_type
import sqlalchemy as sa
from sqlalchemy import Column, types
from sqlalchemy.orm import class_mapper
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSONB

# Import database utilities for connection management
try:
    from ckanext.pages.db_utils import with_db_retry, ensure_valid_session, safe_rollback
except ImportError:
    # Fallback if db_utils is not available
    def with_db_retry(max_retries=3, delay=0.5):
        def decorator(func):
            return func
        return decorator
    def ensure_valid_session():
        pass
    def safe_rollback():
        try:
            from ckan import model
            model.Session.rollback()
        except Exception:
            pass

try:
    from sqlalchemy.engine import Row
except ImportError:
    try:
        from sqlalchemy.engine.result import RowProxy as Row
    except ImportError:
        from sqlalchemy.engine.base import RowProxy as Row

from ckan import model
from ckan.model.domain_object import DomainObject

try:
    from ckan.plugins.toolkit import BaseModel
except ImportError:
    # CKAN <= 2.9
    from ckan.model.meta import metadata
    from sqlalchemy.ext.declarative import declarative_base

    BaseModel = declarative_base(metadata=metadata)

pages_table = None

log = logging.getLogger(__name__)


def make_uuid():
    return text_type(uuid.uuid4())


class Page(DomainObject, BaseModel):

    __tablename__ = "ckanext_pages"

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    title = Column(types.UnicodeText, default=u'')
    name = Column(types.UnicodeText, default=u'')
    content = Column(types.UnicodeText, default=u'')
    lang = Column(types.UnicodeText, default=u'')
    order = Column(types.UnicodeText, default=u'')
    private = Column(types.Boolean, default=True)
    group_id = Column(types.UnicodeText, default=None)
    user_id = Column(types.UnicodeText, default=u'')
    publish_date = Column(types.DateTime)
    page_type = Column(types.UnicodeText)
    created = Column(types.DateTime, default=datetime.datetime.utcnow)
    modified = Column(types.DateTime, default=datetime.datetime.utcnow)
    extras = Column(types.UnicodeText, default=u'{}')
    revisions = Column(MutableDict.as_mutable(JSONB), default=u'{}')
    # Submission workflow and organization management
    submission_status = Column(types.UnicodeText, default=u'draft')  # 'draft', 'pending', 'approved', 'rejected'
    ihp_organization = Column(types.UnicodeText, default=None)  # IHP WINS Organization
    submitted_at = Column(types.DateTime, default=None)  # When submitted for approval
    reviewed_at = Column(types.DateTime, default=None)  # When reviewed by admin
    reviewed_by = Column(types.UnicodeText, default=None)  # Admin user who reviewed

    @classmethod
    @with_db_retry(max_retries=3, delay=0.5)
    def get(cls, **kw):
        '''Finds a single entity in the register.'''
        try:
            ensure_valid_session()
            query = model.Session.query(cls).autoflush(False)
            return query.filter_by(**kw).first()
        except Exception as e:
            log.error("Error in Page.get: %s", str(e))
            # Rollback on error to prevent connection pool issues
            safe_rollback()
            return None

    @classmethod
    @with_db_retry(max_retries=3, delay=0.5)
    def pages(cls, **kw):
        '''Finds a single entity in the register.'''
        log = logging.getLogger(__name__)
        try:
            ensure_valid_session()
            order = kw.pop('order', False)
            order_publish_date = kw.pop('order_publish_date', False)

            # New search and filter parameters
            q = kw.pop('q', None)
            event_type = kw.pop('event_type', None)
            priority = kw.pop('priority', None)
            severity = kw.pop('severity', None)  # Added missing severity filter
            country = kw.pop('country', None)
            activity_status = kw.pop('activity_status', None)
            order_by = kw.pop('order_by', None)
            limit = kw.pop('limit', None)
            offset = kw.pop('offset', None)

            # Base query - explicitly select all columns to avoid column mapping issues
            query = model.Session.query(cls).autoflush(False)

            # Handle submission_status filter
            submission_status = kw.pop('submission_status', None)

            # DEBUG: Log all filter parameters
            log.info(
                f"[DB.PAGES] Query filters - kw: {kw}, submission_status: {submission_status}, "
                f"limit: {limit}, offset: {offset}"
            )

            # Apply basic filters
            query = query.filter_by(**kw)

            # Apply submission status filter
            if submission_status:
                query = query.filter(cls.submission_status == submission_status)
                log.info(f"[DB.PAGES] Applying submission_status filter: {submission_status}")
            
            # Apply search query
            if q:
                search_filter = sa.or_(
                    cls.title.ilike('%' + q + '%'),
                    cls.content.ilike('%' + q + '%'),
                    cls.extras.ilike('%' + q + '%')
                )
                query = query.filter(search_filter)
            
            # Apply event type filter (stored in extras JSON)
            if event_type:
                # Map legacy filter values to descriptive subtitles (rapid response)
                event_type_mapping = {
                    'cyclone': 'Tropical Cyclone',
                    'earthquake': 'Earthquake',
                    'tsunami': 'Tsunami',
                    'flood': 'Flood',
                    'fire': 'Wildfire',
                    'conflict': 'Armed Conflict',
                    'volcano': 'Volcanic Eruption',
                    'drought': 'Drought'
                }
                actual_subtitle = event_type_mapping.get(event_type.lower(), event_type)

                # Build a list of candidate titles to support both IDs and human-readable values
                candidate_titles = {actual_subtitle}
                candidate_titles.add(event_type)
                candidate_titles.add(event_type.replace('-', ' ').title())

                event_type_filters = [
                    cls.extras.ilike('%"event_type": "' + event_type + '"%'),
                    cls.extras.ilike('%"event_type": "' + actual_subtitle + '"%'),
                ]

                for title in candidate_titles:
                    event_type_filters.append(
                        cls.extras.ilike('%"subtitle": "' + title + '"%')
                    )

                query = query.filter(sa.or_(*event_type_filters))
            
            # Apply priority filter (stored in extras JSON)
            if priority:
                query = query.filter(
                    cls.extras.ilike('%"priority": "' + priority + '"%')
                )
            
            # Apply severity filter (stored in extras JSON)
            if severity:
                # Debug logging for severity filtering
                log = logging.getLogger(__name__)
                if log.isEnabledFor(logging.DEBUG):
                    log.debug(f"Applying severity filter: {severity}")
                
                severity_filter = sa.or_(
                    # Severity stored in extras JSON - exact match
                    cls.extras.ilike('%"severity": "' + severity + '"%'),
                    # Also check if it's stored without quotes around value
                    cls.extras.ilike('%"severity":' + severity + '%'),
                    # Check for alternative storage format
                    cls.extras.ilike('%severity%' + severity + '%')
                )
                query = query.filter(severity_filter)
            
            # Apply country filter (stored in extras JSON)
            if country:
                # Debug logging for country filtering
                log = logging.getLogger(__name__)
                if log.isEnabledFor(logging.DEBUG):
                    log.debug(f"Applying country filter: {country}")
                
                # Support both new countries_affected format and legacy country format
                country_filter = sa.or_(
                    # New format: countries_affected with JSON array - check for country name in array
                    cls.extras.ilike('%"name": "' + country + '"%'),
                    cls.extras.ilike('%"display_name": "' + country + '"%'),
                    # Legacy format: country field
                    cls.extras.ilike('%"country": "' + country + '"%'),
                    # Backward compatibility: single country field
                    cls.extras.ilike('%"countries_affected": "' + country + '"%'),
                    # Additional patterns for different JSON storage
                    cls.extras.ilike('%"' + country + '"%'),
                    # General search in case of different JSON structure (but more specific)
                    cls.extras.ilike('%' + country + '%')
                )
                query = query.filter(country_filter)
            
            # Apply activity status filter (stored in extras JSON)
            if activity_status:
                # Debug logging for activity status filtering
                log = logging.getLogger(__name__)
                if log.isEnabledFor(logging.DEBUG):
                    log.debug(f"Applying activity_status filter: {activity_status}")
                
                activity_filter = sa.or_(
                    # Activity status stored in extras JSON - exact match
                    cls.extras.ilike('%"activity_status": "' + activity_status + '"%'),
                    # Also handle JSON without spaces after colon
                    cls.extras.ilike('%"activity_status":"' + activity_status + '"%')
                )
                query = query.filter(activity_filter)
            
            # Open-source-software specific filters (stored in extras JSON)
            # Handle category filter (can be list or single value)
            category = kw.pop('category', None)
            if category:
                if isinstance(category, list):
                    # Multiple categories - use OR condition
                    category_filters = []
                    for cat in category:
                        if cat.strip():
                            cat_filter = sa.or_(
                                cls.extras.ilike('%"software_category": "' + cat.strip() + '"%'),
                                cls.extras.ilike('%"software_category":' + cat.strip() + '%')
                            )
                            category_filters.append(cat_filter)
                    if category_filters:
                        query = query.filter(sa.or_(*category_filters))
                else:
                    # Single category
                    category_filter = sa.or_(
                        cls.extras.ilike('%"software_category": "' + category + '"%'),
                        cls.extras.ilike('%"software_category":' + category + '%')
                    )
                    query = query.filter(category_filter)
            
            # Handle language filter (can be list or single value)
            language = kw.pop('language', None)
            if language:
                if isinstance(language, list):
                    # Multiple languages - use OR condition
                    language_filters = []
                    for lang in language:
                        if lang.strip():
                            lang_filter = sa.or_(
                                cls.extras.ilike('%"programming_language": "' + lang.strip() + '"%'),
                                cls.extras.ilike('%"programming_language":' + lang.strip() + '%')
                            )
                            language_filters.append(lang_filter)
                    if language_filters:
                        query = query.filter(sa.or_(*language_filters))
                else:
                    # Single language
                    language_filter = sa.or_(
                        cls.extras.ilike('%"programming_language": "' + language + '"%'),
                        cls.extras.ilike('%"programming_language":' + language + '%')
                    )
                    query = query.filter(language_filter)
            
            # Handle other open-source-software filters
            for filter_name, field_name in [
                ('access_type', 'access_type'),
                ('license', 'software_license'), 
                ('platform', 'platform'),
                ('attribution', 'attribution')
            ]:
                filter_value = kw.pop(filter_name, None)
                if filter_value:
                    filter_condition = sa.or_(
                        cls.extras.ilike('%"' + field_name + '": "' + filter_value + '"%'),
                        cls.extras.ilike('%"' + field_name + '":' + filter_value + '%')
                    )
                    query = query.filter(filter_condition)

            # AI Water Tools specific filters (stored in extras JSON)
            # Handle ai_technique filter (can be list or single value)
            ai_technique = kw.pop('ai_technique', None)
            if ai_technique:
                if isinstance(ai_technique, list):
                    technique_filters = []
                    for tech in ai_technique:
                        if tech.strip():
                            tech_filter = sa.or_(
                                cls.extras.ilike('%"ai_technique": "' + tech.strip() + '"%'),
                                cls.extras.ilike('%"ai_technique":' + tech.strip() + '%')
                            )
                            technique_filters.append(tech_filter)
                    if technique_filters:
                        query = query.filter(sa.or_(*technique_filters))
                else:
                    technique_filter = sa.or_(
                        cls.extras.ilike('%"ai_technique": "' + ai_technique + '"%'),
                        cls.extras.ilike('%"ai_technique":' + ai_technique + '%')
                    )
                    query = query.filter(technique_filter)

            # Handle water_application filter (can be list or single value)
            water_application = kw.pop('water_application', None)
            if water_application:
                if isinstance(water_application, list):
                    app_filters = []
                    for app in water_application:
                        if app.strip():
                            app_filter = sa.or_(
                                cls.extras.ilike('%"water_application": "' + app.strip() + '"%'),
                                cls.extras.ilike('%"water_application":' + app.strip() + '%')
                            )
                            app_filters.append(app_filter)
                    if app_filters:
                        query = query.filter(sa.or_(*app_filters))
                else:
                    app_filter = sa.or_(
                        cls.extras.ilike('%"water_application": "' + water_application + '"%'),
                        cls.extras.ilike('%"water_application":' + water_application + '%')
                    )
                    query = query.filter(app_filter)

            # Handle other ai-water-tools filters
            for filter_name, field_name in [
                ('maturity_level', 'maturity_level'),
                ('scalability', 'scalability'),
                ('ai_model_type', 'ai_model_type'),
                ('development_status', 'development_status'),
                ('water_application_category', 'water_application_category'),
                ('technology_readiness_level', 'technology_readiness_level'),
                ('spatial_scale', 'spatial_scale'),
                ('temporal_scale', 'temporal_scale'),
            ]:
                filter_value = kw.pop(filter_name, None)
                if filter_value:
                    filter_condition = sa.or_(
                        cls.extras.ilike('%"' + field_name + '": "' + filter_value + '"%'),
                        cls.extras.ilike('%"' + field_name + '":' + filter_value + '%')
                    )
                    query = query.filter(filter_condition)
            
            # Apply ordering - improved with GDACS Alert Level
            if order_by == 'recent':
                query = query.order_by(cls.publish_date.desc().nullslast(), cls.created.desc())
            elif order_by == 'oldest':
                # New: Oldest first option
                query = query.order_by(cls.publish_date.asc().nullsfirst(), cls.created.asc())
            elif order_by == 'gdacs_alert':
                # New: Order by GDACS Alert Level (post-processing for complex logic)
                query = query.order_by(cls.publish_date.desc().nullslast(), cls.created.desc())
            elif order_by == 'severity':
                # Order by severity using post-processing (kept for backward compatibility)
                query = query.order_by(cls.publish_date.desc().nullslast(), cls.created.desc())
            elif order_by == 'country':
                # Order alphabetically by title (kept for backward compatibility)  
                query = query.order_by(cls.title.asc())
            elif order:
                # Safe ordering by order field
                try:
                    query = query.filter(cls.order != '').order_by(sa.cast(cls.order, sa.Integer))
                except (sa.exc.DataError, sa.exc.ProgrammingError, Exception):
                    # Fallback to string ordering if cast fails
                    query = query.filter(cls.order != '').order_by(cls.order)
            elif order_publish_date:
                query = query.order_by(cls.publish_date.desc().nullslast(), cls.created.desc())
            else:
                # Default ordering
                query = query.order_by(cls.created.desc())

            # Apply pagination controls if provided
            if offset:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            
            # Execute query with error handling
            try:
                results = query.all()
                
                # Post-process results for complex sorting if needed
                if order_by == 'severity':
                    results = cls._sort_by_severity(results)
                elif order_by == 'gdacs_alert':
                    results = cls._sort_by_gdacs_alert_level(results)
                    
                return results
                
            except Exception as e:
                log.error("Error executing query in Page.pages: %s", str(e))
                log.error("Query filters: %s", kw)
                # Rollback on error to prevent connection pool issues
                safe_rollback()
                # Re-raise to trigger retry
                raise
                
        except Exception as e:
            log.error("Error in Page.pages: %s", str(e))
            # Rollback on error to prevent connection pool issues
            safe_rollback()
            # Re-raise to trigger retry
            raise

    @classmethod
    def _sort_by_severity(cls, pages):
        """Sort pages by priority and severity using Python instead of SQL"""
        def get_priority_weight(page):
            try:
                if hasattr(page, 'extras') and page.extras:
                    extras = json.loads(page.extras) if isinstance(page.extras, str) else page.extras
                    priority = extras.get('priority', 'high').lower()
                    priority_weights = {
                        'urgent': 4,
                        'high': 3,
                        'medium': 2,
                        'low': 1
                    }
                    return priority_weights.get(priority, 3)
                return 3
            except (ValueError, TypeError, KeyError):
                return 3

        def get_severity_weight(page):
            try:
                if hasattr(page, 'extras') and page.extras:
                    extras = json.loads(page.extras) if isinstance(page.extras, str) else page.extras
                    severity = extras.get('severity', '').lower()
                    severity_weights = {
                        'critical': 4,
                        'high': 3,
                        'moderate': 2,
                        'low': 1
                    }
                    return severity_weights.get(severity, 0)
                return 0
            except (ValueError, TypeError, KeyError):
                return 0

        try:
            return sorted(pages, key=lambda p: (
                get_priority_weight(p),
                get_severity_weight(p),
                p.publish_date.timestamp() if p.publish_date else 0,
                p.created.timestamp() if p.created else 0
            ), reverse=True)
        except Exception as e:
            log.error("Error sorting by severity: %s", str(e))
            return pages

    @classmethod
    def _sort_by_priority(cls, pages):
        """Sort pages by priority only (simpler and more user-friendly than severity)"""
        def get_priority_weight(page):
            try:
                if hasattr(page, 'extras') and page.extras:
                    extras = json.loads(page.extras) if isinstance(page.extras, str) else page.extras
                    priority = extras.get('priority', 'medium').lower()
                    priority_weights = {
                        'urgent': 4,
                        'high': 3,
                        'medium': 2,
                        'low': 1
                    }
                    return priority_weights.get(priority, 2)  # Default to medium
                return 2
            except (ValueError, TypeError, KeyError):
                return 2

        try:
            return sorted(pages, key=lambda p: (
                get_priority_weight(p),
                p.publish_date.timestamp() if p.publish_date else 0,
                p.created.timestamp() if p.created else 0
            ), reverse=True)
        except Exception as e:
            log.error("Error sorting by priority: %s", str(e))
            return pages

    @classmethod
    def _sort_by_gdacs_alert_level(cls, pages):
        """Sort pages by GDACS Alert Level - most critical first"""
        def get_gdacs_alert_weight(page):
            try:
                if hasattr(page, 'extras') and page.extras:
                    extras = json.loads(page.extras) if isinstance(page.extras, str) else page.extras
                    severity = extras.get('severity', '').lower()
                    
                    # GDACS Alert Level weights (highest to lowest priority)
                    gdacs_weights = {
                        # General GDACS Alerts (Floods, Drought, Volcano, Tsunami, Earthquake, Wildfire)
                        'red_alert': 10,        # Most critical
                        'orange_alert': 8,      # High severity
                        'green_alert': 6,       # Moderate severity
                        
                        # Tropical Cyclone Categories (most severe first)
                        'category_5': 9,        # Catastrophic damage
                        'category_4': 8,        # Extreme damage 
                        'category_3': 7,        # Extensive damage
                        'category_2': 5,        # Moderate damage
                        'category_1': 4,        # Light damage
                        'tropical_storm': 3,    # Minimal hurricane-force winds
                        'tropical_depression': 2, # Organized low pressure
                        
                        # Legacy compatibility
                        'critical': 9,
                        'high': 7,
                        'moderate': 5,
                        'low': 3
                    }
                    
                    return gdacs_weights.get(severity, 1)  # Default to 1 for unknown levels
                return 1
            except Exception as e:
                log.error("Error getting GDACS alert weight for page: %s", str(e))
                return 1

        try:
            return sorted(pages, key=lambda p: (
                get_gdacs_alert_weight(p),
                p.publish_date.timestamp() if p.publish_date else 0,
                p.created.timestamp() if p.created else 0
            ), reverse=True)
        except Exception as e:
            log.error("Error sorting by GDACS alert level: %s", str(e))
            return pages

    def get_ordered_revisions(self):
        # Compare timestamps to avoid different datetime formats error
        try:
            if not self.revisions:
                return OrderedDict()
            
            return OrderedDict(reversed(sorted(
                    self.revisions.items(),
                    key=lambda x: datetime.datetime.timestamp(
                        datetime.datetime.fromisoformat(x[1]['created'])
                        )
            )))
        except Exception as e:
            log.error("Error in get_ordered_revisions: %s", str(e))
            return OrderedDict()


def table_dictize(obj, context, **kw):
    '''Get any model object and represent it as a dict'''
    result_dict = {}

    try:
        if isinstance(obj, Row):
            fields = obj.keys()
        else:
            ModelClass = obj.__class__
            table = class_mapper(ModelClass).mapped_table
            fields = [field.name for field in table.c]

        for field in fields:
            name = field
            if name in ('current', 'expired_timestamp', 'expired_id'):
                continue
            if name == 'continuity_id':
                continue
            
            try:
                value = getattr(obj, name)
                if name == 'extras' and value:
                    try:
                        extras_dict = json.loads(value) if isinstance(value, str) else value
                        if isinstance(extras_dict, dict):
                            result_dict.update(extras_dict)
                    except (ValueError, TypeError):
                        # If JSON parsing fails, store as string
                        result_dict[name] = value
                elif value is None:
                    result_dict[name] = value
                elif isinstance(value, dict):
                    result_dict[name] = value
                elif isinstance(value, int):
                    result_dict[name] = value
                elif isinstance(value, datetime.datetime):
                    result_dict[name] = value.isoformat()
                elif isinstance(value, list):
                    result_dict[name] = value
                else:
                    result_dict[name] = text_type(value)
            except Exception as e:
                log.error("Error processing field %s: %s", name, str(e))
                # Skip problematic fields
                continue

        result_dict.update(kw)

        # HACK For optimisation to get metadata_modified created faster.
        context['metadata_modified'] = max(result_dict.get('revision_timestamp', ''),
                                           context.get('metadata_modified', ''))

        return result_dict
        
    except Exception as e:
        log.error("Error in table_dictize: %s", str(e))
        return {}
