# Guía de Tags de Recursos para Herramientas de Gestión de Agua

## Resumen de Mejoras Implementadas

He solucionado los siguientes problemas:

### ✅ Problemas Resueltos

1. **Tool Overview no se guardaba**
   - Mejoré la sincronización del editor Quill
   - Agregué eventos de cambio automáticos
   - Función de sincronización global antes del envío del formulario

2. **Logo no se mostraba en las opciones de header**
   - Corregí la lógica del header display mode
   - Mejoré las variables de template para el logo

3. **Problemas con las tarjetas de recursos HTML mal formateadas**
   - Nuevo sistema de procesamiento de HTML del editor Quill
   - Sistema de tags especiales para crear tarjetas limpias
   - Auto-detección mejorada de enlaces

## 🚀 Nuevo Sistema de Tags de Recursos

### Formato de Tag Especial

```
[RESOURCE:tipo:url:título:descripción]
```

### Tipos de Recursos Disponibles

| Tipo | Icono | Descripción | Ejemplo de Uso |
|------|-------|-------------|----------------|
| `documentation` | 📄 | Documentación y manuales | Guías de usuario, API docs |
| `github` | 🐙 | Repositorios GitHub | Código fuente, ejemplos |
| `youtube` | ▶️ | Videos de YouTube | Tutoriales, demos |
| `openlearning` | 🎓 | Cursos UNESCO OpenLearning | Capacitación oficial |
| `website` | 🌐 | Sitios web oficiales | Páginas del proyecto |
| `tutorial` | 📚 | Tutoriales y guías | Instrucciones paso a paso |
| `guide` | 📖 | Guías y manuales | Documentación detallada |
| `manual` | 📋 | Manuales técnicos | Especificaciones técnicas |
| `course` | 🏫 | Cursos en línea | Formación estructurada |
| `download` | ⬇️ | Enlaces de descarga | Instaladores, releases |

### Ejemplos de Uso

#### Para Tool Overview:
```
Este es el contenido principal de la herramienta...

[RESOURCE:documentation:https://docs.qgis.org:Documentación QGIS:Guía completa de usuario y desarrollo]
[RESOURCE:github:https://github.com/qgis/QGIS:Código Fuente:Repositorio oficial del proyecto QGIS]
```

#### Para Installation & Usage:
```
Instrucciones de instalación...

[RESOURCE:download:https://qgis.org/downloads:Descargar QGIS:Obtén la última versión estable]
[RESOURCE:tutorial:https://docs.qgis.org/install:Guía de Instalación:Instrucciones paso a paso para tu sistema operativo]
```

#### Para Learning Resources:
```
Recursos de aprendizaje disponibles...

[RESOURCE:youtube:https://youtube.com/watch?v=kCnNWyl9qSE:Tutorial QGIS Básico:Aprende los fundamentos en 30 minutos]
[RESOURCE:openlearning:https://openlearning.unesco.org/qgis-course:Curso UNESCO QGIS:Formación oficial certificada]
[RESOURCE:course:https://coursera.org/learn/qgis:Curso Avanzado QGIS:Especialización en análisis geoespacial]
```

#### Para Examples & Use Cases:
```
Casos de uso reales...

[RESOURCE:website:https://project-example.com:Caso de Estudio: Gestión de Cuencas:Proyecto real de manejo de recursos hídricos]
[RESOURCE:github:https://github.com/water-project/examples:Ejemplos de Código:Scripts y casos de uso prácticos]
```

## 🔧 Compatibilidad con Enlaces Automáticos

El sistema mantiene compatibilidad con la detección automática de enlaces:

- **YouTube**: Los enlaces de `youtube.com` y `youtu.be` se detectan automáticamente
- **OpenLearning**: Los enlaces de `openlearning.unesco.org` se estilizan automáticamente con branding UNESCO
- **GitHub**: Los enlaces de `github.com` se detectan como repositorios
- **Documentación**: Enlaces que contienen `readthedocs`, `docs`, `manual`, etc. se detectan automáticamente

## 💡 Consejos de Uso

### 1. Títulos Descriptivos
- ✅ Bueno: "Guía de Instalación para Ubuntu"
- ❌ Malo: "docs.example.com"

### 2. Descripciones Útiles
- ✅ Bueno: "Instrucciones paso a paso para configurar el entorno"
- ❌ Malo: "Haz clic aquí"

### 3. Combinación de Formatos
Puedes combinar tags especiales con texto normal:

```
QGIS es una herramienta poderosa para análisis geoespacial.

[RESOURCE:documentation:https://docs.qgis.org:Manual de Usuario:Documentación completa]

También incluye características avanzadas como:
- Análisis de redes
- Modelado de elevación
- Procesamiento de imágenes satelitales

[RESOURCE:youtube:https://youtube.com/watch?v=abc123:Tutorial Avanzado:Análisis de cuencas hidrográficas con QGIS]
```

## 🎨 Resultado Visual

Los tags se convierten automáticamente en tarjetas visuales profesionales con:
- Iconos específicos por tipo de recurso
- Colores diferenciados (YouTube rojo, GitHub negro, UNESCO azul, etc.)
- Hover effects y animaciones
- Layout responsive
- Enlaces que abren en nueva pestaña

## 🐛 Solución de Problemas

### El contenido no se guarda
- El editor Quill ahora sincroniza automáticamente
- Se ejecuta una sincronización adicional antes del envío del formulario
- Verifica la consola del navegador para mensajes de depuración

### El logo no aparece
- Asegúrate de haber subido una imagen de logo
- Verifica que hayas seleccionado "Logo Only" o "Logo Above Text" en las opciones de header
- El logo debe estar en el campo "Header Image URL"

### Las tarjetas no se generan
- Verifica que el formato del tag sea exacto: `[RESOURCE:tipo:url:título:descripción]`
- Asegúrate de que el tipo sea uno de los válidos
- No debe haber espacios extra alrededor de los dos puntos
- El tag debe estar en una línea separada

## 🔄 Migración desde el Sistema Anterior

El nuevo sistema es compatible con el contenido existente:
- Los enlaces existentes seguirán funcionando
- Se recomienda actualizar gradualmente a los nuevos tags para mejor presentación
- Los enlaces de YouTube y OpenLearning ya existentes se estilizan automáticamente 