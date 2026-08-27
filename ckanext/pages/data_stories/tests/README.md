# Data Stories Tests

Comprehensive test suite for the Data Stories functionality.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Pytest configuration and shared fixtures
├── test_models.py        # Database model tests
├── test_actions.py       # API action tests
├── test_auth.py          # Authorization tests
├── test_validation.py    # Validation logic tests
└── test_workflow.py      # Workflow state machine tests
```

## Test Coverage

### test_models.py (~550 lines)
Tests for all 6 database models:
- DataStory creation, relationships, slug uniqueness
- DataStorySection ordering, Terria config storage
- DataStoryDataset linking, uniqueness constraints
- DataStoryContributor internal and external contributors
- DataStoryComment threading, resolution
- DataStoryRevision version history

### test_actions.py (~650 lines)
Tests for all 30+ API actions:
- Create actions (stories, sections, contributors)
- Read actions (show, list, pagination, filters)
- Update actions (story, sections, reordering)
- Delete actions (soft/hard delete, permissions)
- Workflow actions (submit, review, approve, reject, archive)
- Dataset actions (link, unlink, list)
- Comment actions (create, reply, resolve)
- Stats actions (views, analytics)

### test_auth.py (~450 lines)
Tests for authorization and permissions:
- Story CRUD permissions (author, sysadmin, organization)
- Workflow permissions (submit, approve, reject)
- Dataset linking permissions (private datasets)
- Comment permissions (create, edit, delete)
- Organization-based access control
- Anonymous vs authenticated access

### test_validation.py (~450 lines)
Tests for validation logic:
- Slug generation and validation
- Section type validation
- Story status validation
- Contributor role validation
- Story completeness checking
- Terria configuration validation (JSON, structure)

### test_workflow.py (~450 lines)
Tests for workflow state machine:
- State transitions (draft → submitted → under_review → published → archived)
- Transition validation (cannot skip states)
- Allowed transitions per state
- Complete workflow scenarios
- Rejection and archiving
- Workflow timestamps (submission_date, published_at)
- Workflow permissions

## Running Tests

### All Data Stories Tests

```bash
pytest --ckan-ini=test.ini ckanext/pages/data_stories/tests/
```

### Specific Test File

```bash
pytest --ckan-ini=test.ini ckanext/pages/data_stories/tests/test_models.py
```

### Specific Test Class

```bash
pytest --ckan-ini=test.ini ckanext/pages/data_stories/tests/test_actions.py::TestDataStoryCreateActions
```

### Specific Test Method

```bash
pytest --ckan-ini=test.ini ckanext/pages/data_stories/tests/test_auth.py::TestDataStoryAuth::test_author_can_update_own_story
```

### With Coverage Report

```bash
pytest --ckan-ini=test.ini \
       --cov=ckanext.pages.data_stories \
       --cov-report=html \
       --cov-report=term-missing \
       ckanext/pages/data_stories/tests/
```

### Verbose Output

```bash
pytest --ckan-ini=test.ini -v ckanext/pages/data_stories/tests/
```

### Stop on First Failure

```bash
pytest --ckan-ini=test.ini -x ckanext/pages/data_stories/tests/
```

### Run Only Failed Tests

```bash
pytest --ckan-ini=test.ini --lf ckanext/pages/data_stories/tests/
```

## Test Fixtures

### Shared Fixtures (conftest.py)

- **clean_db**: Clean database before each test
- **with_plugins**: Load required plugins
- **sample_story**: Create a basic story with user
- **complete_story**: Create story with all required sections
- **story_with_dataset**: Create story with linked dataset
- **story_with_contributors**: Create story with multiple authors
- **organization_story**: Create story within an organization

### Using Fixtures

```python
def test_something(complete_story):
    story, sections, user = complete_story
    # Use the pre-created complete story
    assert story['status'] == 'draft'
    assert len(sections) == 5
