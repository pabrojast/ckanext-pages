# Index

Tags: #hub #onboarding
Actualizado: 2026-03-26

## Qué es este proyecto

`ckanext-pages` es una extensión de CKAN que parte como CMS de páginas simples y luego crece hacia varios dominios de contenido y publicación:

- páginas y blog
- rapid response
- water family
- open source software
- AI water tools
- CRIDA case studies
- módulos opcionales de `data_stories` y `featured_viewers`

La mejor forma de entenderlo es como un plugin CKAN con varios subproductos sobre una base común de rutas Flask, acciones CKAN, validación NAVL, tablas SQLAlchemy y plantillas Jinja.

## Rol de esta documentación

`docs/obsidian-vault/` es la documentación principal para humanos y el punto de referencia que deben revisar los asistentes de código cuando cambie el sistema.

## Lectura rápida sugerida

1. [[Arquitectura]]
2. [[Estructura del Repo]]
3. [[Setup Local]]
4. [[Modulos]]
5. [[Flujos Importantes]]
6. [[Testing]]
7. [[Deployment]]

## Mapa de navegación

### Onboarding

- [[Setup Local]]
- [[Comandos Utiles]]
- [[Troubleshooting]]

### Sistema

- [[Arquitectura]]
- [[Rutas y Entrypoints]]
- [[Modulos]]
- [[Datos y Persistencia]]
- [[Frontend y Plantillas]]

### Operación

- [[Variables de Entorno]]
- [[Deployment]]
- [[Testing]]
- [[Guia de Mantenimiento]]

### Referencia

- [[Glosario]]
- [[Convenciones de la Vault]]
- [[Backlog Documentacion]]

## Resumen ejecutivo

- Entry point principal: plugin CKAN `pages` en `ckanext/pages/plugin.py`.
- Entry point secundario: resource view `textboxview`.
- Persistencia base: tabla `ckanext_pages` más `extras` en JSON serializado y `revisions` en JSONB.
- Módulos opcionales: `data_stories` y `featured_viewers`, activados por config.
- CI detectada: una workflow de GitHub Actions para lint y tests.
- Infra de despliegue productiva: no encontrada en este repo.

## Pendiente por confirmar

- Procedimiento exacto de despliegue productivo fuera de CI.
- Configuración productiva de CKAN, web server, procesos y almacenamiento.
- Uso real en producción de todos los módulos opcionales.

## Inferencia

Por estructura y configuración, este repo está pensado para instalarse sobre una instancia CKAN ya existente, no para bootstrapping completo desde cero. Ver [[Setup Local]] y [[Deployment]].
