"""
SQLAlchemy models for Featured Viewers

Defines the database schema for featured thematic viewers and related entities.
"""

import datetime
import logging

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from ckan import model
from ckan.model.domain_object import DomainObject

try:
    from ckan.plugins.toolkit import BaseModel
except ImportError:
    from ckan.model.meta import metadata
    from sqlalchemy.ext.declarative import declarative_base
    BaseModel = declarative_base(metadata=metadata)

log = logging.getLogger(__name__)


class FeaturedViewer(DomainObject, BaseModel):
    """
    A thematic map viewer with pre-configured Terria map room.

    Provides direct access to curated geospatial data layers
    organized by thematic category.
    """

    __tablename__ = 'featured_viewers'

    # Core fields
    id = Column(String(100), primary_key=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)

    # Categorization
    category = Column(String(100), index=True)
    initiative = Column(String(100), nullable=True, index=True)
    icon_class = Column(String(100))
    thumbnail_url = Column(Text)

    # Terria integration
    terria_share_link = Column(Text)
    terria_config = Column(JSONB)
    map_layers = Column(JSONB)

    # Metadata
    tags = Column(JSONB)
    countries = Column(JSONB)

    # Visibility and ordering
    is_featured = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)
    status = Column(String(50), default='draft', index=True)

    # Ownership
    author_id = Column(String(100), ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    organization_id = Column(String(100), ForeignKey('group.id', ondelete='SET NULL'), nullable=True)

    # Statistics
    view_count = Column(Integer, default=0)

    # SEO
    meta_description = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    datasets = relationship('ViewerDataset', back_populates='viewer', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_featured_viewers_status', 'status'),
        Index('idx_featured_viewers_category', 'category'),
        Index('idx_featured_viewers_initiative', 'initiative'),
        Index('idx_featured_viewers_author', 'author_id'),
        Index('idx_featured_viewers_featured', 'is_featured'),
        Index('idx_featured_viewers_order', 'order_index'),
    )

    def __repr__(self):
        return f'<FeaturedViewer(id={self.id}, title={self.title}, status={self.status})>'

    @classmethod
    def get(cls, **kwargs):
        """Get a single viewer by any field."""
        try:
            query = model.Session.query(cls).autoflush(False)
            return query.filter_by(**kwargs).first()
        except Exception as e:
            log.error(f"Error in FeaturedViewer.get: {str(e)}")
            return None

    @classmethod
    def all(cls, **kwargs):
        """Get all viewers matching criteria."""
        try:
            query = model.Session.query(cls).autoflush(False)
            if kwargs:
                query = query.filter_by(**kwargs)
            return query.all()
        except Exception as e:
            log.error(f"Error in FeaturedViewer.all: {str(e)}")
            return []


class ViewerDataset(DomainObject, BaseModel):
    """
    Links featured viewers to CKAN datasets.
    """

    __tablename__ = 'viewer_datasets'

    id = Column(String(100), primary_key=True)
    viewer_id = Column(String(100), ForeignKey('featured_viewers.id', ondelete='CASCADE'), nullable=False, index=True)
    dataset_id = Column(String(100), nullable=False, index=True)

    description = Column(Text)
    order_index = Column(Integer)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    viewer = relationship('FeaturedViewer', back_populates='datasets')

    __table_args__ = (
        UniqueConstraint('viewer_id', 'dataset_id', name='uq_viewer_dataset'),
        Index('idx_viewer_datasets_viewer', 'viewer_id'),
        Index('idx_viewer_datasets_dataset', 'dataset_id'),
    )

    def __repr__(self):
        return f'<ViewerDataset(viewer_id={self.viewer_id}, dataset_id={self.dataset_id})>'

    @classmethod
    def get(cls, **kwargs):
        """Get a single dataset link by any field."""
        try:
            query = model.Session.query(cls).autoflush(False)
            return query.filter_by(**kwargs).first()
        except Exception as e:
            log.error(f"Error in ViewerDataset.get: {str(e)}")
            return None

    @classmethod
    def all(cls, **kwargs):
        """Get all dataset links matching criteria."""
        try:
            query = model.Session.query(cls).autoflush(False)
            if kwargs:
                query = query.filter_by(**kwargs)
            return query.order_by(cls.order_index).all()
        except Exception as e:
            log.error(f"Error in ViewerDataset.all: {str(e)}")
            return []


class MapRoom(DomainObject, BaseModel):
    """
    A Map Room groups multiple featured viewers into a thematic collection.
    """

    __tablename__ = 'map_rooms'

    id = Column(String(100), primary_key=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    thumbnail_url = Column(Text)
    category = Column(String(100), index=True)
    initiative = Column(String(100), nullable=True, index=True)
    status = Column(String(50), default='draft', index=True)
    is_featured = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)

    # Ownership
    author_id = Column(
        String(100),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    # Relationships
    room_viewers = relationship(
        'MapRoomViewer', back_populates='room',
        cascade='all, delete-orphan',
        order_by='MapRoomViewer.order_index',
    )

    __table_args__ = (
        Index('idx_map_rooms_status', 'status'),
        Index('idx_map_rooms_category', 'category'),
        Index('idx_map_rooms_initiative', 'initiative'),
    )

    def __repr__(self):
        return f'<MapRoom(id={self.id}, title={self.title})>'

    @classmethod
    def get(cls, **kwargs):
        try:
            return model.Session.query(cls).autoflush(False)\
                .filter_by(**kwargs).first()
        except Exception as e:
            log.error(f"Error in MapRoom.get: {str(e)}")
            return None

    @classmethod
    def all(cls, **kwargs):
        try:
            query = model.Session.query(cls).autoflush(False)
            if kwargs:
                query = query.filter_by(**kwargs)
            return query.order_by(cls.order_index).all()
        except Exception as e:
            log.error(f"Error in MapRoom.all: {str(e)}")
            return []


class MapRoomViewer(DomainObject, BaseModel):
    """
    Junction table linking map rooms to featured viewers.
    """

    __tablename__ = 'map_room_viewers'

    id = Column(String(100), primary_key=True)
    room_id = Column(
        String(100),
        ForeignKey('map_rooms.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    viewer_id = Column(
        String(100),
        ForeignKey('featured_viewers.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    room = relationship('MapRoom', back_populates='room_viewers')
    viewer = relationship('FeaturedViewer')

    __table_args__ = (
        UniqueConstraint(
            'room_id', 'viewer_id',
            name='uq_map_room_viewer',
        ),
    )
