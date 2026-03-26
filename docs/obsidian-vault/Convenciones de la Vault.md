# Convenciones de la Vault

Tags: #referencia #documentacion
Actualizado: 2026-03-26

## Convención de nombres

- Usar nombres de nota en Title Case y en español.
- Una nota por concepto operativo o arquitectónico.
- Evitar prefijos numéricos salvo que la vault crezca mucho.
- Mantener los nombres estables para no romper wikilinks.

## Convención de tags

Tags recomendados:

- `#hub`
- `#onboarding`
- `#arquitectura`
- `#operacion`
- `#testing`
- `#deployment`
- `#frontend`
- `#backend`
- `#datos`
- `#modulo/pages`
- `#modulo/data-stories`
- `#modulo/featured-viewers`
- `#estado/inferencia`
- `#estado/pendiente`

## Convención estructural

Cada nota debería incluir, cuando aplique:

- propósito de la nota
- hechos confirmados
- enlaces a notas relacionadas
- `Pendiente por confirmar` si falta información
- `Inferencia` si se deduce algo del código o de la estructura

## Convención editorial

- Explicar, no copiar código.
- Preferir rutas de archivos y responsabilidades antes que dumps de implementación.
- Si una afirmación depende de código no completamente cubierto, marcarla como inferencia.
- Si el repo no contiene la evidencia, no asumir entorno productivo.

## Convención de mantenimiento

- Actualizar [[Index]] si aparecen notas nuevas relevantes.
- Si cambia un módulo, revisar [[Modulos]], [[Arquitectura]], [[Flujos Importantes]] y [[Testing]].
- Si cambia la configuración, revisar [[Variables de Entorno]], [[Setup Local]] y [[Deployment]].

Relacionadas: [[README]], [[Guia de Mantenimiento]], [[Backlog Documentacion]]
