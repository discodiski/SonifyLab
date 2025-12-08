# SonifyLab Pro

![SonifyLab Pro Logo](icono.png)

> 🎵 **Herramienta profesional de conversión de audio por lotes**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![GTK4](https://img.shields.io/badge/GTK4-Libadwaita-4a86cf.svg)](https://gtk.org/)
[![Tests](https://img.shields.io/badge/tests-15%20passed-brightgreen.svg)](tests/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey.svg)]()

---

## 📖 Descripción

**SonifyLab Pro** es una aplicación de escritorio moderna para convertir archivos de audio entre múltiples formatos. La versión principal usa **GTK4 + Libadwaita** para un look 100% nativo en GNOME/Zorin OS. También incluye una versión PyQt5 para compatibilidad con Windows.

![Pantalla Principal](pantallaprincipal.png)

---

## ✨ Características

| Característica | Descripción |
|----------------|-------------|
| 🔄 **Conversión por lotes** | Convierte múltiples archivos simultáneamente |
| 🎵 **10 formatos soportados** | mp3, wav, flac, aac, ogg, m4a, wma, opus, aiff, alac |
| ⚙️ **Personalización** | Selecciona bitrate (128k-320k) y formato de salida |
| 🚀 **Procesamiento paralelo** | Aprovecha todos los núcleos de tu CPU |
| 📊 **Progreso en tiempo real** | Barra de progreso y contador de archivos |
| 📁 **Añadir carpetas** | Escanea recursivamente carpetas completas |
| 🌙 **Tema automático** | Sigue el tema oscuro/claro del sistema (Linux) |
| 📝 **Registro detallado** | Historial de conversiones realizadas |

---

## 📋 Requisitos

- **Python** 3.8 o superior
- **FFmpeg** instalado y accesible desde terminal
- **Sistema operativo:** Linux (recomendado) o Windows

---

## 🚀 Instalación

### Linux (Ubuntu 22.04+, Zorin OS 17+, Fedora 38+) ⭐ Recomendado

```bash
# Clonar el repositorio
git clone https://github.com/discodiski/SonifyLab.git
cd SonifyLab

# Ejecutar instalador automático
chmod +x install.sh
./install.sh
```

El instalador automáticamente:
- ✅ Instala GTK4 y Libadwaita (look nativo)
- ✅ Instala FFmpeg
- ✅ Crea acceso directo en el menú de aplicaciones

### Windows

```powershell
# Clonar el repositorio
git clone https://github.com/discodiski/SonifyLab.git
cd SonifyLab

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python SonifyLab.py
```

> **Nota:** En Windows necesitas [FFmpeg](https://ffmpeg.org/download.html) instalado y añadido al PATH.

---

## 🎯 Uso

### Desde el menú de aplicaciones (Linux)
1. Busca "SonifyLab" en el menú de aplicaciones
2. ¡Listo para usar!

### Desde terminal

**Linux (GTK4 - recomendado):**
```bash
python3 sonifylab_gtk.py
```

**Windows (PyQt5):**
```bash
python SonifyLab.py
```

### Flujo de trabajo
1. **Añadir archivos:** Click en "+" o "📁" para añadir archivos o carpetas
2. **Configurar:** Selecciona formato de salida y calidad (bitrate)
3. **Carpeta de salida:** Selecciona dónde guardar los archivos convertidos
4. **Convertir:** Click en "▶" para iniciar la conversión
5. **Monitorear:** Observa el progreso en la barra inferior

---

## 📁 Estructura del proyecto

```
SonifyLab/
├── sonifylab_gtk.py     # Versión GTK4 + Libadwaita (Linux) ⭐
├── SonifyLab.py         # Versión PyQt5 (Windows)
├── style.qss            # Estilos para PyQt5
├── requirements.txt     # Dependencias de Python
├── pyproject.toml       # Configuración de empaquetado (v2.0.0)
├── install.sh           # Instalador para Linux (GTK4)
├── install.bat          # Instalador para Windows
├── pytest.ini           # Configuración de tests
├── CHANGELOG.md         # Historial de cambios
├── tests/
│   ├── __init__.py
│   └── test_sonifylab.py  # 15 tests unitarios
├── icono.png            # Icono de la aplicación
├── icono.ico            # Icono para Windows
├── pantallaprincipal.png  # Captura de pantalla (GTK4)
├── LICENSE              # Licencia GPL-3.0
└── README.md            # Este archivo
```

---

## 🔧 Formatos soportados

| Formato | Extensión | Descripción |
|---------|-----------|-------------|
| MP3 | `.mp3` | El más compatible, buena compresión |
| WAV | `.wav` | Sin pérdida, archivos grandes |
| FLAC | `.flac` | Sin pérdida, comprimido |
| AAC | `.aac` | Alta calidad, usado en Apple |
| OGG | `.ogg` | Código abierto, buena calidad |
| M4A | `.m4a` | Contenedor AAC de Apple |
| WMA | `.wma` | Formato de Microsoft |
| OPUS | `.opus` | Moderno, excelente compresión |
| AIFF | `.aiff` | Sin pérdida, formato Apple |
| ALAC | `.alac` | Apple Lossless |

---

## 🛠️ Desarrollo

### Ejecutar desde código fuente

**Linux (GTK4):**
```bash
git clone https://github.com/discodiski/SonifyLab.git
cd SonifyLab
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 ffmpeg
python3 sonifylab_gtk.py
```

**Windows (PyQt5):**
```bash
git clone https://github.com/discodiski/SonifyLab.git
cd SonifyLab
pip install -r requirements.txt
python SonifyLab.py
```

### Ejecutar tests
```bash
# Instalar dependencias de desarrollo
pip install pytest pytest-qt

# Ejecutar tests
python -m pytest tests/ -v

# Resultado esperado: 15 passed
```

---

## 📄 Licencia

Este proyecto está licenciado bajo la **GNU General Public License v3.0**.

Ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 👤 Autor

**Discaury Salas** — [@discodiski](https://github.com/discodiski)

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## ⭐ Tecnologías

- [FFmpeg](https://ffmpeg.org/) — Motor de conversión de audio
- [GTK4](https://gtk.org/) + [Libadwaita](https://gnome.pages.gitlab.gnome.org/libadwaita/) — Interfaz nativa Linux
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) — Interfaz Windows
- [pytest](https://pytest.org/) — Framework de testing
