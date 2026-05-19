# 🎵 SonifyLab Pro v2.0.0 - Documentación Principal

**Conversor de audio profesional con interfaz gráfica dual (PyQt5/GTK4)**

![Versión](https://img.shields.io/badge/versión-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-green)
![Licencia](https://img.shields.io/badge/licencia-MIT-yellow)

## 📖 Índice

- [Descripción](#descripción)
- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Arquitectura](#arquitectura)
- [Desarrollo](#desarrollo)
- [Tests](#tests)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

---

## Descripción

SonifyLab Pro es una aplicación de escritorio para conversión de archivos de audio entre múltiples formatos. Construido con una arquitectura modular moderna que separa completamente la lógica de negocio de la interfaz gráfica, permitiendo soporte nativo para múltiples toolkits gráficos (PyQt5 y GTK4).

### ¿Qué's Nuevo en v2.0.0?

- ✅ **Arquitectura 100% modular** - Código reorganizado en capas independientes
- ✅ **Doble interfaz gráfica** - Soporte automático para PyQt5 o GTK4
- ✅ **Tipado estático completo** - Mejor soporte IDE y detección temprana de errores
- ✅ **Tests unitarios** - Cobertura completa del core y modelos
- ✅ **Documentación SDD** - Desarrollado con Spec-Driven Development

---

## Características

### Formatos Soportados
- **Entrada**: MP3, WAV, FLAC, OGG, M4A, AAC, WMA
- **Salida**: WAV, MP3, FLAC, OGG, M4A

### Funcionalidades Clave
- 🔄 Conversión por lotes (múltiples archivos simultáneos)
- ⚙️ Configuración personalizada (bitrate, sample rate, canales)
- 📊 Barra de progreso en tiempo real
- ❌ Manejo robusto de errores con mensajes descriptivos
- 🎯 Validación de archivos antes de conversión
- 📝 Logging detallado para debugging
- 🖥️ Detección automática de interfaz gráfica disponible

### Interfaz Gráfica
- **PyQt5**: Interfaz moderna y pulida para Windows/Linux/macOS
- **GTK4**: Integración nativa con entornos GNOME/Linux

---

## Requisitos

### Sistema
- Python 3.8 o superior
- FFmpeg instalado y disponible en PATH

### Dependencias Python

**Obligatorio:**
```bash
# Uno de los siguientes (o ambos)
PyQt5>=5.15.0
PyGObject>=3.40.0  # Para GTK4
```

**Opcional (desarrollo):**
```bash
pytest>=7.0.0
pytest-cov>=3.0.0
black>=22.0.0
flake8>=4.0.0
mypy>=0.950
```

### Instalar FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Fedora:**
```bash
sudo dnf install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
1. Descargar desde https://ffmpeg.org/download.html
2. Extraer y agregar `bin/` al PATH del sistema

---

## Instalación

### Método 1: Desde Repositorio (Recomendado)

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/sonifylab-pro.git
cd sonifylab-pro

# Crear entorno virtual
python -m venv venv

# Activar entorno
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Método 2: Pip (Próximamente)

```bash
pip install sonifylab-pro
```

---

## Uso

### Ejecución Básica

```bash
# La aplicación detectará automáticamente la UI disponible
python -m sonifylab.run
```

### Forzar Interfaz Específica

```bash
# Usar PyQt5 explícitamente
python -m sonifylab.run --ui pyqt5

# Usar GTK4 explícitamente
python -m sonifylab.run --ui gtk4
```

### Flujo de Trabajo

1. **Abrir aplicación**: Ejecutar `python -m sonifylab.run`
2. **Agregar archivos**: Click en "Agregar Archivos" o arrastrar y soltar
3. **Configurar opciones**: Seleccionar formato de salida, bitrate, sample rate
4. **Iniciar conversión**: Click en "Convertir"
5. **Monitorear progreso**: Ver barras de progreso en tiempo real
6. **Acceder resultados**: Los archivos convertidos se guardan en el directorio especificado

### Capturas de Pantalla

*(Espacio reservado para capturas de las interfaces PyQt5 y GTK4)*

---

## Arquitectura

SonifyLab Pro v2.0.0 sigue principios de **Clean Architecture** adaptados para aplicaciones de escritorio:

```
┌─────────────────────────────────────────────┐
│              Capa de Presentación           │
│  ┌──────────────┐    ┌──────────────┐      │
│  │   PyQt5 UI   │    │    GTK4 UI   │      │
│  └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────┘
                    ↓ usa
┌─────────────────────────────────────────────┐
│            Capa de Modelos                  │
│  ┌──────────────┐    ┌──────────────┐      │
│  │  FileItem    │    │ConversionCfg │      │
│  └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────┘
                    ↓ usa
┌─────────────────────────────────────────────┐
│             Capa Core (Negocio)             │
│  ┌──────────────────────────────────┐      │
│  │       AudioConverter             │      │
│  └──────────────────────────────────┘      │
└─────────────────────────────────────────────┘
                    ↓ usa
┌─────────────────────────────────────────────┐
│          Capa de Utilidades                 │
│  ┌──────────────┐    ┌──────────────┐      │
│  │  Validators  │    │   Logger     │      │
│  └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────┘
```

### Estructura de Directorios

```
sonifylab/
├── models/               # Modelos de datos
│   ├── __init__.py
│   ├── file_item.py      # Modelo FileItem
│   └── conversion_config.py  # Configuración
├── core/                 # Lógica de negocio
│   ├── __init__.py
│   ├── converter.py      # Motor de conversión
│   └── exceptions.py     # Excepciones personalizadas
├── ui/                   # Interfaces gráficas
│   ├── __init__.py
│   ├── base.py           # Clase abstracta UIBase
│   ├── pyqt5_interface.py  # Implementación PyQt5
│   └── gtk4_interface.py   # Implementación GTK4
├── utils/                # Utilidades
│   ├── __init__.py
│   ├── file_validator.py   # Validación de archivos
│   └── logger.py         # Sistema de logging
├── run.py                # Entry point principal
└── __init__.py           # Constantes y versión
```

### Principios de Diseño

1. **Separación estricta**: El core no conoce nada de la UI
2. **Inmutabilidad**: Los modelos son dataclasses inmutables
3. **Tipado estático**: Todo el código está completamente tipado
4. **Excepciones específicas**: Errores del dominio bien definidos
5. **Logging centralizado**: Un único punto para logs

---

## Desarrollo

Ver documentación completa en [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)

### Quick Start

```bash
# Configurar entorno de desarrollo
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# Ejecutar tests
pytest tests/ -v

# Linting
flake8 sonifylab/
black --check sonifylab/

# Type checking
mypy sonifylab/
```

---

## Tests

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=sonifylab --cov-report=html

# Tests específicos
pytest tests/test_core.py -v
pytest tests/test_models.py -v
```

### Estructura de Tests

- `tests/test_models.py` - Tests de modelos de datos
- `tests/test_core.py` - Tests del motor de conversión
- `tests/test_utils.py` - Tests de utilidades
- `tests/test_ui_pyqt5.py` - Tests de interfaz PyQt5
- `tests/test_ui_gtk4.py` - Tests de interfaz GTK4

Ver [`tests/README.md`](tests/README.md) para más detalles.

---

## Contribuir

¡Las contribuciones son bienvenidas! Por favor sigue estos pasos:

1. **Fork** el repositorio
2. **Crea una rama** para tu feature (`git checkout -b feature/amazing-feature`)
3. **Commit** tus cambios (`git commit -m 'feat: add amazing feature'`)
4. **Push** a la rama (`git push origin feature/amazing-feature`)
5. **Abre un Pull Request**

### Convenciones de Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Cambios en documentación
- `style:` Formato, faltantes, etc.
- `refactor:` Refactorización de código
- `test:` Agregar o corregir tests
- `chore:` Cambios en build, dependencias, etc.

### Código de Conducta

- Sé respetuoso y constructivo
- Sigue los estándares de código existentes
- Escribe tests para nuevas funcionalidades
- Documenta cambios importantes

Ver [`CONTRIBUTING.md`](CONTRIBUTING.md) para guía detallada.

---

## Licencia

Este proyecto está licenciado bajo la **MIT License** - ver el archivo [LICENSE](LICENSE) para detalles.

---

## Agradecimientos

- [FFmpeg](https://ffmpeg.org/) - El corazón de la conversión de audio
- [PyQt5](https://www.riverbankcomputing.com/static/Docs/PyQt5/) - Framework gráfico
- [GTK4](https://gtk.org/) - Toolkit gráfico moderno
- Todos los contribuidores al proyecto

---

## Contacto

- **Issues**: Reporta bugs o solicita features en [GitHub Issues](https://github.com/tu-usuario/sonifylab-pro/issues)
- **Discusiones**: Únete a las discusiones en [GitHub Discussions](https://github.com/tu-usuario/sonifylab-pro/discussions)

---

**Hecho con ❤️ para la comunidad de audio digital**

*Última actualización: 2024 | Versión: 2.0.0*
