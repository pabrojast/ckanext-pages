# Backlog Documentacion

Tags: #referencia #estado/pendiente
Actualizado: 2026-03-26

Relacionadas: [[Deployment]], [[Variables de Entorno]], [[Testing]], [[Guia de Mantenimiento]]

## Vacíos principales detectados

- Falta documentación del entorno CKAN base requerido para desarrollo local.
- No hay documentación de despliegue productivo ni infraestructura declarativa en el repo.
- No hay contrato claro de configuración productiva por entorno.
- No se observó documentación de almacenamiento de uploads.
- No se observó matriz formal de permisos por módulo y rol.

## Inconsistencias detectadas

- `data_stories/README.md` menciona `ckanext.data_stories.terria_base_url`, pero el código usa `ckanext.pages.terria_base_url`.
- `data_stories/README.md` menciona `ckanext.data_stories.require_review`, pero no se encontró uso en el código inspeccionado.
- `setup.py` declara Python 3.8 a 3.10, mientras CI y guías operativas visibles giran alrededor de 3.9 y 3.10.

## Deuda técnica/documental observable

- CRUD de event types parece no persistir cambios realmente.
- `utils.py` concentra demasiada lógica de negocio y web.
- `crida_admin_reseed()` aparece duplicada en `utils.py`.
- `featured_viewers` no muestra una suite de tests visible como `data_stories`.
- CI principal no parece correr los tests de `data_stories`.

## Diferido deliberadamente (storymap, sep-2026)

- Hidratación client-side de steps cuando la resolución server-side de un share falla (hoy: warning en logs + reintento natural al siguiente render; el viewer ya tiene `extractStories()` si se quisiera).
- Mapas simultáneos side-by-side por escena (el JS del viewer es singleton de iframe; cada Terria tarda ~10 s en arrancar). Hoy: tabs + secuencia en scroll.
- Botón de upload de imágenes en el editor de stories de Terria (TinyMCE es URL-only; el patch iría en el fork `pabrojast/terriajs`, `lib/ReactViews/Generic/Editor.jsx` — `images_upload_handler`/`file_picker_callback`). Mientras: subir la imagen a CKAN y pegar la URL.

## Documentación futura recomendada

- Runbook de despliegue por ambiente.
- Matriz de permisos por rol y por vertical.
- Guía de cambios de schema base vs módulos opcionales.
- Catálogo funcional de templates y snippets.
- Convención de assets frontend y su carga.

## Pendiente por confirmar

- Qué partes del backlog son conocidas por el equipo y cuáles son hallazgos nuevos.
- Si existen docs fuera del repo que cubran varios de estos puntos.
