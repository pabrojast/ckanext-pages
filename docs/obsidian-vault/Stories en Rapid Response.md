# Stories en Rapid Response

Tags: #modulo/pages #frontend #datos
Actualizado: 2026-09-24

Relacionadas: [[Modulos]], [[Arquitectura]], [[Datos y Persistencia]], [[Frontend y Plantillas]], [[Flujos Importantes]], [[Testing]]

## Flujo editorial

Cada emergencia conserva su página, URL, permisos y ficha de Rapid Response. Su narrativa usa capítulos que pueden añadirse, renombrarse, moverse y eliminarse. Una página nueva propone Context, Impact Assessment, Response Activities, Recovery y Resilience. Los capítulos admiten texto, imágenes, vídeos/iframes, pestañas Terria y escenas importadas; los datasets relacionados se seleccionan mediante las acciones CKAN.

`rapid-response-story-edit.js` mantiene identidades estables de capítulos, bloques y fuentes de mapas. Mover contenido no recrea los editores. `story-editor-core.js`, compartido con Data Stories, conserva el HTML original hasta una edición real. El contenido antiguo que Quill no puede representar se conserva como `legacy_html`, con vista previa aislada y edición de código fuente explícita.

Las subidas siguen usando `/pages_upload` y `rapid-response-images.js`. Guardar espera las subidas; un fallo conserva el archivo para reintentar y bloquea el envío. Las escenas Terria guardan snapshots; refrescarlas conserva sus IDs y las escenas que desaparecieron de la fuente.

## Persistencia y compatibilidad

`rapid_response_story.py` valida el documento versión 1 almacenado en `extras.rapid_response_story`. Contiene `sections` (ID, origen, título, orden y bloques) y `datasets` (IDs CKAN). No requiere tablas ni migraciones nuevas, ni activar `ckanext.data_stories.enabled`.

Las páginas existentes se adaptan al leer, sin escrituras ni conversión masiva. Se aceptan los metadatos históricos nativos, JSON, JSON doblemente serializado y repr antiguo. El primer guardado persiste la narrativa y proyecta los campos históricos (`content`, fases, mapas y metadatos). Sin cambios en los bloques, conserva el HTML histórico exactamente. Un cliente antiguo que modifica explícitamente un campo actualiza el capítulo correspondiente. Una lista vacía significa eliminación, no reutilización del valor anterior.

La validación rechaza documentos malformados, identidades duplicadas y URLs nuevas inválidas sin reemplazar el contenido. Los datasets nuevos se validan y normalizan a IDs; al leer se comprueban los permisos de cada dataset. Referencias existentes inaccesibles se conservan en el documento, pero no se exponen sus títulos al lector.

Las revisiones nuevas incluyen narrativa, fases, metadatos, imágenes, ficha y timeline. Antes de convertir una página se guarda una instantánea de su contenido previo. Las revisiones antiguas contienen solo el overview: restaurarlas reemplaza ese capítulo y conserva los demás.

## Vista pública y resoluciones

Rapid Response y Data Stories comparten `data_stories/components/storymap_viewer.html` y el visor StoryMap. Rapid Response conserva banner, ficha, timeline y galería. La narrativa ofrece navegación por capítulos, imágenes y escenas de mapa. En móvil, `mobileStackedMedia` coloca el mapa después del texto del capítulo activo, evitando que lo tape; en escritorio se conserva la disposición lateral.

`rapid-response-story.css` limita los estilos del compositor y reduce los márgenes anidados en móvil. La revisión local cubrió 320, 390, 768, 1366 y 1920 px de ancho, en formulario y vista pública. Las capturas están en `output/playwright/` (no versionadas).

## Verificación

- `test_rapid_response_story.py`: adaptación sin escrituras, conservación de HTML, identidades, borrado, revisiones, compatibilidad y permisos de datasets.
- `test_rapid_response_story_integration.py`: acciones y DB CKAN reales, guardar/restaurar, formularios autenticados y vista pública con Data Stories desactivado.
- `rapid_response_story_browser.cjs`: Quill real, reapertura sin cambios, IDs con huecos, reordenar/editar/eliminar, Terria, datasets y errores/reintentos de subida; comprueba los cinco anchos.
- Las suites compartidas de Stories y de imágenes siguen siendo necesarias. Comandos en [[Testing]].

## Pendiente por confirmar

La revisión de dev se limitó a lectura. El despliegue de esta implementación y su comprobación con el tema completo de dev se verifican por separado; las pruebas integradas usan una instancia CKAN local aislada. No se modificaron registros de emergencias en dev.
