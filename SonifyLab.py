import sys
import os
import subprocess
import logging
import json
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QProgressBar,
    QTextEdit, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox,
    QComboBox, QAction, QMenuBar, QLineEdit, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSpacerItem,
    QSizePolicy
)
from PyQt5.QtCore import (
    Qt, QObject, pyqtSlot, QProcess, pyqtSignal, QLocale, QTranslator
)
from PyQt5.QtGui import QIcon

# Configuración del registro
logging.basicConfig(
    filename='conversion.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Lista de formatos soportados
SUPPORTED_FORMATS = [
    "mp3", "wav", "flac", "aac", "ogg", "m4a", "wma", "opus", "aiff", "alac"
]


class ConversionProcess(QObject):
    """
    Clase que maneja la conversión de un archivo utilizando QProcess.
    """
    progress_update = pyqtSignal(int, float)  # Índice, progreso (%)
    status_update = pyqtSignal(int, str)
    error_occurred = pyqtSignal(int, str)
    info_update = pyqtSignal(int, str)  # Información adicional
    finished = pyqtSignal(int, int)  # Índice, código de retorno

    def __init__(self, index, input_file, output_file, bitrate, format):
        super().__init__()
        self.index = index
        self.input_file = input_file
        self.output_file = output_file
        self.bitrate = bitrate
        self.format = format
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
        Inicializa la interfaz de usuario.
        """
        main_layout = QVBoxLayout()

        # Menú
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu(self.tr("&Archivo"))

        add_folder_action = QAction(self.tr("Añadir carpeta"), self)
        add_folder_action.triggered.connect(self.add_folder)
        file_menu.addAction(add_folder_action)

        exit_action = QAction(self.tr("&Salir"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menu_bar.addMenu(self.tr("&Ayuda"))
        about_action = QAction(self.tr("&Acerca de"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Archivos de entrada
        files_label = QLabel(self.tr("Archivos de entrada:"))
        main_layout.addWidget(files_label)

        self.files_table = QTableWidget(0, 4)
        self.files_table.setHorizontalHeaderLabels(
            [self.tr('Archivo'), self.tr('Estado'), self.tr('Progreso'), self.tr('Información')]
        )
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.files_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.files_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.files_table.setSelectionMode(QAbstractItemView.MultiSelection)
        main_layout.addWidget(self.files_table)

        buttons_layout = QHBoxLayout()
        self.add_files_btn = QPushButton(self.tr("Añadir archivos"))
        self.add_files_btn.clicked.connect(self.add_files)
        buttons_layout.addWidget(self.add_files_btn)

        self.remove_files_btn = QPushButton(self.tr("Eliminar archivos"))
        self.remove_files_btn.clicked.connect(self.remove_files)
        buttons_layout.addWidget(self.remove_files_btn)

        self.clear_files_btn = QPushButton(self.tr("Limpiar lista"))
        self.clear_files_btn.clicked.connect(self.clear_files)
        buttons_layout.addWidget(self.clear_files_btn)

        main_layout.addLayout(buttons_layout)

        # Carpeta de salida
        output_layout = QHBoxLayout()
        output_label = QLabel(self.tr("Carpeta de salida:"))
        self.output_line_edit = QLineEdit()
        browse_output_btn = QPushButton(self.tr("Examinar"))
        browse_output_btn.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_line_edit)
        output_layout.addWidget(browse_output_btn)
        main_layout.addLayout(output_layout)

        # Configuración
        config_layout = QHBoxLayout()
        bitrate_label = QLabel(self.tr("Bitrate:"))
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["128k", "192k", "256k", "320k"])
        self.bitrate_combo.setCurrentText("192k")
        config_layout.addWidget(bitrate_label)
        config_layout.addWidget(self.bitrate_combo)

        format_label = QLabel(self.tr("Formato:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(SUPPORTED_FORMATS)
        self.format_combo.setCurrentText("mp3")
        config_layout.addWidget(format_label)
        config_layout.addWidget(self.format_combo)

        main_layout.addLayout(config_layout)

        # Opciones adicionales
        options_layout = QHBoxLayout()
        self.overwrite_checkbox = QCheckBox(self.tr("Sobrescribir archivos existentes"))
        options_layout.addWidget(self.overwrite_checkbox)
        main_layout.addLayout(options_layout)

        # Botones de conversión
        buttons_layout2 = QHBoxLayout()
        self.convert_btn = QPushButton(self.tr("Iniciar Conversión"))
        self.convert_btn.clicked.connect(self.start_conversion)
        buttons_layout2.addWidget(self.convert_btn)

        self.stop_btn = QPushButton(self.tr("Detener"))
        self.stop_btn.clicked.connect(self.stop_conversion)
        self.stop_btn.setEnabled(False)
        buttons_layout2.addWidget(self.stop_btn)

        # Espacio para alinear los botones a la derecha
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        buttons_layout2.addItem(spacer)

        main_layout.addLayout(buttons_layout2)

        # Barra de progreso general
        self.overall_progress_bar = QProgressBar()
        main_layout.addWidget(self.overall_progress_bar)

        # Registro de conversión
        log_label = QLabel(self.tr("Registro de conversión:"))
        main_layout.addWidget(log_label)

        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        main_layout.addWidget(self.log_text_edit)

        # Créditos
        credits_label = QLabel(self.tr("Creado por Discaury Salas"))
        credits_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(credits_label)

        container = QWidget()
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
        Registra la conversión en un archivo JSON.
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "input_files": self.files,
            "output_folder": self.output_folder,
            "output_format": self.format_combo.currentText()
        }
        try:
            with open("conversion_log.json", "a") as log_file:
                json.dump(log_entry, log_file)
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


def main():
    app = QApplication(sys.argv)

    # Configurar la traducción (internacionalización)
    # Si tienes archivos de traducción, puedes cargarlos aquí
    # translator = QTranslator()
    # locale = QLocale.system().name()
    # translator.load("app_" + locale)  # Por ejemplo: app_es.qm
    # app.installTranslator(translator)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
