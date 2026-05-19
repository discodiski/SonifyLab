"""
Interfaz gráfica PyQt5 para SonifyLab Pro.

Esta implementación utiliza QThread para ejecutar conversiones en segundo plano
sin bloquear la interfaz gráfica, conectándose al AudioConverter del core.
"""

import os
import logging
from typing import List, Optional
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QProgressBar,
    QTextEdit, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox,
    QComboBox, QAction, QLineEdit, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSpacerItem,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

from ..models.file_item import FileItem, ConversionStatus
from ..models.conversion_config import ConversionConfig
from ..core.converter import AudioConverter
from .base import UIBase


# Constantes de formatos y bitrates
SUPPORTED_FORMATS = [
    "mp3", "wav", "flac", "aac", "ogg", "m4a", "wma", "opus", "aiff", "alac"
]
BITRATE_OPTIONS = ["128k", "192k", "256k", "320k"]


class ConversionWorker(QObject):
    """
    Worker que ejecuta la conversión en un hilo separado.
    
    Esta clase envuelve AudioConverter para proporcionar comunicación
    thread-safe con la UI principal mediante señales Qt.
    """
    
    # Señales para comunicación con la UI
    progress_update = pyqtSignal(int, float)  # index, progreso
    status_update = pyqtSignal(int, str)       # index, estado
    error_occurred = pyqtSignal(int, str)      # index, error
    info_update = pyqtSignal(int, str)         # index, info
    finished = pyqtSignal(int, int)            # index, return_code
    
    def __init__(
        self,
        file_item: FileItem,
        output_file: str,
        bitrate: str,
        overwrite: bool,
        index: int
    ):
        super().__init__()
        self.file_item = file_item
        self.output_file = output_file
        self.bitrate = bitrate
        self.overwrite = overwrite
        self.index = index
        self.converter: Optional[AudioConverter] = None
    
    def run(self):
        """Ejecuta la conversión en el hilo del worker."""
        try:
            # Crear instancia del converter
            self.converter = AudioConverter(
                file_item=self.file_item,
                output_file=self.output_file,
                bitrate=self.bitrate,
                overwrite=self.overwrite
            )
            
            # Conectar callbacks a señales Qt
            self.converter.progress_callback = lambda idx, prog: self.progress_update.emit(idx, prog)
            self.converter.status_callback = lambda idx, status: self.status_update.emit(idx, status)
            self.converter.error_callback = lambda idx, err: self.error_occurred.emit(idx, err)
            self.converter.info_callback = lambda idx, info: self.info_update.emit(idx, info)
            self.converter.finished_callback = lambda idx, code: self.finished.emit(idx, code)
            
            # Iniciar conversión (bloqueante, pero estamos en thread separado)
            self.converter.start(index=self.index)
            
        except Exception as e:
            logging.error(f"Error en worker de conversión: {e}")
            self.error_occurred.emit(self.index, str(e))
            self.finished.emit(self.index, -1)
    
    def stop(self):
        """Detiene la conversión actual."""
        if self.converter:
            self.converter.stop()


