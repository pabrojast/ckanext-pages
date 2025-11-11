# Data Stories Implementation Plan

## Executive Summary

This document outlines a comprehensive plan to implement a **Data Stories** feature for open-access scientific articles related to water resources. The system will enable researchers to create narrative-driven explanations of their datasets, methodologies, and spatial analyses, similar to ArcGIS Story Maps but specifically designed for hydrological research papers.

### Key Objectives

1. **Narrative-Driven Data Explanation**: Allow researchers to tell the story behind their datasets
2. **Spatial Visualization Integration**: Seamless integration with Terria for interactive maps
3. **Methodological Documentation**: Detailed sections for data sources, processing, and analysis
4. **User Access Control**: Granular permissions for creating, reviewing, and publishing stories
5. **Modular Architecture**: Clean separation of concerns with maintainable, testable code
6. **Dataset Linking**: Direct connection between stories and CKAN datasets

---

## Table of Contents

1. [Vision & Concept](#vision--concept)
2. [Architecture Overview](#architecture-overview)
3. [Current Problems & Solutions](#current-problems--solutions)
4. [Database Design](#database-design)
5. [Module Structure](#module-structure)
6. [API Endpoints](#api-endpoints)
7. [User Roles & Permissions](#user-roles--permissions)
8. [Data Story Sections](#data-story-sections)
9. [Terria Integration](#terria-integration)
10. [Implementation Phases](#implementation-phases)
11. [Testing Strategy](#testing-strategy)
12. [Migration Path](#migration-path)

---

## Vision & Concept

### What is a Data Story?

A **Data Story** is a comprehensive, narrative-driven explanation of a research paper's data and methodology. It transforms dry datasets into engaging, understandable stories that showcase:

- **The Research Question**: What problem is being addressed?
- **Data Sources**: Where did the data come from?
- **Methodology**: How was the data collected and processed?
- **Spatial Context**: Interactive maps showing study areas and results
- **Key Findings**: Visual representations of results
- **Impact**: Real-world applications and implications
- **Reproducibility**: Clear documentation for data reuse

### Inspiration from ArcGIS Story Maps

Like ArcGIS Story Maps, Data Stories will feature:

- **Narrative Flow**: Sequential sections that tell a cohesive story
- **Rich Media**: Images, videos, charts, and interactive maps
- **Spatial Context**: Embedded Terria map instances
- **Responsive Design**: Beautiful presentation on all devices
- **Engagement**: Interactive elements that draw readers in

### Target Audience

- **Primary**: Researchers publishing open-access water resources papers
- **Secondary**: Data users, policymakers, students, and the general public
- **Reviewers**: Journal editors, data curators, research administrators

---

## Architecture Overview

### Design Principles

1. **Separation of Concerns**: Each functionality in its own module
2. **Single Responsibility**: Each module has one clear purpose
3. **DRY (Don't Repeat Yourself)**: Reusable components and utilities
4. **Testability**: All modules independently testable
5. **Scalability**: Easy to add new features without breaking existing code
6. **Maintainability**: Clear structure makes debugging straightforward

### High-Level Architecture

```
ckanext-pages/
├── ckanext/pages/
│   ├── data_stories/                    # NEW: Data Stories module
│   │   ├── __init__.py
│   │   ├── actions/                     # Action handlers
│   │   │   ├── __init__.py
│   │   │   ├── create.py                # Story creation
│   │   │   ├── read.py                  # Story retrieval
│   │   │   ├── update.py                # Story updates
│   │   │   ├── delete.py                # Story deletion
│   │   │   └── publish.py               # Publishing workflow
│   │   ├── auth/                        # Authorization logic
│   │   │   ├── __init__.py
│   │   │   ├── permissions.py           # Permission checks
│   │   │   └── roles.py                 # Role definitions
│   │   ├── blueprint/                   # Flask routes
│   │   │   ├── __init__.py
│   │   │   └── routes.py                # URL endpoints
│   │   ├── db/                          # Database layer
│   │   │   ├── __init__.py
│   │   │   ├── models.py                # SQLAlchemy models
│   │   │   └── migrations.py            # Database migrations
│   │   ├── logic/                       # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── validation.py            # Data validation
│   │   │   ├── schema.py                # Schema definitions
│   │   │   └── workflow.py              # Publication workflow
│   │   ├── templates/                   # Jinja2 templates
│   │   │   ├── list.html                # Story listing
│   │   │   ├── view.html                # Story display
│   │   │   ├── edit.html                # Story editor
│   │   │   ├── sections/                # Individual sections
│   │   │   └── components/              # Reusable components
│   │   ├── static/                      # Static assets
│   │   │   ├── css/
│   │   │   │   ├── data-stories.css     # Main styles
│   │   │   │   └── sections.css         # Section styles
│   │   │   ├── js/
│   │   │   │   ├── editor.js            # Story editor
│   │   │   │   ├── terria-integration.js
│   │   │   │   └── sections.js          # Section management
│   │   │   └── img/
│   │   ├── helpers/                     # Template helpers
│   │   │   ├── __init__.py
│   │   │   ├── formatting.py            # Display formatting
│   │   │   └── terria.py                # Terria helpers
│   │   ├── utils/                       # Utility functions
│   │   │   ├── __init__.py
│   │   │   ├── dataset_linking.py       # Link to datasets
│   │   │   ├── image_processing.py      # Image handling
│   │   │   └── export.py                # Export functionality
│   │   └── tests/                       # Unit tests
│   │       ├── test_actions.py
│   │       ├── test_auth.py
│   │       ├── test_logic.py
│   │       └── test_workflow.py
```

---

## Current Problems & Solutions

### Problems with Current Architecture

| Problem | Current State | Impact |
|---------|--------------|--------|
| **Monolithic actions.py** | 1377 lines, all types mixed | Hard to maintain, debug, extend |
| **No separation** | Everything in one module | Changes affect unrelated features |
| **Unclear structure** | Logic scattered across files | Difficult onboarding for new devs |
| **Generic table** | All page types in one table | Schema pollution, hard queries |
| **JSON extras overload** | Type-specific fields in JSON | Poor performance, no validation |
| **Limited permissions** | Basic auth checks only | No granular access control |
| **Tight coupling** | Direct dependencies everywhere | Hard to test, brittle code |

### Solutions in New Architecture

| Solution | Implementation | Benefit |
|----------|----------------|---------|
| **Modular structure** | Separate directories per concern | Easy to find, modify, test code |
| **Small, focused files** | Max ~200 lines per file | Readable, maintainable |
| **Clear separation** | actions/, auth/, logic/, db/ | Single responsibility principle |
| **Dedicated tables** | data_stories table with proper schema | Better performance, validation |
| **Typed fields** | Real columns, not JSON extras | Database-level validation |
| **Role-based auth** | Permission matrix by role | Fine-grained access control |
| **Dependency injection** | Loose coupling via interfaces | Testable, flexible |

---

## Database Design

### New Tables

#### 1. data_stories

Primary table for storing data stories.

```sql
CREATE TABLE data_stories (
    -- Core fields
    id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,

    -- Content sections
    abstract TEXT,
    research_question TEXT,
    study_area TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP NULL,

    -- Relationships
    author_id VARCHAR(100) NOT NULL REFERENCES "user"(id),
    organization_id VARCHAR(100) REFERENCES "group"(id),

    -- Publication workflow
    status VARCHAR(50) DEFAULT 'draft',  -- draft, submitted, under_review, published, archived
    submission_date TIMESTAMP NULL,
    review_date TIMESTAMP NULL,
    reviewer_id VARCHAR(100) NULL REFERENCES "user"(id),

    -- Visibility and access
    is_public BOOLEAN DEFAULT FALSE,
    is_featured BOOLEAN DEFAULT FALSE,

    -- Statistics
    view_count INTEGER DEFAULT 0,

    -- Versioning
    version INTEGER DEFAULT 1,
    parent_version_id VARCHAR(100) NULL REFERENCES data_stories(id),

    -- SEO
    meta_description TEXT,
    meta_keywords TEXT,

    CONSTRAINT fk_author FOREIGN KEY (author_id) REFERENCES "user"(id) ON DELETE CASCADE,
    CONSTRAINT fk_organization FOREIGN KEY (organization_id) REFERENCES "group"(id) ON DELETE SET NULL,
    CONSTRAINT fk_reviewer FOREIGN KEY (reviewer_id) REFERENCES "user"(id) ON DELETE SET NULL
);

CREATE INDEX idx_data_stories_status ON data_stories(status);
CREATE INDEX idx_data_stories_author ON data_stories(author_id);
CREATE INDEX idx_data_stories_published ON data_stories(published_at);
CREATE INDEX idx_data_stories_slug ON data_stories(slug);
```

#### 2. data_story_sections

Modular sections within a story (similar to Story Map sidecar/narrative).

```sql
CREATE TABLE data_story_sections (
    id VARCHAR(100) PRIMARY KEY,
    story_id VARCHAR(100) NOT NULL REFERENCES data_stories(id) ON DELETE CASCADE,

    -- Section identity
    section_type VARCHAR(50) NOT NULL,  -- introduction, data_sources, methodology, spatial_analysis, results, conclusions
    title VARCHAR(255),
    order_index INTEGER NOT NULL,

    -- Content
    content TEXT,

    -- Media
    image_url TEXT,
    video_url TEXT,

    -- Terria integration
    terria_config JSONB,  -- Terria initialization JSON
    terria_share_link TEXT,

    -- Visibility
    is_visible BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_story FOREIGN KEY (story_id) REFERENCES data_stories(id) ON DELETE CASCADE
);

CREATE INDEX idx_sections_story ON data_story_sections(story_id);
CREATE INDEX idx_sections_order ON data_story_sections(story_id, order_index);
CREATE INDEX idx_sections_type ON data_story_sections(section_type);
```

#### 3. data_story_datasets

Links stories to CKAN datasets.

```sql
CREATE TABLE data_story_datasets (
    id VARCHAR(100) PRIMARY KEY,
    story_id VARCHAR(100) NOT NULL REFERENCES data_stories(id) ON DELETE CASCADE,
    dataset_id VARCHAR(100) NOT NULL,  -- CKAN package ID

    -- Relationship metadata
    relationship_type VARCHAR(50),  -- primary, supporting, derived, referenced
    description TEXT,
    order_index INTEGER,

    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_story_dataset FOREIGN KEY (story_id) REFERENCES data_stories(id) ON DELETE CASCADE,
    UNIQUE(story_id, dataset_id)
);

CREATE INDEX idx_story_datasets_story ON data_story_datasets(story_id);
CREATE INDEX idx_story_datasets_dataset ON data_story_datasets(dataset_id);
```

#### 4. data_story_contributors

Track multiple contributors beyond the primary author.

```sql
CREATE TABLE data_story_contributors (
    id VARCHAR(100) PRIMARY KEY,
    story_id VARCHAR(100) NOT NULL REFERENCES data_stories(id) ON DELETE CASCADE,

    -- Contributor info
    user_id VARCHAR(100) NULL REFERENCES "user"(id),
    name VARCHAR(255),  -- For external contributors
    email VARCHAR(255),
    affiliation VARCHAR(255),
    orcid VARCHAR(50),

    -- Role
    role VARCHAR(50),  -- co-author, data-provider, reviewer, editor
    order_index INTEGER,

    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_story_contrib FOREIGN KEY (story_id) REFERENCES data_stories(id) ON DELETE CASCADE
);

CREATE INDEX idx_contributors_story ON data_story_contributors(story_id);
CREATE INDEX idx_contributors_user ON data_story_contributors(user_id);
```

#### 5. data_story_comments

Enable review and feedback (for review workflow).

```sql
CREATE TABLE data_story_comments (
    id VARCHAR(100) PRIMARY KEY,
    story_id VARCHAR(100) NOT NULL REFERENCES data_stories(id) ON DELETE CASCADE,

    -- Comment info
    user_id VARCHAR(100) NOT NULL REFERENCES "user"(id),
    section_id VARCHAR(100) NULL REFERENCES data_story_sections(id),

    content TEXT NOT NULL,
    comment_type VARCHAR(50) DEFAULT 'comment',  -- comment, suggestion, required_change

    -- Threading
    parent_comment_id VARCHAR(100) NULL REFERENCES data_story_comments(id),

    -- Status
    is_resolved BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_story_comment FOREIGN KEY (story_id) REFERENCES data_stories(id) ON DELETE CASCADE,
    CONSTRAINT fk_comment_user FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    CONSTRAINT fk_comment_section FOREIGN KEY (section_id) REFERENCES data_story_sections(id) ON DELETE CASCADE
);

CREATE INDEX idx_comments_story ON data_story_comments(story_id);
CREATE INDEX idx_comments_user ON data_story_comments(user_id);
CREATE INDEX idx_comments_section ON data_story_comments(section_id);
```

#### 6. data_story_revisions

Track version history.

```sql
CREATE TABLE data_story_revisions (
    id VARCHAR(100) PRIMARY KEY,
    story_id VARCHAR(100) NOT NULL REFERENCES data_stories(id) ON DELETE CASCADE,

    -- Version info
    version INTEGER NOT NULL,

    -- Snapshot
    title VARCHAR(255),
    content_snapshot JSONB,  -- Full story snapshot

    -- Change tracking
    changed_by VARCHAR(100) NOT NULL REFERENCES "user"(id),
    change_summary TEXT,

    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_revision_story FOREIGN KEY (story_id) REFERENCES data_stories(id) ON DELETE CASCADE,
    CONSTRAINT fk_revision_user FOREIGN KEY (changed_by) REFERENCES "user"(id)
);

CREATE INDEX idx_revisions_story ON data_story_revisions(story_id);
CREATE INDEX idx_revisions_version ON data_story_revisions(story_id, version);
```

### Migration Strategy

1. **Phase 1**: Create new tables alongside existing `ckanext_pages` table
2. **Phase 2**: Populate new tables with any existing rapid-response data (if applicable)
3. **Phase 3**: Run both systems in parallel during testing
4. **Phase 4**: Deprecate old endpoints once new system is stable

---

## Module Structure

### 1. Actions Module (`data_stories/actions/`)

Each action in its own file for clarity and maintainability.

#### `create.py`

```python
"""
Data story creation actions.

Handles the creation of new data stories with validation,
initial section setup, and author assignment.
"""

def data_story_create(context, data_dict):
    """
    Create a new data story.

    Args:
        context: CKAN context dict with user info
        data_dict: Dict containing:
            - title: Story title (required)
            - slug: URL-friendly slug (auto-generated if not provided)
            - abstract: Brief summary
            - research_question: Main research question
            - organization_id: Organization ID (optional)

    Returns:
        Dict with created story data

    Raises:
        NotAuthorized: If user lacks permission
        ValidationError: If data validation fails
    """
    # Implementation
    pass


def data_story_section_create(context, data_dict):
    """
    Add a new section to an existing story.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - story_id: Parent story ID (required)
            - section_type: Type of section (required)
            - title: Section title
            - content: Section content
            - order_index: Position in story
            - terria_config: Terria map configuration (optional)

    Returns:
        Dict with created section data
    """
    pass
```

#### `read.py`

```python
"""
Data story retrieval actions.

Handles fetching stories, sections, and related data.
"""

def data_story_show(context, data_dict):
    """
    Get a single data story by ID or slug.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (optional)
            - slug: Story slug (optional)
            - include_sections: Include sections (default: True)
            - include_datasets: Include linked datasets (default: True)

    Returns:
        Dict with story data

    Raises:
        NotFound: If story doesn't exist
        NotAuthorized: If story is private and user lacks access
    """
    pass


def data_story_list(context, data_dict):
    """
    List data stories with filtering and pagination.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - status: Filter by status (optional)
            - author_id: Filter by author (optional)
            - organization_id: Filter by organization (optional)
            - q: Search query (optional)
            - sort: Sort order (recent, popular, alphabetical)
            - limit: Results per page (default: 20)
            - offset: Pagination offset (default: 0)

    Returns:
        Dict with:
            - stories: List of story dicts
            - count: Total number of stories
            - facets: Aggregated facet data
    """
    pass
```

#### `update.py`

```python
"""
Data story update actions.

Handles modifications to existing stories and sections.
"""

def data_story_update(context, data_dict):
    """
    Update an existing data story.

    Args:
        context: CKAN context dict
        data_dict: Dict containing story ID and fields to update

    Returns:
        Dict with updated story data

    Raises:
        NotFound: If story doesn't exist
        NotAuthorized: If user lacks permission
        ValidationError: If data validation fails
    """
    pass


def data_story_section_update(context, data_dict):
    """
    Update a story section.

    Args:
        context: CKAN context dict
        data_dict: Dict containing section ID and fields to update

    Returns:
        Dict with updated section data
    """
    pass


def data_story_reorder_sections(context, data_dict):
    """
    Reorder sections within a story.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - story_id: Story ID
            - section_order: List of section IDs in desired order

    Returns:
        Dict with success status
    """
    pass
```

#### `delete.py`

```python
"""
Data story deletion actions.

Handles soft and hard deletion of stories and sections.
"""

def data_story_delete(context, data_dict):
    """
    Delete a data story.

    By default, performs soft delete (changes status to 'archived').
    Admins can perform hard delete.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (required)
            - hard_delete: Permanently delete (admin only)

    Returns:
        Dict with success status

    Raises:
        NotFound: If story doesn't exist
        NotAuthorized: If user lacks permission
    """
    pass


def data_story_section_delete(context, data_dict):
    """
    Delete a story section.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Section ID (required)

    Returns:
        Dict with success status
    """
    pass
```

#### `publish.py`

```python
"""
Data story publication workflow actions.

Handles submission, review, and publication processes.
"""

def data_story_submit(context, data_dict):
    """
    Submit a story for review.

    Changes status from 'draft' to 'submitted'.
    Validates that all required sections are present.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (required)
            - submission_notes: Notes for reviewers (optional)

    Returns:
        Dict with updated story data

    Raises:
        ValidationError: If story is incomplete
    """
    pass


def data_story_review(context, data_dict):
    """
    Transition story to under_review status.

    Only available to users with reviewer role.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (required)

    Returns:
        Dict with updated story data
    """
    pass


def data_story_approve(context, data_dict):
    """
    Approve and publish a story.

    Changes status to 'published' and makes story public.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (required)
            - approval_notes: Notes for author (optional)

    Returns:
        Dict with published story data
    """
    pass


def data_story_request_changes(context, data_dict):
    """
    Request changes to a submitted story.

    Returns story to 'draft' status with reviewer comments.

    Args:
        context: CKAN context dict
        data_dict: Dict containing:
            - id: Story ID (required)
            - required_changes: Description of changes needed (required)

    Returns:
        Dict with updated story data
    """
    pass
```

### 2. Authorization Module (`data_stories/auth/`)

#### `permissions.py`

```python
"""
Permission checks for data story actions.

Implements fine-grained access control based on user roles,
story ownership, and organization membership.
"""

def data_story_create(context, data_dict):
    """
    Check if user can create a data story.

    Rules:
    - Must be logged in
    - Must have 'create_story' permission
    - If organization specified, must be member

    Returns:
        {'success': True/False}
    """
    pass


def data_story_update(context, data_dict):
    """
    Check if user can update a data story.

    Rules:
    - Must be story author, OR
    - Must be organization admin, OR
    - Must be sysadmin
    - Story must not be published (unless sysadmin)

    Returns:
        {'success': True/False}
    """
    pass


def data_story_publish(context, data_dict):
    """
    Check if user can publish a data story.

    Rules:
    - Must have 'reviewer' or 'editor' role, OR
    - Must be organization admin, OR
    - Must be sysadmin

    Returns:
        {'success': True/False}
    """
    pass


def data_story_delete(context, data_dict):
    """
    Check if user can delete a data story.

    Rules:
    - Must be story author (soft delete only), OR
    - Must be organization admin, OR
    - Must be sysadmin (can hard delete)

    Returns:
        {'success': True/False}
    """
    pass
```

#### `roles.py`

```python
"""
Role definitions and role-based permission helpers.
"""

ROLES = {
    'story_author': {
        'display_name': 'Story Author',
        'description': 'Can create and edit own data stories',
        'permissions': [
            'data_story_create',
            'data_story_update_own',
            'data_story_delete_own',
            'data_story_submit',
        ]
    },
    'story_reviewer': {
        'display_name': 'Story Reviewer',
        'description': 'Can review and approve submitted stories',
        'permissions': [
            'data_story_review',
            'data_story_approve',
            'data_story_request_changes',
            'data_story_comment',
        ]
    },
    'story_editor': {
        'display_name': 'Story Editor',
        'description': 'Can edit any story in their organization',
        'permissions': [
            'data_story_create',
            'data_story_update_any',
            'data_story_delete_any',
            'data_story_publish',
        ]
    },
}


def has_role(user_id, role_name, org_id=None):
    """
    Check if user has a specific role.

    Args:
        user_id: User ID
        role_name: Role to check
        org_id: Optional organization context

    Returns:
        Boolean
    """
    pass


def get_user_roles(user_id, org_id=None):
    """
    Get all roles for a user.

    Args:
        user_id: User ID
        org_id: Optional organization context

    Returns:
        List of role names
    """
    pass
```

### 3. Logic Module (`data_stories/logic/`)

#### `validation.py`

```python
"""
Business logic validation for data stories.

Separate from schema validation - these are business rules.
"""

def validate_story_completeness(story_dict):
    """
    Check if story has all required sections for submission.

    Required sections:
    - Introduction
    - Data Sources
    - Methodology
    - At least one spatial analysis section
    - Conclusions

    Args:
        story_dict: Story data dict

    Returns:
        Tuple of (is_valid, error_messages)
    """
    pass


def validate_terria_config(terria_config_dict):
    """
    Validate Terria initialization JSON.

    Checks for required fields and valid structure.

    Args:
        terria_config_dict: Terria config dict

    Returns:
        Tuple of (is_valid, error_messages)
    """
    pass


def validate_dataset_link(dataset_id, story_id):
    """
    Validate that a dataset can be linked to a story.

    Checks:
    - Dataset exists
    - User has access to dataset
    - Dataset not already linked

    Args:
        dataset_id: CKAN package ID
        story_id: Story ID

    Returns:
        Tuple of (is_valid, error_message)
    """
    pass
```

#### `schema.py`

```python
"""
Schema definitions for data stories.

Uses CKAN validators for consistency.
"""

def data_story_schema():
    """
    Schema for creating/updating data stories.

    Returns:
        Dict of field validators
    """
    return {
        'id': [ignore_empty, unicode_safe],
        'title': [not_empty, unicode_safe, max_length(255)],
        'slug': [not_empty, unicode_safe, slug_validator, max_length(255)],
        'abstract': [ignore_missing, unicode_safe],
        'research_question': [ignore_missing, unicode_safe],
        'study_area': [ignore_missing, unicode_safe],
        'author_id': [not_empty, user_id_exists],
        'organization_id': [ignore_missing, group_id_exists],
        'status': [ignore_missing, one_of(['draft', 'submitted', 'under_review', 'published', 'archived'])],
        'is_public': [ignore_missing, boolean_validator],
        'is_featured': [ignore_missing, boolean_validator],
        'meta_description': [ignore_missing, unicode_safe, max_length(500)],
        'meta_keywords': [ignore_missing, unicode_safe],
    }


def data_story_section_schema():
    """
    Schema for story sections.

    Returns:
        Dict of field validators
    """
    return {
        'id': [ignore_empty, unicode_safe],
        'story_id': [not_empty, story_id_exists],
        'section_type': [not_empty, one_of([
            'introduction', 'data_sources', 'methodology',
            'spatial_analysis', 'results', 'conclusions',
            'references', 'acknowledgments'
        ])],
        'title': [ignore_missing, unicode_safe, max_length(255)],
        'content': [ignore_missing, unicode_safe],
        'order_index': [not_empty, int_validator],
        'image_url': [ignore_missing, url_validator],
        'video_url': [ignore_missing, url_validator],
        'terria_config': [ignore_missing, json_validator],
        'terria_share_link': [ignore_missing, url_validator],
        'is_visible': [ignore_missing, boolean_validator],
    }
```

#### `workflow.py`

```python
"""
Publication workflow state machine.

Manages transitions between story states.
"""

class StoryWorkflow:
    """
    State machine for data story publication workflow.
    """

    STATES = {
        'draft': {
            'allowed_transitions': ['submitted'],
            'required_permissions': ['data_story_update_own'],
        },
        'submitted': {
            'allowed_transitions': ['under_review', 'draft'],
            'required_permissions': ['data_story_review'],
        },
        'under_review': {
            'allowed_transitions': ['published', 'draft'],
            'required_permissions': ['data_story_approve'],
        },
        'published': {
            'allowed_transitions': ['archived'],
            'required_permissions': ['data_story_update_any'],
        },
        'archived': {
            'allowed_transitions': ['draft'],
            'required_permissions': ['data_story_update_any'],
        },
    }

    def can_transition(self, from_state, to_state, user_id):
        """
        Check if transition is allowed.

        Args:
            from_state: Current state
            to_state: Target state
            user_id: User requesting transition

        Returns:
            Tuple of (allowed, reason)
        """
        pass

    def transition(self, story_id, to_state, user_id):
        """
        Execute state transition.

        Args:
            story_id: Story ID
            to_state: Target state
            user_id: User executing transition

        Returns:
            Updated story dict

        Raises:
            ValidationError: If transition not allowed
        """
        pass
```

### 4. Templates (`data_stories/templates/`)

#### Template Structure

```
templates/
├── list.html                    # Story listing page
├── view.html                    # Story display page
├── edit.html                    # Story editor
├── review.html                  # Review interface
├── sections/
│   ├── introduction.html        # Introduction section template
│   ├── data_sources.html        # Data sources template
│   ├── methodology.html         # Methodology template
│   ├── spatial_analysis.html    # Spatial analysis with Terria
│   ├── results.html             # Results template
│   └── conclusions.html         # Conclusions template
├── components/
│   ├── story_card.html          # Story preview card
│   ├── section_editor.html      # Section editor component
│   ├── terria_embed.html        # Terria map embed
│   └── dataset_link.html        # Linked dataset display
└── partials/
    ├── header.html              # Story header
    ├── navigation.html          # Section navigation
    └── metadata.html            # Story metadata display
```

---

## API Endpoints

### RESTful API Design

All endpoints follow REST conventions and return JSON.

#### Base URL

```
/api/3/action/data_story_*
```

#### Story Management

| Method | Endpoint | Action | Description |
|--------|----------|--------|-------------|
| POST | `/data_story_create` | `data_story_create` | Create a new story |
| GET | `/data_story_show` | `data_story_show` | Get a story by ID/slug |
| GET | `/data_story_list` | `data_story_list` | List stories with filters |
| POST | `/data_story_update` | `data_story_update` | Update a story |
| POST | `/data_story_delete` | `data_story_delete` | Delete a story |

#### Section Management

| Method | Endpoint | Action | Description |
|--------|----------|--------|-------------|
| POST | `/data_story_section_create` | `data_story_section_create` | Add section to story |
| GET | `/data_story_section_show` | `data_story_section_show` | Get a section |
| GET | `/data_story_section_list` | `data_story_section_list` | List story sections |
| POST | `/data_story_section_update` | `data_story_section_update` | Update a section |
| POST | `/data_story_section_delete` | `data_story_section_delete` | Delete a section |
| POST | `/data_story_reorder_sections` | `data_story_reorder_sections` | Reorder sections |

#### Publication Workflow

| Method | Endpoint | Action | Description |
|--------|----------|--------|-------------|
| POST | `/data_story_submit` | `data_story_submit` | Submit for review |
| POST | `/data_story_review` | `data_story_review` | Start review |
| POST | `/data_story_approve` | `data_story_approve` | Approve and publish |
| POST | `/data_story_request_changes` | `data_story_request_changes` | Request changes |

#### Dataset Linking

| Method | Endpoint | Action | Description |
|--------|----------|--------|-------------|
| POST | `/data_story_link_dataset` | `data_story_link_dataset` | Link a dataset |
| POST | `/data_story_unlink_dataset` | `data_story_unlink_dataset` | Unlink a dataset |
| GET | `/data_story_datasets` | `data_story_datasets` | List linked datasets |

#### Comments & Review

| Method | Endpoint | Action | Description |
|--------|----------|--------|-------------|
| POST | `/data_story_comment_create` | `data_story_comment_create` | Add a comment |
| GET | `/data_story_comment_list` | `data_story_comment_list` | List comments |
| POST | `/data_story_comment_update` | `data_story_comment_update` | Update a comment |
| POST | `/data_story_comment_delete` | `data_story_comment_delete` | Delete a comment |
| POST | `/data_story_comment_resolve` | `data_story_comment_resolve` | Resolve a comment |

#### Statistics & Analytics

| Method | Endpoint | Action | Description |
|--------|----------|--------|-------------|
| POST | `/data_story_record_view` | `data_story_record_view` | Record a view |
| GET | `/data_story_stats` | `data_story_stats` | Get story statistics |

### Web UI Routes

Flask blueprint for HTML views.

```python
# Blueprint routes
blueprint.add_url_rule(
    '/data-stories',
    view_func=data_stories_list,
    endpoint='data_stories_list'
)

blueprint.add_url_rule(
    '/data-stories/new',
    view_func=data_story_create_form,
    methods=['GET', 'POST'],
    endpoint='data_story_create_form'
)

blueprint.add_url_rule(
    '/data-stories/<slug>',
    view_func=data_story_view,
    endpoint='data_story_view'
)

blueprint.add_url_rule(
    '/data-stories/<slug>/edit',
    view_func=data_story_edit,
    methods=['GET', 'POST'],
    endpoint='data_story_edit'
)

blueprint.add_url_rule(
    '/data-stories/<slug>/review',
    view_func=data_story_review_page,
    endpoint='data_story_review'
)
```

---

## User Roles & Permissions

### Role Hierarchy

```
Sysadmin
    |
    +-- Story Editor (Organization Admin)
    |       |
    |       +-- Story Reviewer
    |               |
    |               +-- Story Author (Regular User)
```

### Permission Matrix

| Action | Author | Reviewer | Editor | Sysadmin |
|--------|--------|----------|--------|----------|
| Create story | ✅ Own | ✅ Own | ✅ Any | ✅ Any |
| View draft | ✅ Own | ❌ | ✅ Org | ✅ Any |
| Edit draft | ✅ Own | ❌ | ✅ Org | ✅ Any |
| Submit story | ✅ Own | ❌ | ✅ Org | ✅ Any |
| Review story | ❌ | ✅ Org | ✅ Org | ✅ Any |
| Approve story | ❌ | ✅ Org | ✅ Org | ✅ Any |
| Edit published | ❌ | ❌ | ✅ Org | ✅ Any |
| Delete story | ✅ Own (soft) | ❌ | ✅ Org | ✅ Any (hard) |
| Feature story | ❌ | ❌ | ✅ Org | ✅ Any |

### Role Assignment

Roles can be assigned at multiple levels:

1. **System level**: Sysadmin sets global roles
2. **Organization level**: Org admins assign roles within their org
3. **Story level**: Fine-grained permissions per story (future enhancement)

---

## Data Story Sections

### Standard Section Types

#### 1. Introduction

**Purpose**: Set the stage and engage readers

**Content**:
- Research context and motivation
- Brief overview of the study
- Key objectives
- Significance of the work

**Media**: Hero image, short video introduction

#### 2. Research Question

**Purpose**: Define what the study addresses

**Content**:
- Primary research question
- Secondary questions
- Hypotheses (if applicable)
- Expected outcomes

**Media**: Infographic, conceptual diagram

#### 3. Study Area

**Purpose**: Describe geographic and environmental context

**Content**:
- Location description
- Geographic characteristics
- Climate, topography, hydrology
- Why this area was chosen

**Media**: Terria map showing study region, photos

#### 4. Data Sources

**Purpose**: Document all data used in the study

**Content**:
- Primary data sources (links to datasets)
- Secondary data sources
- Data collection methods
- Temporal and spatial coverage
- Data quality and limitations

**Media**: Dataset preview cards, source logos

**Special Features**:
- Direct links to CKAN datasets
- Data preview widgets
- Download buttons

#### 5. Methodology

**Purpose**: Explain how the research was conducted

**Content**:
- Data processing workflow
- Analysis techniques
- Software and tools used
- Quality control measures
- Reproducibility information

**Media**: Workflow diagrams, code snippets

#### 6. Spatial Analysis

**Purpose**: Present geospatial analysis with interactive visualization

**Content**:
- Analysis approach
- Key spatial patterns
- Interpretation of results
- Comparison with other studies

**Media**: **Terria map instance** with layers, time series

**Special Features**:
- Embedded Terria initialization
- Predefined map views
- Layer toggles
- Timeline controls

#### 7. Results

**Purpose**: Present findings clearly and compellingly

**Content**:
- Key findings
- Statistical results
- Visual representations
- Limitations and uncertainties

**Media**: Charts, graphs, maps, tables

#### 8. Discussion

**Purpose**: Interpret results in broader context

**Content**:
- What the results mean
- Comparison with literature
- Implications for water management
- Future research directions

**Media**: Synthesis diagrams

#### 9. Conclusions

**Purpose**: Summarize key takeaways

**Content**:
- Main conclusions
- Practical applications
- Recommendations
- Impact statement

**Media**: Summary infographic

#### 10. References

**Purpose**: Cite sources and related work

**Content**:
- Bibliography
- Related datasets
- Related publications
- External resources

**Format**: Structured citation list

#### 11. Acknowledgments

**Purpose**: Credit contributors and funding

**Content**:
- Funding sources
- Contributing organizations
- Individual contributors
- Data providers

**Media**: Funder logos, contributor photos

---

## Terria Integration

### Overview

Terria is a powerful open-source web-based geospatial visualization platform. Data Stories will deeply integrate with Terria to provide interactive maps within story sections.

### Integration Approach

#### 1. Terria Initialization JSON

Each spatial analysis section can include a Terria initialization JSON that:

- Defines the catalog (data layers)
- Sets the initial view (camera position)
- Enables specific layers
- Configures timeline (for temporal data)
- Sets styling and legends

**Example Terria Config**:

```json
{
  "initSources": [
    {
      "catalog": [
        {
          "name": "Study Data",
          "type": "group",
          "items": [
            {
              "name": "Precipitation - 2020",
              "type": "wms",
              "url": "https://water-data.org/geoserver/wms",
              "layers": "rainfall:precip_2020",
              "opacity": 0.8
            },
            {
              "name": "River Network",
              "type": "geojson",
              "url": "https://water-data.org/datasets/rivers.geojson",
              "style": {
                "stroke": "#0077be",
                "stroke-width": 2
              }
            }
          ]
        }
      ],
      "workbench": [
        "Precipitation - 2020"
      ],
      "viewerMode": "3d",
      "homeCamera": {
        "west": -10.0,
        "south": 35.0,
        "east": 5.0,
        "north": 45.0
      }
    }
  ]
}
```

#### 2. Terria Share Links

Users can:

1. Configure a Terria map instance manually
2. Use Terria's "Share" feature to generate a share link
3. Paste the share link into the section editor
4. The system automatically extracts the initialization JSON

#### 3. Embedding Terria in Sections

The `terria_embed.html` component:

```html
{% if section.terria_config %}
<div class="terria-map-container" id="terria-{{ section.id }}">
    <iframe
        src="{{ terria_base_url }}#share={{ section.terria_share_link }}"
        width="100%"
        height="600px"
        frameborder="0"
        allow="geolocation">
    </iframe>
</div>
{% endif %}
```

#### 4. Terria Helper Functions

```python
# helpers/terria.py

def parse_terria_share_link(share_link):
    """
    Extract initialization JSON from Terria share link.

    Args:
        share_link: Terria share URL

    Returns:
        Dict with Terria init JSON
    """
    pass


def generate_terria_embed_url(init_json):
    """
    Generate Terria embed URL from init JSON.

    Args:
        init_json: Terria initialization dict

    Returns:
        String URL for iframe src
    """
    pass


def validate_terria_config(init_json):
    """
    Validate Terria configuration structure.

    Args:
        init_json: Terria initialization dict

    Returns:
        Tuple of (is_valid, errors)
    """
    pass
```

### Configuration

Add to CKAN config:

```ini
# Terria Map Integration
ckanext.data_stories.terria_base_url = https://terria.water-data.org
ckanext.data_stories.terria_catalog_url = https://terria.water-data.org/catalog.json
ckanext.data_stories.terria_enable_embed = true
```

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-3)

**Goal**: Establish core architecture and database schema

**Tasks**:
1. Create `data_stories/` module structure
2. Implement database models (`db/models.py`)
3. Write database migration scripts
4. Set up basic blueprint and routes
5. Create base templates (list, view, edit)
6. Implement basic CRUD actions
7. Write unit tests for models and actions

**Deliverables**:
- Working database schema
- Basic CRUD operations
- Skeleton templates
- ~50% test coverage

### Phase 2: Core Features (Weeks 4-6)

**Goal**: Implement essential data story functionality

**Tasks**:
1. Complete all action modules (create, read, update, delete, publish)
2. Implement authorization module with permission checks
3. Build section management system
4. Create dataset linking functionality
5. Develop story editor interface
6. Implement slug generation and validation
7. Add image upload and processing

**Deliverables**:
- Full CRUD with authorization
- Section management
- Dataset linking
- Story editor
- ~70% test coverage

### Phase 3: Publication Workflow (Weeks 7-8)

**Goal**: Implement review and publication system

**Tasks**:
1. Implement workflow state machine
2. Create review interface (templates)
3. Build comment system for reviews
4. Add email notifications for workflow events
5. Implement reviewer assignment
6. Create admin dashboard for story management
7. Add bulk actions for admins

**Deliverables**:
- Complete workflow (draft → submitted → under_review → published)
- Review interface
- Comment system
- Notifications
- ~80% test coverage

### Phase 4: Terria Integration (Weeks 9-10)

**Goal**: Deep integration with Terria for spatial visualization

**Tasks**:
1. Implement Terria config parser
2. Create Terria embed component
3. Build Terria section editor
4. Add Terria share link support
5. Implement Terria validation
6. Create Terria helper functions
7. Add Terria configuration documentation

**Deliverables**:
- Working Terria embeds in stories
- Section editor with Terria support
- Terria helper functions
- ~85% test coverage

### Phase 5: Polish & Enhancement (Weeks 11-12)

**Goal**: Improve UX, add enhancements, and optimize

**Tasks**:
1. Improve UI/UX based on feedback
2. Add story templates (pre-filled section structures)
3. Implement story duplication
4. Add export functionality (PDF, Markdown)
5. Optimize database queries
6. Improve search and filtering
7. Add analytics dashboard
8. Implement story versioning and revision history
9. Comprehensive documentation

**Deliverables**:
- Polished UI
- Export functionality
- Analytics
- Versioning
- Complete documentation
- ~90% test coverage

### Phase 6: Testing & Deployment (Weeks 13-14)

**Goal**: Thorough testing and production deployment

**Tasks**:
1. Comprehensive integration testing
2. User acceptance testing (UAT)
3. Performance testing and optimization
4. Security audit
5. Accessibility audit (WCAG 2.1 AA)
6. Cross-browser testing
7. Production deployment
8. Monitoring setup
9. User training materials
10. Launch!

**Deliverables**:
- Production-ready system
- Test reports
- Deployment documentation
- User guides
- ~95% test coverage

---

## Testing Strategy

### Test Pyramid

```
        /\
       /E2E\
      /------\
     /Integration\
    /--------------\
   /   Unit Tests   \
  /------------------\
```

### Unit Tests

**Location**: `data_stories/tests/`

**Coverage**: All modules (actions, auth, logic, helpers, utils)

**Tools**: pytest, pytest-ckan

**Example**:

```python
# tests/test_actions_create.py

def test_data_story_create_success():
    """Test successful story creation"""
    context = {'user': 'test_user'}
    data_dict = {
        'title': 'Test Story',
        'slug': 'test-story',
        'abstract': 'A test story'
    }

    result = data_story_create(context, data_dict)

    assert result['title'] == 'Test Story'
    assert result['slug'] == 'test-story'
    assert result['status'] == 'draft'


def test_data_story_create_missing_title():
    """Test story creation fails without title"""
    context = {'user': 'test_user'}
    data_dict = {'slug': 'test-story'}

    with pytest.raises(ValidationError):
        data_story_create(context, data_dict)
```

### Integration Tests

**Focus**: End-to-end workflows

**Scenarios**:
1. Create story → Add sections → Submit → Review → Publish
2. Link datasets to story
3. Terria integration
4. Permission checks across workflow
5. Comment and review cycle

### API Tests

**Tool**: pytest with requests

**Coverage**: All API endpoints

**Example**:

```python
def test_api_data_story_create():
    """Test story creation via API"""
    response = requests.post(
        'http://localhost:5000/api/3/action/data_story_create',
        json={
            'title': 'API Test Story',
            'slug': 'api-test-story'
        },
        headers={'Authorization': api_key}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['result']['title'] == 'API Test Story'
```

### UI Tests

**Tool**: Selenium or Playwright

**Scenarios**:
1. User can create a story through the web interface
2. User can add and reorder sections
3. User can submit story for review
4. Reviewer can approve story
5. Published story displays correctly

### Performance Tests

**Tool**: Locust or Apache JMeter

**Metrics**:
- Response time for story list (target: <500ms)
- Response time for story view (target: <1s)
- Concurrent users supported (target: 100)
- Database query optimization

### Accessibility Tests

**Tool**: axe-core, WAVE

**Standards**: WCAG 2.1 AA

**Checks**:
- Keyboard navigation
- Screen reader compatibility
- Color contrast
- Form labels
- Semantic HTML

---

## Migration Path

### From Existing System

If migrating existing rapid-response content to data stories:

#### Step 1: Data Mapping

Map existing fields:

```
ckanext_pages.page_type='rapid-response'
    ↓
data_stories table

ckanext_pages.extras JSON fields
    ↓
data_story_sections records
```

#### Step 2: Migration Script

```python
# migration_script.py

def migrate_rapid_response_to_stories():
    """
    Migrate rapid-response pages to data stories.
    """
    # Get all rapid-response pages
    pages = db.Page.pages(page_type='rapid-response')

    for page in pages:
        # Create story
        story = create_story_from_page(page)

        # Extract sections from extras
        sections = extract_sections_from_extras(page.extras)

        # Create sections
        for section in sections:
            create_section(story.id, section)

        # Mark page as migrated
        mark_as_migrated(page.id)
```

#### Step 3: Dual System Period

- Run both systems in parallel for 2-4 weeks
- Provide migration UI for users to convert their content
- Gradual rollout to minimize disruption

#### Step 4: Deprecation

- Announce end-of-life for old system
- Final migration of remaining content
- Archive old system
- Redirect old URLs to new data stories

---

## Configuration

### CKAN Config Settings

Add to `ckan.ini`:

```ini
# ========================================
# Data Stories Configuration
# ========================================

# Enable/disable data stories
ckanext.data_stories.enabled = true

# Require review before publishing
ckanext.data_stories.require_review = true

# Auto-assign reviewers based on organization
ckanext.data_stories.auto_assign_reviewers = true

# Maximum number of sections per story
ckanext.data_stories.max_sections = 20

# Allow external contributors (non-CKAN users)
ckanext.data_stories.allow_external_contributors = true

# Featured stories on homepage
ckanext.data_stories.featured_count = 3

# Default story visibility
ckanext.data_stories.default_visibility = private

# Terria Integration
ckanext.data_stories.terria_base_url = https://terria.water-data.org
ckanext.data_stories.terria_catalog_url = https://terria.water-data.org/catalog.json
ckanext.data_stories.terria_enable_embed = true

# Image settings
ckanext.data_stories.max_image_size = 5  # MB
ckanext.data_stories.allowed_image_formats = png,jpg,jpeg,gif,webp

# Export settings
ckanext.data_stories.enable_pdf_export = true
ckanext.data_stories.enable_markdown_export = true

# Email notifications
ckanext.data_stories.notify_on_submit = true
ckanext.data_stories.notify_on_review = true
ckanext.data_stories.notify_on_publish = true

# Analytics
ckanext.data_stories.track_views = true
ckanext.data_stories.google_analytics_id = UA-XXXXX-Y
```

---

## Success Metrics

### Key Performance Indicators (KPIs)

1. **Adoption Rate**
   - Number of stories created per month
   - Number of active authors
   - Growth rate

2. **Engagement**
   - Story views
   - Time spent on stories
   - Section interaction (Terria maps, datasets)

3. **Quality**
   - Stories with all required sections
   - Stories linked to datasets
   - Stories using Terria integration

4. **Workflow Efficiency**
   - Average time from submission to publication
   - Review turnaround time
   - Revision cycles per story

5. **Technical Performance**
   - Page load time
   - API response time
   - Error rate

6. **User Satisfaction**
   - User surveys
   - Feature requests
   - Support tickets

---

## Future Enhancements

### Phase 7+ (Post-Launch)

1. **Advanced Features**
   - Story templates (pre-built section structures)
   - Collaborative editing (multiple authors)
   - Version comparison (diff view)
   - Story collections (thematic groupings)
   - Story recommendations (ML-based)

2. **Integration Enhancements**
   - DOI minting for published stories
   - ORCID integration for authors
   - CrossRef citation linking
   - Altmetrics integration
   - Social media sharing optimization

3. **Visualization Enhancements**
   - Chart.js integration for data visualization
   - Timeline.js for temporal narratives
   - 3D model viewers
   - Video player with annotations

4. **API Enhancements**
   - GraphQL API
   - WebSocket support for real-time collaboration
   - Webhook notifications
   - OpenAPI documentation

5. **Mobile Experience**
   - Native mobile app
   - Offline reading
   - Mobile-optimized editor

6. **Localization**
   - Multi-language support
   - Translation workflow
   - RTL language support

---

## Risks & Mitigation

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Database performance issues | High | Medium | Query optimization, indexing, caching |
| Terria integration complexity | Medium | High | Thorough testing, fallback to iframe embed |
| Large file uploads | Medium | Medium | Chunked uploads, CDN for static assets |
| Migration from old system | High | Medium | Comprehensive testing, rollback plan |

### Project Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Scope creep | High | High | Strict phase boundaries, MVP focus |
| User resistance to change | Medium | Medium | User training, migration assistance |
| Insufficient testing | High | Medium | Dedicated QA phase, automated tests |
| Documentation gaps | Medium | Low | Documentation as part of DoD |

---

## Conclusion

This implementation plan provides a comprehensive roadmap for building a world-class Data Stories system for open-access water resources research. By learning from the current rapid-response implementation and addressing its limitations, we will create a modular, maintainable, and scalable system that empowers researchers to tell compelling stories about their data.

### Key Takeaways

1. **Modular Architecture**: Clean separation of concerns makes the codebase maintainable and testable
2. **Granular Permissions**: Role-based access control enables collaborative workflows
3. **Deep Terria Integration**: Spatial visualization is first-class, not an afterthought
4. **Publication Workflow**: Built-in review process ensures quality
5. **Dataset Linking**: Direct connection to CKAN datasets promotes data reuse
6. **Phased Implementation**: Incremental delivery reduces risk and enables feedback

### Next Steps

1. Review and approve this plan with stakeholders
2. Set up development environment
3. Begin Phase 1: Foundation
4. Schedule regular sprint reviews
5. Gather user feedback early and often

---

## Appendix A: Code Examples

### Example: Creating a Story via API

```python
import requests

api_key = 'your-api-key'
base_url = 'http://localhost:5000'

# Create a story
response = requests.post(
    f'{base_url}/api/3/action/data_story_create',
    json={
        'title': 'Groundwater Depletion in the Indus Basin',
        'slug': 'groundwater-indus-basin',
        'abstract': 'This study analyzes groundwater trends in the Indus Basin using satellite data.',
        'research_question': 'How has groundwater storage changed in the Indus Basin from 2002-2020?',
        'organization_id': 'ihp-wins'
    },
    headers={'Authorization': api_key}
)

story = response.json()['result']
print(f"Created story: {story['id']}")

# Add a spatial analysis section with Terria
requests.post(
    f'{base_url}/api/3/action/data_story_section_create',
    json={
        'story_id': story['id'],
        'section_type': 'spatial_analysis',
        'title': 'Groundwater Trends Map',
        'content': 'The map below shows groundwater storage anomalies...',
        'order_index': 1,
        'terria_share_link': 'https://terria.water-data.org/#share=abc123'
    },
    headers={'Authorization': api_key}
)

# Link a dataset
requests.post(
    f'{base_url}/api/3/action/data_story_link_dataset',
    json={
        'story_id': story['id'],
        'dataset_id': 'grace-groundwater-indus',
        'relationship_type': 'primary',
        'description': 'GRACE satellite groundwater data'
    },
    headers={'Authorization': api_key}
)

# Submit for review
requests.post(
    f'{base_url}/api/3/action/data_story_submit',
    json={
        'id': story['id'],
        'submission_notes': 'Ready for review'
    },
    headers={'Authorization': api_key}
)

print("Story submitted for review!")
```

---

## Appendix B: Database Schema Diagram

```
┌─────────────────────────┐
│     data_stories        │
├─────────────────────────┤
│ id (PK)                 │
│ title                   │
│ slug (UNIQUE)           │
│ abstract                │
│ research_question       │
│ study_area              │
│ author_id (FK)          │
│ organization_id (FK)    │
│ status                  │
│ submission_date         │
│ reviewer_id (FK)        │
│ published_at            │
│ is_public               │
│ is_featured             │
│ view_count              │
│ created_at              │
│ updated_at              │
└─────────────────────────┘
            │
            │ 1:N
            ▼
┌─────────────────────────┐
│  data_story_sections    │
├─────────────────────────┤
│ id (PK)                 │
│ story_id (FK)           │
│ section_type            │
│ title                   │
│ content                 │
│ order_index             │
│ image_url               │
│ terria_config (JSONB)   │
│ terria_share_link       │
│ is_visible              │
│ created_at              │
│ updated_at              │
└─────────────────────────┘

┌─────────────────────────┐
│  data_story_datasets    │
├─────────────────────────┤
│ id (PK)                 │
│ story_id (FK)           │
│ dataset_id              │
│ relationship_type       │
│ description             │
│ order_index             │
│ created_at              │
└─────────────────────────┘

┌─────────────────────────┐
│ data_story_contributors │
├─────────────────────────┤
│ id (PK)                 │
│ story_id (FK)           │
│ user_id (FK)            │
│ name                    │
│ email                   │
│ affiliation             │
│ orcid                   │
│ role                    │
│ order_index             │
│ created_at              │
└─────────────────────────┘

┌─────────────────────────┐
│  data_story_comments    │
├─────────────────────────┤
│ id (PK)                 │
│ story_id (FK)           │
│ section_id (FK)         │
│ user_id (FK)            │
│ content                 │
│ comment_type            │
│ parent_comment_id (FK)  │
│ is_resolved             │
│ created_at              │
│ updated_at              │
└─────────────────────────┘

┌─────────────────────────┐
│  data_story_revisions   │
├─────────────────────────┤
│ id (PK)                 │
│ story_id (FK)           │
│ version                 │
│ title                   │
│ content_snapshot (JSONB)│
│ changed_by (FK)         │
│ change_summary          │
│ created_at              │
└─────────────────────────┘
```

---

## Appendix C: UI Mockups

### Story List Page

```
┌────────────────────────────────────────────────────────────┐
│ CKAN                                          [Search] [+New]│
├────────────────────────────────────────────────────────────┤
│ Data Stories                                                │
├────────────────────────────────────────────────────────────┤
│ [All] [Published] [Draft] [Under Review]                   │
│                                                             │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ [Image]  Groundwater Depletion in Indus Basin       │   │
│ │          by Dr. Sarah Chen • Mar 15, 2024           │   │
│ │          This study analyzes groundwater trends...  │   │
│ │          [View Story] [5 datasets] [1.2k views]     │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ [Image]  Flood Risk Assessment - Mekong Delta       │   │
│ │          by Dr. John Smith • Mar 10, 2024           │   │
│ │          Using satellite imagery and hydraulic...   │   │
│ │          [View Story] [3 datasets] [850 views]      │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ [Load More]                                                 │
└────────────────────────────────────────────────────────────┘
```

### Story View Page

```
┌────────────────────────────────────────────────────────────┐
│ CKAN                                      [Edit] [Share] [↓]│
├────────────────────────────────────────────────────────────┤
│ Groundwater Depletion in the Indus Basin                   │
│ by Dr. Sarah Chen • Published Mar 15, 2024                 │
├────────────────────────────────────────────────────────────┤
│ [Hero Image]                                                │
│                                                             │
│ Navigation: [Introduction] [Data] [Methods] [Results]      │
├────────────────────────────────────────────────────────────┤
│                                                             │
│ ## Introduction                                             │
│                                                             │
│ The Indus Basin is one of the most water-stressed...      │
│                                                             │
│ ## Study Area                                               │
│                                                             │
│ [Terria Map - Interactive]                                 │
│                                                             │
│ ## Data Sources                                             │
│                                                             │
│ ┌────────────────────────────────────────────────────┐     │
│ │ 📊 GRACE Groundwater Data                          │     │
│ │    NASA JPL • 2002-2020 • 0.5° resolution         │     │
│ │    [View Dataset] [Download]                       │     │
│ └────────────────────────────────────────────────────┘     │
│                                                             │
│ ## Methodology                                              │
│ ...                                                         │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### Story Editor

```
┌────────────────────────────────────────────────────────────┐
│ CKAN - Edit Story                    [Save Draft] [Preview]│
├────────────────────────────────────────────────────────────┤
│ Title: [Groundwater Depletion in the Indus Basin        ] │
│ Slug:  [groundwater-indus-basin                          ] │
│                                                             │
│ Abstract:                                                   │
│ [This study analyzes groundwater trends in the Indus... ] │
│                                                             │
│ Research Question:                                          │
│ [How has groundwater storage changed from 2002-2020?    ] │
│                                                             │
│ ── Sections ──                                              │
│                                                             │
│ [+] Add Section                                             │
│                                                             │
│ ┌────────────────────────────────────────────────────┐     │
│ │ ≡ Introduction                            [Edit] [×]│     │
│ │   The Indus Basin is one of the most...            │     │
│ └────────────────────────────────────────────────────┘     │
│                                                             │
│ ┌────────────────────────────────────────────────────┐     │
│ │ ≡ Spatial Analysis                        [Edit] [×]│     │
│ │   [Terria Map Preview]                              │     │
│ └────────────────────────────────────────────────────┘     │
│                                                             │
│ ── Linked Datasets ──                                       │
│                                                             │
│ [+] Link Dataset                                            │
│                                                             │
│ 📊 GRACE Groundwater Data                        [Unlink]  │
│                                                             │
│ [Submit for Review]                                         │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

**End of Implementation Plan**

*This document is a living plan and will be updated as the project progresses.*
