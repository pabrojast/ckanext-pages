# Checklist de Testing - Correcciones Open Source Admin

## Pre-requisitos
- [ ] Acceso como sysadmin a la instancia CKAN
- [ ] Al menos una entrada de open-source-software en estado 'pending'
- [ ] Acceso a los logs del servidor
- [ ] Navegador con modo incógnito disponible

## Test Suite 1: Cambio de Organización

### Setup
- [ ] Login como sysadmin
- [ ] Navegar a `/open-source-admin`
- [ ] Identificar una entrada pendiente con organización actual

### Ejecución
- [ ] Paso 1: Anotar nombre de la entrada: _________________
- [ ] Paso 2: Anotar organización actual: _________________
- [ ] Paso 3: Seleccionar una organización diferente del dropdown
- [ ] Paso 4: Click en "Set Organization"
- [ ] Paso 5: Observar mensaje flash

### Verificación
- [ ] ✓ Aparece mensaje de éxito "Organization changed to [nombre] successfully"
- [ ] ✓ NO aparece mensaje de error
- [ ] ✓ Refrescar página (F5)
- [ ] ✓ La organización mostrada es la nueva seleccionada
- [ ] ✓ En logs aparece: `[CHANGE_ORG] Before change`
- [ ] ✓ En logs aparece: `[CHANGE_ORG] After change - ihp_organization: [nuevo_id]`
- [ ] ✓ NO hay mensajes de error en logs

### Si Falla
- [ ] Capturar screenshot del mensaje de error
- [ ] Copiar logs relevantes con timestamp
- [ ] Anotar organización esperada vs. organización actual
- [ ] Verificar en BD: `SELECT ihp_organization FROM ckanext_pages WHERE name='[nombre_entrada]';`

---

## Test Suite 2: Aprobación de Entrada

### Setup
- [ ] Login como sysadmin
- [ ] Navegar a `/open-source-admin`
- [ ] Identificar una entrada pendiente para aprobar

### Ejecución - Parte 1: Aprobación
- [ ] Paso 1: Anotar nombre de la entrada: _________________
- [ ] Paso 2: Anotar título visible: _________________
- [ ] Paso 3: Click en "Approve & Publish"
- [ ] Paso 4: Confirmar en el diálogo de confirmación
- [ ] Paso 5: Observar mensaje flash

### Verificación - Parte 1
- [ ] ✓ Aparece mensaje "Open source software entry approved and published successfully"
- [ ] ✓ NO aparece mensaje de error
- [ ] ✓ La entrada desaparece de la lista de pendientes
- [ ] ✓ En logs aparece: `[APPROVE] Before approval - submission_status: pending, private: True`
- [ ] ✓ En logs aparece: `[APPROVE] After approval - submission_status: approved, private: False`

### Ejecución - Parte 2: Visibilidad Pública
- [ ] Paso 6: Cerrar sesión de admin
- [ ] Paso 7: Abrir navegador en modo incógnito
- [ ] Paso 8: Navegar a `/open-source-software` (sin login)
- [ ] Paso 9: Buscar la entrada aprobada en la lista

### Verificación - Parte 2
- [ ] ✓ La entrada aprobada aparece en la lista pública
- [ ] ✓ El título coincide con el anotado
- [ ] ✓ Se puede hacer click y ver el detalle completo
- [ ] ✓ NO aparecen errores 404 o permisos
- [ ] ✓ En logs aparece: `[PAGES_LIST] Filtering open-source-software - private: False, submission_status: approved`
- [ ] ✓ En logs aparece: `[PAGES_LIST] Query returned X results` (X > 0)

### Si Falla - Entrada No Visible
1. **Verificar en Base de Datos**:
   ```sql
   SELECT name, title, submission_status, private 
   FROM ckanext_pages 
   WHERE name='[nombre_entrada]' AND page_type='open-source-software';
   ```
   - [ ] ✓ submission_status = 'approved'
   - [ ] ✓ private = False (o 'f')

2. **Verificar Logs**:
   - [ ] Buscar `[APPROVE] After approval` - confirmar valores
   - [ ] Buscar `[PAGES_LIST]` - confirmar filtros aplicados
   - [ ] Buscar errores o warnings relacionados

3. **Test Manual de Query**:
   ```sql
   SELECT COUNT(*) FROM ckanext_pages 
   WHERE page_type='open-source-software' 
   AND submission_status='approved' 
   AND private=False;
   ```
   - [ ] ✓ Resultado > 0 (debe incluir la entrada aprobada)

---

## Test Suite 3: Combinación de Operaciones

### Objetivo
Verificar que cambio de organización + aprobación funcionan correctamente juntos

