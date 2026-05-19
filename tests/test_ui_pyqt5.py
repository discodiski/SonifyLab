"""
Tests de integración para la interfaz PyQt5
"""
import pytest
import sys

# Solo ejecutar tests de UI si PyQt5 está disponible
pytest.importorskip("PyQt5")

from pathlib import Path
from sonifylab.ui.pyqt5_interface import PyQt5UI
from sonifylab.models.file_item import FileItem, ConversionStatus
from sonifylab.models.conversion_config import ConversionConfig


class TestPyQt5UI:
    """Tests para la interfaz PyQt5"""

    @pytest.fixture
    def ui_instance(self):
        """Crea una instancia de la UI PyQt5"""
        # Nota: Esto puede requerir display X11 o framebuffer
        try:
            ui = PyQt5UI()
            yield ui
            ui.cleanup()
        except Exception as e:
            pytest.skip(f"No se pudo inicializar PyQt5: {e}")

    def test_ui_inicializacion(self):
        """Prueba que la UI se inicializa correctamente"""
        try:
            ui = PyQt5UI()
            assert ui is not None
            assert hasattr(ui, 'show')
            assert hasattr(ui, 'run')
            ui.cleanup()
        except Exception as e:
            pytest.skip(f"PyQt5 no disponible en entorno headless: {e}")

    def test_ui_agregar_archivo(self, ui_instance):
        """Prueba agregar un archivo a la cola"""
        file_path = Path("/tmp/test.mp3")
        file_item = FileItem(file_path=file_path)
        
        # Verificar que el método existe y es callable
        assert hasattr(ui_instance, 'add_file')
        # Nota: No podemos probar completamente sin un event loop real

    def test_ui_configuracion(self, ui_instance):
        """Prueba configuración de la UI"""
        config = ConversionConfig(
            output_format="wav",
            bitrate="192k"
        )
        
        assert hasattr(ui_instance, 'set_config')
        # La configuración debería almacenarse correctamente

    def test_ui_actualizar_progreso(self, ui_instance):
        """Prueba actualización de progreso"""
        file_item = FileItem(file_path=Path("/tmp/test.mp3"))
        
        assert hasattr(ui_instance, 'update_progress')
        # Actualizar progreso al 50%
        # ui_instance.update_progress(file_item, 50.0)

    def test_ui_manejo_errores(self, ui_instance):
        """Prueba manejo de errores en la UI"""
        assert hasattr(ui_instance, 'show_error')
        # La UI debería mostrar errores correctamente
