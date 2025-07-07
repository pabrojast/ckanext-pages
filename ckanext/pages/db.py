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

    @classmethod
    def get(cls, **kw):
        '''Finds a single entity in the register.'''
        try:
            query = model.Session.query(cls).autoflush(False)
            return query.filter_by(**kw).first()
        except Exception as e:
            log.error("Error in Page.get: %s", str(e))
            return None

    @classmethod
    def pages(cls, **kw):
        '''Finds a single entity in the register.'''
        try:
            order = kw.pop('order', False)
            order_publish_date = kw.pop('order_publish_date', False)
            
            # New search and filter parameters
            q = kw.pop('q', None)
            event_type = kw.pop('event_type', None) 
            priority = kw.pop('priority', None)
            country = kw.pop('country', None)
            order_by = kw.pop('order_by', None)

            # Base query - explicitly select all columns to avoid column mapping issues
            query = model.Session.query(cls).autoflush(False)
            
            # Apply basic filters
            query = query.filter_by(**kw)
            
            # Apply search query
            if q:
                search_filter = sa.or_(
                    cls.title.ilike('%' + q + '%'),
                    cls.content.ilike('%' + q + '%'),
                    cls.extras.ilike('%' + q + '%')
                )
                query = query.filter(search_filter)
            
            # Apply event type filter (stored in subtitle field in extras JSON)
            if event_type:
                # Map filter values to actual subtitle values
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
                query = query.filter(
                    cls.extras.ilike('%"subtitle": "' + actual_subtitle + '"%')
                )
            
            # Apply priority filter (stored in extras JSON)
            if priority:
                query = query.filter(
                    cls.extras.ilike('%"priority": "' + priority + '"%')
                )
            
            # Apply country filter (stored in extras JSON)
            if country:
                # Support both new countries_affected format and legacy country format
                country_filter = sa.or_(
                    # New format: countries_affected with JSON array
                    cls.extras.ilike('%"countries_affected": %' + country + '%'),
                    # Legacy format: country field
                    cls.extras.ilike('%"country": "%' + country + '%"%'),
                    # Also check if it's in the backward compatibility field in new format
                    cls.extras.ilike('%' + country + '%')
                )
                query = query.filter(country_filter)
            
            # Apply ordering - simplified to avoid complex CASE statements that might cause issues
            if order_by == 'recent':
                query = query.order_by(cls.publish_date.desc().nullslast(), cls.created.desc())
            elif order_by == 'severity':
                # Simplified ordering - order by publish_date and created as fallback
                query = query.order_by(cls.publish_date.desc().nullslast(), cls.created.desc())
            elif order_by == 'country':
                # Order by title as fallback
                query = query.order_by(cls.title.asc())
            elif order:
                # Safe ordering by order field
                try:
                    query = query.filter(cls.order != '').order_by(sa.cast(cls.order, sa.Integer))
                except:
                    # Fallback to string ordering if cast fails
                    query = query.filter(cls.order != '').order_by(cls.order)
            elif order_publish_date:
                query = query.order_by(cls.publish_date.desc().nullslast(), cls.created.desc())
            else:
                # Default ordering
                query = query.order_by(cls.created.desc())
            
            # Execute query with error handling
            try:
                results = query.all()
                
                # Post-process results for complex sorting if needed
                if order_by == 'severity':
                    results = cls._sort_by_severity(results)
                    
                return results
                
            except Exception as e:
                log.error("Error executing query in Page.pages: %s", str(e))
                log.error("Query filters: %s", kw)
                # Return empty list as fallback
                return []
                
        except Exception as e:
            log.error("Error in Page.pages: %s", str(e))
            return []

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
            except:
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
            except:
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
