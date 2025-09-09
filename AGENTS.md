# Repository Guidelines

## Project Structure & Module Organization
- Source: `ckanext/pages/`
  - `plugin.py` (entry point `pages`), `blueprint.py` (routes), `actions.py` (logic actions), `logic/` (schemas), `validators.py`, `assets/` and `public/` (JS/CSS/images), `theme/` (Jinja templates), `migration/` (alembic), `commands/` (CLI).
- Tests: `ckanext/pages/tests/` (pytest). Config: `test.ini`.
- Packaging: `setup.py`, i18n in `setup.cfg` and `ckanext/pages/i18n/`.

## Build, Test, and Development Commands
- Create dev env (editable install):
  - `pip install -r requirements.txt -r dev-requirements.txt`
  - `pip install -e .`
- Lint (CI mirrors this):
  - `flake8 . --count --max-line-length=127 --exclude ckan`
- Init DB for tests (CKAN >= 2.9):
  - `ckan -c test.ini db init`
  - `ckan -c test.ini db upgrade -p pages`
- Run tests with coverage:
  - `pytest --ckan-ini=test.ini --cov=ckanext.pages --cov-report=term-missing ckanext/pages/tests`

## Coding Style & Naming Conventions
- Python 3.9–3.10. Follow PEP 8 with `flake8` checks; max line length 127.
- Indentation: 4 spaces. Use descriptive names (`pages_update`, not `upd`).
- Templates: Jinja blocks follow CKAN conventions; keep template overrides minimal.
- JS/CSS in `assets/` follow CKAN webassets structure; prefer small, focused modules.

## Testing Guidelines
- Frameworks: `pytest`, `pytest-ckan`, `pytest-cov`.
- Name tests `test_*.py` inside `ckanext/pages/tests/`.
- Use CKAN factories/helpers; mark config with `@pytest.mark.ckan_config` when needed.
- Aim to cover new logic, validators, and routes. Add fixtures to `fixtures.py` if required.

## Commit & Pull Request Guidelines
- Commits: imperative, concise, scoped (e.g., `Fix z-index overlap in dropdown`).
- PRs must include: summary, rationale, before/after (screenshots for UI), test notes, and linked issues.
- Update docs (`README.md`) when changing behavior or configuration.

## Security & Configuration Tips
- Do not commit secrets. Use `test.ini` for local runs; production CKAN config is external.
- Database changes go through `migration/` and `db upgrade -p pages`.

## Agent-Specific Instructions
- Keep patches focused; preserve existing structure and naming.
- Conform to `flake8` and existing templates/styles.
- Place new tests under `ckanext/pages/tests/` and run the test commands above before proposing changes.

