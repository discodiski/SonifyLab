"""
Utilidades para trabajar con FFmpeg.
"""

import subprocess
import logging
from typing import Optional
from pathlib import Path


class FFmpegUtils:
    """
    Clase utilitaria para operaciones con FFmpeg.
    
    Proporciona métodos estáticos para verificar la disponibilidad de FFmpeg,
    obtener duración de archivos y otras operaciones comunes.
    """
    
    @staticmethod
    def is_available() -> bool:
        """
        Verifica si FFmpeg está instalado y accesible.
        
        Returns:
            True si FFmpeg está disponible, False en caso contrario
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    @staticmethod
    def is_ffprobe_available() -> bool:
        """
        Verifica si ffprobe está instalado y accesible.
        
        Returns:
            True si ffprobe está disponible, False en caso contrario
        """
        try:
            result = subprocess.run(
                ['ffprobe', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    @staticmethod
    def get_duration(file_path: str) -> float:
        """
        Obtiene la duración de un archivo de audio en segundos.
        
        Args:
            file_path: Ruta al archivo de audio
            
        Returns:
            Duración en segundos, o 0 si hubo un error
        """
        try:
            result = subprocess.run(
                [
                    'ffprobe', 
                    '-v', 'error', 
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    file_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            if result.stdout.strip():
                return float(result.stdout.strip())
            return 0.0
            
        except (subprocess.SubprocessError, FileNotFoundError, ValueError) as e:
            logging.error(f"Error al obtener la duración del archivo {file_path}: {e}")
            return 0.0
    
    @staticmethod
    def build_conversion_command(
        input_file: str,
        output_file: str,
        bitrate: str,
        overwrite: bool = False
    ) -> list[str]:
        """
        Construye el comando de conversión para FFmpeg.
        
        Args:
            input_file: Ruta del archivo de entrada
            output_file: Ruta del archivo de salida
            bitrate: Bitrate deseado (ej: '192k')
            overwrite: Si True, sobrescribe el archivo de salida si existe
            
        Returns:
            Lista de argumentos para subprocess
        """
        command = [
            'ffmpeg',
            '-i', input_file,
            '-b:a', bitrate,
            '-progress', 'pipe:1',
        ]
        
        if overwrite:
            command.append('-y')
        
        command.append(output_file)
        
        return command
    
    @staticmethod
    def check_requirements() -> tuple[bool, Optional[str]]:
        """
        Verifica que todos los requisitos de FFmpeg estén disponibles.
        
        Returns:
            Tuple con (es_valido, mensaje_error)
        """
        if not FFmpegUtils.is_available():
            return False, "FFmpeg no está instalado o no es accesible desde el PATH"
        
        if not FFmpegUtils.is_ffprobe_available():
            return False, "ffprobe no está instalado (requerido para obtener duración)"
        
        return True, None
