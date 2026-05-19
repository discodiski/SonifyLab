#!/usr/bin/env python3
"""
SonifyLab Pro - Interfaz GTK4 + Libadwaita
===========================================

Implementación de la interfaz gráfica usando GTK4 y Libadwaita.
Esta interfaz se conecta al core agnóstico para realizar conversiones de audio.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib, GObject, Pango
import threading
import os
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from sonifylab.ui.base import UIBase
from sonifylab.models.file_item import FileItem
from sonifylab.models.conversion_config import ConversionConfig
from sonifylab.core.converter import AudioConverter
from sonifylab.utils.logger import get_logger

logger = get_logger(__name__)


class GTKFileItem(GObject.Object):
    """Modelo de datos para un archivo en la lista (compatible con GTK4)."""
    
    __gtype_name__ = 'GTKFileItem'
    
    def __init__(self, file_item: FileItem):
        super().__init__()
        self._file_item = file_item
        self._status = "En espera"
        self._progress = 0.0
        self._info = ""
    
    @GObject.Property(type=str)
    def name(self) -> str:
        return self._file_item.name
    
    @GObject.Property(type=str)
    def path(self) -> str:
        return self._file_item.path
    
    @GObject.Property(type=str)
    def status(self) -> str:
        return self._status
    
    @status.setter
    def status(self, value: str):
        self._status = value
        self.notify("status")
    
    @GObject.Property(type=float)
    def progress(self) -> float:
        return self._progress
    
    @progress.setter
    def progress(self, value: float):
        self._progress = value
        self.notify("progress")
    
    @GObject.Property(type=str)
    def info(self) -> str:
        return self._info
    
    @info.setter
    def info(self, value: str):
        self._info = value
        self.notify("info")


class WorkerThread(threading.Thread):
    """Hilo de trabajo para ejecutar conversiones sin bloquear la UI."""
    
    def __init__(self, converter: AudioConverter, job_index: int, 
                 output_dir: str, config: ConversionConfig,
                 update_callback, complete_callback):
        super().__init__()
        self.converter = converter
        self.job_index = job_index
        self.output_dir = output_dir
        self.config = config
        self.update_callback = update_callback
        self.complete_callback = complete_callback
        self.daemon = True
    
    def run(self):
        try:
            result = self.converter.convert(
                job_index=self.job_index,
                output_dir=self.output_dir,
                config=self.config
            )
            GLib.idle_add(self.complete_callback, self.job_index, result, None)
        except Exception as e:
            logger.error(f"Error en conversión {self.job_index}: {e}")
            GLib.idle_add(self.complete_callback, self.job_index, None, e)


class GTK4Interface(UIBase):
    """Interfaz gráfica para SonifyLab Pro usando GTK4 + Libadwaita."""
    
    def __init__(self):
        super().__init__()
        self.app: Optional[Adw.Application] = None
        self.window: Optional[Adw.ApplicationWindow] = None
        self.file_list: List[GTKFileItem] = []
        self.list_store: Optional[Gio.ListStore] = None
        self.selection_model: Optional[Gtk.SingleSelection] = None
        self.converter = AudioConverter()
        self.workers: List[WorkerThread] = []
        self.is_converting = False
        
        # Configuración por defecto
        self.current_format = "mp3"
        self.current_bitrate = "192k"
        self.current_sample_rate = "44100"
        self.current_channels = "stereo"
        self.output_dir = str(Path.home())
    
    def setup_ui(self, app: Adw.Application):
        """Configurar la interfaz de usuario principal."""
        self.app = app
        
        # Ventana principal
        self.window = Adw.ApplicationWindow(application=app)
        self.window.set_title("SonifyLab Pro")
        self.window.set_default_size(900, 650)
        
        # Header bar
        header_bar = Adw.HeaderBar()
        header_bar.set_show_end_title_buttons(True)
        
        # Botón de acerca de
        about_button = Gtk.Button()
        about_button.set_icon_name("help-about-symbolic")
        about_button.connect("clicked", self.on_about_clicked)
        header_bar.pack_end(about_button)
        
        self.window.set_titlebar(header_bar)
        
        # Contenedor principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        
        # Panel de configuración
        config_frame = self.create_config_panel()
        main_box.append(config_frame)
        
        # Lista de archivos
        list_frame = self.create_file_list()
        main_box.append(list_frame)
        
        # Barra de acciones
        action_box = self.create_action_bar()
        main_box.append(action_box)
        
        # Barra de estado
        self.status_bar = Gtk.Label(label="Listo")
        self.status_bar.add_css_class("statusbar")
        self.status_bar.set_halign(Gtk.Align.START)
        main_box.append(self.status_bar)
        
        self.window.set_child(main_box)
        
        # Drag and drop
        self.setup_drag_drop()
        
        logger.info("Interfaz GTK4 inicializada correctamente")
    
    def create_config_panel(self) -> Gtk.Widget:
        """Crear el panel de configuración de conversión."""
        frame = Adw.PreferencesGroup()
        frame.set_title("Configuración de Conversión")
        
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(6)
        grid.set_margin_start(6)
        grid.set_margin_end(6)
        grid.set_margin_top(6)
        grid.set_margin_bottom(6)
        
        # Formato
        format_label = Gtk.Label(label="Formato:")
        format_label.set_halign(Gtk.Align.END)
        grid.attach(format_label, 0, 0, 1, 1)
        
        self.format_combo = Gtk.ComboBoxText()
        for fmt in ["mp3", "wav", "flac", "aac", "ogg", "m4a", "wma", "opus", "aiff", "alac"]:
            self.format_combo.append_text(fmt)
        self.format_combo.set_active_id("mp3")
        self.format_combo.connect("changed", self.on_format_changed)
        grid.attach(self.format_combo, 1, 0, 1, 1)
        
        # Bitrate
        bitrate_label = Gtk.Label(label="Bitrate:")
        bitrate_label.set_halign(Gtk.Align.END)
        grid.attach(bitrate_label, 2, 0, 1, 1)
        
        self.bitrate_combo = Gtk.ComboBoxText()
        for br in ["128k", "192k", "256k", "320k"]:
            self.bitrate_combo.append_text(br)
        self.bitrate_combo.set_active_id("192k")
        self.bitrate_combo.connect("changed", self.on_bitrate_changed)
        grid.attach(self.bitrate_combo, 3, 0, 1, 1)
        
        # Sample Rate
        sample_rate_label = Gtk.Label(label="Sample Rate:")
        sample_rate_label.set_halign(Gtk.Align.END)
        grid.attach(sample_rate_label, 0, 1, 1, 1)
        
        self.sample_rate_combo = Gtk.ComboBoxText()
        for sr in ["22050", "44100", "48000", "96000"]:
            self.sample_rate_combo.append_text(sr)
        self.sample_rate_combo.set_active_id("44100")
        self.sample_rate_combo.connect("changed", self.on_sample_rate_changed)
        grid.attach(self.sample_rate_combo, 1, 1, 1, 1)
        
        # Canales
        channels_label = Gtk.Label(label="Canales:")
        channels_label.set_halign(Gtk.Align.END)
        grid.attach(channels_label, 2, 1, 1, 1)
        
        self.channels_combo = Gtk.ComboBoxText()
        for ch in ["mono", "stereo"]:
            self.channels_combo.append_text(ch)
        self.channels_combo.set_active_id("stereo")
        self.channels_combo.connect("changed", self.on_channels_changed)
        grid.attach(self.channels_combo, 3, 1, 1, 1)
        
        # Directorio de salida
        dir_label = Gtk.Label(label="Salida:")
        dir_label.set_halign(Gtk.Align.END)
        grid.attach(dir_label, 0, 2, 1, 1)
        
        dir_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.dir_entry = Gtk.Entry()
        self.dir_entry.set_text(str(Path.home()))
        self.dir_entry.set_hexpand(True)
        self.dir_entry.set_editable(False)
        dir_box.append(self.dir_entry)
        
        dir_button = Gtk.Button()
        dir_button.set_label("Examinar...")
        dir_button.connect("clicked", self.on_select_output_dir)
        dir_box.append(dir_button)
        
        grid.attach(dir_box, 1, 2, 3, 1)
        
        frame.add(grid)
        return frame
    
    def create_file_list(self) -> Gtk.Widget:
        """Crear la lista de archivos para convertir."""
        frame = Adw.PreferencesGroup()
        frame.set_title("Archivos para Convertir")
        frame.set_description("Arrastra archivos aquí o usa los botones para agregar")
        
        # ListStore y SelectionModel
        self.list_store = Gio.ListStore(item_type=GTKFileItem)
        self.file_list = []
        
        self.selection_model = Gtk.SingleSelection(model=self.list_store)
        
        # ListView
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.on_list_setup)
        factory.connect("bind", self.on_list_bind)
        
        list_view = Gtk.ListView(
            model=self.selection_model,
            factory=factory
        )
        list_view.set_vexpand(True)
        
        # ScrolledWindow
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)
        scrolled.set_child(list_view)
        
        frame.add(scrolled)
        return frame
    
    def on_list_setup(self, factory, list_item):
        """Configurar cada elemento de la lista."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(6)
        box.set_margin_end(6)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        
        # Icono
        icon = Gtk.Image.new_from_icon_name("audio-x-generic")
        icon.set_pixel_size(32)
        box.append(icon)
        
        # Información del archivo
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)
        
        name_label = Gtk.Label()
        name_label.set_halign(Gtk.Align.START)
        name_label.add_css_class("heading")
        info_box.append(name_label)
        
        status_label = Gtk.Label()
        status_label.set_halign(Gtk.Align.START)
        status_label.add_css_class("dim-label")
        info_box.append(status_label)
        
        box.append(info_box)
        
        # Progress bar
        progress = Gtk.ProgressBar()
        progress.set_valign(Gtk.Align.CENTER)
        box.append(progress)
        
        # Botón eliminar
        remove_button = Gtk.Button()
        remove_button.set_icon_name("list-remove-symbolic")
        remove_button.add_css_class("circular")
        remove_button.add_css_class("destructive-action")
        box.append(remove_button)
        
        list_item.set_child(box)
        
        # Guardar referencias
        list_item.data = {
            "name_label": name_label,
            "status_label": status_label,
            "progress": progress,
            "remove_button": remove_button
        }
    
    def on_list_bind(self, factory, list_item):
        """Vincular datos a cada elemento de la lista."""
        data = list_item.data
        item = list_item.get_item()
        
        data["name_label"].set_text(item.name)
        data["status_label"].set_text(f"{item.status} - {item.info}" if item.info else item.status)
        data["progress"].set_fraction(item.progress / 100.0)
        
        # Conectar botón eliminar
        def on_remove_clicked(_):
            self.remove_file(list_item.get_position())
        
        data["remove_button"].connect("clicked", on_remove_clicked)
    
    def create_action_bar(self) -> Gtk.Widget:
        """Crear la barra de acciones."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_halign(Gtk.Align.CENTER)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # Botón agregar
        add_button = Gtk.Button()
        add_button.set_label("Agregar Archivos")
        add_button.add_css_class("suggested-action")
        add_button.connect("clicked", self.on_add_files)
        box.append(add_button)
        
        # Botón convertir
        self.convert_button = Gtk.Button()
        self.convert_button.set_label("Convertir")
        self.convert_button.add_css_class("suggested-action")
        self.convert_button.connect("clicked", self.on_convert)
        box.append(self.convert_button)
        
        # Botón limpiar
        clear_button = Gtk.Button()
        clear_button.set_label("Limpiar Lista")
        clear_button.connect("clicked", self.on_clear_list)
        box.append(clear_button)
        
        return box
    
    def setup_drag_drop(self):
        """Configurar drag and drop para archivos."""
        drop_target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_drop)
        self.window.add_controller(drop_target)
    
    def on_drop(self, target, value, x, y):
        """Manejar archivo soltado."""
        if isinstance(value, Gio.File):
            path = value.get_path()
            if path and self.validate_file(path):
                self.add_file(path)
                return True
        return False
    
    # Métodos de eventos
    def on_format_changed(self, combo):
        self.current_format = combo.get_active_text()
        logger.debug(f"Formato cambiado a: {self.current_format}")
    
    def on_bitrate_changed(self, combo):
        self.current_bitrate = combo.get_active_text()
        logger.debug(f"Bitrate cambiado a: {self.current_bitrate}")
    
    def on_sample_rate_changed(self, combo):
        self.current_sample_rate = combo.get_active_text()
        logger.debug(f"Sample rate cambiado a: {self.current_sample_rate}")
    
    def on_channels_changed(self, combo):
        self.current_channels = combo.get_active_text()
        logger.debug(f"Canales cambiados a: {self.current_channels}")
    
    def on_select_output_dir(self, button):
        """Seleccionar directorio de salida."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Seleccionar Directorio de Salida")
        dialog.set_action(Gtk.FileDialogAction.SELECT_FOLDER)
        
        def on_response(dialog, result):
            try:
                folder = dialog.select_folder_finish(result)
                if folder:
                    path = folder.get_path()
                    self.output_dir = path
                    self.dir_entry.set_text(path)
                    self.update_status(f"Directorio de salida: {path}")
            except Exception as e:
                logger.error(f"Error al seleccionar directorio: {e}")
        
        dialog.select_folder(self.window, None, on_response)
    
    def on_add_files(self, button):
        """Agregar archivos mediante selector."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Seleccionar Archivos de Audio")
        dialog.set_modal(True)
        
        # Filtros
        filter_audio = Gtk.FileFilter()
        filter_audio.set_name("Archivos de Audio")
        for fmt in ["mp3", "wav", "flac", "aac", "ogg", "m4a", "wma", "opus", "aiff", "alac"]:
            filter_audio.add_pattern(f"*.{fmt}")
        filter_audio.add_pattern("*.[A-Z][A-Z][A-Z]")
        dialog.set_filter(filter_audio)
        
        def on_response(dialog, result):
            try:
                files = dialog.open_multiple_finish(result)
                if files:
                    for file in files:
                        path = file.get_path()
                        if path and self.validate_file(path):
                            self.add_file(path)
            except Exception as e:
                logger.error(f"Error al seleccionar archivos: {e}")
        
        dialog.open_multiple(self.window, None, on_response)
    
    def on_convert(self, button):
        """Iniciar conversión."""
        if not self.file_list:
            self.show_error("No hay archivos en la lista")
            return
        
        if self.is_converting:
            self.show_error("Ya hay una conversión en progreso")
            return
        
        self.is_converting = True
        self.convert_button.set_sensitive(False)
        self.update_status("Iniciando conversión...")
        
        config = ConversionConfig(
            target_format=self.current_format,
            bitrate=self.current_bitrate,
            sample_rate=int(self.current_sample_rate),
            channels=self.current_channels
        )
        
        # Iniciar conversiones en hilos separados
        for i, file_item in enumerate(self.file_list):
            worker = WorkerThread(
                converter=self.converter,
                job_index=i,
                output_dir=self.output_dir,
                config=config,
                update_callback=self.on_conversion_update,
                complete_callback=self.on_conversion_complete
            )
            self.workers.append(worker)
            worker.start()
        
        logger.info(f"Iniciadas {len(self.file_list)} conversiones")
    
    def on_conversion_update(self, job_index: int, progress: float, status: str):
        """Actualizar progreso de conversión (llamado desde el hilo)."""
        if 0 <= job_index < len(self.file_list):
            item = self.file_list[job_index]
            item.progress = progress
            item.status = status
            self.list_store.changed(job_index)
    
    def on_conversion_complete(self, job_index: int, result, error):
        """Completar conversión (llamado desde el hilo)."""
        if 0 <= job_index < len(self.file_list):
            item = self.file_list[job_index]
            
            if error:
                item.status = "Error"
                item.info = str(error)
                item.progress = 0
                logger.error(f"Conversión {job_index} falló: {error}")
            elif result:
                item.status = "Completado"
                item.info = f"→ {Path(result.output_file).name}"
                item.progress = 100
                logger.info(f"Conversión {job_index} completada: {result.output_file}")
            
            self.list_store.changed(job_index)
        
        # Verificar si todas terminaron
        all_done = all(
            w.is_alive() == False for w in self.workers
        )
        
        if all_done:
            self.is_converting = False
            self.convert_button.set_sensitive(True)
            completed = sum(1 for item in self.file_list if item.status == "Completado")
            self.update_status(f"Conversión finalizada: {completed}/{len(self.file_list)} completados")
            self.workers.clear()
    
    def on_clear_list(self, button):
        """Limpiar lista de archivos."""
        if self.is_converting:
            self.show_error("No se puede limpiar mientras se convierte")
            return
        
        self.file_list.clear()
        self.list_store.remove_all()
        self.update_status("Lista limpiada")
    
    def on_about_clicked(self, button):
        """Mostrar diálogo Acerca de."""
        about = Adw.AboutWindow(
            application_name="SonifyLab Pro",
            application_icon="audio-x-generic",
            version="2.0.0",
            developers=["Discaury Salas"],
            copyright="© 2024 Discaury Salas",
            license_type=Gtk.License.GPL_3_0,
            website="https://github.com/discodiski/SonifyLab"
        )
        about.set_transient_for(self.window)
        about.present()
    
    # Implementación de métodos abstractos de UIBase
    def validate_file(self, file_path: str) -> bool:
        """Validar que el archivo exista y sea legible."""
        path = Path(file_path)
        if not path.exists():
            self.show_error(f"El archivo no existe: {file_path}")
            return False
        if not path.is_file():
            self.show_error(f"No es un archivo: {file_path}")
            return False
        if not os.access(file_path, os.R_OK):
            self.show_error(f"No tiene permisos de lectura: {file_path}")
            return False
        return True
    
    def add_file(self, file_path: str):
        """Agregar un archivo a la lista."""
        path = Path(file_path)
        file_item = FileItem(path=str(path), name=path.name)
        gtk_item = GTKFileItem(file_item)
        
        self.file_list.append(gtk_item)
        self.list_store.append(gtk_item)
        self.update_status(f"Agregado: {path.name}")
        logger.debug(f"Archivo agregado: {file_path}")
    
    def remove_file(self, index: int):
        """Eliminar un archivo de la lista."""
        if self.is_converting:
            self.show_error("No se puede eliminar mientras se convierte")
            return
        
        if 0 <= index < len(self.file_list):
            item = self.file_list.pop(index)
            self.list_store.remove(index)
            self.update_status(f"Eliminado: {item.name}")
            logger.debug(f"Archivo eliminado: {item.name}")
    
    def update_status(self, message: str):
        """Actualizar la barra de estado."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_bar.set_text(f"[{timestamp}] {message}")
        logger.info(f"Status: {message}")
    
    def show_error(self, message: str):
        """Mostrar mensaje de error."""
        dialog = Adw.MessageDialog(
            transient_for=self.window,
            heading="Error",
            body=message
        )
        dialog.add_response("ok", "Aceptar")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        dialog.present()
        logger.error(f"Error mostrado: {message}")
    
    def show_success(self, message: str):
        """Mostrar mensaje de éxito."""
        dialog = Adw.MessageDialog(
            transient_for=self.window,
            heading="Éxito",
            body=message
        )
        dialog.add_response("ok", "Aceptar")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        dialog.present()
        logger.info(f"Éxito: {message}")
    
    def run(self):
        """Ejecutar la aplicación."""
        self.app = Adw.Application(
            application_id="com.discodiski.sonifylab",
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.app.connect("activate", self.on_app_activate)
        
        exit_code = self.app.run(sys.argv)
        return exit_code
    
    def on_app_activate(self, app):
        """Activar la aplicación."""
        self.setup_ui(app)
        self.window.present()
        self.update_status("SonifyLab Pro listo")
        logger.info("Aplicación GTK4 activada")


class SonifyLabApp(GTK4Interface):
    """Alias de compatibilidad para run.py"""
    pass
