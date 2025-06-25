import datetime
import uuid
import json

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
        query = model.Session.query(cls).autoflush(False)
        return query.filter_by(**kw).first()

    @classmethod
    def pages(cls, **kw):
        '''Finds a single entity in the register.'''
        order = kw.pop('order', False)
        order_publish_date = kw.pop('order_publish_date', False)
        
        # New search and filter parameters
        q = kw.pop('q', None)
        event_type = kw.pop('event_type', None) 
        order_by = kw.pop('order_by', None)

        query = model.Session.query(cls).autoflush(False)
        query = query.filter_by(**kw)
        
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
            query = query.filter(
                cls.extras.ilike('%"event_type": "' + event_type + '"%')
            )
        
        # Apply custom ordering
        if order:
            query = query.order_by(sa.cast(cls.order, sa.Integer)).filter(cls.order != '')
        elif order_by == 'recent':
            query = query.order_by(cls.publish_date.desc().nullslast(), cls.created.desc())
        elif order_by == 'severity':
            # Order by severity (you can customize this logic)
            query = query.order_by(cls.created.desc())
        elif order_by == 'country':
            # Order by country alphabetically (stored in extras)
            query = query.order_by(cls.extras)
        elif order_publish_date:
            # Default for rapid-response: most recent first
            query = query.order_by(cls.publish_date.desc().nullslast(), cls.created.desc())
        else:
            query = query.order_by(cls.created.desc())
        return query.all()

    def get_ordered_revisions(self):
        # Compare timestamps to avoid different datetime formats error
        return OrderedDict(reversed(sorted(
                self.revisions.items(),
                key=lambda x: datetime.datetime.timestamp(
                    datetime.datetime.fromisoformat(x[1]['created'])
                    )
        )))


def table_dictize(obj, context, **kw):
    '''Get any model object and represent it as a dict'''
    result_dict = {}

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
        value = getattr(obj, name)
        if name == 'extras' and value:
            result_dict.update(json.loads(value))
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

    result_dict.update(kw)

    # HACK For optimisation to get metadata_modified created faster.

    context['metadata_modified'] = max(result_dict.get('revision_timestamp', ''),
                                       context.get('metadata_modified', ''))

    return result_dict
