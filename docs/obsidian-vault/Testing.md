# Testing

Tags: #testing #operacion
Actualizado: 2026-10-01

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

El ancho por sección tiene cobertura en `test_section_width.py`: valores válidos/incorrectos, conservación de metadatos del formulario y de continuaciones, rechazo por API antes de acceder a la base de datos y render de las plantillas reales. El navegador usa esas plantillas con assets locales y Quill real para medir Normal/100%/80%/900px, probar reordenación/reapertura, panel lateral y validación.

En un entorno con CKAN y pytest instalados:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest --noconftest -q ckanext/pages/data_stories/tests/test_section_width.py
python ckanext/pages/data_stories/tests/test_section_width.py > /tmp/data-stories-width-fixtures.json
node ckanext/pages/data_stories/tests/section_width_browser.cjs /ruta/playwright_cli.sh /ruta/ckan/public/base/vendor/jquery.js /tmp/data-stories-width-fixtures.json
```

La prueba de navegador recorre Classic, Story Map y Slides a 1920, 1440, 768 y 390px. Genera HTML de prueba junto al JSON temporal. Estos checks locales no equivalen a guardar una story en una instancia desplegada; la prueba de formulario verifica serialización y reconstrucción de los metadatos.

Verificación local del cambio de ancho (2026-10-01): 103 pruebas pasaron al ejecutar conjuntamente `test_section_width.py`, `test_visuals.py`, `test_storymap_helpers.py`, `test_form_metadata.py`, `test_sequence.py` y `pages/tests/test_rapid_response_story.py` en una imagen CKAN temporal con el checkout montado en solo lectura. El navegador confirmó 48 combinaciones de modo/ancho/viewport, conservación tras reordenar y reconstruir el editor, validación y navegación manual. También pasaron `visuals_browser.cjs` y `scroll_browser.cjs` con los assets finales. No se desplegó este cambio.

Suites principales:

- `test_actions.py`
- `test_auth.py`
- `test_models.py`
- `test_routes.py`
- `test_storymap_helpers.py`
- `test_section_width.py`
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

La suite principal de la workflow ejecuta:

```bash
pytest --ckan-ini=test.ini --cov=ckanext.pages --cov-report=term-missing --cov-append --disable-warnings ckanext/pages/tests
```

Hallazgo importante:

- `data_stories/tests` existen
- la workflow también ejecuta las suites puras de helpers, secuencias y metadatos; las demás suites de integración de Data Stories requieren ejecución separada

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

`test_rapid_response_edit.py` también renderiza el selector real de visibilidad con nueve representaciones de `private` y comprueba que exista una sola opción seleccionada. En el flujo autenticado, abrir un borrador debe mostrar Draft y conservarlo después de guardar sin cambios.

Verificación manual en dev: insertar/pegar imágenes, guardar, recargar, comprobar los metadatos de bloques y restaurar una revisión. Comprobar también guardar sin imágenes nuevas: debe producir un POST y redirigir al evento. El reenvío del formulario espera a que termine el evento de envío original; si solo espera microtareas, el navegador puede suprimir el segundo envío cuando no hay subidas pendientes. Comprobar errores de subida y reintento, escritorio/móvil y medios diferidos con red lenta. Medir por separado HTML/TTFB/DOMContentLoaded y la carga de Terria. Ver [[Deployment]].

El test de navegador usa Quill real y un uploader simulado. Cubre pegado, drag/drop, transparencia, guardado durante una subida, deduplicación, metadatos de bloques, error/reintento inmediato y modo fuente. Sus capturas y logs se guardan en `output/playwright/`.

En Rapid Response, comprobar que los iframes alejados aún no tienen navegación iniciada y que esta comienza al acercarse al mapa. No basta con inspeccionar `loading="lazy"`: mover los iframes a un wrapper después del render puede iniciar sus navegaciones. El diseño responsive aplica CSS directamente al iframe y conserva los wrappers ya guardados.

## Plantillas visuales (2026-09-24)

- `test_visuals.py`: dashboard sin mapa, pantalla narrativa completa, referencias, URL interna y rechazo de filtros inválidos.
- `node ckanext/pages/data_stories/tests/visuals_browser.cjs /ruta/playwright_cli.sh /ruta/ckan/public/base/vendor/jquery.js`: Quill real, guardar/reconstruir metadatos, pasos manuales, filtros/restablecimiento, iframe persistente, sección narrativa y viewport móvil.
- Mantener `test_storymap_helpers.py`, `test_sequence.py`, `sequence.test.cjs` y `storymap_browser.cjs` como regresiones de escenas importadas y confirmaciones lentas/fallidas.
- Validación integrada: crear/editar/guardar con sesión real de CKAN en dev, recargar como lector, probar el dashboard accesible y la referencia al mapa. El harness aislado no sustituye permisos ni persistencia real.

`test_featured_viewer_schema.py` requiere `PAGES_SCHEMA_TEST_URL` hacia PostgreSQL aislado. Mantiene un bloqueo ACCESS SHARE como un respaldo y comprueba que el arranque no pide ALTER TABLE para columnas existentes; también verifica creación y persistencia de columnas faltantes. La inicialización consulta el esquema antes de ejecutar una migración, porque `ADD COLUMN IF NOT EXISTS` también solicita un bloqueo exclusivo en PostgreSQL.

`node ckanext/pages/data_stories/tests/scroll_browser.cjs /ruta/playwright_cli.sh` usa desplazamiento real a 1366×768, 1366×650, 390×844 y 844×390. Verifica avance/retroceso, varias fuentes, reanudación tras pestaña manual, imagen seguida de texto y capítulos sin mapa. `visuals_browser.cjs` comprueba además paneles completos Map/Dashboard a 1366×768 y conservación del iframe. El test de runtime de `test_storymap_helpers.py` conserva el servicio original del share al usar el visor de dev.

## Stories en Rapid Response

Con PostgreSQL, Solr y Redis de prueba, ejecutar los tests reales de formulario/acciones:

```bash
pytest --ckan-ini=test.ini ckanext/pages/tests/test_rapid_response_story_integration.py
```

El fixture desactiva Data Stories para comprobar que Rapid Response funciona por sí solo. No ejecutar `clean_db` contra dev ni producción.

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest --noconftest -q ckanext/pages/tests/test_rapid_response_story.py
node ckanext/pages/tests/rapid_response_story_browser.cjs /ruta/al/playwright_cli.sh
```

