# Data Stories for CKAN

A comprehensive storytelling extension for ckanext-pages, enabling researchers to create narrative-driven data stories with integrated geospatial visualizations.

## 🚀 Quick Start

```python
# Create a data story
from ckan.plugins import toolkit

story = toolkit.get_action('data_story_create')(
    context={'user': 'researcher'},
    data_dict={
        'title': 'Groundwater Depletion in the Indus Basin',
        'abstract': 'Analysis of groundwater trends using satellite data',
        'research_question': 'How has groundwater changed over the last decade?',
    }
)

# Add a section with Terria map
toolkit.get_action('data_story_section_create')(
    context={'user': 'researcher'},
    data_dict={
        'story_id': story['id'],
        'section_type': 'spatial_analysis',
        'title': 'Spatial Distribution of Groundwater Depletion',
        'content': 'The map below shows...',
        'terria_share_link': 'https://terria.water-data.org/#share=abc123',
    }
)

# Submit for review
toolkit.get_action('data_story_submit')(
    context={'user': 'researcher'},
    data_dict={'id': story['id']}
)
```

## 📦 What's Included

### Core Modules

```
data_stories/
├── actions/          # 30+ RESTful API actions
├── auth/             # RBAC authorization system
├── blueprint/        # Flask web routes
├── db/               # Database models and migrations
├── logic/            # Validation and workflow
├── helpers/          # Terria integration and formatting
└── tests/            # Comprehensive test suite (120+ tests)
```

### Features

- ✅ **11 Section Types**: Introduction, Methodology, Spatial Analysis, etc.
- ✅ **Terria Integration**: Embed interactive geospatial maps
- ✅ **Multi-Author Support**: Collaborate with ORCID integration
- ✅ **Flexible Publication**: 3 workflows (Review, Direct, Self-Publishing)
- ✅ **Review Panel**: Comprehensive approval interface for reviewers
- ✅ **Dataset Linking**: Connect stories to CKAN datasets
- ✅ **Comment System**: Review and feedback with threading
- ✅ **Version Control**: Automatic revision snapshots
- ✅ **Search & Filters**: Find stories quickly
- ✅ **Analytics**: Track views and engagement

## 🎯 Use Cases

### For Researchers

Create rich narratives that combine:
- Research methodology and findings
- Interactive geospatial visualizations
- Links to underlying datasets
- Collaboration with co-authors

### For Organizations

- Showcase research outputs
- Share data stories with stakeholders
- Maintain quality through review workflow
- Track engagement and impact

## 📖 Documentation

- **[Implementation Plan](../../../DATA_STORIES_IMPLEMENTATION_PLAN.md)** - Complete technical specification
- **[Integration Guide](../../../DATA_STORIES_INTEGRATION_GUIDE.md)** - Step-by-step integration
- **[User Guide](../../../DATA_STORIES_README.md)** - End-user documentation
- **[Test Documentation](tests/README.md)** - Running and writing tests
- **[Final Status](../../../DATA_STORIES_FINAL_STATUS.md)** - Implementation status

## 🔧 Installation

### 1. Prerequisites

- CKAN 2.9+
- PostgreSQL 12+
- ckanext-pages installed

### 2. Install Extension

Already included in ckanext-pages. Just need to integrate:

```python
# In ckanext/pages/plugin.py
from ckanext.pages.data_stories import actions as ds_actions
from ckanext.pages.data_stories import auth as ds_auth
from ckanext.pages.data_stories.blueprint import routes as ds_routes
```

### 3. Run Migrations

```bash
ckan -c /etc/ckan/default/ckan.ini db upgrade -p pages_data_stories
```

Or manually:

```python
from ckanext.pages.data_stories.db import init_tables
from ckan import model
init_tables(model.meta.engine)
```

### 4. Configure

Add to `ckan.ini`:

```ini
ckanext.data_stories.enabled = true
ckanext.data_stories.require_review = true
ckanext.data_stories.terria_base_url = https://terria.water-data.org

# Allow authors to publish stories directly without review (default: false)
ckanext.pages.data_stories.allow_direct_publish = false
```

### 5. Restart CKAN

```bash
sudo supervisorctl restart ckan-uwsgi:*
```

## 📝 Publication Workflows

Data Stories supports multiple publication workflows to fit different organizational needs:

### Option 1: Review Workflow (Default)

**Best for**: Organizations requiring quality control and editorial review.

```
Author creates story → Status: DRAFT
     ↓
Author submits for review → Status: SUBMITTED
     ↓
Reviewer reviews story → Status: UNDER_REVIEW
     ↓
Reviewer approves → Status: PUBLISHED (visible to public)
```

