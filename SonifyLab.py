"""
SonifyLab Pro - Herramienta de conversión de audio por lotes
=============================================================

Una aplicación de escritorio profesional para convertir archivos de audio
entre múltiples formatos utilizando FFmpeg como motor de conversión.

Autor: Discaury Salas
Licencia: GPL-3.0
Repositorio: https://github.com/discodiski/SonifyLab
"""

from __future__ import annotations

import sys
import os
import subprocess
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QProgressBar,
    QTextEdit, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox,
    QComboBox, QAction, QLineEdit, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSpacerItem,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QObject, pyqtSlot, QProcess, pyqtSignal
from PyQt5.QtGui import QIcon

# Información de la aplicación
__version__ = "1.0.0"
__author__ = "Discaury Salas"
__app_name__ = "SonifyLab Pro"

# Directorio de la aplicación (para logs y configuración)
APP_DIR: Path = Path(__file__).parent.resolve()
LOG_FILE: Path = APP_DIR / 'conversion.log'
CONVERSION_LOG: Path = APP_DIR / 'conversion_history.jsonl'

# Configuración del registro
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Lista de formatos soportados
SUPPORTED_FORMATS: List[str] = [
    "mp3", "wav", "flac", "aac", "ogg", "m4a", "wma", "opus", "aiff", "alac"
]

# Opciones de bitrate disponibles
BITRATE_OPTIONS: List[str] = ["128k", "192k", "256k", "320k"]


class ConversionProcess(QObject):
    """
    Clase que maneja la conversión de un archivo utilizando QProcess.
    
    Attributes:
        index: Índice del archivo en la lista de conversión
        input_file: Ruta al archivo de entrada
        output_file: Ruta al archivo de salida
        bitrate: Bitrate de salida (ej: '192k')
        output_format: Formato de salida (ej: 'mp3')
    """
    
    # Señales Qt para comunicación con la interfaz
    progress_update = pyqtSignal(int, float)  # Índice, progreso (%)
    status_update = pyqtSignal(int, str)       # Índice, estado
    error_occurred = pyqtSignal(int, str)      # Índice, mensaje de error
    info_update = pyqtSignal(int, str)         # Índice, información adicional
    finished = pyqtSignal(int, int)            # Índice, código de retorno

    def __init__(
        self, 
        index: int, 
        input_file: str, 
        output_file: str, 
        bitrate: str, 
        output_format: str
    ) -> None:
        super().__init__()
        self.index: int = index
        self.input_file: str = input_file
        self.output_file: str = output_file
        self.bitrate: str = bitrate
        self.output_format: str = output_format
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.process_finished)
        self.duration = self.get_duration()
        self.start_time = None

    def start(self):
        command = [
            '-i', self.input_file,
            '-b:a', self.bitrate,
            '-progress', 'pipe:1',
            '-y', self.output_file
        ]
        self.process.start('ffmpeg', command)
        self.status_update.emit(self.index, "En proceso")
        self.start_time = datetime.now()

    def read_output(self):
        while self.process.canReadLine():
            line = self.process.readLine().data().decode().strip()
            self.parse_progress(line)

    def parse_progress(self, line):
        if line.startswith('out_time='):
            out_time_str = line.split('=')[1]
            out_time = self.ffmpeg_time_to_seconds(out_time_str)
            if self.duration > 0:
                progress = (out_time / self.duration) * 100
                self.progress_update.emit(self.index, progress)
                # Calcular velocidad y tiempo restante
                elapsed_time = (datetime.now() - self.start_time).total_seconds()
                speed = out_time / elapsed_time if elapsed_time > 0 else 0
                remaining_time = (self.duration - out_time) / speed if speed > 0 else 0
                info = f"Velocidad: {speed:.2f}x, Restante: {self.format_time(remaining_time)}"
                self.info_update.emit(self.index, info)
        elif line.startswith('progress='):
            if line.split('=')[1] == 'end':
                self.progress_update.emit(self.index, 100)
                self.info_update.emit(self.index, "Conversión completada")

    def ffmpeg_time_to_seconds(self, time_str):
        try:
            if '.' in time_str:
                hms, ms = time_str.split('.')
                ms = float('0.' + ms)
            else:
                hms = time_str
                ms = 0
            h, m, s = map(int, hms.split(':'))
            total_seconds = h * 3600 + m * 60 + s + ms
            return total_seconds
        except ValueError:
            return 0

    def format_time(self, seconds):
        return str(timedelta(seconds=int(seconds)))

    def process_finished(self):
        return_code = self.process.exitCode()
        if return_code == 0:
            self.status_update.emit(self.index, "Completado")
            self.progress_update.emit(self.index, 100)
        else:
            self.status_update.emit(self.index, "Error")
            error_message = self.process.readAllStandardError().data().decode('utf-8')
            self.error_occurred.emit(self.index, error_message)
        self.finished.emit(self.index, return_code)

    def get_duration(self):
        """
        Obtiene la duración del archivo de entrada en segundos.
        """
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', self.input_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            duration = float(result.stdout.strip())
            return duration
        except Exception as e:
            logging.error(f"Error al obtener la duración del archivo: {e}")
            return 0


