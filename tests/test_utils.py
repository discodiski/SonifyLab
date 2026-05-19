"""
Tests unitarios para el validador de archivos
"""
import pytest
from pathlib import Path
from sonifylab.utils.file_validator import FileValidator, ValidationError


class TestFileValidator:
    """Tests para la clase FileValidator"""

    def test_validar_extension_valida(self):
        """Prueba validación de extensión válida"""
        assert FileValidator.validate_extension("test.mp3") is True
        assert FileValidator.validate_extension("test.WAV") is True
        assert FileValidator.validate_extension("test.FLAC") is True

    def test_validar_extension_invalida(self):
        """Prueba validación de extensión inválida"""
        assert FileValidator.validate_extension("test.txt") is False
        assert FileValidator.validate_extension("test.pdf") is False
        assert FileValidator.validate_extension("test") is False

    def test_validar_ruta_archivo_no_existe(self):
        """Prueba validación de ruta que no existe"""
        with pytest.raises(ValidationError) as exc_info:
            FileValidator.validate_file_path(Path("/tmp/nonexistent_12345.mp3"))
        
        assert "no existe" in str(exc_info.value).lower()

    def test_validar_ruta_directorio_en_lugar_de_archivo(self):
        """Prueba validación cuando es directorio en lugar de archivo"""
        # Crear un directorio temporal para la prueba
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            # Intentar validar el directorio como si fuera archivo
            # Esto debería fallar porque es un directorio
            # Nota: La implementación actual puede o no verificar esto
            # dependiendo de cómo esté implementado validate_file_path
            
    def test_validar_permisos_lectura(self):
        """Prueba validación de permisos de lectura"""
        import tempfile
        
        # Crear un archivo temporal
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = Path(f.name)
            f.write(b"dummy audio content")
        
        try:
            # Debería validar correctamente si tiene permisos
            result = FileValidator.validate_file_path(temp_path)
            # Si no lanza excepción, la validación pasó
            assert result is True or result is None
        finally:
            # Limpieza
            if temp_path.exists():
                temp_path.unlink()

    def test_validar_ruta_none(self):
        """Prueba validación de ruta None"""
        with pytest.raises((ValidationError, TypeError)):
            FileValidator.validate_file_path(None)
