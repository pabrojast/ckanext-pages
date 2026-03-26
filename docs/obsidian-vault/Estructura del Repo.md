# Estructura del Repo

Tags: #arquitectura #onboarding
Actualizado: 2026-03-26

Relacionadas: [[Arquitectura]], [[Modulos]], [[Frontend y Plantillas]], [[Testing]]

## Raíz del repositorio

- `setup.py`
  Empaquetado, entry points y metadatos del plugin.
- `requirements.txt`
  Dependencia runtime explícita: `Pillow`.
- `dev-requirements.txt`
  Dependencias de testing: `pytest-ckan`, `pytest-cov`.
- `test.ini`
  Configuración de pruebas para CKAN.
- `.github/workflows/test.yml`
  CI con lint y tests.
- `fix_broken_datasets.py`
  Script standalone de reparación de datasets.
- `fix_broken_datasets_simple.py`
  Variante simplificada del reparador.

## Código fuente

### `ckanext/pages/`

Subdirectorios principales:

- `plugin.py`
- `blueprint.py`
- `actions.py`
- `auth.py`
- `utils.py`
- `db.py`
- `db_utils.py`
- `db_init.py`
- `logic/`
- `commands/`
- `migration/`
- `theme/`
- `public/`
- `assets/`
- `tests/`

## Submódulos relevantes

- `ckanext/pages/data_stories/`
  Módulo opcional con blueprint, auth, actions, db, helpers, tests.
- `ckanext/pages/featured_viewers/`
  Módulo opcional con blueprint, auth, actions, db, helpers.
- `ckanext/pages/textbox/`
  Resource view tipo WYSIWYG para recursos CKAN.

## Capa de presentación

- `ckanext/pages/theme/templates_main/ckanext_pages/`
  Templates del módulo base y verticales.
- `ckanext/pages/theme/templates_main/data_stories/`
  Templates del módulo `data_stories`.
- `ckanext/pages/theme/templates_main/featured_viewers/`
  Templates del módulo `featured_viewers`.
- `ckanext/pages/public/`
  JS y CSS de contenido especializado.
- `ckanext/pages/assets/`
  Recursos públicos y vendor assets, incluyendo CKEditor.

## Persistencia y migraciones

- `ckanext/pages/migration/pages/versions/`
  Migraciones Alembic del módulo base.
- `ckanext/pages/data_stories/db/`
  Modelos y utilidades de tablas propias.
- `ckanext/pages/featured_viewers/db/`
  Modelos y utilidades de tablas propias.

## Testing

- `ckanext/pages/tests/`
  Suite base del módulo `pages`.
- `ckanext/pages/data_stories/tests/`
  Suite del módulo `data_stories`.

## Dónde tocar según el cambio

- Nueva ruta del módulo base: `blueprint.py` + `utils.py`
- Nueva acción CKAN: `actions.py` + `auth.py`
- Nuevo campo del contenido base: `logic/schema.py` + templates/form
- Cambio de render: `theme/templates_main/...`
- Cambio de flujo editorial: `utils.py`, `actions.py`, `auth.py`
- Cambio DB base: `db.py` + `migration/`
- Cambio `data_stories`: tocar dentro de `ckanext/pages/data_stories/`
- Cambio `featured_viewers`: tocar dentro de `ckanext/pages/featured_viewers/`

## No encontrado en el repo

- `Dockerfile`
- `docker-compose.yml`
- charts Helm
- Terraform
- manifests Kubernetes

Eso limita la documentación de despliegue. Ver [[Deployment]].
