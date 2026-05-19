# Reestructuración de SonifyLab Pro

## Nueva Estructura del Proyecto

```
sonifylab/
├── __init__.py              # Constantes y metadatos compartidos
├── run.py                   # Punto de entrada principal (auto-detecta UI)
│
├── core/                    # Lógica de negocio (agnóstica a la UI)
│   ├── __init__.py
│   ├── converter.py         # Motor de conversión AudioConverter
│   └── ffmpeg_utils.py      # Utilidades de FFmpeg
│
├── models/                  # Modelos de datos
│   ├── __init__.py
│   ├── file_item.py         # Modelo FileItem con estados
│   └── conversion_config.py # Configuración de conversión
│
├── ui/                      # Interfaces gráficas
│   ├── __init__.py          # Detección de backends disponibles
│   ├── base.py              # Clase abstracta UIBase
│   └── pyqt5_interface.py   # Implementación PyQt5
│
└── utils/                   # Utilidades generales
    ├── __init__.py
    ├── file_validator.py    # Validación de archivos
    └── logger.py            # Sistema de logging
```

## Ventajas de la Nueva Estructura

### 1. **Separación de Responsabilidades**
- **core/**: Lógica pura de conversión, sin dependencias de UI
- **models/**: Estructuras de datos bien definidas
- **ui/**: Capas de presentación intercambiables
- **utils/**: Funcionalidades transversales reutilizables

### 2. **Mantenibilidad Mejorada**
- Cada módulo tiene una responsabilidad única
- Fácil de testear individualmente
- Código más legible y organizado

### 3. **Escalabilidad**
- Se pueden añadir nuevas interfaces (GTK4, CLI, Web) sin modificar el core
- Nuevos formatos de audio se agregan en un solo lugar
- Testing más sencillo con mocks

### 4. **Reutilización de Código**
- El motor de conversión es compartido entre PyQt5 y GTK4
- Validaciones y utilidades centralizadas
- Configuración consistente en toda la app

## Migración desde la Versión Anterior

### Archivos Originales → Nueva Ubicación

| Archivo Original | Nueva Ubicación | Notas |
|-----------------|----------------|-------|
| `SonifyLab.py` | `sonifylab/ui/pyqt5_interface.py` | UI PyQt5 refactorizada |
| `sonifylab_gtk.py` | `sonifylab/ui/gtk4_interface.py` | (pendiente) UI GTK4 |
| Constantes | `sonifylab/__init__.py` | Centralizadas |
| `ConversionProcess` | `sonifylab/core/converter.py` | Refactorizado como `AudioConverter` |
| Utilidades varias | `sonifylab/utils/` | Separadas por funcionalidad |

## Uso

### Ejecución Automática (Recomendado)
```bash
python -m sonifylab.run
# O directamente:
python sonifylab/run.py
```

### Ejecución Específica por UI

**PyQt5 (Windows):**
```bash
python -c "from sonifylab.ui.pyqt5_interface import main; main()"
```

**GTK4 (Linux):**
```bash
python -c "from sonifylab.ui.gtk4_interface import main; main()"
```

## Testing

Los tests deben actualizarse para usar la nueva estructura:

```python
from sonifylab.core.converter import AudioConverter
from sonifylab.models.file_item import FileItem, ConversionStatus
from sonifylab.models.conversion_config import ConversionConfig
from sonifylab.utils.file_validator import FileValidator
```

## Próximos Pasos

1. ✅ Crear estructura de directorios
2. ✅ Extraer modelos de datos
3. ✅ Extraer lógica de conversión
4. ✅ Crear utilidades
5. ✅ Refactorizar interfaz PyQt5
6. ⏳ Refactorizar interfaz GTK4
7. ⏳ Actualizar tests
8. ⏳ Documentación completa

## Autor

Discaury Salas - 2024
