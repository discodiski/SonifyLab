#!/usr/bin/env python3
"""
Punto de entrada principal para SonifyLab Pro.

Este script detecta automáticamente la mejor interfaz disponible
y lanza la aplicación.
"""

import sys
from pathlib import Path

# Añadir el directorio padre al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_pyqt5():
    """Ejecuta la versión PyQt5 (Windows)."""
    from sonifylab.ui.pyqt5_interface import MainWindow
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


def run_gtk4():
    """Ejecuta la versión GTK4 (Linux)."""
    from sonifylab.ui.gtk4_interface import SonifyLabApp
    
    app = SonifyLabApp()
    sys.exit(app.run(sys.argv))


def main():
    """Detecta y ejecuta la mejor interfaz disponible."""
    # Intentar GTK4 primero (preferido en Linux)
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        print("🎨 Usando interfaz GTK4 + Libadwaita")
        run_gtk4()
        return
    except (ImportError, ValueError):
        pass
    
    # Intentar PyQt5
    try:
        import PyQt5
        print("🎨 Usando interfaz PyQt5")
        run_pyqt5()
        return
    except ImportError:
        pass
    
    # Si nada funciona
    print("❌ Error: No se encontró ninguna interfaz gráfica disponible.")
    print("\nInstala una de las siguientes opciones:")
    print("  - GTK4 (Linux): sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1")
    print("  - PyQt5 (Windows): pip install PyQt5")
    sys.exit(1)


if __name__ == '__main__':
    main()
