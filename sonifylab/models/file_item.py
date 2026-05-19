"""
Modelo de datos para un archivo en la lista de conversión.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ConversionStatus(Enum):
    """Estados posibles de un archivo en conversión."""
    PENDING = "En espera"
    PROCESSING = "En proceso"
    COMPLETED = "Completado"
    ERROR = "Error"
    CANCELLED = "Cancelado"


@dataclass
class FileItem:
    """
    Representa un archivo en la lista de conversión.
    
    Attributes:
        path: Ruta completa al archivo
        name: Nombre del archivo
        status: Estado actual de la conversión
        progress: Progreso en porcentaje (0-100)
        info: Información adicional (velocidad, tiempo restante, etc.)
        duration: Duración del audio en segundos
        error_message: Mensaje de error si ocurrió alguno
    """
    path: str
    name: str
    status: ConversionStatus = ConversionStatus.PENDING
    progress: float = 0.0
    info: str = ""
    duration: float = 0.0
    error_message: Optional[str] = None
    
    def reset(self):
        """Reinicia el estado del archivo a pendiente."""
        self.status = ConversionStatus.PENDING
        self.progress = 0.0
        self.info = ""
        self.error_message = None
    
    def is_complete(self) -> bool:
        """Verifica si la conversión está completada."""
        return self.status == ConversionStatus.COMPLETED
    
    def has_error(self) -> bool:
        """Verifica si hubo un error en la conversión."""
        return self.status == ConversionStatus.ERROR
