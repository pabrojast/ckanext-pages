# CLAUDE.md

## Propósito del repo

`ckanext-pages` es una extensión de CKAN para CMS y verticales de contenido. El detalle funcional y técnico para humanos vive en `docs/obsidian-vault/`.

## Fuente de verdad

- La documentación humana principal es `docs/obsidian-vault/`.
- Empieza por `docs/obsidian-vault/Index.md`.
- Usa `docs/obsidian-vault/README.md` para el rol de la vault.
- Usa `docs/obsidian-vault/Convenciones de la Vault.md` para convenciones editoriales.
- Usa `docs/obsidian-vault/Guia de Mantenimiento.md` para mantenimiento documental.
- Si `CLAUDE.md` contradice la vault, la vault manda para contexto humano y onboarding.

## Reglas persistentes

- No inventes comportamiento, configuración ni deployment.
- Si algo no está confirmado por el repo, escríbelo como `Pendiente por confirmar`.
- Si algo es deducido del código o de la estructura, escríbelo como `Inferencia`.
- Mantén el onboarding simple, útil y rápido de recorrer.

## Mantenimiento documental

- Cuando cambie el código, revisa si también debe cambiar `docs/obsidian-vault/`.
- Actualiza la vault si cambian arquitectura, rutas, comandos, configuración, variables de entorno, testing, persistencia o deployment.
- Evita duplicar documentación extensa en este archivo; referencia la nota adecuada de la vault.

## Comportamiento esperado

- Antes de cerrar un cambio relevante, comprueba si la vault sigue siendo correcta.
- Si aparecen vacíos o inconsistencias, documéntalos en la vault y en `docs/obsidian-vault/Backlog Documentacion.md` cuando corresponda.
