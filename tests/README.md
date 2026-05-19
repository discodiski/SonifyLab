# Tests para SonifyLab Pro

Este directorio contiene los tests unitarios y de integración para la nueva arquitectura modular de SonifyLab Pro.

## Estructura de Tests

- `test_models.py` - Tests para modelos de datos (FileItem, ConversionConfig)
- `test_core.py` - Tests para el motor de conversión (AudioConverter)
- `test_utils.py` - Tests para utilidades (validadores, logger)
- `test_ui_pyqt5.py` - Tests de integración para interfaz PyQt5
- `test_ui_gtk4.py` - Tests de integración para interfaz GTK4 (pendiente)

## Ejecutar Tests

### Requisitos previos

```bash
pip install pytest pytest-cov
```

### Ejecutar todos los tests

```bash
pytest tests/ -v
```

### Ejecutar con cobertura de código

```bash
pytest tests/ --cov=sonifylab --cov-report=html
```

### Ejecutar tests específicos

```bash
# Solo tests de modelos
pytest tests/test_models.py -v

# Solo tests del core
pytest tests/test_core.py -v

# Solo tests de UI (requiere PyQt5)
pytest tests/test_ui_pyqt5.py -v
```

## Notas Importantes

1. **Tests de UI**: Los tests de interfaz gráfica pueden fallar en entornos headless (sin display). Usa un framebuffer virtual o ejecuta solo tests de core/models en servidores.

2. **Archivos de prueba**: Algunos tests crean archivos temporales que se limpian automáticamente. Asegúrate de tener permisos de escritura en `/tmp`.

3. **FFmpeg**: Los tests de conversión requieren FFmpeg instalado en el sistema. Si no está disponible, esos tests se omitirán automáticamente.

## Agregar Nuevos Tests

Sigue este patrón para agregar nuevos tests:

```python
"""
Tests para [módulo específico]
"""
import pytest
from sonifylab.[modulo] import [Clase]

class Test[NombreClase]:
    """Tests para la clase [NombreClase]"""
    
    def test_descripcion_prueba(self):
        """Descripción de lo que prueba"""
        # Arrange
        # Act
        # Assert
        assert True
```

## Integración Continua

Para integrar con CI/CD (GitHub Actions, GitLab CI, etc.):

```yaml
# Ejemplo GitHub Actions
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: pip install -r requirements.txt && pip install pytest pytest-cov
      - name: Run tests
        run: pytest tests/ --cov=sonifylab --cov-report=xml
```
