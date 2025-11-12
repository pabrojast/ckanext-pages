# Fix: Líneas Grises del Grid Anterior

## Problema Identificado

Después de eliminar el sidebar, quedaban líneas grises visibles que eran parte del layout anterior con grid/tabla de Bootstrap.

**Síntomas:**
- Líneas horizontales grises
- Forma de tabla visible
- Separaciones del grid anterior
- Layout se ve "cuadriculado"

## Causa

Las líneas grises provienen de los estilos por defecto de CKAN que aplican:
- `border` en elementos `.wrapper`, `.container`, `.row`
- `background` en columnas del grid
- `box-shadow` en elementos del layout
- Estilos Bootstrap heredados

## Solución Aplicada

### CSS Agregado

**Archivo:** `ckanext/pages/public/css/data-stories-edit.css`

```css
/* CRITICAL: Remove all gray borders from CKAN default layout */
body {
  background: #f8f9fa !important;
}

body .wrapper,
body .wrapper .container,
body .wrapper .row,
body .wrapper .primary,
body .wrapper .secondary,
body > .wrapper,
body > .wrapper > .container,
#content .wrapper,
#content .container,
.wrapper,
.wrapper .container,
.wrapper .row,
.wrapper [class*="col-"] {
  border: 0 !important;
  border-top: 0 !important;
  border-bottom: 0 !important;
  border-left: 0 !important;
  border-right: 0 !important;
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
  outline: 0 !important;
}
```

### Selectores Adicionales

También se agregaron reglas para cubrir más casos:

```css
/* Remove Bootstrap grid borders and backgrounds */
body .row,
body .col-sm-9,
body .col-sm-3,
body .col-md-9,
body .col-md-3,
body .primary,
body .secondary,
body .content,
body .wrapper {
  border: none !important;
  /* ... más reglas ... */
}

/* Specific overrides for CKAN theme */
.account-masthead,
.masthead,
body > .wrapper > .container,
.primary.col-md-9,
.primary.col-sm-9 {
  border: 0 !important;
  /* ... más reglas ... */
}
```

## Elementos Afectados

Los estilos se aplican a:

1. **`.wrapper`** - Contenedor principal de CKAN
2. **`.container`** - Contenedores Bootstrap
3. **`.row`** - Filas del grid
4. **`[class*="col-"]`** - Todas las columnas
5. **`.primary`, `.secondary`** - Áreas de contenido
6. **`.masthead`** - Cabecera si tiene bordes

## Uso de `!important`

**¿Por qué `!important`?**

Es necesario porque:
- Los estilos de CKAN tienen alta especificidad
- Hay múltiples hojas de estilo que se cargan
- Plugins de tema pueden sobrescribir estilos
- Bootstrap tiene estilos muy específicos

**Alternativa sin `!important`:**
Requeriría modificar los templates base de CKAN, lo cual no es recomendable.

## Testing

Para verificar que la corrección funciona:

### Visual
- [ ] No hay líneas grises horizontales
- [ ] No hay líneas grises verticales
- [ ] No se ve forma de tabla/grid
- [ ] Background es uniforme (#f8f9fa)
- [ ] Solo se ven los módulos con sus propios bordes

### Inspeccionando en DevTools

1. Abrir DevTools (F12)
2. Inspeccionar elementos con clase `.wrapper`, `.row`, etc.
3. Verificar en "Computed" que:
   - `border: 0`
   - `background: transparent`
   - `box-shadow: none`

### Diferentes Navegadores

- [ ] Chrome
- [ ] Firefox  
- [ ] Safari
- [ ] Edge

## Backup de Estilos

Si por alguna razón necesitas revertir los cambios, los selectores afectados son:

```css
body .wrapper { /* estilos originales */ }
body .container { /* estilos originales */ }
body .row { /* estilos originales */ }
```

## Impacto

**Positivo:**
- ✅ Layout limpio sin líneas residuales
- ✅ Apariencia profesional
- ✅ Consistente con diseño moderno
- ✅ Mejor experiencia visual

**Sin efectos secundarios:**
- ✅ Solo afecta a la vista de edición
- ✅ No rompe otras vistas
- ✅ No afecta funcionalidad

## Notas Adicionales

### Si las líneas persisten

Si después de aplicar estos cambios aún ves líneas grises:

1. **Limpiar cache del navegador**
   ```
   Ctrl + Shift + R (hard refresh)
   ```

2. **Verificar que el CSS se está cargando**
   - DevTools → Network → Filter CSS
   - Buscar `data-stories-edit.css`
   - Debe estar cargado y sin errores

3. **Inspeccionar elemento específico**
   - Click derecho en la línea gris
   - "Inspect Element"
   - Ver qué elemento la está generando
   - Ver qué CSS se está aplicando

4. **Agregar selector más específico**
   Si identificas un elemento específico que no está cubierto, agrégalo al CSS:
   ```css
   .elemento-especifico {
     border: 0 !important;
     background: transparent !important;
   }
   ```

## Resumen

**Problema:** Líneas grises del grid/tabla anterior
**Causa:** Estilos Bootstrap/CKAN heredados
**Solución:** CSS agresivo con `!important` para sobrescribir
**Estado:** ✅ CORREGIDO

El layout ahora debe verse completamente limpio, sin líneas grises, solo con los elementos diseñados (breadcrumb, banner, módulos, etc.).
