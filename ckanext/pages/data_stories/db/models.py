"""
SQLAlchemy models for Data Stories

Defines the database schema for data stories and related entities.
"""

import datetime
import logging
from typing import Optional, List

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
    # CKAN <= 2.9
    from ckan.model.meta import metadata
    from sqlalchemy.ext.declarative import declarative_base
    BaseModel = declarative_base(metadata=metadata)

log = logging.getLogger(__name__)


class DataStory(DomainObject, BaseModel):
    """
    Main data story entity.

    Represents a complete data story with narrative sections,
    linked datasets, and publication workflow.
    """

    __tablename__ = 'data_stories'

    # Core fields
    id = Column(String(100), primary_key=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)

    # Content sections (long text fields)
    abstract = Column(Text)
    research_question = Column(Text)
    study_area = Column(Text)

    # Metadata
    countries = Column(JSONB)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    author_id = Column(String(100), ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    organization_id = Column(String(100), ForeignKey('group.id', ondelete='SET NULL'), nullable=True)

    # Publication workflow
    status = Column(String(50), default='draft', index=True)  # draft, submitted, under_review, published, archived
    submission_date = Column(DateTime, nullable=True)
    review_date = Column(DateTime, nullable=True)
    reviewer_id = Column(String(100), ForeignKey('user.id', ondelete='SET NULL'), nullable=True)

    # Visibility and access
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)

    # Statistics
    view_count = Column(Integer, default=0)

    # Versioning
    version = Column(Integer, default=1)
    parent_version_id = Column(String(100), ForeignKey('data_stories.id', ondelete='SET NULL'), nullable=True)

    # SEO
    meta_description = Column(Text)
    meta_keywords = Column(Text)

    # Relationships
    sections = relationship('DataStorySection', back_populates='story', cascade='all, delete-orphan', order_by='DataStorySection.order_index')
    datasets = relationship('DataStoryDataset', back_populates='story', cascade='all, delete-orphan')
    contributors = relationship('DataStoryContributor', back_populates='story', cascade='all, delete-orphan')
    comments = relationship('DataStoryComment', back_populates='story', cascade='all, delete-orphan')
    revisions = relationship('DataStoryRevision', back_populates='story', cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        Index('idx_data_stories_status', 'status'),
        Index('idx_data_stories_author', 'author_id'),
        Index('idx_data_stories_published', 'published_at'),
        Index('idx_data_stories_featured', 'is_featured'),
    )

    def __repr__(self):
        return f'<DataStory(id={self.id}, title={self.title}, status={self.status})>'

    @classmethod
    def get(cls, **kwargs):
        """Get a single story by any field."""
        try:
            query = model.Session.query(cls).autoflush(False)
            return query.filter_by(**kwargs).first()
        except Exception as e:
            log.error(f"Error in DataStory.get: {str(e)}")
            return None

    @classmethod
    def all(cls, **kwargs):
        """Get all stories matching criteria."""
        try:
            query = model.Session.query(cls).autoflush(False)
            if kwargs:
                query = query.filter_by(**kwargs)
            return query.all()
        except Exception as e:
            log.error(f"Error in DataStory.all: {str(e)}")
            return []