El test de navegador comprueba 320, 390, 768, 1366 y 1920 px. La revisión de diseño debe añadir las páginas completas de CKAN, el banner, capítulos con y sin mapa y controles de edición. Ver [[Stories en Rapid Response]]. CI incluye ahora las suites puras compartidas de StoryMap y los navegadores de imágenes y compositor.

### Revisión con el tema de dev (2026-09-24)

Se revisaron `/rapid-response` y los detalles de Melissa e Idai en `https://data.dev-wins.com` a 320, 390, 768, 1024, 1366 y 1920 px. Las 18 combinaciones no presentaron desbordamiento horizontal ni excepciones JavaScript; el banner del listado recortaba texto a 320 y 390 px. El formulario generado por CKAN se obtuvo con conexiones SQL de solo lectura y se abrió como snapshot con los assets de dev y solicitudes de escritura bloqueadas; también recortaba su banner en móvil.

La vista previa con el CSS local corrigió ambos banners en los seis anchos y comprobó los márgenes móviles del editor. Las capturas y resultados están en `output/playwright/rapid-response-dev-review/` (no versionado). Esta prueba valida diseño, no guardado ni persistencia en dev. No se modificaron eventos ni archivos del servidor.

En esa revisión, el pod de dev aún tenía `ckanext-pages` en `0b69977dc8b9549d103cd97a116a9799b05faec7`; faltaban `rapid_response_story.py` y `rapid-response-story-edit.js`, cuya URL pública devolvía 404. La integración de Stories estaba en Git (`51e4c4160316b765d0f5b338d8e10d6bcf4e07b8`), pero no desplegada allí. Ver [[Deployment]] para distinguir los contextos Kubernetes.

## Regresión de encabezados de Rapid Response

Comprobar listado, los cuatro eventos públicos y los banners de alta y edición a 320, 390, 768, 800, 820, 991, 992, 1024, 1199, 1366, 1440 y 1920 px. Además de comparar el ancho de documento y viewport, verificar que los rectángulos del texto estén contenidos en el banner. Repetir con un título largo, palabras sin espacios y la ruta en español. Las pruebas visuales del banner del editor renderizan su fragmento Jinja real sobre el tema servido; no prueban guardado ni persistencia.

Validar los assets de la imagen candidata y repetir sobre las URLs públicas después del rollout. Evidencia local privada: `output/rapid-response/header-release-20261001/`. Ver [[Frontend y Plantillas]] y el registro de release del repositorio Docker.

### Consolidación en RapidResponseAndRecovery (2026-10-01)

La combinación de `f725475` (Stories) y `8acd275` (encabezados) pasó 148 pruebas Python sin servicios de integración y cinco pruebas Node de secuencias. Se repitieron las 48 combinaciones de ancho de sección, el navegador del compositor de Rapid Response (guardado sin cambios, reordenación, HTML heredado, importación de escenas, datasets y reintentos de subida) y 30 comprobaciones del banner de alta/edición con el CSS del compositor, sin errores JavaScript.

Los assets de encabezado de listado, detalle y editor son idénticos a los del fix productivo; las resoluciones de las acciones y el editor de Data Stories conservan el código de la rama Stories. Las pruebas del compositor simulan uploads y acciones CKAN, y el banner se renderiza desde su fragmento Jinja sobre el tema real: no equivalen a guardar eventos en producción. Evidencia local: `output/playwright/merge-rapid-20261001/`. Esta verificación corresponde al merge en Git, sin nuevo despliegue; ver [[Deployment]].


## Composiciones, referencias y reproduccion

`test_compositions.py` valida la importacion de composiciones nativas, medios, presentacion acotada y persistencia en Rapid Response. `node --test ckanext/pages/data_stories/tests/sequence.test.cjs ckanext/pages/data_stories/tests/playback.test.cjs` cubre IDs importados y el temporizador coordinado con confirmaciones visuales.

Los harnesses `visuals_browser.cjs`, `section_width_browser.cjs` y `tests/rapid_response_story_browser.cjs` usan Playwright CLI y jQuery real de CKAN. Pasar el wrapper como primer argumento y el archivo local jquery.js como segundo; el de anchos recibe ademas el JSON generado por `test_section_width.py`. Comprueban filtros, iframe reutilizado, 48 combinaciones de anchos/modos y preservacion/reordenamiento del editor RR. Las rutas reales y autenticacion requieren una segunda comprobacion integrada en DEV.

La demo de composiciones verifica nombres de capitulos, controles tactiles, lectura de medios en movil, video sin autoplay y pausa al cambiar de capitulo. `test_compositions.py` cubre controles multimedia, escape del titulo e iframes etiquetados. Validar ademas los enlaces del texto contra escenas y filtros reales en DEV.
