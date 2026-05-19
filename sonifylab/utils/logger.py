"""
Sistema de logging para conversiones.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene una instancia de logger configurada.
    
    Args:
        name: Nombre del logger (usualmente __name__)
        
    Returns:
        Instancia de logging.Logger
    """
    return logging.getLogger(name)


@dataclass
class ConversionRecord:
    """Registro de una conversión completada."""
    timestamp: str
    input_file: str
    output_file: str
    format: str
    bitrate: str
    duration: float
    success: bool
    error_message: Optional[str] = None


class ConversionLogger:
    """
    Maneja el registro de conversiones en archivo y logs del sistema.
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Inicializa el logger.
        
        Args:
            log_dir: Directorio para guardar logs (por defecto, directorio actual)
        """
        self.log_dir = log_dir or Path.cwd()
        self.log_file = self.log_dir / 'conversion.log'
        self.history_file = self.log_dir / 'conversion_history.jsonl'
        
        # Configurar logging estándar
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura el logging del sistema."""
        logging.basicConfig(
            filename=str(self.log_file),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def log_conversion(
        self,
        input_file: str,
        output_file: str,
        output_format: str,
        bitrate: str,
        duration: float,
        success: bool,
        error_message: Optional[str] = None
    ):
        """
        Registra una conversión completada.
        
        Args:
            input_file: Ruta del archivo de entrada
            output_file: Ruta del archivo de salida
            output_format: Formato de salida
            bitrate: Bitrate utilizado
            duration: Duración de la conversión en segundos
            success: Si la conversión fue exitosa
            error_message: Mensaje de error si hubo uno
        """
        record = ConversionRecord(
            timestamp=datetime.now().isoformat(),
            input_file=input_file,
            output_file=output_file,
            format=output_format,
            bitrate=bitrate,
            duration=duration,
            success=success,
            error_message=error_message
        )
        
        # Guardar en archivo JSONL
        self._save_record(record)
        
        # Log estándar
        if success:
            self.logger.info(f"Conversión exitosa: {input_file} -> {output_file}")
        else:
            self.logger.error(f"Conversión fallida: {input_file} - {error_message}")
    
    def _save_record(self, record: ConversionRecord):
        """Guarda un registro en el archivo JSONL."""
        try:
            with open(self.history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(record)) + '\n')
        except IOError as e:
            self.logger.error(f"Error al guardar registro: {e}")
    
    def get_history(
        self, 
        limit: int = 100,
        success_only: bool = False
    ) -> List[Dict]:
        """
        Obtiene el historial de conversiones.
        
        Args:
            limit: Número máximo de registros a retornar
            success_only: Si True, solo retorna conversiones exitosas
            
        Returns:
            Lista de registros de conversión
        """
        records = []
        
        if not self.history_file.exists():
            return records
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        if success_only and not record.get('success', False):
                            continue
                        records.append(record)
        except (IOError, json.JSONDecodeError) as e:
            self.logger.error(f"Error al leer historial: {e}")
            return []
        
        # Ordenar por timestamp descendente y limitar
        records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return records[:limit]
    
    def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas de conversiones.
        
        Returns:
            Diccionario con estadísticas
        """
        history = self.get_history(limit=10000)  # Últimas 10000 conversiones
        
        if not history:
            return {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0.0
            }
        
        total = len(history)
        successful = sum(1 for r in history if r.get('success', False))
        failed = total - successful
        
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0.0
        }
    
    def clear_history(self):
        """Limpia el historial de conversiones."""
        if self.history_file.exists():
            try:
                self.history_file.unlink()
                self.logger.info("Historial de conversiones limpiado")
            except IOError as e:
                self.logger.error(f"Error al limpiar historial: {e}")
