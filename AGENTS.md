# AGENTS.md

## Alcance

Este repo contiene `ckanext-pages`, una extensión CKAN con un núcleo CMS y módulos especializados. La documentación para humanos vive en `docs/obsidian-vault/` y debe mantenerse como referencia principal.

Para contexto funcional y técnico:

- empieza por `docs/obsidian-vault/Index.md`
- usa `docs/obsidian-vault/Convenciones de la Vault.md` para convenciones
- usa `docs/obsidian-vault/Guia de Mantenimiento.md` para saber qué actualizar

## Orden recomendado de trabajo

1. Explorar el código y la vault.
2. Planificar el cambio.
3. Implementar un parche mínimo y focalizado.
4. Verificar con lint, tests o comprobaciones proporcionales al cambio.
5. Documentar o actualizar la vault si el cambio afecta comportamiento relevante.

## Reglas operativas

- No inventes comportamiento, rutas, permisos ni despliegue.
- Mantén consistencia con `CLAUDE.md`; si un detalle pertenece a la vault, refiérelo en vez de duplicarlo.
- Mantén cambios mínimos y focalizados; evita mezclar refactors no pedidos.

## Obligación documental

- Actualiza `docs/obsidian-vault/` cuando cambien arquitectura, comandos, configuración, variables de entorno, testing, flujos importantes, persistencia o deployment.
- Sigue las convenciones de `docs/obsidian-vault/Convenciones de la Vault.md` en vez de redefinirlas aquí.

## Convención para dudas y supuestos

- Duda no resuelta en la vault: `Pendiente por confirmar`
- Deducción razonable en la vault: `Inferencia`

## Checklist antes de cerrar una tarea

- El cambio está acotado al objetivo.
- No se inventó comportamiento no observado.
- La verificación ejecutada quedó clara.
- La vault fue revisada y actualizada si correspondía.
- `AGENTS.md`, `CLAUDE.md` y la vault siguen siendo coherentes entre sí.
