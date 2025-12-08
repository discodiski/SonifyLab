#!/bin/bash
# ============================================
# SonifyLab Pro - Instalador para Linux (GTK4)
# ============================================
# Autor: Discaury Salas
# Compatible con: Ubuntu 22.04+, Zorin OS 17+, Fedora 38+
# ============================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin color

# Directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="SonifyLab Pro"
DESKTOP_FILE="$HOME/.local/share/applications/sonifylab.desktop"

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ${GREEN}$APP_NAME - Instalador GTK4/Libadwaita${BLUE}     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar que estamos en Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}Error: Este instalador es solo para Linux${NC}"
    exit 1
fi

# Función para verificar comandos
check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $1 encontrado"
        return 0
    else
        echo -e "  ${RED}✗${NC} $1 no encontrado"
        return 1
    fi
}

# ============================================
# PASO 1: Verificar dependencias del sistema
# ============================================
echo -e "${YELLOW}[1/5]${NC} Verificando dependencias del sistema..."

NEED_INSTALL=false

if ! check_command python3; then
    NEED_INSTALL=true
fi

if ! check_command ffmpeg; then
    NEED_INSTALL=true
fi

if ! check_command ffprobe; then
    NEED_INSTALL=true
fi

# ============================================
# PASO 2: Instalar dependencias faltantes
# ============================================
echo ""
echo -e "${YELLOW}[2/5]${NC} Instalando dependencias del sistema..."

# Detectar el gestor de paquetes
if command -v apt &> /dev/null; then
    echo "  Detectado: apt (Ubuntu/Debian/Zorin)"
    sudo apt update
    sudo apt install -y python3 python3-pip python3-gi python3-gi-cairo \
        gir1.2-gtk-4.0 gir1.2-adw-1 ffmpeg libadwaita-1-0
elif command -v dnf &> /dev/null; then
    echo "  Detectado: dnf (Fedora)"
    sudo dnf install -y python3 python3-pip python3-gobject gtk4 \
        libadwaita ffmpeg
elif command -v pacman &> /dev/null; then
    echo "  Detectado: pacman (Arch)"
    sudo pacman -S --noconfirm python python-pip python-gobject gtk4 \
        libadwaita ffmpeg
else
    echo -e "${RED}Error: Gestor de paquetes no soportado${NC}"
    echo "Instala manualmente: python3, python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1, ffmpeg"
    exit 1
fi

echo -e "  ${GREEN}✓${NC} Dependencias instaladas"

# ============================================
# PASO 3: Verificar GTK4 y Libadwaita
# ============================================
echo ""
echo -e "${YELLOW}[3/5]${NC} Verificando GTK4 y Libadwaita..."

python3 -c "
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
print('  ✓ GTK4 versión:', Gtk.MAJOR_VERSION, '.', Gtk.MINOR_VERSION, sep='')
print('  ✓ Libadwaita disponible')
" 2>/dev/null || {
    echo -e "${RED}Error: GTK4 o Libadwaita no están disponibles${NC}"
    exit 1
}

# ============================================
# PASO 4: Hacer ejecutable el script
# ============================================
echo ""
echo -e "${YELLOW}[4/5]${NC} Configurando la aplicación..."

chmod +x "$SCRIPT_DIR/sonifylab_gtk.py"
echo -e "  ${GREEN}✓${NC} Archivo ejecutable configurado"

# ============================================
# PASO 5: Crear entrada en el menú
# ============================================
echo ""
echo -e "${YELLOW}[5/5]${NC} Creando entrada en el menú de aplicaciones..."

# Crear directorio si no existe
mkdir -p "$HOME/.local/share/applications"

# Crear archivo .desktop
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=SonifyLab Pro
Comment=Conversor de audio profesional (GTK4)
Exec=python3 "$SCRIPT_DIR/sonifylab_gtk.py"
Icon=audio-x-generic
Terminal=false
Type=Application
Categories=AudioVideo;Audio;AudioVideoEditing;GTK;
Keywords=audio;converter;mp3;wav;flac;ffmpeg;
StartupWMClass=com.discodiski.sonifylab
EOF

chmod +x "$DESKTOP_FILE"

# Actualizar base de datos de aplicaciones
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

echo -e "  ${GREEN}✓${NC} Acceso directo creado en el menú"

# ============================================
# RESUMEN FINAL
# ============================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       ¡Instalación completada con éxito!           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Puedes ejecutar $APP_NAME de dos formas:"
echo ""
echo -e "  ${BLUE}1.${NC} Desde el menú de aplicaciones (busca 'SonifyLab')"
echo ""
echo -e "  ${BLUE}2.${NC} Desde terminal:"
echo -e "     python3 $SCRIPT_DIR/sonifylab_gtk.py"
echo ""
echo -e "${YELLOW}Nota:${NC} Esta versión usa GTK4 + Libadwaita para un look nativo."
echo ""
