"""
Tests unitarios para el modelo FileItem
"""
import pytest
from pathlib import Path
from sonifylab.models.file_item import FileItem, ConversionStatus


class TestFileItem:
    """Tests para la clase FileItem"""

    def test_creacion_fileitem_valido(self):
        """Prueba creación de un FileItem válido"""
        file_path = Path("/tmp/test.mp3")
        item = FileItem(file_path=file_path)
        
        assert item.file_path == file_path
        assert item.status == ConversionStatus.PENDING
        assert item.progress == 0.0
        assert item.error_message is None
        assert item.output_path is None

    def test_fileitem_con_estado_personalizado(self):
        """Prueba creación con estado personalizado"""
        file_path = Path("/tmp/test.wav")
        item = FileItem(
            file_path=file_path,
            status=ConversionStatus.PROCESSING,
            progress=50.0
        )
        
        assert item.status == ConversionStatus.PROCESSING
        assert item.progress == 50.0

    def test_fileitem_con_error(self):
        """Prueba FileItem con mensaje de error"""
        file_path = Path("/tmp/invalid.mp3")
        error_msg = "Archivo no encontrado"
        
        item = FileItem(
            file_path=file_path,
            status=ConversionStatus.ERROR,
            error_message=error_msg
        )
        
        assert item.status == ConversionStatus.ERROR
        assert item.error_message == error_msg

    def test_fileitem_con_output_path(self):
        """Prueba FileItem con ruta de salida"""
        input_path = Path("/tmp/input.mp3")
        output_path = Path("/tmp/output.wav")
        
        item = FileItem(
            file_path=input_path,
            output_path=output_path,
            status=ConversionStatus.COMPLETED,
            progress=100.0
        )
        
        assert item.output_path == output_path
        assert item.status == ConversionStatus.COMPLETED
        assert item.progress == 100.0

    def test_fileitem_repr(self):
        """Prueba representación string de FileItem"""
        file_path = Path("/tmp/test.mp3")
        item = FileItem(file_path=file_path)
        
        repr_str = repr(item)
        assert "test.mp3" in repr_str
        assert "PENDING" in repr_str
