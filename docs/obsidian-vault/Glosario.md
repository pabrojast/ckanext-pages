# Glosario

Tags: #referencia #onboarding
Actualizado: 2026-03-26

Relacionadas: [[Arquitectura]], [[Modulos]]

## CKAN

Plataforma open source para catálogos de datos. Esta extensión se instala sobre CKAN.

## Plugin CKAN

Componente Python que registra hooks, blueprints, acciones, permisos, helpers y comandos.

## Blueprint

Conjunto de rutas Flask. En este repo hay uno base y dos opcionales.

## Action

Función expuesta vía `tk.get_action(...)` en el estilo CKAN.

## Auth Function

Función que decide si una action está autorizada.

## `page_type`

Campo clave que diferencia los tipos de contenido que comparten `ckanext_pages`.

## `extras`

Columna texto JSON donde se guardan muchos campos especializados del contenido base.

## `revisions`

Columna JSONB donde se guardan snapshots del contenido.

## Water Family

Conjunto de verticales:

- water news
- water events
- water publications

## Rapid Response

Tipo de contenido orientado a incidentes/eventos con filtros y campos de severidad.

## Open Source Software

Catálogo editorial de software open source vinculado a organización.

## AI Water Tools

Catálogo editorial de herramientas de IA aplicadas al agua.

## CRIDA

Vertical de casos de estudio con hub web, APIs y seed desde archivos locales.

## Data Story

Narrativa estructurada con secciones, datasets y workflow editorial.

## Featured Viewer

Viewer temático con integración Terria y posibles datasets vinculados.

## Map Room

Colección de featured viewers agrupados temáticamente.

## Terria

Plataforma o integración de mapas/visualización geoespacial usada por `data_stories` y `featured_viewers`.

## TextBoxView

Resource view CKAN `wysiwyg` para mostrar texto libre en recursos.

## IHP Organization

Organización CKAN asociada al contenido editorial de algunas verticales.