class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SonifyLab Pro")
        self.resize(800, 700)

        # Obtener la ruta del icono
        if getattr(sys, 'frozen', False):
            # Si está empaquetado como ejecutable
            bundle_dir = sys._MEIPASS
        else:
            # Si se ejecuta como script
            bundle_dir = os.path.dirname(os.path.abspath(__file__))

        icon_path = os.path.join(bundle_dir, "icono.png")
        self.setWindowIcon(QIcon(icon_path))

        self.files = []
        self.output_folder = ''
        self.bitrate = '192k'
        self.format = 'mp3'
        self.overwrite = False
        self.is_converting = False
        self.active_processes = []
        self.conversion_queue = []
        self.max_concurrent_processes = max(1, os.cpu_count() - 1)
        self.total_files = 0
        self.completed_files = 0
        self.failed_files = []

        self.init_ui()

    def init_ui(self):
        """
        Inicializa la interfaz de usuario con diseño moderno.
        """
        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ========== MENÚ ==========
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu(self.tr("&Archivo"))

        add_folder_action = QAction(self.tr("📁 Añadir carpeta"), self)
        add_folder_action.setShortcut("Ctrl+Shift+O")
        add_folder_action.triggered.connect(self.add_folder)
        file_menu.addAction(add_folder_action)

        file_menu.addSeparator()

        exit_action = QAction(self.tr("❌ Salir"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menu_bar.addMenu(self.tr("&Ayuda"))
        about_action = QAction(self.tr("ℹ️ Acerca de"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # ========== SECCIÓN: ARCHIVOS DE ENTRADA ==========
        files_label = QLabel(self.tr("📂 Archivos de entrada"))
        files_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B;")
        main_layout.addWidget(files_label)

        # Tabla de archivos
        self.files_table = QTableWidget(0, 4)
        self.files_table.setHorizontalHeaderLabels(
            [self.tr('Archivo'), self.tr('Estado'), self.tr('Progreso'), self.tr('Información')]
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
        
        self.add_files_btn = QPushButton(self.tr("Añadir archivos"))
        self.add_files_btn.setToolTip("Seleccionar archivos de audio para convertir (Ctrl+O)")
        self.add_files_btn.setShortcut("Ctrl+O")
        self.add_files_btn.clicked.connect(self.add_files)
        buttons_layout.addWidget(self.add_files_btn)

        self.remove_files_btn = QPushButton(self.tr("Eliminar archivos"))
        self.remove_files_btn.setToolTip("Eliminar archivos seleccionados de la lista")
        self.remove_files_btn.clicked.connect(self.remove_files)
        buttons_layout.addWidget(self.remove_files_btn)

        self.clear_files_btn = QPushButton(self.tr("Limpiar lista"))
        self.clear_files_btn.setToolTip("Eliminar todos los archivos de la lista")
        self.clear_files_btn.clicked.connect(self.clear_files)
        buttons_layout.addWidget(self.clear_files_btn)

        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        # ========== SECCIÓN: CONFIGURACIÓN ==========
        config_label = QLabel(self.tr("⚙️ Configuración"))
        config_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; margin-top: 10px;")
        main_layout.addWidget(config_label)

        # Carpeta de salida
        output_layout = QHBoxLayout()
        output_layout.setSpacing(10)
        output_label = QLabel(self.tr("Carpeta de salida:"))
        output_label.setMinimumWidth(120)
        self.output_line_edit = QLineEdit()
        self.output_line_edit.setPlaceholderText("Selecciona una carpeta donde guardar los archivos convertidos...")
        browse_output_btn = QPushButton(self.tr("Examinar"))
        browse_output_btn.setToolTip("Seleccionar carpeta de destino")
        browse_output_btn.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_line_edit)
        output_layout.addWidget(browse_output_btn)
        main_layout.addLayout(output_layout)

        # Bitrate y Formato
        config_layout = QHBoxLayout()
        config_layout.setSpacing(20)
        
        bitrate_label = QLabel(self.tr("Bitrate:"))
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(BITRATE_OPTIONS)
        self.bitrate_combo.setCurrentText("192k")
        self.bitrate_combo.setToolTip("Calidad del audio de salida (mayor = mejor calidad, más tamaño)")
        config_layout.addWidget(bitrate_label)
        config_layout.addWidget(self.bitrate_combo)

        config_layout.addSpacing(30)

        format_label = QLabel(self.tr("Formato:"))
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
        self.overwrite_checkbox = QCheckBox(self.tr("Sobrescribir archivos existentes"))
        self.overwrite_checkbox.setToolTip("Si está marcado, reemplazará archivos con el mismo nombre")
        options_layout.addWidget(self.overwrite_checkbox)
        options_layout.addStretch()
        main_layout.addLayout(options_layout)

        # ========== SECCIÓN: CONVERSIÓN ==========
        conversion_label = QLabel(self.tr("🚀 Conversión"))
        conversion_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; margin-top: 10px;")
        main_layout.addWidget(conversion_label)

        # Botones de conversión
        buttons_layout2 = QHBoxLayout()
        buttons_layout2.setSpacing(12)
        
        self.convert_btn = QPushButton(self.tr("Iniciar Conversión"))
        self.convert_btn.setToolTip("Comenzar la conversión de todos los archivos (Ctrl+Enter)")
        self.convert_btn.setShortcut("Ctrl+Return")
        self.convert_btn.clicked.connect(self.start_conversion)
        self.convert_btn.setMinimumHeight(45)
        buttons_layout2.addWidget(self.convert_btn)

        self.stop_btn = QPushButton(self.tr("Detener"))
        self.stop_btn.setToolTip("Detener la conversión en curso (Escape)")
        self.stop_btn.setShortcut("Escape")
        self.stop_btn.clicked.connect(self.stop_conversion)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(45)
        buttons_layout2.addWidget(self.stop_btn)

        buttons_layout2.addStretch()
        main_layout.addLayout(buttons_layout2)

        # Barra de progreso general
        progress_layout = QHBoxLayout()
        progress_label = QLabel(self.tr("Progreso total:"))
        progress_label.setMinimumWidth(100)
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setMinimumHeight(20)
        self.overall_progress_bar.setTextVisible(True)
        self.overall_progress_bar.setFormat("%p%")
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.overall_progress_bar)
        main_layout.addLayout(progress_layout)

        # ========== SECCIÓN: REGISTRO ==========
        log_label = QLabel(self.tr("📋 Registro de conversión"))
        log_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; margin-top: 10px;")
        main_layout.addWidget(log_label)

        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setMaximumHeight(120)
        self.log_text_edit.setPlaceholderText("Los mensajes de conversión aparecerán aquí...")
        main_layout.addWidget(self.log_text_edit)

        # ========== CRÉDITOS ==========
        credits_label = QLabel(self.tr(f"✨ {__app_name__} v{__version__} — Creado por {__author__}"))
        credits_label.setAlignment(Qt.AlignCenter)
        credits_label.setStyleSheet("color: #64748B; font-size: 12px; padding: 10px;")
        main_layout.addWidget(credits_label)

        # Contenedor principal
        container = QWidget()
        container.setObjectName("centralwidget")
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def add_files(self):
        """
        Añade archivos a la lista de conversión.
        """
        files, _ = QFileDialog.getOpenFileNames(
            self, self.tr("Selecciona archivos de entrada"), "",
            self.tr("Archivos de audio ({0})").format(' '.join(['*.' + ext for ext in SUPPORTED_FORMATS]))
        )
        if files:
            for file in files:
                if file not in self.files and self.is_valid_file(file):
                    self.files.append(file)
                    self.add_file_to_table(file)

    def add_file_to_table(self, file_path):
        row_position = self.files_table.rowCount()
        self.files_table.insertRow(row_position)
        file_item = QTableWidgetItem(os.path.basename(file_path))
        status_item = QTableWidgetItem(self.tr("En espera"))
        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        info_item = QTableWidgetItem("")
        self.files_table.setItem(row_position, 0, file_item)
        self.files_table.setItem(row_position, 1, status_item)
        self.files_table.setCellWidget(row_position, 2, progress_bar)
        self.files_table.setItem(row_position, 3, info_item)

    def add_folder(self):
        """
        Añade todos los archivos de audio de una carpeta a la lista.
        """
        folder = QFileDialog.getExistingDirectory(self, self.tr("Selecciona carpeta"))
        if folder:
            added_files = 0
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(tuple(SUPPORTED_FORMATS)):
                        full_path = os.path.join(root, file)
                        if full_path not in self.files and self.is_valid_file(full_path):
                            self.files.append(full_path)
                            self.add_file_to_table(full_path)
                            added_files += 1
            if added_files > 0:
                QMessageBox.information(
                    self, self.tr("Información"),
                    self.tr("Se añadieron {0} archivos desde la carpeta seleccionada.").format(added_files)
                )
            else:
                QMessageBox.information(
                    self, self.tr("Información"),
                    self.tr("No se encontraron archivos de audio en la carpeta seleccionada.")
                )

    def remove_files(self):
        """
        Elimina los archivos seleccionados de la lista.
        """
        selected_rows = self.files_table.selectionModel().selectedRows()
        for row in sorted(selected_rows, key=lambda x: x.row(), reverse=True):
            self.files.pop(row.row())
            self.files_table.removeRow(row.row())

    def clear_files(self):
        """
        Limpia la lista de archivos.
        """
        self.files.clear()
        self.files_table.setRowCount(0)

    def browse_output_folder(self):
        """
        Permite seleccionar la carpeta de salida.
        """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Selecciona carpeta de salida")
        )
        if folder:
            self.output_folder = folder
            self.output_line_edit.setText(folder)

    def is_valid_file(self, file_path):
        """
        Verifica si el archivo es válido utilizando ffprobe.
        """
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_streams',
                 '-select_streams', 'a', file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.stdout:
                return True
            else:
                logging.warning(f"El archivo {file_path} no es válido o está corrupto.")
                return False
        except Exception as e:
            logging.error(f"Error al validar el archivo {file_path}: {e}")
            return False

    def start_conversion(self):
        """
        Inicia el proceso de conversión.
        """
        if self.is_converting:
            QMessageBox.warning(
                self, self.tr("Advertencia"),
                self.tr("La conversión ya está en curso.")
            )
            return
        if not self.validate_inputs():
            return
        self.is_converting = True
        self.convert_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.set_interface_enabled(False)
        self.failed_files = []
        self.completed_files = 0
        self.total_files = len(self.files)
        self.active_processes = []
        self.conversion_queue = []
        self.overall_progress_bar.setValue(0)
        self.log_text_edit.clear()

        for index, input_file in enumerate(self.files):
            output_file = os.path.join(
                self.output_folder,
                os.path.splitext(os.path.basename(input_file))[0]
                + "." + self.format_combo.currentText()
            )
            if os.path.exists(output_file) and not self.overwrite_checkbox.isChecked():
                self.update_status(index, self.tr("Omitido"))
                self.update_progress(index, 100)
                continue
            process = ConversionProcess(
                index, input_file, output_file, self.bitrate_combo.currentText(),
                self.format_combo.currentText()
            )
            process.status_update.connect(self.update_status)
            process.error_occurred.connect(self.handle_error)
            process.progress_update.connect(self.update_progress)
            process.info_update.connect(self.update_info)
            process.finished.connect(self.process_finished)
            self.conversion_queue.append(process)
        self.start_next_processes()

    def start_next_processes(self):
        """
        Inicia los siguientes procesos de conversión si hay capacidad.
        """
        while (len(self.active_processes) < self.max_concurrent_processes and
               self.conversion_queue):
            process = self.conversion_queue.pop(0)
            self.active_processes.append(process)
            process.start()

    def validate_inputs(self):
        """
        Valida que los datos de entrada sean correctos.
        """
        if not self.files:
            QMessageBox.warning(
                self, self.tr("Advertencia"),
                self.tr("No has seleccionado archivos de entrada.")
            )
            return False
        if not self.output_line_edit.text():
            QMessageBox.warning(
                self, self.tr("Advertencia"),
                self.tr("No has seleccionado una carpeta de salida.")
            )
            return False
        if not os.path.exists(self.output_line_edit.text()):
            QMessageBox.warning(
                self, self.tr("Advertencia"),
                self.tr("La carpeta de salida no existe.")
            )
            return False
        self.output_folder = self.output_line_edit.text()
        if not self.check_ffmpeg():
            QMessageBox.critical(
                self, self.tr("Error"),
                self.tr("ffmpeg no está instalado o no se encuentra en el PATH del sistema.")
            )
            return False
        return True

    def check_ffmpeg(self):
        """
        Verifica si ffmpeg está instalado y accesible.
        """
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except FileNotFoundError:
            return False

    @pyqtSlot(int, str)
    def update_status(self, index, status):
        """
        Actualiza el estado de un archivo en la tabla.
        """
        self.files_table.item(index, 1).setText(status)

    @pyqtSlot(int, str)
    def update_info(self, index, info):
        """
        Actualiza la información adicional (velocidad, tiempo restante).
        """
        self.files_table.item(index, 3).setText(info)

    @pyqtSlot(int, float)
    def update_progress(self, index, progress):
        """
        Actualiza la barra de progreso individual de un archivo.
        """
        progress_bar = self.files_table.cellWidget(index, 2)
        progress_bar.setValue(int(progress))

    @pyqtSlot(int, str)
    def handle_error(self, index, error_message):
        """
        Maneja errores ocurridos durante la conversión.
        """
        logging.error(error_message)
        self.log_text_edit.append(f"ERROR: {error_message}")
        self.log_text_edit.ensureCursorVisible()
        self.failed_files.append(self.files[index])
        self.update_status(index, self.tr("Error"))

    @pyqtSlot(int, int)
    def process_finished(self, index, return_code):
        """
        Maneja la finalización de un proceso de conversión.
        """
        self.completed_files += 1
        progress = int((self.completed_files / self.total_files) * 100)
        self.overall_progress_bar.setValue(progress)
        # Remover el proceso de la lista activa
        for p in self.active_processes:
            if p.index == index:
                self.active_processes.remove(p)
                break
        # Iniciar el siguiente proceso si hay alguno en cola
        self.start_next_processes()
        if self.completed_files == self.total_files:
            self.is_converting = False
            self.set_interface_enabled(True)
            self.convert_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.log_conversion()
            if self.failed_files:
                failed_files_names = ', '.join(
                    [os.path.basename(f) for f in self.failed_files]
                )
                QMessageBox.warning(
                    self, self.tr("Advertencia"),
                    self.tr("Algunos archivos no se pudieron convertir:\n{0}").format(
                        failed_files_names
                    )
                )
            else:
                QMessageBox.information(
                    self, self.tr("Información"),
                    self.tr("Conversión completada exitosamente.")
                )

    def stop_conversion(self):
        """
        Detiene el proceso de conversión.
        """
        for process in self.active_processes:
            if process.process.state() != QProcess.NotRunning:
                process.process.kill()
        self.conversion_queue.clear()
        self.is_converting = False
        self.set_interface_enabled(True)
        self.convert_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        QMessageBox.information(
            self, self.tr("Información"), self.tr("Conversión detenida por el usuario.")
        )

    def set_interface_enabled(self, enabled):
        """
        Habilita o deshabilita elementos de la interfaz.
        """
        self.files_table.setEnabled(enabled)
        self.output_line_edit.setEnabled(enabled)
        self.bitrate_combo.setEnabled(enabled)
        self.format_combo.setEnabled(enabled)
        self.overwrite_checkbox.setEnabled(enabled)
        self.add_files_btn.setEnabled(enabled)
        self.remove_files_btn.setEnabled(enabled)
        self.clear_files_btn.setEnabled(enabled)

    def log_conversion(self):
        """
        Registra la conversión en un archivo JSONL (JSON Lines).
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "input_files": self.files,
            "output_folder": self.output_folder,
            "output_format": self.format_combo.currentText(),
            "total_files": self.total_files,
            "failed_files": [os.path.basename(f) for f in self.failed_files]
        }
        try:
            with open(CONVERSION_LOG, "a", encoding="utf-8") as log_file:
                json.dump(log_entry, log_file, ensure_ascii=False)
                log_file.write("\n")
        except Exception as e:
            logging.error(f"Error al escribir el archivo de registro: {e}")

        self.log_text_edit.append(self.tr("Conversión completada."))

    def show_about(self):
        """
        Muestra información acerca de la aplicación.
        """
        QMessageBox.information(
            self, self.tr("Acerca de"),
            self.tr("SonifyLab Pro\nHerramienta de conversión de audio.\n\n"
                    "Creado por Discaury Salas.")
        )

    def closeEvent(self, event):
        """
        Maneja el evento de cerrar la aplicación.
        """
        if self.is_converting:
            result = QMessageBox.question(
                self, self.tr("Salir"),
                self.tr("Hay una conversión en curso. ¿Deseas salir de todos modos?"),
                QMessageBox.Yes | QMessageBox.No
            )
            if result == QMessageBox.Yes:
                self.stop_conversion()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def load_stylesheet() -> str:
    """Carga el archivo de estilos QSS."""
    style_path = APP_DIR / 'style.qss'
    if style_path.exists():
        with open(style_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def main():
    """Punto de entrada principal de la aplicación."""
    # Configurar la aplicación
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Discaury Salas")
    
    # Cargar estilos personalizados
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
    
    # Crear y mostrar la ventana principal
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
