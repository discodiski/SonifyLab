"""
Configuración de conversión de audio.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ConversionConfig:
    """
    Configuración para la conversión de archivos de audio.
    
    Attributes:
        output_format: Formato de salida (mp3, wav, flac, etc.)
        bitrate: Bitrate de salida (ej: '192k')
        output_folder: Carpeta donde se guardarán los archivos convertidos
        overwrite: Si True, sobrescribe archivos existentes
        max_concurrent_processes: Número máximo de procesos simultáneos
    """
    output_format: str = "mp3"
    bitrate: str = "192k"
    output_folder: str = ""
    overwrite: bool = False
    max_concurrent_processes: int = 1
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Valida la configuración actual.
        
        Returns:
            Tuple con (es_valido, mensaje_error)
        """
        if not self.output_folder:
            return False, "No se ha seleccionado una carpeta de salida"
        
        if not self.output_format:
            return False, "El formato de salida no es válido"
        
        if not self.bitrate:
            return False, "El bitrate no es válido"
        
        return True, None
    
    def get_output_path(self, input_path: str) -> str:
        """
        Genera la ruta de salida para un archivo dado.
        
        Args:
            input_path: Ruta del archivo de entrada
            
        Returns:
            Ruta completa del archivo de salida
        """
        import os
        from pathlib import Path
        
        input_file = Path(input_path)
        output_file = input_file.stem + f".{self.output_format}"
        return str(Path(self.output_folder) / output_file)
