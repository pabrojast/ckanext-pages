# Testing

Tags: #testing #operacion
Actualizado: 2026-03-26

Relacionadas: [[Setup Local]], [[Comandos Utiles]], [[Troubleshooting]]

## Stack de pruebas

- `pytest`
- `pytest-ckan`
- `pytest-cov`

## Configuración

- `test.ini`
- `conftest.py`
- `ckanext/pages/tests/fixtures.py`

Fixtures visibles:

- `clean_db`
- `clean_pages`

## Suites detectadas

### Módulo base

Archivos `test_*.py` detectados: 4

- `test_logic.py`
- `test_action.py`
- `test_crida.py`
- `test_water_family_api.py`

Cobertura observable:

- rendering HTML/Markdown
- formularios y revisiones
- workflow de aprobación
- API pública Water Family
- CRIDA actions y GeoJSON

### Data Stories

Archivos `test_*.py` detectados: 7

- `test_actions.py`
- `test_auth.py`
- `test_models.py`
- `test_routes.py`
- `test_storymap_helpers.py`
- `test_validation.py`
- `test_workflow.py`

Cobertura observable:

- modelos
- permisos
- rutas
- workflow editorial
- validación
- linking de datasets
- normalización de escenas `#share` y `#start`
- Story Slides únicas, imágenes nativas y capítulos sin mapa

El `test.ini` activa `ckanext.data_stories.enabled = True`; sin esa opción las rutas y acciones del módulo no quedan registradas en el entorno de prueba.

Comando focalizado para los cambios de editor/storymap:

```bash
pytest --ckan-ini=test.ini ckanext/pages/data_stories/tests/test_storymap_helpers.py ckanext/pages/data_stories/tests/test_routes.py
```

### Featured Viewers

No se encontró un directorio de tests dedicado en `ckanext/pages/featured_viewers/`.

## Comando principal

```bash
pytest --ckan-ini=test.ini --cov=ckanext.pages --cov-report=term-missing ckanext/pages/tests
```

## CI actual

La workflow detectada corre solo:

```bash
pytest --ckan-ini=test.ini --cov=ckanext.pages --cov-report=term-missing --cov-append --disable-warnings ckanext/pages/tests
```

Hallazgo importante:

- `data_stories/tests` existen
- pero no se observó su ejecución en la workflow principal

## Qué revisar antes de mergear cambios

- tests del módulo tocado
- lint `flake8`
- migraciones si cambió DB base
- forms y rendering si cambiaste templates o schema

## Pendiente por confirmar

- si `data_stories/tests` se ejecutan en otro pipeline no visible aquí
- si existen tests manuales o end-to-end fuera del repo

## Inferencia

La cobertura más madura parece estar en `pages` y `data_stories`. `featured_viewers` parece menos cubierto formalmente.