class DataStorySection(DomainObject, BaseModel):
    """
    Modular section within a data story.

    Sections form the narrative structure of a story,
    with support for different content types including
    spatial visualizations.
    """

    __tablename__ = 'data_story_sections'

    id = Column(String(100), primary_key=True)
    story_id = Column(String(100), ForeignKey('data_stories.id', ondelete='CASCADE'), nullable=False, index=True)

    # Section identity
    section_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255))
    order_index = Column(Integer, nullable=False)

    # Content
    content = Column(Text)

    # Media
    image_url = Column(Text)
    video_url = Column(Text)

    # Terria integration
    terria_config = Column(JSONB)
    terria_share_link = Column(Text)

    # Block structure metadata
    blocks_metadata = Column(JSONB)

    # Visibility
    is_visible = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    story = relationship('DataStory', back_populates='sections')
    comments = relationship('DataStoryComment', back_populates='section', cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        Index('idx_sections_story', 'story_id'),
        Index('idx_sections_order', 'story_id', 'order_index'),
        Index('idx_sections_type', 'section_type'),
    )

    def __repr__(self):
        return f'<DataStorySection(id={self.id}, story_id={self.story_id}, type={self.section_type})>'

    @classmethod
    def get(cls, **kwargs):
        """Get a single section by any field."""
        try:
            query = model.Session.query(cls).autoflush(False)
            return query.filter_by(**kwargs).first()
        except Exception as e:
            log.error(f"Error in DataStorySection.get: {str(e)}")
            return None

    @classmethod
    def all(cls, **kwargs):
        """Get all sections matching criteria."""
        try:
            query = model.Session.query(cls).autoflush(False)
            if kwargs:
                query = query.filter_by(**kwargs)
            return query.order_by(cls.order_index).all()
        except Exception as e:
            log.error(f"Error in DataStorySection.all: {str(e)}")
            return []


class DataStoryDataset(DomainObject, BaseModel):
    """
    Links data stories to CKAN datasets.

    Establishes relationships between stories and the
    datasets they reference or analyze.
    """

    __tablename__ = 'data_story_datasets'

    id = Column(String(100), primary_key=True)
    story_id = Column(String(100), ForeignKey('data_stories.id', ondelete='CASCADE'), nullable=False, index=True)
    dataset_id = Column(String(100), nullable=False, index=True)  # CKAN package ID

    # Relationship metadata
    relationship_type = Column(String(50))  # primary, supporting, derived, referenced
    description = Column(Text)
    order_index = Column(Integer)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    story = relationship('DataStory', back_populates='datasets')

    # Constraints
    __table_args__ = (
        UniqueConstraint('story_id', 'dataset_id', name='uq_story_dataset'),
        Index('idx_story_datasets_story', 'story_id'),
        Index('idx_story_datasets_dataset', 'dataset_id'),
    )

    def __repr__(self):
        return f'<DataStoryDataset(story_id={self.story_id}, dataset_id={self.dataset_id})>'

    @classmethod
    def get(cls, **kwargs):
        """Get a single dataset link by any field."""
        try:
            query = model.Session.query(cls).autoflush(False)
            return query.filter_by(**kwargs).first()
        except Exception as e:
            log.error(f"Error in DataStoryDataset.get: {str(e)}")
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
            log.error(f"Error in DataStoryDataset.all: {str(e)}")
            return []


