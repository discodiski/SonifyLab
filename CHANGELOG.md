# Changelog

Todos los cambios notables de este proyecto serán documentados aquí.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

## [2.0.0] - 2025-12-08

### Añadido
- **Nueva versión GTK4 + Libadwaita** (`sonifylab_gtk.py`)
- Look 100% nativo de GNOME/Zorin OS
- Tema oscuro/claro automático del sistema
- ToastOverlay para notificaciones
- Thread safety con locks
- Tracking de archivos fallidos

### Mejorado
- Instalador actualizado para GTK4
- Entrada del menú apunta a versión GTK4
- Documentación actualizada

### Técnico
- HeaderBar con Adw.WindowTitle
- PreferencesGroup para secciones
- ComboRow y SwitchRow para configuración
- ExpanderRow colapsable para log

## [1.0.0] - 2025-12-08

### Añadido
- Sistema de tests unitarios con pytest (15 tests)
- Instalador para Windows (`install.bat`)
- Archivo `pyproject.toml` para empaquetado moderno
- Type hints en el código principal
- Archivos de log en directorio de la aplicación
- Historial de conversiones en formato JSONL

### Corregido
- Logs ahora se guardan en el directorio de la aplicación
- Archivo de historial renombrado a `.jsonl`
- Eliminados imports no utilizados (`QLocale`, `QTranslator`)
- Código comentado de internacionalización eliminado

### Mejorado
- README.md completamente reescrito con badges e instrucciones
- `.gitignore` profesional añadido
- Instalador Linux con integración al menú de aplicaciones
- Estructura del proyecto más profesional

## [0.1.0] - 2024-XX-XX

### Añadido
- Versión inicial de SonifyLab Pro
- Interfaz gráfica con PyQt5
- Conversión de audio con FFmpeg
- Soporte para 10 formatos de audio
- Procesamiento paralelo
- Barra de progreso individual y global
