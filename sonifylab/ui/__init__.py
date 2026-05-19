"""
Módulo de interfaces gráficas para SonifyLab Pro.
"""

# Las interfaces se importan condicionalmente según disponibilidad
__all__ = ['get_available_interfaces', 'UI_BACKENDS']

UI_BACKENDS = {
    'pyqt5': 'PyQt5 - Interfaz para Windows',
    'gtk4': 'GTK4 + Libadwaita - Interfaz nativa Linux'
}


def get_available_interfaces() -> list:
    """
    Retorna lista de backends de UI disponibles.
    
    Returns:
        Lista de nombres de backends disponibles
    """
    available = []
    
    # Verificar PyQt5
    try:
        import PyQt5
        available.append('pyqt5')
    except ImportError:
        pass
    
    # Verificar GTK4
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        available.append('gtk4')
    except (ImportError, ValueError):
        pass
    
    return available
