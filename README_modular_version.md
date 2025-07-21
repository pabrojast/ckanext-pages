# Open Source Software Edit Form - Modular Version

Este documento explica la nueva versión modular del formulario de edición de herramientas de software de código abierto.

## Archivos Creados

### CSS
- `assets/css/open-source-software-edit.css` - Estilos CSS separados del HTML

### JavaScript
- `assets/js/open-source-software-edit.js` - Funcionalidad principal del formulario
- `assets/js/organization-loader.js` - Carga de organizaciones (con URL dinámica)
- `assets/js/member-states.js` - Gestión de estados miembros (con URL dinámica)  
- `assets/js/image-upload.js` - Gestión de carga de imágenes
- `assets/js/quill-editor-manager.js` - Gestión de editores WYSIWYG
- `assets/js/data-initialization.js` - Inicialización de datos

### Templates
- `templates_main/ckanext_pages/open-source-software_edit_modular.html` - Template HTML simplificado

### Configuración
- `assets/webassets.yml` - Configuración actualizada de assets

## URLs y Endpoints

### Versión Original (sigue funcionando)
- URL: `/open-source-software_edit`
- URL: `/open-source-software_edit/<page>`  
- Endpoint: `pages.open_source_software_new`
- Endpoint: `pages.open_source_software_edit`

### Versión Modular (nueva)
- URL: `/open-source-software-modular_edit`
- URL: `/open-source-software-modular_edit/<page>`
- Endpoint: `pages.open_source_software_modular_new` 
- Endpoint: `pages.open_source_software_modular_edit`

## URLs de API Dinámicas

La nueva versión construye las URLs de API dinámicamente basándose en el dominio actual:

```javascript
// Antes (hardcodeado):
url: 'https://data.dev-wins.com/api/3/action/organization_list'

// Ahora (dinámico):
function getApiUrl() {
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;  
  const port = window.location.port;
  
  let apiUrl = protocol + '//' + hostname;
  if (port && port !== '80' && port !== '443') {
    apiUrl += ':' + port;
  }
  return apiUrl + '/api/3/action/';
}
```

## Funciones del Blueprint

### blueprint.py
- `open_source_software_edit()` - Función original (sin cambios)
- `open_source_software_edit_modular()` - Nueva función para versión modular

### utils.py  
- `pages_edit()` - Función original (sin cambios)
- `pages_edit_modular()` - Nueva función que usa el template modular

## Cómo Usar la Versión Modular

1. **Para crear una nueva entrada:**
   ```
   http://tu-sitio.com/open-source-software-modular_edit
   ```

2. **Para editar una entrada existente:**
   ```
   http://tu-sitio.com/open-source-software-modular_edit/nombre-de-la-entrada
   ```

3. **En plantillas Jinja2:**
   ```html
   <!-- Para crear nuevo -->
   <a href="{{ h.url_for('pages.open_source_software_modular_new') }}">Crear Nueva Herramienta</a>
   
   <!-- Para editar existente -->
   <a href="{{ h.url_for('pages.open_source_software_modular_edit', page=page.name) }}">Editar</a>
   ```

## Ventajas de la Versión Modular

1. **Código más limpio:** CSS y JS separados del HTML
2. **URLs dinámicas:** Se adapta automáticamente al dominio donde está instalado
3. **Mejor mantenimiento:** Cada funcionalidad en su propio archivo
4. **Mejor rendimiento:** Assets se pueden minificar y cachear por separado
5. **Desarrollo más fácil:** Cada módulo es independiente y reutilizable

## Migración

La versión original sigue funcionando sin cambios. Para migrar gradualmente:

1. Probar la versión modular en desarrollo
2. Actualizar enlaces de navegación cuando esté lista
3. Eventualmente reemplazar la versión original

## Archivos de Assets

Los archivos CSS y JS se generan automáticamente por Webassets y se sirven como:
- `ckanext-pages/<version>_open-source-software-edit.css`  
- `ckanext-pages/<version>_open-source-software-edit.js`