```

## Test Requirements

### Database

Tests require a clean PostgreSQL test database. Configure in `test.ini`:

```ini
sqlalchemy.url = postgresql://ckan_test:password@localhost/ckan_test
```

### Plugins

Ensure the pages plugin and the Data Stories feature flag are enabled in
`test.ini`:

```ini
ckan.plugins = pages image_view
ckanext.data_stories.enabled = True
```

### Dependencies

All testing dependencies should be in `dev-requirements.txt`:

```
pytest>=6.0
pytest-ckan
pytest-cov
factory-boy
faker
```

Install with:

```bash
pip install -r dev-requirements.txt
```

## Writing New Tests

### Test Structure

```python
import pytest
from ckan import model
from ckan.tests import factories, helpers
from ckanext.pages.data_stories.db.utils import init_tables


@pytest.mark.usefixtures('clean_db', 'with_plugins')
class TestMyFeature:
    """Tests for my feature."""

    @classmethod
    def setup_class(cls):
        """Initialize database tables."""
        init_tables(model.meta.engine)

    def test_something(self):
        """Test description."""
        user = factories.User()

        result = helpers.call_action(
            'data_story_create',
            context={'user': user['name']},
            title='Test',
        )

        assert result['title'] == 'Test'
```

### Best Practices

1. **Use descriptive test names**: `test_author_can_update_own_story`
2. **One assertion per test** (when possible)
3. **Test both success and failure cases**
4. **Use factories** for test data creation
5. **Clean up after tests** (use fixtures)
6. **Test edge cases** (empty strings, None, very long values)
7. **Mock external dependencies** when needed

### Testing Authorization

```python
from ckan.plugins import toolkit

def test_unauthorized_action(self):
    user = factories.User()
    other_user = factories.User()

    # Create as user
    story = helpers.call_action(
        'data_story_create',
        context={'user': user['name']},
        title='Story',
    )

    # Try to modify as other_user
    with pytest.raises(toolkit.NotAuthorized):
        helpers.call_action(
            'data_story_update',
            context={'user': other_user['name']},
            id=story['id'],
            title='Hacked',
        )
```

### Testing Validation

```python
from ckan.plugins import toolkit

def test_validation_error(self):
    user = factories.User()

    # Try to submit incomplete story
    story = helpers.call_action(
        'data_story_create',
        context={'user': user['name']},
        title='Incomplete',
    )

    with pytest.raises(toolkit.ValidationError) as exc:
        helpers.call_action(
            'data_story_submit',
            context={'user': user['name']},
            id=story['id'],
        )

    # Check specific error message
    assert 'missing' in str(exc.value).lower()
```

## Continuous Integration

### GitHub Actions

Example workflow file (`.github/workflows/test.yml`):

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:12
        env:
          POSTGRES_USER: ckan_test
          POSTGRES_PASSWORD: password
          POSTGRES_DB: ckan_test

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r dev-requirements.txt

      - name: Run tests
        run: |
          pytest --ckan-ini=test.ini \
                 --cov=ckanext.pages.data_stories \
                 ckanext/pages/data_stories/tests/
```

## Troubleshooting

### Database Connection Errors

If you see connection errors:
1. Ensure PostgreSQL is running
2. Check database credentials in test.ini
3. Verify test database exists: `createdb -U ckan_test ckan_test`

### Import Errors

If modules cannot be imported:
1. Ensure extension is installed: `pip install -e .`
2. Check PYTHONPATH includes the extension
3. Verify `__init__.py` files exist

### Plugin Loading Errors

If plugins fail to load:
1. Check test.ini has correct plugins list
2. Ensure all plugin dependencies are installed
3. Verify plugin classes are properly registered

### Fixture Errors

If fixtures fail:
1. Check conftest.py is in tests directory
2. Ensure clean_db fixture is used
3. Verify database tables are initialized

## Test Statistics

- **Total Test Files**: 6
- **Total Lines**: ~2,550
- **Test Classes**: 25+
- **Test Methods**: 120+
- **Estimated Coverage**: 85-90%

## Next Steps

1. Run all tests to verify implementation
2. Add integration tests for complete workflows
3. Add performance tests for large datasets
4. Add UI/frontend tests (if applicable)
5. Set up CI/CD pipeline
6. Generate and review coverage reports

---

*Last Updated: 2025-11-10*
