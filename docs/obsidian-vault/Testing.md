# Testing

Tags: #testing #operacion
Actualizado: 2026-09-11

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

## Secuencias y geocodificación

Pruebas unitarias: `test_storymap_helpers.py`, `test_sequence.py`, `test_geocoding.py`, `test_form_metadata.py` bajo `ckanext/pages/data_stories/tests`. Pueden ejecutarse con pytest `--noconftest` en un entorno CKAN sin base de datos (evita cargar fixtures generales de integración).

`node --test ckanext/pages/data_stories/tests/sequence.test.cjs` verifica reconciliación, orden e identidades. `node ckanext/pages/data_stories/tests/storymap_browser.cjs /ruta/playwright_cli.sh` comprueba en navegador recepción lenta, fallo, reintento de la misma escena y fin de transición. La compilación de Terria y sus pruebas de cola se ejecutan en su propio repositorio.

## Imágenes y rendimiento de Rapid Response

Pruebas focalizadas en un entorno con las dependencias de CKAN, sin servicios de integración:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest --noconftest -q ckanext/pages/tests/test_rapid_response_media.py ckanext/pages/tests/test_rapid_response_image_migration.py ckanext/pages/tests/test_rapid_response_edit.py
node ckanext/pages/tests/rapid_response_images_browser.cjs /ruta/al/playwright_cli.sh
node --check ckanext/pages/public/js/rapid-response-images.js
node --check ckanext/pages/public/js/rapid-response-edit.js
```

La suite cubre reducción de fotografías, transparencia, animación, conservación del HTML/JSON, simulación sin escrituras, deduplicación, repetición segura, fallos de almacenamiento, ediciones simultáneas y restauración con comprobación de hashes. Las pruebas de migración usan SQLite y un uploader simulado.

Verificación manual en dev: insertar/pegar imágenes, guardar, recargar, comprobar los metadatos de bloques y restaurar una revisión. Comprobar también guardar sin imágenes nuevas: debe producir un POST y redirigir al evento. El reenvío del formulario espera a que termine el evento de envío original; si solo espera microtareas, el navegador puede suprimir el segundo envío cuando no hay subidas pendientes. Comprobar errores de subida y reintento, escritorio/móvil y medios diferidos con red lenta. Medir por separado HTML/TTFB/DOMContentLoaded y la carga de Terria. Ver [[Deployment]].

El test de navegador usa Quill real y un uploader simulado. Cubre pegado, drag/drop, transparencia, guardado durante una subida, deduplicación, metadatos de bloques, error/reintento inmediato y modo fuente. Sus capturas y logs se guardan en `output/playwright/`.

En Rapid Response, comprobar que los iframes alejados aún no tienen navegación iniciada y que esta comienza al acercarse al mapa. No basta con inspeccionar `loading="lazy"`: mover los iframes a un wrapper después del render puede iniciar sus navegaciones. El diseño responsive aplica CSS directamente al iframe y conserva los wrappers ya guardados.

## Plantillas visuales (2026-09-24)

- `test_visuals.py`: dashboard sin mapa, pantalla narrativa completa, referencias, URL interna y rechazo de filtros inválidos.
- `node ckanext/pages/data_stories/tests/visuals_browser.cjs /ruta/playwright_cli.sh /ruta/ckan/public/base/vendor/jquery.js`: Quill real, guardar/reconstruir metadatos, pasos manuales, filtros/restablecimiento, iframe persistente, sección narrativa y viewport móvil.
- Mantener `test_storymap_helpers.py`, `test_sequence.py`, `sequence.test.cjs` y `storymap_browser.cjs` como regresiones de escenas importadas y confirmaciones lentas/fallidas.
- Validación integrada: crear/editar/guardar con sesión real de CKAN en dev, recargar como lector, probar el dashboard accesible y la referencia al mapa. El harness aislado no sustituye permisos ni persistencia real.

`test_featured_viewer_schema.py` requiere `PAGES_SCHEMA_TEST_URL` hacia PostgreSQL aislado. Mantiene un bloqueo ACCESS SHARE como un respaldo y comprueba que el arranque no pide ALTER TABLE para columnas existentes; también verifica creación y persistencia de columnas faltantes. La inicialización consulta el esquema antes de ejecutar una migración, porque `ADD COLUMN IF NOT EXISTS` también solicita un bloqueo exclusivo en PostgreSQL.
