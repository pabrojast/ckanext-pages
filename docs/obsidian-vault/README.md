# Vault Obsidian

Tags: #hub #obsidian #documentacion
Actualizado: 2026-03-26

Esta carpeta convierte el repositorio en una base de conocimiento navegable desde Obsidian para onboarding técnico, mantenimiento y entendimiento funcional.

## Rol de esta carpeta

Esta vault es la documentación para humanos y la fuente de verdad operativa del repositorio.

- `CLAUDE.md` debe referenciar esta vault en lugar de duplicarla.
- `AGENTS.md` debe usarla como referencia para cambios y verificación documental.

## Cómo usarla

1. Abrir `docs/obsidian-vault/` como vault o subcarpeta en Obsidian.
2. Empezar por [[Index]].
3. Usar backlinks, graph view y búsqueda por nombre de nota.
4. Mantener los enlaces internos con formato `[[Nombre de Nota]]`.

## Punto de entrada recomendado

- [[Index]]
- [[Setup Local]]
- [[Arquitectura]]
- [[Modulos]]
- [[Flujos Importantes]]

## Convenciones

- La convención editorial y de tags está en [[Convenciones de la Vault]].
- La guía para mantener actualizada la documentación está en [[Guia de Mantenimiento]].
- Los vacíos detectados y deuda documental están en [[Backlog Documentacion]].

## Alcance actual

La vault documenta:

- El plugin principal `pages` y el resource view `textboxview`.
- El módulo base de páginas CMS y sus variantes especializadas.
- Los módulos opcionales [[Modulos]] `data_stories` y `featured_viewers`.
- Setup local, testing, despliegue conocido y troubleshooting básico.

## Límite explícito

No se encontró infraestructura declarativa de despliegue dentro del repo como Docker, Helm o Terraform. Ese vacío está documentado en [[Deployment]] y [[Backlog Documentacion]].
