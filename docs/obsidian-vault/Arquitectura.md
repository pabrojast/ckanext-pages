# Arquitectura

Tags: #arquitectura #backend
Actualizado: 2026-03-26

Relacionadas: [[Rutas y Entrypoints]], [[Modulos]], [[Datos y Persistencia]], [[Frontend y Plantillas]]

## Vista general

El proyecto implementa un plugin CKAN multifunción con esta forma base:

```text
CKAN
  -> plugin `pages`
    -> blueprints Flask
    -> actions CKAN
    -> auth functions CKAN
    -> helpers Jinja
    -> modelos SQLAlchemy
    -> templates y assets
```

## Componentes principales

- `ckanext/pages/plugin.py`
  Registra plugin interfaces CKAN, blueprints, helpers, acciones, auth y comandos.
- `ckanext/pages/blueprint.py`
  Expone las rutas del módulo base y de varios tipos de contenido especializados.
- `ckanext/pages/utils.py`
  Orquesta formularios, renderizado, dashboards admin, uploads y flows web.
- `ckanext/pages/actions.py`
  Implementa la capa de acciones CKAN y APIs públicas del módulo base.
- `ckanext/pages/auth.py`
  Implementa permisos base y reglas de ownership/organización.
- `ckanext/pages/db.py`
  Define el modelo `Page` y la consulta principal `Page.pages(...)`.
- `ckanext/pages/logic/schema.py`
  Define el schema NAVL del contenido y validaciones.

## Patrón de ejecución típico

### Flujo web

`request HTTP` -> `Blueprint Flask` -> `utils.py` -> `tk.get_action(...)` -> `actions.py` -> `db.py` -> `template Jinja`

### Flujo API/action

`helper/route/CLI` -> `tk.get_action(...)` -> `actions.py` -> `auth.py` -> `db.py`

## Persistencia

### Núcleo

- Tabla principal: `ckanext_pages`
- Datos estructurados variables: columna `extras` como texto JSON
- Historial: columna `revisions` como JSONB
- Workflow editorial: columnas `submission_status`, `ihp_organization`, `submitted_at`, `reviewed_at`, `reviewed_by`

### Módulos opcionales

- `data_stories` crea sus propias tablas con `init_tables(...)`
- `featured_viewers` crea sus propias tablas con `init_tables(...)`

Detalles en [[Datos y Persistencia]].

## Módulos funcionales

La base `pages` soporta varios `page_type` sobre la misma tabla:

- `page`
- `blog`
- `rapid-response`
- `water-news`
- `water-events`
- `water-publications`
- `open-source-software`
- `ai-water-tools`
- `crida-case-study`

Además, existen dos dominios separados con tablas propias:

- [[Modulos]] `data_stories`
- [[Modulos]] `featured_viewers`

## Activación condicional por config

En `plugin.py` se detectan flags para registrar blueprints y tablas opcionales:

- `ckanext.data_stories.enabled`
- `ckanext.featured_viewers.enabled`

## Inicialización

En `configure(...)`, el plugin intenta:

- asegurar la existencia de `ckanext_pages`
- crear tablas opcionales de `data_stories`
- crear tablas opcionales de `featured_viewers`

Esto implica que parte del esquema se inicializa en arranque, no solo por migraciones. Ver [[Deployment]].

## Decisiones arquitectónicas visibles

- Se reutiliza una sola tabla para muchos tipos de contenido del módulo base.
- La especialización fuerte se hace con `page_type` + campos en `extras`.
- Los módulos más ricos (`data_stories`, `featured_viewers`) usan modelos y tablas independientes.
- Hay mezcla de capas: `utils.py` concentra bastante lógica de flujo y administración además del render web.

## Riesgos arquitectónicos observables

- `utils.py` es un archivo muy grande y concentra muchas responsabilidades.
- Gran parte del dominio base vive en `extras`, lo que reduce tipado y trazabilidad.
- El CRUD de event types y disaster types no persiste claramente fuera del runtime actual. Ver [[Datos y Persistencia]] y [[Troubleshooting]].
- Existe al menos una definición duplicada de `crida_admin_reseed()` en `utils.py`, señal de deuda técnica.

## Pendiente por confirmar

- Estrategia oficial para separar dominio CMS base vs verticales especializados.
- Política de compatibilidad futura entre CKAN 2.9, 2.10 y 2.11.

## Inferencia

La evolución del repo parece incremental: primero CMS simple y luego verticales de producto agregados sobre la misma extensión. Eso explica la coexistencia de una tabla genérica con módulos más especializados.