class PyQt5Interface(QMainWindow):
    """
    Interfaz gráfica principal de SonifyLab usando PyQt5.
    
    Implementa todos los métodos de UIBase y proporciona
    una interfaz moderna y responsiva para conversión de audio por lotes.
    """
    
    def __init__(self, app: QApplication):
        QMainWindow.__init__(self)
        
        self.app = app
        self.files: List[FileItem] = []
        self.config = ConversionConfig()
        self.is_converting = False
        self.active_workers: List[ConversionWorker] = []
        self.active_threads: List[QThread] = []
        self.conversion_queue: List[int] = []  # Índices pendientes
        self.completed_count = 0
        self.failed_indices: List[int] = []
        
        # Configuración de ventana
        self.setWindowTitle("SonifyLab Pro")
        self.resize(1000, 850)
        self.setMinimumSize(800, 700)
        
        # Intentar cargar icono
        icon_path = Path(__file__).parent.parent.parent / "icono.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        self._init_ui()
        self._log_message("SonifyLab Pro iniciado correctamente")
    
    def _init_ui(self):
        """Inicializa la interfaz de usuario."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # ========== MENÚ ==========
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Archivo")
        
        add_folder_action = QAction("📁 Añadir carpeta", self)
        add_folder_action.setShortcut("Ctrl+Shift+O")
        add_folder_action.triggered.connect(self._add_folder)
        file_menu.addAction(add_folder_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("❌ Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        help_menu = menu_bar.addMenu("&Ayuda")
        about_action = QAction("ℹ️ Acerca de", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # ========== ARCHIVOS DE ENTRADA ==========
        files_label = QLabel("📂 Archivos de entrada")
        files_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B;")
        main_layout.addWidget(files_label)
        
        # Tabla de archivos
        self.files_table = QTableWidget(0, 4)
        self.files_table.setHorizontalHeaderLabels(
            ['Archivo', 'Estado', 'Progreso', 'Información']
        )
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.files_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.files_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.files_table.setColumnWidth(2, 150)
        self.files_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.files_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.files_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.files_table.setAlternatingRowColors(True)
        self.files_table.setMinimumHeight(200)
        main_layout.addWidget(self.files_table)
        
        # Botones de archivos
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.add_files_btn = QPushButton("Añadir archivos")
        self.add_files_btn.setToolTip("Seleccionar archivos de audio para convertir (Ctrl+O)")
        self.add_files_btn.setShortcut("Ctrl+O")
        self.add_files_btn.clicked.connect(self._add_files)
        buttons_layout.addWidget(self.add_files_btn)
        
        self.remove_files_btn = QPushButton("Eliminar archivos")
        self.remove_files_btn.setToolTip("Eliminar archivos seleccionados de la lista")
        self.remove_files_btn.clicked.connect(self.remove_selected_files)
        buttons_layout.addWidget(self.remove_files_btn)
        
        self.clear_files_btn = QPushButton("Limpiar lista")
        self.clear_files_btn.setToolTip("Eliminar todos los archivos de la lista")
        self.clear_files_btn.clicked.connect(self.clear_files)
        buttons_layout.addWidget(self.clear_files_btn)
        
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)
        
        # ========== CONFIGURACIÓN ==========
        config_label = QLabel("⚙️ Configuración")
        config_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; margin-top: 10px;")
        main_layout.addWidget(config_label)
        
        # Carpeta de salida
        output_layout = QHBoxLayout()
        output_layout.setSpacing(10)
        output_label = QLabel("Carpeta de salida:")
        output_label.setMinimumWidth(120)
        self.output_line_edit = QLineEdit()
        self.output_line_edit.setPlaceholderText("Selecciona una carpeta donde guardar los archivos convertidos...")
        browse_output_btn = QPushButton("Examinar")
        browse_output_btn.setToolTip("Seleccionar carpeta de destino")
        browse_output_btn.clicked.connect(self._browse_output_folder)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_line_edit)
        output_layout.addWidget(browse_output_btn)
        main_layout.addLayout(output_layout)
        
        # Bitrate y Formato
        config_layout = QHBoxLayout()
        config_layout.setSpacing(20)
        
        bitrate_label = QLabel("Bitrate:")
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(BITRATE_OPTIONS)
        self.bitrate_combo.setCurrentText("192k")
        self.bitrate_combo.setToolTip("Calidad del audio de salida (mayor = mejor calidad, más tamaño)")
        config_layout.addWidget(bitrate_label)
        config_layout.addWidget(self.bitrate_combo)
        
        config_layout.addSpacing(30)
        
        format_label = QLabel("Formato:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(SUPPORTED_FORMATS)
        self.format_combo.setCurrentText("mp3")
        self.format_combo.setToolTip("Formato de audio de salida")
        config_layout.addWidget(format_label)
        config_layout.addWidget(self.format_combo)
        
        config_layout.addStretch()
        main_layout.addLayout(config_layout)
        
        # Opciones adicionales
        options_layout = QHBoxLayout()
        self.overwrite_checkbox = QCheckBox("Sobrescribir archivos existentes")
        self.overwrite_checkbox.setToolTip("Si está marcado, reemplazará archivos con el mismo nombre")
        options_layout.addWidget(self.overwrite_checkbox)
        options_layout.addStretch()
        main_layout.addLayout(options_layout)
        
        # ========== CONVERSIÓN ==========
        conversion_label = QLabel("🚀 Conversión")
        conversion_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; margin-top: 10px;")
        main_layout.addWidget(conversion_label)
        
        # Botones de conversión
        buttons_layout2 = QHBoxLayout()
        buttons_layout2.setSpacing(12)
        
        self.convert_btn = QPushButton("Iniciar Conversión")
        self.convert_btn.setToolTip("Comenzar la conversión de todos los archivos (Ctrl+Enter)")
        self.convert_btn.setShortcut("Ctrl+Return")
        self.convert_btn.clicked.connect(self._start_conversion)
        self.convert_btn.setMinimumHeight(45)
        buttons_layout2.addWidget(self.convert_btn)
        
        self.stop_btn = QPushButton("Detener")
        self.stop_btn.setToolTip("Detener la conversión en curso (Escape)")
        self.stop_btn.setShortcut("Escape")
        self.stop_btn.clicked.connect(self._stop_conversion)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(45)
        buttons_layout2.addWidget(self.stop_btn)
        
        buttons_layout2.addStretch()
        main_layout.addLayout(buttons_layout2)
        
        # Barra de progreso general
        progress_layout = QHBoxLayout()
        progress_label = QLabel("Progreso total:")
        progress_label.setMinimumWidth(100)
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setMinimumHeight(20)
        self.overall_progress_bar.setTextVisible(True)
        self.overall_progress_bar.setFormat("%p%")
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.overall_progress_bar)
        main_layout.addLayout(progress_layout)
        
        # ========== REGISTRO ==========
        log_label = QLabel("📋 Registro de conversión")
        log_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; margin-top: 10px;")
        main_layout.addWidget(log_label)
        
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setMaximumHeight(120)
        self.log_text_edit.setPlaceholderText("Los mensajes de conversión aparecerán aquí...")
        main_layout.addWidget(self.log_text_edit)
        
        # Créditos
        credits_label = QLabel("✨ SonifyLab Pro v1.0.0 — Creado por Discaury Salas")
        credits_label.setAlignment(Qt.AlignCenter)
        credits_label.setStyleSheet("color: #64748B; font-size: 12px; padding: 10px;")
        main_layout.addWidget(credits_label)
        
        # Contenedor principal
        container = QWidget()
        container.setObjectName("centralwidget")
        container.setLayout(main_layout)
        self.setCentralWidget(container)
    
    # ========== Métodos de gestión de archivos ==========
    
    def _add_files(self):
        """Añade archivos seleccionados por el usuario."""
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self, "Selecciona archivos de entrada", "",
            f"Archivos de audio ({' '.join(['*.' + ext for ext in SUPPORTED_FORMATS])})"
        )
        if file_paths:
            self.add_files(file_paths)
    
    def add_files(self, file_paths: List[str]):
        """Implementación de UIBase.add_files"""
        for file_path in file_paths:
            if file_path not in [f.path for f in self.files]:
                if self._is_valid_file(file_path):
                    file_item = FileItem(
                        path=file_path,
                        name=os.path.basename(file_path)
                    )
                    self.files.append(file_item)
                    self._add_file_to_table(file_item, len(self.files) - 1)
        self._log_message(f"{len(file_paths)} archivos añadidos")
    
    def _add_file_to_table(self, file_item: FileItem, index: int):
        """Añade una fila a la tabla para un archivo."""
        row_position = self.files_table.rowCount()
        self.files_table.insertRow(row_position)
        
        file_name_item = QTableWidgetItem(file_item.name)
        status_item = QTableWidgetItem(file_item.status.value)
        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        info_item = QTableWidgetItem("")
        
        self.files_table.setItem(row_position, 0, file_name_item)
        self.files_table.setItem(row_position, 1, status_item)
        self.files_table.setCellWidget(row_position, 2, progress_bar)
        self.files_table.setItem(row_position, 3, info_item)
    
    def _add_folder(self):
        """Añade todos los archivos de audio de una carpeta."""
        folder = QFileDialog.getExistingDirectory(self, "Selecciona carpeta")
        if folder:
            added_count = 0
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(tuple(SUPPORTED_FORMATS)):
                        full_path = os.path.join(root, file)
                        if full_path not in [f.path for f in self.files]:
                            if self._is_valid_file(full_path):
                                file_item = FileItem(
                                    path=full_path,
                                    name=file
                                )
                                self.files.append(file_item)
                                self._add_file_to_table(file_item, len(self.files) - 1)
                                added_count += 1
            
            if added_count > 0:
                QMessageBox.information(
                    self, "Información",
                    f"Se añadieron {added_count} archivos de la carpeta."
                )
                self._log_message(f"Carpeta añadida: {added_count} archivos")
    
    def remove_selected_files(self):
        """Elimina los archivos seleccionados de la lista."""
        selected_rows = set()
        for index in self.files_table.selectionModel().selectedRows():
            selected_rows.add(index.row())
        
        if not selected_rows:
            return
        
        # Eliminar en orden inverso para mantener índices correctos
        for row in sorted(selected_rows, reverse=True):
            if 0 <= row < len(self.files):
                self.files.pop(row)
        
        # Reconstruir tabla
        self.files_table.setRowCount(0)
        for idx, file_item in enumerate(self.files):
            self._add_file_to_table(file_item, idx)
        
        self._log_message(f"{len(selected_rows)} archivos eliminados")
    
    def clear_files(self):
        """Limpia todos los archivos de la lista."""
        if self.is_converting:
            QMessageBox.warning(
                self, "Advertencia",
                "No se puede limpiar la lista mientras hay una conversión en curso."
            )
            return
        
        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Estás seguro de que deseas eliminar todos los archivos?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.files.clear()
            self.files_table.setRowCount(0)
            self._log_message("Lista limpiada")
    
    def _is_valid_file(self, file_path: str) -> bool:
        """Valida que un archivo sea válido."""
        path = Path(file_path)
        if not path.exists():
            self._show_error("Archivo no encontrado", f"El archivo '{file_path}' no existe.")
            return False
        if not path.is_file():
            self._show_error("No es un archivo", f"'{file_path}' no es un archivo válido.")
            return False
        return True
    
    def _browse_output_folder(self):
        """Abre diálogo para seleccionar carpeta de salida."""
        folder = QFileDialog.getExistingDirectory(
            self, "Selecciona carpeta de salida"
        )
        if folder:
            self.output_line_edit.setText(folder)
            self._log_message(f"Carpeta de salida: {folder}")
    
    # ========== Métodos de conversión ==========
    
    def _start_conversion(self):
        """Inicia el proceso de conversión."""
        if self.is_converting:
            return
        
        # Actualizar configuración desde UI
        self.config.output_format = self.format_combo.currentText()
        self.config.bitrate = self.bitrate_combo.currentText()
        self.config.output_folder = self.output_line_edit.text()
        self.config.overwrite = self.overwrite_checkbox.isChecked()
        
        # Validar configuración
        is_valid, error_msg = self.config.validate()
        if not is_valid:
            self._show_error("Configuración inválida", error_msg)
            return
        
        if not self.files:
            self._show_error("Sin archivos", "No hay archivos en la lista para convertir.")
            return
        
        # Verificar FFmpeg
        if not self._check_ffmpeg():
            return
        
        # Preparar conversión
        self.is_converting = True
        self.completed_count = 0
        self.failed_indices = []
        self.conversion_queue = list(range(len(self.files)))
        
        # Resetear estados
        for file_item in self.files:
            file_item.reset()
        
        # Actualizar UI
        self._set_interface_enabled(False)
        self.overall_progress_bar.setValue(0)
        self._log_message("=" * 50)
        self._log_message(f"Iniciando conversión de {len(self.files)} archivos")
        self._log_message(f"Formato: {self.config.output_format}, Bitrate: {self.config.bitrate}")
        self._log_message("=" * 50)
        
        # Iniciar primeros procesos
        self._start_next_processes()
    
    def _start_next_processes(self):
        """Inicia los siguientes procesos en la cola."""
        if not self.conversion_queue or self.is_converting is False:
            return
        
        max_concurrent = max(1, os.cpu_count() - 1)
        
        while self.conversion_queue and len(self.active_workers) < max_concurrent:
            index = self.conversion_queue.pop(0)
            file_item = self.files[index]
            
            # Generar ruta de salida
            output_path = self.config.get_output_path(file_item.path)
            
            # Crear worker y thread
            worker = ConversionWorker(
                file_item=file_item,
                output_file=output_path,
                bitrate=self.config.bitrate,
                overwrite=self.config.overwrite,
                index=index
            )
            
            thread = QThread()
            worker.moveToThread(thread)
            
            # Conectar señales
            worker.progress_update.connect(self._on_worker_progress)
            worker.status_update.connect(self._on_worker_status)
            worker.error_occurred.connect(self._on_worker_error)
            worker.info_update.connect(self._on_worker_info)
            worker.finished.connect(lambda idx, code: self._on_worker_finished(idx, code, thread, worker))
            
            # Conectar inicio
            thread.started.connect(worker.run)
            
            # Guardar referencias
            self.active_workers.append(worker)
            self.active_threads.append(thread)
            
            # Iniciar thread
            thread.start()
            self._log_message(f"Iniciando: {file_item.name}")
    
    def _on_worker_progress(self, index: int, progress: float):
        """Maneja actualización de progreso desde worker."""
        if 0 <= index < len(self.files):
            self.update_file_progress(index, progress)
    
    def _on_worker_status(self, index: int, status: str):
        """Maneja actualización de estado desde worker."""
        if 0 <= index < len(self.files):
            self.update_file_status(index, status)
    
    def _on_worker_error(self, index: int, error: str):
        """Maneja error desde worker."""
        if 0 <= index < len(self.files):
            self.files[index].error_message = error
            self._log_message(f"ERROR en {self.files[index].name}: {error}")
    
    def _on_worker_info(self, index: int, info: str):
        """Maneja información desde worker."""
        if 0 <= index < len(self.files):
            self.update_file_info(index, info)
    
    def _on_worker_finished(self, index: int, return_code: int, thread: QThread, worker: ConversionWorker):
        """Maneja finalización de worker."""
        # Limpiar recursos
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        if thread in self.active_threads:
            self.active_threads.remove(thread)
        
        # Actualizar contadores
        if return_code == 0:
            self.completed_count += 1
            self._log_message(f"Completado: {self.files[index].name}")
        else:
            self.failed_indices.append(index)
        
        # Actualizar progreso general
        total_completed = self.completed_count + len(self.failed_indices)
        overall_progress = (total_completed / len(self.files)) * 100 if self.files else 0
        self.set_overall_progress(overall_progress)
        
        # Detener thread
        thread.quit()
        thread.wait()
        
        # Iniciar siguiente si hay cola
        self._start_next_processes()
        
        # Verificar si terminó todo
        if not self.active_workers and not self.conversion_queue:
            self._conversion_complete()
    
    def _conversion_complete(self):
        """Maneja la finalización de todas las conversiones."""
        self.is_converting = False
        self._set_interface_enabled(True)
        
        total = len(self.files)
        completed = self.completed_count
        failed = len(self.failed_indices)
        
        self._log_message("=" * 50)
        self._log_message(f"Conversión completada")
        self._log_message(f"Total: {total}, Exitosos: {completed}, Fallidos: {failed}")
        self._log_message("=" * 50)
        
        if failed > 0:
            QMessageBox.warning(
                self, "Conversión completada con errores",
                f"Se completaron {completed} de {total} archivos.\n{failed} archivos fallaron."
            )
        else:
            QMessageBox.information(
                self, "Conversión completada",
                f"Todos los archivos ({total}) se convirtieron exitosamente."
            )
    
    def _stop_conversion(self):
        """Detiene todas las conversiones en curso."""
        if not self.is_converting:
            return
        
        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Estás seguro de que deseas detener todas las conversiones en curso?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._log_message("Deteniendo conversiones...")
            
            # Detener workers activos
            for worker in self.active_workers:
                worker.stop()
            
            # Limpiar cola
            self.conversion_queue.clear()
            
            # Marcar como no convirtiendo (pero esperar a que terminen los threads)
            self.is_converting = False
            self._set_interface_enabled(True)
    
    def _set_interface_enabled(self, enabled: bool):
        """Habilita o deshabilita la interfaz durante conversión."""
        self.is_converting = not enabled
        self.add_files_btn.setEnabled(enabled)
        self.remove_files_btn.setEnabled(enabled)
        self.clear_files_btn.setEnabled(enabled)
        self.output_line_edit.setEnabled(enabled)
        self.browse_output_btn = self.findChild(QPushButton, "Examinar") or QPushButton()
        for btn in self.findChildren(QPushButton):
            if btn.text() == "Examinar":
                btn.setEnabled(enabled)
        self.bitrate_combo.setEnabled(enabled)
        self.format_combo.setEnabled(enabled)
        self.overwrite_checkbox.setEnabled(enabled)
        self.convert_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(not enabled)
    
    def _check_ffmpeg(self) -> bool:
        """Verifica que FFmpeg esté disponible."""
        import subprocess
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            if result.returncode != 0:
                raise Exception("FFmpeg no respondió correctamente")
            return True
        except FileNotFoundError:
            self._show_error(
                "FFmpeg no encontrado",
                "No se encontró FFmpeg en el sistema. Por favor instálalo y asegúrate de que esté en el PATH."
            )
            return False
        except Exception as e:
            self._show_error("Error con FFmpeg", str(e))
            return False
    
    # ========== Implementación de métodos abstractos UIBase ==========
    
    def show(self):
        """Muestra la ventana principal."""
        super().show()
    
    def hide(self):
        """Oculta la ventana principal."""
        super().hide()
    
    def close(self):
        """Cierra la aplicación."""
        if self.is_converting:
            reply = QMessageBox.question(
                self, "Confirmar salida",
                "Hay una conversión en curso. ¿Estás seguro de que deseas salir?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        super().close()
    
    def update_file_status(self, index: int, status: str):
        """Actualiza el estado de un archivo en la tabla."""
        if 0 <= index < self.files_table.rowCount():
            item = self.files_table.item(index, 1)
            if item:
                item.setText(status)
    
    def update_file_progress(self, index: int, progress: float):
        """Actualiza el progreso de un archivo en la tabla."""
        if 0 <= index < self.files_table.rowCount():
            widget = self.files_table.cellWidget(index, 2)
            if isinstance(widget, QProgressBar):
                widget.setValue(int(progress))
    
    def update_file_info(self, index: int, info: str):
        """Actualiza información adicional de un archivo."""
        if 0 <= index < self.files_table.rowCount():
            item = self.files_table.item(index, 3)
            if item:
                item.setText(info)
    
    def set_overall_progress(self, progress: float):
        """Actualiza la barra de progreso general."""
        self.overall_progress_bar.setValue(int(progress))
    
    def log_message(self, message: str):
        """Añade un mensaje al registro."""
        self._log_message(message)
    
    def _log_message(self, message: str):
        """Implementación interna de logging."""
        timestamp = "[{}] ".format(__import__('datetime').datetime.now().strftime("%H:%M:%S"))
        self.log_text_edit.append(timestamp + message)
        logging.info(message)
    
    def show_error(self, title: str, message: str):
        """Muestra un diálogo de error."""
        QMessageBox.critical(self, title, message)
    
    def _show_error(self, title: str, message: str):
        """Alias interno para show_error."""
        self.show_error(title, message)
    
    def show_about(self):
        """Muestra el diálogo 'Acerca de'."""
        about_text = """
        <h2>SonifyLab Pro</h2>
        <p>Versión 1.0.0</p>
        <p>Herramienta profesional de conversión de audio por lotes.</p>
        <p><b>Autor:</b> Discaury Salas</p>
        <p><b>Licencia:</b> GPL-3.0</p>
        <p><b>Repositorio:</b> https://github.com/discodiski/SonifyLab</p>
        <p>Utiliza FFmpeg como motor de conversión.</p>
        """
        QMessageBox.about(self, "Acerca de SonifyLab Pro", about_text)
    
    def set_conversion_mode(self, converting: bool):
        """Cambia entre modo normal y modo conversión."""
        self._set_interface_enabled(not converting)
    
    def get_config(self) -> ConversionConfig:
        """Obtiene la configuración actual de la UI."""
        self.config.output_format = self.format_combo.currentText()
        self.config.bitrate = self.bitrate_combo.currentText()
        self.config.output_folder = self.output_line_edit.text()
        self.config.overwrite = self.overwrite_checkbox.isChecked()
        return self.config
    
    def set_config(self, config: ConversionConfig):
        """Establece la configuración desde código."""
        self.config = config
        if config.output_format in SUPPORTED_FORMATS:
            self.format_combo.setCurrentText(config.output_format)
        if config.bitrate in BITRATE_OPTIONS:
            self.bitrate_combo.setCurrentText(config.bitrate)
        if config.output_folder:
            self.output_line_edit.setText(config.output_folder)
        self.overwrite_checkbox.setChecked(config.overwrite)
    
    def closeEvent(self, event):
        """Maneja el evento de cierre de ventana."""
        if self.is_converting:
            reply = QMessageBox.question(
                self, "Confirmar salida",
                "Hay una conversión en curso. ¿Estás seguro de que deseas salir?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # Detener todas las conversiones
                for worker in self.active_workers:
                    worker.stop()
                for thread in self.active_threads:
                    thread.quit()
                    thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def create_interface(app: QApplication) -> UIBase:
    """Factory function para crear la interfaz PyQt5."""
    return PyQt5Interface(app)


class MainWindow(PyQt5Interface):
    """Alias de compatibilidad para run.py"""
    pass