class DataStoryContributor(DomainObject, BaseModel):
    """
    Track multiple contributors beyond the primary author.

    Supports both CKAN users and external contributors
    with ORCID integration.
    """

    __tablename__ = 'data_story_contributors'

    id = Column(String(100), primary_key=True)
    story_id = Column(String(100), ForeignKey('data_stories.id', ondelete='CASCADE'), nullable=False, index=True)

    # Contributor info
    user_id = Column(String(100), ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    name = Column(String(255))  # For external contributors
    email = Column(String(255))
    affiliation = Column(String(255))
    orcid = Column(String(50))

    # Role
    role = Column(String(50))  # co-author, data-provider, reviewer, editor
    order_index = Column(Integer)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    story = relationship('DataStory', back_populates='contributors')

    # Indexes
    __table_args__ = (
        Index('idx_contributors_story', 'story_id'),
        Index('idx_contributors_user', 'user_id'),
    )

    def __repr__(self):
        return f'<DataStoryContributor(story_id={self.story_id}, name={self.name}, role={self.role})>'

    @classmethod
    def get(cls, **kwargs):
        """Get a single contributor by any field."""
        try:
            query = model.Session.query(cls).autoflush(False)
            return query.filter_by(**kwargs).first()
        except Exception as e:
            log.error(f"Error in DataStoryContributor.get: {str(e)}")
            return None

    @classmethod
    def all(cls, **kwargs):
        """Get all contributors matching criteria."""
        try:
            query = model.Session.query(cls).autoflush(False)
            if kwargs:
                query = query.filter_by(**kwargs)
            return query.order_by(cls.order_index).all()
        except Exception as e:
            log.error(f"Error in DataStoryContributor.all: {str(e)}")
            return []


class DataStoryComment(DomainObject, BaseModel):
    """
    Enable review and feedback on data stories.

    Supports threaded comments and resolution tracking
    for the review workflow.
    """

    __tablename__ = 'data_story_comments'

    id = Column(String(100), primary_key=True)
    story_id = Column(String(100), ForeignKey('data_stories.id', ondelete='CASCADE'), nullable=False, index=True)

    # Comment info
    user_id = Column(String(100), ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    section_id = Column(String(100), ForeignKey('data_story_sections.id', ondelete='CASCADE'), nullable=True, index=True)

    content = Column(Text, nullable=False)
    comment_type = Column(String(50), default='comment')  # comment, suggestion, required_change

    # Threading
    parent_comment_id = Column(String(100), ForeignKey('data_story_comments.id', ondelete='CASCADE'), nullable=True)

    # Status
    is_resolved = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    story = relationship('DataStory', back_populates='comments')
    section = relationship('DataStorySection', back_populates='comments')

    # Indexes
    __table_args__ = (
        Index('idx_comments_story', 'story_id'),
        Index('idx_comments_user', 'user_id'),
        Index('idx_comments_section', 'section_id'),
    )

    def __repr__(self):
        return f'<DataStoryComment(id={self.id}, story_id={self.story_id}, type={self.comment_type})>'

    @classmethod
    def get(cls, **kwargs):
        """Get a single comment by any field."""
        try:
            query = model.Session.query(cls).autoflush(False)
            return query.filter_by(**kwargs).first()
        except Exception as e:
            log.error(f"Error in DataStoryComment.get: {str(e)}")
            return None

    @classmethod
    def all(cls, **kwargs):
        """Get all comments matching criteria."""
        try:
            query = model.Session.query(cls).autoflush(False)
            if kwargs:
                query = query.filter_by(**kwargs)
            return query.order_by(cls.created_at).all()
        except Exception as e:
            log.error(f"Error in DataStoryComment.all: {str(e)}")
            return []


class DataStoryRevision(DomainObject, BaseModel):
    """
    Track version history of data stories.

    Creates snapshots of stories at each save to enable
    revision comparison and rollback.
    """

    __tablename__ = 'data_story_revisions'

    id = Column(String(100), primary_key=True)
    story_id = Column(String(100), ForeignKey('data_stories.id', ondelete='CASCADE'), nullable=False, index=True)

    # Version info
    version = Column(Integer, nullable=False)

    # Snapshot
    title = Column(String(255))
    content_snapshot = Column(JSONB)  # Full story snapshot

    # Change tracking
    changed_by = Column(String(100), ForeignKey('user.id'), nullable=False)
    change_summary = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    story = relationship('DataStory', back_populates='revisions')

    # Indexes
    __table_args__ = (
        Index('idx_revisions_story', 'story_id'),
        Index('idx_revisions_version', 'story_id', 'version'),
    )

    def __repr__(self):
        return f'<DataStoryRevision(story_id={self.story_id}, version={self.version})>'

    @classmethod
    def get(cls, **kwargs):
        """Get a single revision by any field."""
        try:
            query = model.Session.query(cls).autoflush(False)
            return query.filter_by(**kwargs).first()
        except Exception as e:
            log.error(f"Error in DataStoryRevision.get: {str(e)}")
            return None

    @classmethod
    def all(cls, **kwargs):
        """Get all revisions matching criteria."""
        try:
            query = model.Session.query(cls).autoflush(False)
            if kwargs:
                query = query.filter_by(**kwargs)
            return query.order_by(cls.version.desc()).all()
        except Exception as e:
            log.error(f"Error in DataStoryRevision.all: {str(e)}")
            return []
