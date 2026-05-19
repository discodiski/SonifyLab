# Documentación de Desarrollo - SonifyLab Pro

Esta carpeta contiene documentación técnica para desarrolladores que trabajan en SonifyLab Pro.

## Índice de Documentos

### Arquitectura y Diseño
- `ARCHITECTURE.md` - Visión general de la arquitectura modular
- `SDD_METHODOLOGY.md` - Metodología Spec-Driven Development utilizada
- `DECISION_RECORDS.md` - Decisiones de diseño y trade-offs

### Guías Prácticas
- `CONTRIBUTING.md` - Guía para contribuir al proyecto
- `CODING_STANDARDS.md` - Estándares de código y convenciones
- `TESTING_GUIDE.md` - Guía completa de testing

### Referencias Técnicas
- `API_REFERENCE.md` - Referencia completa de la API
- `DEPENDENCIES.md` - Lista de dependencias y justificación
- `MIGRATION_GUIDE.md` - Guía de migración desde versiones anteriores

## Quick Start para Desarrolladores

### 1. Configurar Entorno de Desarrollo

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/sonifylab-pro.git
cd sonifylab-pro

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt
```

### 2. Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=sonifylab --cov-report=html

# Tests específicos
pytest tests/test_core.py -v
```

### 3. Ejecutar la Aplicación

```bash
# Usando el entry point
python -m sonifylab.run

# O directamente
python sonifylab/run.py
```

### 4. Desarrollo Activo

```bash
# Modo watch para desarrollo (auto-reload)
pip install watchdog
# (implementar script de watch según necesidad)

# Linting y formato
flake8 sonifylab/
black sonifylab/
isort sonifylab/
```

## Estructura del Proyecto

```
sonifylab/
├── models/           # Modelos de datos
│   ├── file_item.py
│   └── conversion_config.py
├── core/             # Lógica de negocio
│   ├── converter.py
│   └── exceptions.py
├── ui/               # Interfaces gráficas
│   ├── base.py
│   ├── pyqt5_interface.py
│   └── gtk4_interface.py
├── utils/            # Utilidades
│   ├── file_validator.py
│   └── logger.py
└── run.py            # Entry point
```

## Principios de Diseño

### 1. Separación de Responsabilidades
- **Core**: Lógica pura, sin dependencias de UI
- **UI**: Solo presentación y manejo de eventos
- **Models**: Datos inmutables y tipados

### 2. Inmutabilidad
- Los modelos de datos no deben modificarse después de creados
- Usar dataclasses con `frozen=True` cuando sea posible

### 3. Tipado Estático
- Todo el código debe estar completamente tipado
- Usar `mypy` para validación: `mypy sonifylab/`

### 4. Manejo de Errores
- El core lanza excepciones específicas
- La UI captura y muestra errores al usuario
- Nunca silenciar excepciones sin logging

## Flujo de Trabajo Git

```bash
# Crear rama para nueva feature
git checkout -b feature/nueva-funcionalidad

# Commits atómicos y descriptivos
git commit -m "feat: agregar soporte para formato OGG"
git commit -m "fix: corregir cálculo de progreso en GTK4"
git commit -m "test: añadir tests para conversor WAV"

# Push y PR
git push origin feature/nueva-funcionalidad
# Crear Pull Request en GitHub/GitLab
```

## Convenciones de Nomenclatura

### Archivos
- `snake_case.py` para todos los archivos Python
- `test_*.py` para archivos de test
- `*_interface.py` para implementaciones de UI

### Clases y Funciones
- `PascalCase` para clases: `AudioConverter`, `FileItem`
- `snake_case` para funciones: `convert_file`, `validate_path`
- Verbos descriptivos para métodos: `get_status()`, `update_progress()`

### Excepciones
- Terminar en `Error`: `ConversionError`, `ValidationError`
- Heredar de excepciones estándar cuando corresponda

## Debugging

### Logging
```python
from sonifylab.utils.logger import get_logger

logger = get_logger(__name__)
logger.debug("Mensaje debug")
logger.info("Información general")
logger.warning("Advertencia")
logger.error("Error ocurrido")
```

### Debug Mode
```bash
# Habilitar logging verbose
export SONIFYLAB_LOG_LEVEL=DEBUG
python -m sonifylab.run
```

## Performance Tips

1. **Evitar bloqueos en UI**: Siempre usar threads para operaciones largas
2. **Reutilizar instancias**: No crear nuevos converters innecesariamente
3. **Lazy loading**: Cargar recursos solo cuando se necesitan
4. **Profile regular**: Usar `cProfile` para identificar bottlenecks

## Recursos Adicionales

- [Documentación oficial PyQt5](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [Guía GTK4](https://docs.gtk.org/gtk4/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [Python Data Classes](https://docs.python.org/3/library/dataclasses.html)

---

**Mantenimiento**: Equipo de Desarrollo SonifyLab
**Última actualización**: 2024
**Versión**: 2.0.0
