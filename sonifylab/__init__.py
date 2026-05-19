"""
SonifyLab Pro - Herramienta de conversión de audio por lotes
=============================================================

Una aplicación de escritorio profesional para convertir archivos de audio
entre múltiples formatos utilizando FFmpeg como motor de conversión.

Autor: Discaury Salas
Licencia: GPL-3.0
Repositorio: https://github.com/discodiski/SonifyLab
"""

__version__ = "2.1.0"
__author__ = "Discaury Salas"
__app_name__ = "SonifyLab Pro"

# Constantes compartidas
SUPPORTED_FORMATS = [
    "mp3", "wav", "flac", "aac", "ogg", "m4a", "wma", "opus", "aiff", "alac"
]

BITRATE_OPTIONS = ["128k", "192k", "256k", "320k"]

DEFAULT_BITRATE = "192k"
DEFAULT_FORMAT = "mp3"
