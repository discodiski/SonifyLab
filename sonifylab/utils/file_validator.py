"""
Validación de archivos de audio.
"""

import os
from pathlib import Path
from typing import List, Optional

from .. import SUPPORTED_FORMATS


class FileValidator:
    """
    Clase utilitaria para validar archivos de audio.
    """
    
    @staticmethod
    def is_audio_file(file_path: str) -> bool:
        """
        Verifica si un archivo es un archivo de audio válido.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            True si es un archivo de audio válido, False en caso contrario
        """
        if not file_path or not os.path.exists(file_path):
            return False
        
        if not os.path.isfile(file_path):
            return False
        
        # Verificar extensión
        extension = Path(file_path).suffix.lower().lstrip('.')
        return extension in SUPPORTED_FORMATS
    
    @staticmethod
    def is_valid_file(file_path: str) -> tuple[bool, Optional[str]]:
        """
        Valida un archivo y retorna mensaje de error si corresponde.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Tuple con (es_valido, mensaje_error)
        """
        if not file_path:
            return False, "La ruta del archivo está vacía"
        
        if not os.path.exists(file_path):
            return False, f"El archivo no existe: {file_path}"
        
        if not os.path.isfile(file_path):
            return False, f"No es un archivo: {file_path}"
        
        extension = Path(file_path).suffix.lower().lstrip('.')
        if extension not in SUPPORTED_FORMATS:
            return False, f"Formato no soportado: .{extension}"
        
        # Verificar permisos de lectura
        if not os.access(file_path, os.R_OK):
            return False, f"No hay permisos de lectura: {file_path}"
        
        return True, None
    
    @staticmethod
    def scan_folder(folder_path: str, recursive: bool = True) -> List[str]:
        """
        Escanea una carpeta en busca de archivos de audio.
        
        Args:
            folder_path: Ruta a la carpeta
            recursive: Si True, escanea subcarpetas recursivamente
            
        Returns:
            Lista de rutas a archivos de audio encontrados
        """
        audio_files = []
        folder = Path(folder_path)
        
        if not folder.exists() or not folder.is_dir():
            return audio_files
        
        pattern = '**/*' if recursive else '*'
        
        for file_path in folder.glob(pattern):
            if file_path.is_file() and FileValidator.is_audio_file(str(file_path)):
                audio_files.append(str(file_path))
        
        return sorted(audio_files)
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """
        Obtiene información básica de un archivo.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Diccionario con información del archivo
        """
        path = Path(file_path)
        
        info = {
            'name': path.name,
            'size': path.stat().st_size if path.exists() else 0,
            'extension': path.suffix.lower().lstrip('.'),
            'path': str(path.absolute()),
            'exists': path.exists(),
            'is_valid': FileValidator.is_audio_file(str(file_path))
        }
        
        # Convertir tamaño a formato legible
        size_mb = info['size'] / (1024 * 1024)
        info['size_formatted'] = f"{size_mb:.2f} MB"
        
        return info
