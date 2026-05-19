"""
Módulo core con la lógica de conversión de audio.
"""

from .converter import AudioConverter
from .ffmpeg_utils import FFmpegUtils

__all__ = ['AudioConverter', 'FFmpegUtils']