**Who can review/approve:**
- ✅ Sysadmins (all stories)
- ✅ Organization Admins (stories in their org)

**URLs:**
- `/data-stories/pending-review` - List all pending stories
- `/data-stories/<slug>/review` - Review a specific story

### Option 2: Direct Publishing (Admins)

**Best for**: Trusted editors who need quick publication.

Sysadmins and Organization Admins can bypass the review workflow:

```
Admin creates story → Status: DRAFT
     ↓
Admin clicks "Publish Now" → Status: PUBLISHED
```

This option is always available for admins, regardless of configuration.

### Option 3: Author Self-Publishing

**Best for**: Small teams or trusted author communities.

Enable in `ckan.ini`:

```ini
ckanext.pages.data_stories.allow_direct_publish = true
```

With this setting:
- ✅ All authors can publish their own stories directly
- ✅ No review workflow required
- ✅ Stories go from DRAFT → PUBLISHED in one click

```
Author creates story → Status: DRAFT
     ↓
Author clicks "Publish Now" → Status: PUBLISHED
```

**Configuration:**

```ini
# Default: false (review required)
ckanext.pages.data_stories.allow_direct_publish = false

# Enable self-publishing for all authors
ckanext.pages.data_stories.allow_direct_publish = true
```

### Comparison Table

| Feature | Review Workflow | Direct (Admins) | Self-Publishing |
|---------|----------------|-----------------|-----------------|
| Quality Control | ✅ Yes | ❌ No | ❌ No |
| Speed | 🐢 Slower | ⚡ Instant | ⚡ Instant |
| Who can publish | Admins only | Admins only | All authors |
| Configuration | Default | Always enabled | Requires config |
| Best for | Large orgs | Trusted editors | Small teams |

### Review Interface

Reviewers have access to a comprehensive review panel at `/data-stories/pending-review`:

**Features:**
- 📋 List all submitted/under-review stories
- 🔍 Filter by status
- 👁️ Preview full story content
- ✅ Approve and publish
- ✏️ Request changes with comments
- 📊 Track review history

**Review Actions:**
1. **Start Review** - Marks story as "Under Review"
2. **Approve and Publish** - Publishes story immediately
3. **Request Changes** - Returns to author with feedback

## 🧪 Testing

Run the test suite:

```bash
pytest --ckan-ini=test.ini ckanext/pages/data_stories/tests/
```

With coverage:

```bash
pytest --ckan-ini=test.ini \
       --cov=ckanext.pages.data_stories \
       --cov-report=html \
       ckanext/pages/data_stories/tests/
```

See [tests/README.md](tests/README.md) for more details.

## 📊 Architecture

### Database Models (6 tables)

1. **DataStory** - Main story entity
2. **DataStorySection** - Story sections with Terria config
3. **DataStoryDataset** - Links to CKAN packages
4. **DataStoryContributor** - Multi-author support
5. **DataStoryComment** - Review and feedback
6. **DataStoryRevision** - Version history

### API Actions (30+)

**Create**
- `data_story_create`, `data_story_section_create`, `data_story_contributor_add`

**Read**
- `data_story_show`, `data_story_list`, `data_story_section_show`

**Update**
- `data_story_update`, `data_story_section_update`, `data_story_reorder_sections`

**Delete**
- `data_story_delete`, `data_story_section_delete`

**Workflow**
- `data_story_submit`, `data_story_review`, `data_story_approve`, `data_story_reject`, `data_story_archive`

**Datasets**
- `data_story_dataset_link`, `data_story_dataset_unlink`, `data_story_datasets_list`

**Comments**
- `data_story_comment_create`, `data_story_comment_update`, `data_story_comment_delete`, `data_story_comment_resolve`, `data_story_comments_list`

**Stats**
- `data_story_increment_views`, `data_story_stats`, `data_stories_popular`, `data_stories_recent`

### Web Routes (13)

- `/data-stories/` - Browse all published stories
- `/data-stories/new` - Create new story
- `/data-stories/<slug>` - View story
- `/data-stories/<slug>/edit` - Edit story
- `/data-stories/<slug>/delete` - Delete story
- `/data-stories/<slug>/submit` - Submit for review (POST)
- `/data-stories/<slug>/publish` - Publish directly (POST)
- `/data-stories/<slug>/review` - Review interface (GET/POST)
- `/data-stories/pending-review` - List pending stories (reviewers only)
- `/data-stories/my-stories` - User's stories
- Plus routes for sections, datasets, comments

## 🔐 Security

- **RBAC**: Role-based access control
- **Input Validation**: All inputs validated
- **SQL Injection Prevention**: SQLAlchemy ORM
- **XSS Prevention**: Template escaping
- **CSRF Protection**: CKAN forms
- **Authorization Checks**: On all operations