### Ejecución
- [ ] Paso 1: Tomar entrada pendiente
- [ ] Paso 2: Cambiar organización
- [ ] Paso 3: Verificar cambio exitoso
- [ ] Paso 4: Aprobar entrada
- [ ] Paso 5: Verificar aprobación exitosa
- [ ] Paso 6: Verificar visibilidad pública
- [ ] Paso 7: Verificar que mantiene la organización cambiada

### Verificación
- [ ] ✓ Ambas operaciones exitosas
- [ ] ✓ Entrada visible públicamente
- [ ] ✓ Organización correcta en vista pública
- [ ] ✓ Todos los logs correctos

---

## Test Suite 4: Casos Edge

### Test 4.1: Cambio a Misma Organización
- [ ] Seleccionar organización actual
- [ ] Click "Set Organization"
- [ ] ✓ Mensaje de éxito (aunque sea la misma)
- [ ] ✓ Sin errores

### Test 4.2: Aprobar Entrada Ya Aprobada
- [ ] Navegar directamente a `/open-source-admin/approve/[nombre-ya-aprobado]`
- [ ] ✓ Manejo correcto (o error claro)
- [ ] ✓ Sin corrupción de datos

### Test 4.3: Entrada Sin Organización
- [ ] Tomar entrada sin ihp_organization
- [ ] Aprobar
- [ ] ✓ Se aprueba correctamente
- [ ] ✓ Visible públicamente

---

## Revisión de Logs - Checklist

### Logs de Cambio de Organización
```
[CHANGE_ORG] Before change - page: XXX, current_org: YYY, new_org: ZZZ
[CHANGE_ORG] Attempting to update ihp_organization to: ZZZ
[PAGES_UPDATE] Setting 'ihp_organization' attribute: ZZZ
[PAGES_UPDATE] Final state - submission_status: ..., private: ..., ihp_organization: ZZZ
[CHANGE_ORG] After change - ihp_organization: ZZZ
```

### Logs de Aprobación
```
[APPROVE] Before approval - page: XXX, submission_status: pending, private: True
[APPROVE] Attempting to update - submission_status: approved, private: False
[PAGES_UPDATE] Setting 'submission_status' attribute: approved
[PAGES_UPDATE] Setting 'private' attribute: False
[PAGES_UPDATE] Final state - submission_status: approved, private: False, ihp_organization: ...
[APPROVE] After approval - submission_status: approved, private: False
```

### Logs de Listado Público
```
[PAGES_LIST] Filtering open-source-software - private: False, submission_status: approved
[PAGES_LIST] Executing query with search params: {...}
[DB.PAGES] Filtering by submission_status: approved
[PAGES_LIST] Query returned N results for open-source-software
```

---

## Registro de Resultados

### Test 1: Cambio de Organización
- **Fecha/Hora**: _________________
- **Tester**: _________________
- **Resultado**: [ ] PASS [ ] FAIL
- **Notas**: _________________

### Test 2: Aprobación y Visibilidad
- **Fecha/Hora**: _________________
- **Tester**: _________________
- **Resultado**: [ ] PASS [ ] FAIL
- **Notas**: _________________

### Test 3: Combinación
- **Fecha/Hora**: _________________
- **Tester**: _________________
- **Resultado**: [ ] PASS [ ] FAIL
- **Notas**: _________________

### Test 4: Casos Edge
- **Fecha/Hora**: _________________
- **Tester**: _________________
- **Resultado**: [ ] PASS [ ] FAIL
- **Notas**: _________________

---

## Sign-off

- [ ] Todos los tests PASS
- [ ] Logs revisados y correctos
- [ ] No hay errores en producción
- [ ] Documentación revisada

**Aprobado por**: _________________
**Fecha**: _________________
**Firma**: _________________

---

## En Caso de Problemas

### Checklist de Diagnóstico
1. [ ] Revisar logs con prefijos [CHANGE_ORG], [APPROVE], [PAGES_LIST]
2. [ ] Verificar estado en BD con queries SQL directas
3. [ ] Confirmar que CKAN está usando la versión actualizada del código
4. [ ] Verificar permisos de escritura en BD
5. [ ] Revisar configuración de transacciones en CKAN
6. [ ] Buscar errores de SQLAlchemy en logs
7. [ ] Verificar que no hay problemas de caché
8. [ ] Confirmar que worker/job queue está procesando correctamente

### Información a Recolectar
- [ ] Logs completos del servidor (últimas 1000 líneas)
- [ ] Output de queries SQL directas a la BD
- [ ] Screenshot de mensajes de error
- [ ] Configuración de CKAN relevante
- [ ] Versión de Python y CKAN
- [ ] Estado de la sesión de SQLAlchemy

### Contacto para Soporte
Si después de estos tests los problemas persisten, documentar:
1. Qué tests fallaron
2. Logs relevantes
3. Estado de BD
4. Pasos para reproducir

Y contactar al equipo de desarrollo con esta información.
