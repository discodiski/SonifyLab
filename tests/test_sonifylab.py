"""
Tests unitarios para SonifyLab Pro
===================================
Ejecutar con: python -m pytest tests/ -v
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt


# Fixture para la aplicación Qt
@pytest.fixture(scope="session")
def app():
    """Crea una instancia de QApplication para los tests."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    yield application


@pytest.fixture
def main_window(app):
    """Crea una instancia de MainWindow para testing."""
    from SonifyLab import MainWindow
    window = MainWindow()
    yield window
    window.close()


class TestMainWindow:
    """Tests para la ventana principal."""

    def test_window_title(self, main_window):
        """Verifica que el título de la ventana sea correcto."""
        assert main_window.windowTitle() == "SonifyLab Pro"

    def test_initial_state(self, main_window):
        """Verifica el estado inicial de la aplicación."""
        assert main_window.files == []
        assert main_window.output_folder == ''
        assert main_window.bitrate == '192k'
        assert main_window.format == 'mp3'
        assert main_window.is_converting == False
        assert main_window.active_processes == []

    def test_supported_formats(self, main_window):
        """Verifica que todos los formatos soportados estén disponibles."""
        expected_formats = [
            "mp3", "wav", "flac", "aac", "ogg", 
            "m4a", "wma", "opus", "aiff", "alac"
        ]
        combo_items = [
            main_window.format_combo.itemText(i) 
            for i in range(main_window.format_combo.count())
        ]
        assert combo_items == expected_formats

    def test_bitrate_options(self, main_window):
        """Verifica las opciones de bitrate disponibles."""
        expected_bitrates = ["128k", "192k", "256k", "320k"]
        combo_items = [
            main_window.bitrate_combo.itemText(i) 
            for i in range(main_window.bitrate_combo.count())
        ]
        assert combo_items == expected_bitrates

    def test_default_bitrate(self, main_window):
        """Verifica el bitrate por defecto."""
        assert main_window.bitrate_combo.currentText() == "192k"

    def test_default_format(self, main_window):
        """Verifica el formato por defecto."""
        assert main_window.format_combo.currentText() == "mp3"

    def test_table_columns(self, main_window):
        """Verifica las columnas de la tabla de archivos."""
        assert main_window.files_table.columnCount() == 4
        headers = [
            main_window.files_table.horizontalHeaderItem(i).text()
            for i in range(main_window.files_table.columnCount())
        ]
        assert "Archivo" in headers[0]
        assert "Estado" in headers[1]
        assert "Progreso" in headers[2]

    def test_clear_files(self, main_window):
        """Verifica que limpiar archivos funcione correctamente."""
        # Simular archivos añadidos
        main_window.files = ["/path/to/file1.mp3", "/path/to/file2.wav"]
        main_window.files_table.insertRow(0)
        main_window.files_table.insertRow(1)
        
        # Limpiar
        main_window.clear_files()
        
        assert main_window.files == []
        assert main_window.files_table.rowCount() == 0

    def test_validate_inputs_no_files(self, main_window):
        """Verifica validación cuando no hay archivos."""
        main_window.files = []
        # Debería retornar False pero sin mostrar mensaje (mock)
        with patch.object(main_window, 'files', []):
            result = main_window.validate_inputs()
            assert result == False

    def test_max_concurrent_processes(self, main_window):
        """Verifica el cálculo de procesos concurrentes."""
        import os
        expected = max(1, os.cpu_count() - 1)
        assert main_window.max_concurrent_processes == expected


class TestConversionProcess:
    """Tests para el proceso de conversión."""

    def test_ffmpeg_time_parsing(self, app):
        """Verifica el parseo de tiempo de FFmpeg."""
        from SonifyLab import ConversionProcess
        
        process = ConversionProcess(
            index=0,
            input_file="/fake/input.mp3",
            output_file="/fake/output.wav",
            bitrate="192k",
            output_format="wav"
        )
        
        # Test con tiempo normal
        assert process.ffmpeg_time_to_seconds("00:01:30.500") == 90.5
        assert process.ffmpeg_time_to_seconds("01:00:00.000") == 3600.0
        assert process.ffmpeg_time_to_seconds("00:00:00.000") == 0.0

    def test_format_time(self, app):
        """Verifica el formateo de tiempo."""
        from SonifyLab import ConversionProcess
        
        process = ConversionProcess(
            index=0,
            input_file="/fake/input.mp3",
            output_file="/fake/output.wav",
            bitrate="192k",
            output_format="wav"
        )
        
        assert process.format_time(90) == "0:01:30"
        assert process.format_time(3600) == "1:00:00"
        assert process.format_time(0) == "0:00:00"


class TestUtilities:
    """Tests para funciones utilitarias."""

    def test_app_dir_exists(self):
        """Verifica que APP_DIR esté definido correctamente."""
        from SonifyLab import APP_DIR
        assert APP_DIR.exists()
        assert APP_DIR.is_dir()

    def test_supported_formats_constant(self):
        """Verifica la constante SUPPORTED_FORMATS."""
        from SonifyLab import SUPPORTED_FORMATS
        assert len(SUPPORTED_FORMATS) == 10
        assert "mp3" in SUPPORTED_FORMATS
        assert "flac" in SUPPORTED_FORMATS


class TestIntegration:
    """Tests de integración (requieren FFmpeg instalado)."""

    @pytest.mark.skipif(
        os.system("which ffmpeg > /dev/null 2>&1") != 0,
        reason="FFmpeg no está instalado"
    )
    def test_check_ffmpeg(self, main_window):
        """Verifica la detección de FFmpeg."""
        assert main_window.check_ffmpeg() == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