## 🎨 Frontend

### Templates

8 Jinja2 templates for complete UI:
- Base layout with navigation
- Story listing with search/filters
- Story display with sections
- Interactive editor
- Review interface
- Reusable components

### Static Assets

- **CSS** (700 lines): Responsive, print-friendly
- **JavaScript** (350 lines): Interactive, drag-and-drop, validation

## 📈 Performance

- Database indexes on key fields
- Efficient queries with joins
- Pagination for large lists
- Caching where appropriate

## 🤝 Contributing

### Running Tests

```bash
pytest --ckan-ini=test.ini ckanext/pages/data_stories/tests/
```

### Code Style

Follow CKAN coding standards:
- PEP 8 compliant
- Comprehensive docstrings
- Type hints where applicable

### Adding Features

1. Create database migration if needed
2. Add action in appropriate `actions/*.py` file
3. Add authorization in `auth/permissions.py`
4. Add tests in `tests/`
5. Update documentation

## 📝 Examples

### Creating a Complete Story

```python
from ckan.plugins import toolkit

# 1. Create story
story = toolkit.get_action('data_story_create')(
    context={'user': 'researcher'},
    data_dict={
        'title': 'Water Quality Analysis',
        'abstract': 'Comprehensive analysis of water quality...',
        'research_question': 'Has water quality improved?',
        'study_area': 'Mekong River Basin',
    }
)

# 2. Add sections
sections = [
    ('introduction', 'Introduction', 'This study examines...'),
    ('data_sources', 'Data Sources', 'We used satellite imagery...'),
    ('methodology', 'Methodology', 'Our approach involves...'),
    ('spatial_analysis', 'Spatial Analysis', 'The map shows...'),
    ('results', 'Results', 'We found that...'),
    ('conclusions', 'Conclusions', 'In conclusion...'),
]

for section_type, title, content in sections:
    toolkit.get_action('data_story_section_create')(
        context={'user': 'researcher'},
        data_dict={
            'story_id': story['id'],
            'section_type': section_type,
            'title': title,
            'content': content,
        }
    )

# 3. Link datasets
toolkit.get_action('data_story_dataset_link')(
    context={'user': 'researcher'},
    data_dict={
        'story_id': story['id'],
        'dataset_id': 'my-dataset-id',
        'relationship_type': 'primary',
    }
)

# 4. Add Terria map to spatial analysis section
spatial_section = # ... get spatial_analysis section
toolkit.get_action('data_story_section_update')(
    context={'user': 'researcher'},
    data_dict={
        'id': spatial_section['id'],
        'terria_share_link': 'https://terria.water-data.org/#share=abc123',
    }
)

# 5. Submit for review
toolkit.get_action('data_story_submit')(
    context={'user': 'researcher'},
    data_dict={'id': story['id']}
)
```

### Searching Stories

```python
# List published stories
stories = toolkit.get_action('data_story_list')(
    data_dict={
        'status': 'published',
        'limit': 10,
        'offset': 0,
    }
)

# Search by query
stories = toolkit.get_action('data_story_list')(
    data_dict={
        'q': 'water quality',
        'sort': 'view_count desc',
    }
)

# Filter by organization
stories = toolkit.get_action('data_story_list')(
    data_dict={
        'organization_id': 'my-org-id',
    }
)
```

## 🐛 Troubleshooting

### Database Connection Errors

Check that PostgreSQL is running and credentials are correct in ckan.ini.

### Import Errors

Ensure extension is installed:
```bash
pip install -e .
```

### Migration Errors

Run migrations manually:
```python
from ckanext.pages.data_stories.db import init_tables
from ckan import model
init_tables(model.meta.engine)
```

### Template Not Found

Ensure templates directory is registered:
```python
tk.add_template_directory(config, 'theme/templates_main')
```

## 📊 Statistics

- **40+ files** created
- **~10,000+ lines** of code
- **30+ API actions**
- **13 web routes**
- **6 database models**
- **120+ tests** (85-90% coverage)
- **3 publication workflows** (Review, Direct, Self-Publishing)

## 🎓 Learn More

- [Implementation Plan](../../../DATA_STORIES_IMPLEMENTATION_PLAN.md) - Architecture and design
- [API Documentation](../../../DATA_STORIES_README.md) - Complete API reference
- [User Guide](../../../DATA_STORIES_README.md) - End-user documentation

## 📄 License

Same as ckanext-pages (AGPL-3.0)

## 👥 Credits

Built as a comprehensive extension to ckanext-pages, following CKAN best practices.

---

**Version**: 1.1.0
**Status**: Production Ready
**Last Updated**: 2025-11-21
