#!/bin/bash
# ============================================
# SonifyLab Pro - Instalador para Linux
# ============================================
# Autor: Discaury Salas
# Compatible con: Ubuntu, Zorin OS, Linux Mint, Debian
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

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       ${GREEN}$APP_NAME - Instalador${BLUE}            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
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

if ! check_command pip3 && ! check_command pip; then
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
if [ "$NEED_INSTALL" = true ]; then
    echo ""
    echo -e "${YELLOW}[2/5]${NC} Instalando dependencias del sistema..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv ffmpeg
else
    echo ""
    echo -e "${YELLOW}[2/5]${NC} Todas las dependencias del sistema están instaladas"
fi

# ============================================
# PASO 3: Crear entorno virtual
# ============================================
echo ""
echo -e "${YELLOW}[3/5]${NC} Configurando entorno virtual de Python..."

cd "$SCRIPT_DIR"

if [ -d "venv" ]; then
    echo "  Actualizando entorno virtual existente..."
else
    echo "  Creando nuevo entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
source venv/bin/activate

# ============================================
# PASO 4: Instalar dependencias de Python
# ============================================
echo ""
echo -e "${YELLOW}[4/5]${NC} Instalando dependencias de Python..."

pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo -e "  ${GREEN}✓${NC} PyQt5 instalado correctamente"

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
Comment=Herramienta de conversión de audio por lotes
Exec=bash -c 'cd "$SCRIPT_DIR" && source venv/bin/activate && python3 SonifyLab.py'
Icon=$SCRIPT_DIR/icono.png
Terminal=false
Type=Application
Categories=AudioVideo;Audio;AudioVideoEditing;
Keywords=audio;converter;mp3;wav;flac;ffmpeg;
StartupWMClass=SonifyLab Pro
EOF

# Hacer ejecutable
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
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     ¡Instalación completada con éxito!     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Puedes ejecutar $APP_NAME de dos formas:"
echo ""
echo -e "  ${BLUE}1.${NC} Desde el menú de aplicaciones (busca 'SonifyLab')"
echo ""
echo -e "  ${BLUE}2.${NC} Desde terminal:"
echo -e "     cd $SCRIPT_DIR"
echo -e "     source venv/bin/activate"
echo -e "     python3 SonifyLab.py"
echo ""
echo -e "${YELLOW}Nota:${NC} Si no aparece en el menú, cierra sesión y vuelve a iniciar."
echo ""
