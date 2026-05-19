"""
Clase base para interfaces gráficas de SonifyLab.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

from ..models.file_item import FileItem
from ..models.conversion_config import ConversionConfig


class UIBase(ABC):
    """
    Clase abstracta base para todas las interfaces de SonifyLab.
    
    Define la interfaz común que deben implementar PyQt5 y GTK4.
    """
    
    @abstractmethod
    def show(self):
        """Muestra la ventana principal."""
        pass
    
    @abstractmethod
    def hide(self):
        """Oculta la ventana principal."""
        pass
    
    @abstractmethod
    def close(self):
        """Cierra la aplicación."""
        pass
    
    @abstractmethod
    def add_files(self, file_paths: List[str]):
        """
        Añade archivos a la lista.
        
        Args:
            file_paths: Lista de rutas de archivos
        """
        pass
    
    @abstractmethod
    def remove_selected_files(self):
        """Elimina los archivos seleccionados de la lista."""
        pass
    
    @abstractmethod
    def clear_files(self):
        """Limpia todos los archivos de la lista."""
        pass
    
    @abstractmethod
    def update_file_status(self, index: int, status: str):
        """
        Actualiza el estado de un archivo.
        
        Args:
            index: Índice del archivo
            status: Nuevo estado
        """
        pass
    
    @abstractmethod
    def update_file_progress(self, index: int, progress: float):
        """
        Actualiza el progreso de un archivo.
        
        Args:
            index: Índice del archivo
            progress: Progreso (0-100)
        """
        pass
    
    @abstractmethod
    def update_file_info(self, index: int, info: str):
        """
        Actualiza información adicional de un archivo.
        
        Args:
            index: Índice del archivo
            info: Información adicional
        """
        pass
    
    @abstractmethod
    def set_overall_progress(self, progress: float):
        """
        Actualiza la barra de progreso general.
        
        Args:
            progress: Progreso total (0-100)
        """
        pass
    
    @abstractmethod
    def log_message(self, message: str):
        """
        Añade un mensaje al registro.
        
        Args:
            message: Mensaje a mostrar
        """
        pass
    
    @abstractmethod
    def show_error(self, title: str, message: str):
        """
        Muestra un diálogo de error.
        
        Args:
            title: Título del diálogo
            message: Mensaje de error
        """
        pass
    
    @abstractmethod
    def show_about(self):
        """Muestra el diálogo 'Acerca de'."""
        pass
    
    @abstractmethod
    def set_conversion_mode(self, converting: bool):
        """
        Cambia entre modo normal y modo conversión.
        
        Args:
            converting: True si está convirtiendo, False en caso contrario
        """
        pass
    
    @abstractmethod
    def get_config(self) -> ConversionConfig:
        """
        Obtiene la configuración actual de la UI.
        
        Returns:
            Objeto ConversionConfig con la configuración actual
        """
        pass
    
    @abstractmethod
    def set_config(self, config: ConversionConfig):
        """
        Establece la configuración desde código.
        
        Args:
            config: Objeto ConversionConfig con la configuración
        """
        pass
