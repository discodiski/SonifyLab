"""
Motor de conversión de audio agnóstico a la UI.

Este módulo proporciona una interfaz síncrona para conversión de audio.
La capa de presentación (UI) es responsable de ejecutar este código
en hilos separados para mantener la interfaz responsiva.
"""

import subprocess
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
from pathlib import Path

from ..models.file_item import FileItem, ConversionStatus
from .ffmpeg_utils import FFmpegUtils


class AudioConverter:
    """
    Clase que maneja la conversión de archivos de audio utilizando FFmpeg.
    
    Esta clase es completamente agnóstica a la interfaz gráfica y puede ser 
    utilizada tanto con PyQt5, GTK4, o cualquier otra UI.
    
    NOTA IMPORTANTE:
    - Los métodos de esta clase son BLOQUEANTES por diseño
    - La UI debe ejecutar start() en un hilo separado
    - Los callbacks permiten comunicación thread-safe con la UI
    
    Attributes:
        file_item: Elemento de archivo a convertir
        output_file: Ruta del archivo de salida
        bitrate: Bitrate deseado
        overwrite: Si True, sobrescribe archivos existentes
        process: Proceso subprocess activo
        start_time: Tiempo de inicio de la conversión
        
    Callbacks (se asignan externamente para comunicación con la UI):
        progress_callback: Callable[[int, float], None] - (index, progreso)
        status_callback: Callable[[int, str], None] - (index, estado)
        error_callback: Callable[[int, str], None] - (index, mensaje_error)
        info_callback: Callable[[int, str], None] - (index, info_adicional)
        finished_callback: Callable[[int, int], None] - (index, codigo_retorno)
    """
    
    def __init__(
        self,
        file_item: FileItem,
        output_file: str,
        bitrate: str,
        overwrite: bool = False
    ):
        """
        Inicializa el convertidor de audio.
        
        Args:
            file_item: Elemento de archivo a convertir
            output_file: Ruta del archivo de salida
            bitrate: Bitrate deseado (ej: '192k')
            overwrite: Si True, sobrescribe archivos existentes
        """
        self.file_item = file_item
        self.output_file = output_file
        self.bitrate = bitrate
        self.overwrite = overwrite
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[datetime] = None
        
        # Callbacks para comunicación con la UI (thread-safe)
        self.progress_callback: Optional[Callable[[int, float], None]] = None
        self.status_callback: Optional[Callable[[int, str], None]] = None
        self.error_callback: Optional[Callable[[int, str], None]] = None
        self.info_callback: Optional[Callable[[int, str], None]] = None
        self.finished_callback: Optional[Callable[[int, int], None]] = None
    
    def start(self, index: int = 0):
        """
        Inicia el proceso de conversión (MÉTODO BLOQUEANTE).
        
        Este método ejecuta FFmpeg y espera hasta que termine.
        Debe ser llamado desde un hilo separado para no bloquear la UI.
        
        Args:
            index: Índice del archivo en la lista de la UI
            
        Raises:
            Exception: Si ocurre un error durante la conversión
        """
        command = FFmpegUtils.build_conversion_command(
            self.file_item.path,
            self.output_file,
            self.bitrate,
            self.overwrite
        )
        
        try:
            logging.info(f"Iniciando conversión: {self.file_item.path} -> {self.output_file}")
            
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Redirigir stderr a stdout para parsing
                universal_newlines=True,
                bufsize=1
            )
            
            self.file_item.status = ConversionStatus.PROCESSING
            self._emit_status(index, "En proceso")
            
            self.start_time = datetime.now()
            
            # Leer output en tiempo real (bloqueante pero permite updates vía callbacks)
            self._read_output(index)
            
        except Exception as e:
            error_msg = f"Error al iniciar conversión: {str(e)}"
            logging.error(error_msg)
            self.file_item.status = ConversionStatus.ERROR
            self.file_item.error_message = error_msg
            self._emit_error(index, error_msg)
            raise
    
    def _emit_status(self, index: int, status: str):
        """Emite actualización de estado si el callback está definido."""
        if self.status_callback:
            self.status_callback(index, status)
    
    def _emit_progress(self, index: int, progress: float):
        """Emite actualización de progreso si el callback está definido."""
        if self.progress_callback:
            self.progress_callback(index, progress)
    
    def _emit_info(self, index: int, info: str):
        """Emite información adicional si el callback está definido."""
        if self.info_callback:
            self.info_callback(index, info)
    
    def _emit_error(self, index: int, error: str):
        """Emite error si el callback está definido."""
        if self.error_callback:
            self.error_callback(index, error)
    
    def _emit_finished(self, index: int, return_code: int):
        """Emite finalización si el callback está definido."""
        if self.finished_callback:
            self.finished_callback(index, return_code)
    
    def _read_output(self, index: int):
        """
        Lee y procesa la salida de FFmpeg línea por línea.
        
        Args:
            index: Índice del archivo en la UI
        """
        if not self.process or not self.process.stdout:
            return
        
        for line in self.process.stdout:
            line = line.strip()
            if line:
                self._parse_progress(line, index)
        
        # Esperar a que termine el proceso y obtener código de retorno
        return_code = self.process.wait()
        self._handle_finished(index, return_code)
    
    def _parse_progress(self, line: str, index: int):
        """
        Analiza la línea de progreso de FFmpeg y emite actualizaciones.
        
        Args:
            line: Línea de salida de FFmpeg
            index: Índice del archivo
        """
        if line.startswith('out_time='):
            out_time_str = line.split('=')[1]
            out_time = self._ffmpeg_time_to_seconds(out_time_str)
            
            if self.file_item.duration > 0:
                progress = (out_time / self.file_item.duration) * 100
                progress = min(100.0, max(0.0, progress))  # Clamp entre 0-100
                
                self.file_item.progress = progress
                self._emit_progress(index, progress)
                
                # Calcular velocidad y tiempo restante
                if self.start_time:
                    elapsed_time = (datetime.now() - self.start_time).total_seconds()
                    speed = out_time / elapsed_time if elapsed_time > 0 else 0
                    remaining_time = (self.file_item.duration - out_time) / speed if speed > 0 and speed < 100 else 0
                    
                    info = f"Velocidad: {speed:.2f}x, Restante: {self._format_time(remaining_time)}"
                    self.file_item.info = info
                    self._emit_info(index, info)
                        
        elif line.startswith('progress='):
            if line.split('=')[1] == 'end':
                self.file_item.progress = 100.0
                self._emit_progress(index, 100.0)
                self._emit_info(index, "Conversión completada")
    
    def _handle_finished(self, index: int, return_code: int):
        """
        Maneja la finalización del proceso de conversión.
        
        Args:
            index: Índice del archivo
            return_code: Código de retorno de FFmpeg (0 = éxito)
        """
        if return_code == 0:
            self.file_item.status = ConversionStatus.COMPLETED
            self.file_item.progress = 100.0
            self._emit_status(index, "Completado")
            self._emit_progress(index, 100.0)
            logging.info(f"Conversión completada: {self.file_item.path}")
        else:
            self.file_item.status = ConversionStatus.ERROR
            error_message = "Error en FFmpeg (código {})".format(return_code)
            if self.process and self.process.stderr:
                error_message = self.process.stderr.read().strip() or error_message
            self.file_item.error_message = error_message
            logging.error(f"Error en conversión {self.file_item.path}: {error_message}")
            self._emit_status(index, "Error")
            self._emit_error(index, error_message)
        
        self._emit_finished(index, return_code)
    
    @staticmethod
    def _ffmpeg_time_to_seconds(time_str: str) -> float:
        """
        Convierte el formato de tiempo de FFmpeg a segundos.
        
        Args:
            time_str: Tiempo en formato HH:MM:SS.microseconds
            
        Returns:
            Tiempo en segundos como float
        """
        try:
            if '.' in time_str:
                hms, ms = time_str.split('.')
                ms = float('0.' + ms)
            else:
                hms = time_str
                ms = 0.0
            
            h, m, s = map(int, hms.split(':'))
            total_seconds = h * 3600 + m * 60 + s + ms
            return total_seconds
        except (ValueError, IndexError):
            return 0.0
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """
        Formatea segundos como string legible (H:MM:SS).
        
        Args:
            seconds: Segundos a formatear
            
        Returns:
            String en formato H:MM:SS o MM:SS
        """
        return str(timedelta(seconds=int(seconds)))
    
    def stop(self):
        """
        Detiene el proceso de conversión si está en ejecución.
        
        Intenta terminar gracefulmente, si no responde después de 5 segundos,
        fuerza la terminación del proceso.
        """
        if self.process and self.process.poll() is None:
            logging.info("Deteniendo conversión...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logging.warning("El proceso no respondió, forzando terminación")
                self.process.kill()
            
            self.file_item.status = ConversionStatus.CANCELLED
            self.file_item.progress = 0.0
            self.file_item.info = "Cancelado por el usuario"
            logging.info(f"Conversión cancelada: {self.file_item.path}")
