# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **ckanext-pages**, a CKAN extension that provides a basic CMS (Content Management System) for adding simple pages to CKAN instances. The extension supports multiple page types including regular pages, blog posts, rapid response pages, water family content (news, events, publications), and open source software listings.

## Development Commands

### Database Setup
```bash
# Initialize database (CKAN >= 2.9)
ckan --config=/etc/ckan/default/ckan.ini db upgrade -p pages

# For development/testing
ckan -c test.ini db init
ckan -c test.ini db upgrade -p pages
```

### Testing
```bash
# Run all tests
pytest --ckan-ini=test.ini --cov=ckanext.pages --cov-report=term-missing --cov-append --disable-warnings ckanext/pages/tests

# Run specific test file
pytest --ckan-ini=test.ini ckanext/pages/tests/test_action.py
pytest --ckan-ini=test.ini ckanext/pages/tests/test_logic.py
```

### Code Quality
```bash
# Syntax check
flake8 . --count --select=E901,E999,F821,F822,F823 --show-source --statistics --exclude ckan

# Full linting
flake8 . --count --max-line-length=127 --statistics --exclude ckan
```

### Installation
```bash
# Install in development mode
pip install -e .

# Install dependencies
pip install -r requirements.txt
pip install -r dev-requirements.txt
```

## Architecture Overview

### Core Components

**Plugin Structure**: The extension implements two main plugins:
- `PagesPlugin`: Main CMS functionality with multiple page types
- `TextBoxView`: WYSIWYG resource view for datasets

**Database Layer** (`db.py`):
- `Page` model: Main entity storing page content with fields for title, content, metadata
- `PageRevision` model: Revision tracking system (up to 3 revisions by default)
- Uses SQLAlchemy ORM with PostgreSQL JSONB for flexible metadata storage

**Actions Layer** (`actions.py`):
- CRUD operations for pages: `pages_show`, `pages_update`, `pages_delete`, `pages_list`
- Specialized actions for organization/group pages when enabled
- File upload handling for page attachments
- Search and filtering capabilities with support for custom ordering

**Authorization** (`auth.py`):
- Role-based permissions for page management
- Special handling for water family content types
- Organization/group-specific permissions when those features are enabled

**Blueprint/Routes** (`blueprint.py`, `utils.py`):
- Flask blueprint defining URL routes
- View functions for rendering pages, editing, revisions
- Specialized routes for different page types (blog, rapid-response, water-*)

### Page Types System

The extension supports multiple specialized page types:
- **page**: Standard CMS pages
- **blog**: Blog posts with publish dates
- **rapid-response**: Emergency/urgent content with priority levels
- **water-news**: Water family news content
- **water-events**: Water family events with timeline support
- **water-publications**: Water family publications
- **open-source-software**: Software listings with categorization

Each page type has its own templates, helper functions, and can have specialized fields.

### Template Architecture

Templates are organized in theme directories:
- `templates_main/`: Core page templates
- `templates_group/`: Group-specific templates (when enabled)
- `templates_organization/`: Organization-specific templates (when enabled)

### Editor Support

The extension supports multiple content editors:
- **Markdown**: Default editor with optional HTML support
- **CKEditor**: Full WYSIWYG editor with extensible configuration
- **Medium**: Alternative WYSIWYG editor

## Configuration Options

Key configuration options in CKAN INI file:
```ini
# Enable organization/group pages
ckanext.pages.organization = True
ckanext.pages.group = True

# Menu customization
ckanext.pages.about_menu = False
ckanext.pages.group_menu = False
ckanext.pages.organization_menu = False

# Content options
ckanext.pages.allow_html = True
ckanext.pages.editor = ckeditor

# Revision system
ckanext.pages.revisions_limit = 3
ckanext.pages.revisions_force_limit = true
```

## Extension Points

### Schema Extension
Implement `IPagesSchema` interface to add custom fields:
```python
from ckanext.pages.interfaces import IPagesSchema

class MyPlugin(plugins.SingletonPlugin):
    plugins.implements(IPagesSchema)
    
    def update_pages_schema(self, schema):
        schema.update({
            'custom_field': [toolkit.get_validator('not_empty')]
        })
        return schema
```

### Template Extension
Extend `ckanext_pages/base_form.html` and override `extra_pages_form` block to add custom form fields.

### CKEditor Configuration
Override CKEditor settings by setting `window.ckan.pages.override_config` in your JavaScript.

## Helper Functions

The plugin provides numerous template helper functions in `plugin.py`:
- `get_recent_*`: Functions for fetching recent content by type
- `get_*_class`: CSS class generators for various content attributes
- `safe_json_loads`: Safe JSON parsing
- Content rendering and formatting utilities

## Testing Strategy

- Uses pytest-ckan for CKAN-specific testing
- Test coverage includes actions, logic, and authorization
- CI/CD runs tests against multiple CKAN versions (2.9, 2.10, 2.11)
- Integration tests with PostgreSQL, Solr, and Redis

## File Upload Support

The extension includes file upload capabilities for page attachments, using CKAN's built-in uploader system with proper permission checks.