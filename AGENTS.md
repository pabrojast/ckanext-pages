# Repository Guidelines

## Project Structure & Module Organization
- Source lives in `ckanext/pages/`:
  - `plugin.py` (entry point `pages`), `blueprint.py` (routes), `actions.py` (logic), `logic/` (schemas), `validators.py`.
  - Frontend: `assets/` and `public/` (JS/CSS/images), templates in `theme/` (Jinja).
  - Migrations in `migration/` (Alembic), CLI in `commands/`.
- Tests in `ckanext/pages/tests/`; test config `test.ini`.
- Packaging via `setup.py`; i18n in `setup.cfg` and `ckanext/pages/i18n/`.

## Build, Test, and Development Commands
- Create dev env (editable install):
  - `pip install -r requirements.txt -r dev-requirements.txt`
  - `pip install -e .`
- Lint code (mirrors CI): `flake8 . --count --max-line-length=127 --exclude ckan`
- Init test DB (CKAN ≥ 2.9):
  - `ckan -c test.ini db init`
  - `ckan -c test.ini db upgrade -p pages`
- Run tests with coverage:
  - `pytest --ckan-ini=test.ini --cov=ckanext.pages --cov-report=term-missing ckanext/pages/tests`

## Coding Style & Naming Conventions
- Python 3.9–3.10; follow PEP 8. Indentation: 4 spaces; line length: 127.
- Use descriptive names (e.g., `pages_update`, not `upd`).
- Keep template overrides minimal; follow CKAN Jinja block conventions.
- JS/CSS in `assets/` follow CKAN webassets patterns; prefer small, focused modules.

## Testing Guidelines
- Frameworks: `pytest`, `pytest-ckan`, `pytest-cov`.
- Name tests `test_*.py` in `ckanext/pages/tests/`.
- Aim to cover new logic, validators, and routes; add fixtures in `fixtures.py` if needed.
- Use CKAN factories/helpers; mark config with `@pytest.mark.ckan_config` when required.

## Commit & Pull Request Guidelines
- Commits: imperative, concise, and scoped (e.g., "Fix z-index overlap in dropdown").
- PRs include summary, rationale, before/after (screenshots for UI), test notes, and linked issues.
- Update `README.md` when behavior or configuration changes.

## Security & Configuration Tips
- Do not commit secrets. Use `test.ini` for local runs; production config is external.
- Database changes go through `migration/` and `ckan -c test.ini db upgrade -p pages`.

## Agent-Specific Instructions
- Keep patches focused; preserve existing structure and naming.
- Conform to `flake8`; avoid unrelated changes.
- Place new tests under `ckanext/pages/tests/` and run the commands above before proposing changes.
