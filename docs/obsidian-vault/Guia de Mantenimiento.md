# Guia de Mantenimiento

Tags: #operacion #documentacion
Actualizado: 2026-03-26

Relacionadas: [[Convenciones de la Vault]], [[Backlog Documentacion]], [[Index]]

## Objetivo

Mantener la vault útil después de cambios de código, no convertirla en una foto vieja del sistema.

También asegurar consistencia ligera con `CLAUDE.md` y `AGENTS.md`, que deben referenciar esta vault en lugar de repetirla.

## Checklist general al cambiar código

- revisar si cambió algún entrypoint, ruta o comando
- revisar si cambió algún flag de configuración
- revisar si cambió persistencia o migraciones
- revisar si cambió un flujo editorial o de aprobación
- revisar si cambió UI, templates o assets
- revisar si cambió cobertura o comandos de test
- agregar o actualizar vacíos en [[Backlog Documentacion]]

## Si cambia backend

Actualizar como mínimo:

- [[Arquitectura]]
- [[Modulos]]
- [[Rutas y Entrypoints]]
- [[Datos y Persistencia]]
- [[Flujos Importantes]]
- [[Testing]]

Revisar especialmente:

- nuevas actions
- nuevas auth functions
- nuevos `page_type`
- cambios en schemas
- cambios en tablas o migraciones

## Si cambia frontend

Actualizar como mínimo:

- [[Frontend y Plantillas]]
- [[Modulos]]
- [[Flujos Importantes]]
- [[Troubleshooting]]

Revisar especialmente:

- templates nuevos o eliminados
- JS/CSS nuevos
- cambios de formularios
- dependencias de editor WYSIWYG

## Si cambia infra o despliegue

Actualizar como mínimo:

- [[Deployment]]
- [[Setup Local]]
- [[Variables de Entorno]]
- [[Troubleshooting]]

Revisar especialmente:

- nuevos servicios externos
- cambios en variables CKAN
- cambios de pipeline CI/CD
- cambios en storage de uploads

## Buenas prácticas

- no documentar suposiciones sin marcarlas
- usar `Pendiente por confirmar` cuando falte evidencia
- enlazar notas relacionadas con `[[...]]`
- actualizar primero la nota temática y luego [[Index]] si cambia la navegación
- preferir explicar decisiones y flujos, no listar archivos sin contexto
- mantener `CLAUDE.md` y `AGENTS.md` breves y referenciales

## Cuándo abrir backlog documental

Agregar ítems a [[Backlog Documentacion]] cuando:

- detectes discrepancias entre README y código
- falten pruebas visibles para un módulo
- haya comportamiento importante sin persistencia clara
- dependa de infraestructura externa no documentada

## Convención práctica para nuevas notas

- nombre en español y Title Case
- scope claro y limitado
- links entrantes/salientes visibles
- tags mínimos y útiles

## Señal de alerta

Si un cambio requiere tocar más de una de estas notas y no se actualizan juntas, la vault probablemente empieza a divergir del sistema real.
