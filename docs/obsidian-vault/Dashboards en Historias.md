# Dashboards en Historias

Tags: #frontend #modulo/data-stories
Actualizado: 2026-10-12

Relacionadas: [[Frontend y Plantillas]], [[Flujos Importantes]], [[Stories en Rapid Response]], [[Rutas y Entrypoints]], [[Testing]], [[Troubleshooting]]

## Selector compartido

Data Stories, Rapid Response y el selector embebido de Terria usan `StoryVisualsEditor.dashboard` en `public/js/data-stories-visuals-edit.js`. La guía IHP-WINS mantiene tres pasos en una pantalla desplazable: buscar conjunto/archivo/dashboard, elegir filtros o gráfico destacado opcionales y añadir el dashboard al capítulo. En los editores CKAN, el tercer paso recuerda guardar la historia.

La vista previa está rotulada como dashboard original: todavía no refleja los filtros ni el gráfico destacado elegidos. Estas opciones se aplican al capítulo y no modifican la vista guardada. La ayuda desplegable explica `Manage views > New view > Dashboard > Save`, requiere permisos de edición del conjunto y ofrece un enlace local al recurso seleccionado. No crea dashboards ni modifica Dashboard Builder.

El picker usa una clase de contenedor propia y omite la barra vacía de navegación: al no tener cabecera del sitio, no reserva los 144 px que el tema añade a `.main`. Los campos del editor de dashboards también anulan el `label::after` de CKAN, que mostraba un `:` en una fila separada bajo cada control. El ajuste queda acotado al picker y a esos campos; los formularios generales conservan sus estilos.

## Idioma y protocolo

`/story-dashboards/picker?lang=en|es` acepta esos dos valores explícitos. Un parámetro no admitido usa el idioma normal de CKAN (sus variantes EN/ES) o inglés. El selector no escribe el idioma de sesión. El HTML inicial ya muestra título y mensaje de carga localizados; JS completa la guía después de cargar jQuery. Los editores CKAN usan el idioma del documento.

Se mantiene `ckan-story-dashboard-selected`, versión 1, con el bloque dashboard declarativo y su ID estable. La vista responde con `Cache-Control: private, no-store` y `X-Frame-Options: SAMEORIGIN`. La carga de metadatos exige origen, ventana actual, versión y vista coincidentes. Los permisos de búsqueda y acceso siguen siendo los de las acciones CKAN y del dashboard.

## Selección y filtros

Cambiar conjunto, recurso o vista borra los metadatos y filtros anteriores; las respuestas tardías de búsquedas/cargas no reemplazan la selección actual. Recargar la vista previa crea otro iframe, de modo que una respuesta del iframe anterior no sirve aunque el ID de vista coincida. Un mensaje `ready` duplicado no borra los filtros que se estén editando.

Insertar requiere los metadatos de la selección actual y filtros válidos. No seleccionar filtros es válido. Añadir una fila incompleta deshabilita inmediatamente la inserción. Los ejemplos corresponden al tipo declarado por el dashboard: números, fechas ISO, booleanos y texto exacto. Se validan 24 condiciones como máximo, 100 valores por lista, 2.000 caracteres por valor, fechas reales e intervalos de dos valores ordenados.

Buscar, no encontrar resultados o fallar la conexión conserva el dashboard previamente guardado al editar un capítulo, pero invalida los metadatos para una inserción nueva. La lectura normal conserva filtros de texto históricos que buscan una celda vacía (`eq: ''` o `in: ['', 'Chile']`), incluso después de cargar metadatos. La inserción estricta pide completar esos valores. Los cambios explícitos de conjunto/recurso/vista sí descartan la selección anterior.

## Verificación local

`tests/test_story_dashboard_picker.py` comprueba la lista de idiomas admitidos, el fallback, headers y que no cambie la sesión. Se ejecutó en una imagen CKAN local con el checkout montado en solo lectura: dos pruebas con múltiples casos, correctas.

```bash
node ckanext/pages/data_stories/tests/dashboard_picker_browser.cjs /ruta/playwright_cli.sh /ruta/ckan/public/base/vendor/jquery.js /ruta/salida-local
```

El harness usa el template Jinja, JS/CSS y jQuery reales, con acciones CKAN y dashboards simulados. Comprueba EN/ES, filtros por tipo y límites, mensaje de inserción, carreras de conjunto/recurso/búsqueda/iframe, duplicados, filtros históricos vacíos y diseños de 1280×800 y 390×844 sin desbordamiento. Las capturas se denominan `picker-es-1280.png`, `picker-es-390.png` y sus variantes `-insert`; son evidencia local, no del despliegue DEV. También se ejecutan las regresiones `visuals_browser.cjs` y `tests/rapid_response_story_browser.cjs` para los dos editores compartidos. La autenticación, permisos y persistencia real requieren comprobación separada en DEV.

Para revisar estilos heredados, abrir el selector con los assets reales del tema: el harness aislado no incluye el padding de cabecera ni los dos puntos de CKAN. El ajuste visual del 12 de octubre se comprobó con esos assets DEV y un override local de CSS/HTML en 1280×800 y 390×844: sin desbordamiento, sin `:` extra y con el contenedor empezando en 0 px en vez de 164 px. Se verificó buscar Madagascar con Enter y elegir su archivo hasta listar el dashboard guardado. Esta comprobación local no acredita el despliegue del parche.

## Dashboards sencillos nativos (2026-10-29)

El selector compartido ofrece también la biblioteca de `/api/simple-dashboards`, si el servidor habilita la función. Seleccionar fija `kind: simple` y `simple: {id, revision}`. El compositor conserva las referencias CKAN `view_id` anteriores. Para el formato nativo, `dashboard_block` construye un embed local Terria con `dashboardOnly=1` y un `start` que contiene únicamente la referencia. No acepta URLs de embed del autor ni serializa resultados.

La revisión fija el diseño y sus filtros; los datos se revalidan en el servidor de dashboards. La biblioteca respeta la sesión y la publicación de cada revisión. El puente conserva los mensajes `dashboard:hello`, `ready` y `stateApplied`; el visor nativo devuelve estado, sin enviar los datos al documento padre.
